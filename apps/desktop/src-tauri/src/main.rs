#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
mod projects;
use projects::Project;
use serde::Serialize;
use std::{
    path::{Path, PathBuf},
    sync::Mutex,
};
use storyboard_core::{Story, Theme};
use tauri::{Emitter, Manager, State};
use tauri_plugin_dialog::DialogExt;
#[derive(Default)]
struct Session {
    asset_root: Mutex<Option<PathBuf>>,
    allowed_drops: Mutex<Vec<PathBuf>>,
}
#[derive(Serialize)]
struct Review {
    story: Story,
    theme: Theme,
    layout: storyboard_core::LayoutDeck,
    diagnostics: storyboard_core::Report,
    previews: Vec<String>,
}
fn review(story: Story, theme: Theme, root: &Path) -> Result<Review, String> {
    let layout = storyboard_core::resolve(&story, &theme).map_err(|e| e.to_string())?;
    let previews = (0..layout.slides.len())
        .map(|i| storyboard_pptx::preview::svg(&layout, i, root).map_err(|e| e.to_string()))
        .collect::<Result<Vec<_>, _>>()?;
    let diagnostics = storyboard_core::diagnose(&story);
    Ok(Review {
        story,
        theme,
        layout,
        diagnostics,
        previews,
    })
}
fn root(session: &Session) -> Result<PathBuf, String> {
    Ok(session
        .asset_root
        .lock()
        .map_err(|_| "Asset session unavailable")?
        .clone()
        .unwrap_or(std::env::temp_dir()))
}
fn storage(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    Ok(app
        .path()
        .app_data_dir()
        .map_err(|e| e.to_string())?
        .join("projects"))
}
#[tauri::command]
fn theme_catalog() -> Vec<Theme> {
    storyboard_core::themes()
}
#[tauri::command]
fn example_brief() -> String {
    include_str!("../../../../examples/startup-pitch.md").into()
}
#[tauri::command]
fn compile_brief(
    input: String,
    markdown: bool,
    theme: Theme,
    session: State<Session>,
) -> Result<Review, String> {
    let theme = if !markdown
        && serde_json::from_str::<serde_json::Value>(&input)
            .ok()
            .is_some_and(|v| v.get("project_version").is_some())
    {
        Project::parse(&input).map_err(|e| e.to_string())?.theme
    } else {
        theme
    };
    let mut story = storyboard_core::compile(&input, markdown).map_err(|e| e.to_string())?;
    story.presentation.theme = theme.name.clone();
    review(story, theme, &root(&session)?)
}
#[tauri::command]
fn review_story(mut story: Story, theme: Theme, session: State<Session>) -> Result<Review, String> {
    story.presentation.theme = theme.name.clone();
    review(story, theme, &root(&session)?)
}
#[tauri::command]
fn save_project(
    project: Project,
    app: tauri::AppHandle,
    session: State<Session>,
) -> Result<(), String> {
    projects::save(&storage(&app)?, &project, &root(&session)?)
}
#[tauri::command]
fn recent_projects(app: tauri::AppHandle) -> Result<Vec<projects::Recent>, String> {
    projects::recent(&storage(&app)?)
}
#[tauri::command]
fn load_project(
    id: String,
    app: tauri::AppHandle,
    session: State<Session>,
) -> Result<Project, String> {
    let root = storage(&app)?;
    let project = projects::load(&root, &id)?;
    *session
        .asset_root
        .lock()
        .map_err(|_| "Asset session unavailable")? = Some(root);
    Ok(project)
}
#[tauri::command]
async fn open_input(
    app: tauri::AppHandle,
    session: State<'_, Session>,
) -> Result<Option<(String, bool)>, String> {
    let dialog = app
        .dialog()
        .file()
        .add_filter("Storyboard input", &["md", "json", "storyboard"]);
    let selected = tauri::async_runtime::spawn_blocking(move || dialog.blocking_pick_file())
        .await
        .map_err(|e| e.to_string())?;
    let Some(selected) = selected else {
        return Ok(None);
    };
    let path = selected.into_path().map_err(|e| e.to_string())?;
    import_file(&path, &session).map(Some)
}
fn import_file(path: &Path, session: &Session) -> Result<(String, bool), String> {
    let meta = std::fs::metadata(path).map_err(|e| e.to_string())?;
    if !meta.is_file() || meta.len() > storyboard_core::project::MAX_PROJECT_BYTES as u64 {
        return Err("Input must be a regular file ≤16 MiB".into());
    }
    let md = path.extension().is_some_and(|s| s == "md");
    let text = std::fs::read_to_string(path).map_err(|e| e.to_string())?;
    storyboard_core::compile(&text, md).map_err(|e| e.to_string())?;
    *session
        .asset_root
        .lock()
        .map_err(|_| "Asset session unavailable")? = path.parent().map(Path::to_path_buf);
    Ok((text, md))
}
#[tauri::command]
fn import_drop(path: String, session: State<Session>) -> Result<(String, bool), String> {
    let path = PathBuf::from(path);
    let mut allowed = session
        .allowed_drops
        .lock()
        .map_err(|_| "Drop session unavailable")?;
    let Some(index) = allowed.iter().position(|p| p == &path) else {
        return Err("Only files from a native drag-and-drop event may be imported".into());
    };
    allowed.remove(index);
    drop(allowed);
    import_file(&path, &session)
}
#[tauri::command]
async fn export_deck(
    story: Story,
    theme: Theme,
    app: tauri::AppHandle,
    session: State<'_, Session>,
) -> Result<Option<String>, String> {
    story.validate().map_err(|e| e.to_string())?;
    theme.validate().map_err(|e| e.to_string())?;
    let asset_root = root(&session)?;
    let dialog = app
        .dialog()
        .file()
        .set_file_name("presentation.pptx")
        .add_filter("PowerPoint", &["pptx"]);
    let selected = tauri::async_runtime::spawn_blocking(move || dialog.blocking_save_file())
        .await
        .map_err(|e| e.to_string())?;
    let Some(selected) = selected else {
        return Ok(None);
    };
    let path = selected.into_path().map_err(|e| e.to_string())?;
    // The native save dialog approves the destination; bundles still retain rollback protection.
    storyboard_pptx::assets::export(&story, &theme, &asset_root, &path, true)
        .map_err(|e| e.to_string())?;
    Ok(Some(path.display().to_string()))
}
#[tauri::command]
async fn import_brand(
    story: Story,
    app: tauri::AppHandle,
    session: State<'_, Session>,
) -> Result<Option<Review>, String> {
    let dialog = app.dialog().file().add_filter("Local brand kit", &["json"]);
    let selected = tauri::async_runtime::spawn_blocking(move || dialog.blocking_pick_file())
        .await
        .map_err(|_| "Brand dialog unavailable".to_string())?;
    let Some(selected) = selected else {
        return Ok(None);
    };
    let path = selected.into_path().map_err(|e| e.to_string())?;
    if std::fs::metadata(&path).map_err(|e| e.to_string())?.len() > 64 * 1024 {
        return Err("Brand kit exceeds 64 KiB".into());
    }
    let kit: storyboard_core::theme::BrandKit =
        serde_json::from_slice(&std::fs::read(&path).map_err(|e| e.to_string())?)
            .map_err(|e| e.to_string())?;
    let destination = storage(&app)?;
    std::fs::create_dir_all(&destination).map_err(|e| e.to_string())?;
    let story = storyboard_pptx::assets::brand_story(
        &story,
        &kit,
        &root(&session)?,
        path.parent().unwrap_or(Path::new(".")),
        &destination,
    )
    .map_err(|e| e.to_string())?;
    let review = review(story, kit.theme, &destination)?;
    *session
        .asset_root
        .lock()
        .map_err(|_| "Asset session unavailable")? = Some(destination);
    Ok(Some(review))
}
#[tauri::command]
async fn draft_brief(
    config: storyboard_ai::Config,
    input: String,
    api_key: Option<String>,
    approved: bool,
) -> Result<String, String> {
    tauri::async_runtime::spawn_blocking(move || {
        storyboard_ai::draft(&config, &input, api_key.as_deref(), approved)
            .map_err(|e| e.to_string())
    })
    .await
    .map_err(|_| "Provider task failed".to_string())?
}
#[tauri::command]
fn finish_close(app: tauri::AppHandle) {
    app.exit(0);
}
fn main() {
    let result = tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .manage(Session::default())
        .setup(|app| {
            let assets = app.path().app_data_dir()?.join("assets");
            std::fs::create_dir_all(&assets)?;
            *app.state::<Session>()
                .asset_root
                .lock()
                .map_err(|_| "Asset session unavailable")? = Some(assets);
            Ok(())
        })
        .on_window_event(|window, event| match event {
            tauri::WindowEvent::DragDrop(tauri::DragDropEvent::Drop { paths, .. }) => {
                if let Ok(mut allowed) = window.state::<Session>().allowed_drops.lock() {
                    *allowed = paths.clone();
                }
            }
            tauri::WindowEvent::CloseRequested { api, .. } => {
                api.prevent_close();
                let _ = window.emit("storyboard-close-requested", ());
            }
            _ => {}
        })
        .invoke_handler(tauri::generate_handler![
            theme_catalog,
            example_brief,
            compile_brief,
            review_story,
            save_project,
            recent_projects,
            load_project,
            open_input,
            import_drop,
            export_deck,
            finish_close,
            draft_brief,
            import_brand
        ])
        .run(tauri::generate_context!());
    if let Err(e) = result {
        eprintln!("Storyboard Studio failed to start: {e}");
        std::process::exit(1);
    }
}
