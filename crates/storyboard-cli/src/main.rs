use clap::{Args, Parser, Subcommand};
use serde::Serialize;
use std::{
    path::{Path, PathBuf},
    time::Instant,
};
use storyboard_core::{Story, Theme, compile, diagnose};
use storyboard_pptx::{preview, receipt};
type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;

#[derive(Parser)]
#[command(
    name = "storyboard",
    version,
    about = "The native local-first presentation compiler",
    long_about = "Compile structured briefs and Markdown into inspectable stories and editable PowerPoint. Offline by default; no Python or provider required."
)]
struct Cli {
    #[command(subcommand)]
    command: Command,
}
#[derive(Subcommand)]
enum Command {
    /// Create a synthetic Markdown project to edit.
    New {
        #[arg(default_value = "presentation.md")]
        path: PathBuf,
        #[arg(long)]
        force: bool,
    },
    /// Compile Markdown or a structured JSON brief into native story JSON.
    Compile {
        input: PathBuf,
        #[arg(short, long)]
        output: Option<PathBuf>,
        #[arg(long)]
        force: bool,
    },
    /// Generate PPTX, story and receipt from a brief or story.
    Build(RenderArgs),
    /// Render a native story into an editable PPTX bundle.
    Render(RenderArgs),
    /// Diagnose narrative, claims, density and ownership.
    Doctor {
        input: PathBuf,
        #[arg(long, conflicts_with = "markdown")]
        json: bool,
        #[arg(long)]
        markdown: bool,
        #[arg(long)]
        fail_on_error: bool,
    },
    /// Inspect validated story or resolved geometry as JSON.
    Inspect {
        input: PathBuf,
        #[arg(long)]
        layout: bool,
    },
    /// Verify receipt artifacts and replay narrative diagnostics.
    Verify {
        input: PathBuf,
        #[arg(long)]
        json: bool,
    },
    /// Validate archive, XML, relationships and text in a PPTX.
    Validate {
        input: PathBuf,
        #[arg(long)]
        json: bool,
    },
    /// Compare two native stories without provider requests.
    Diff {
        old: PathBuf,
        new: PathBuf,
        #[arg(long)]
        json: bool,
    },
    /// Generate a standalone slide preview HTML, or one SVG.
    Preview {
        input: PathBuf,
        #[arg(short, long)]
        output: Option<PathBuf>,
        #[arg(long, default_value_t = 1)]
        slide: usize,
        #[arg(long)]
        svg: bool,
        #[arg(long)]
        force: bool,
    },
    /// List built-in theme definitions.
    Themes {
        #[arg(long)]
        json: bool,
    },
    /// Print the bundled synthetic Markdown example.
    Examples,
    /// Print the native story JSON Schema.
    Schema,
    /// Measure real compile/layout/PPTX times for 10–250 slides.
    Benchmark {
        #[arg(long, default_value_t = 3)]
        iterations: usize,
        #[arg(short, long)]
        output: Option<PathBuf>,
        #[arg(long)]
        force: bool,
    },
    /// Serve a read-only preview on loopback, without a separate runtime.
    Serve {
        input: PathBuf,
        #[arg(long, default_value_t = 4318)]
        port: u16,
    },
}
#[derive(Args)]
struct RenderArgs {
    input: PathBuf,
    #[arg(short, long)]
    output: Option<PathBuf>,
    #[arg(long)]
    theme: Option<String>,
    #[arg(long)]
    brand: Option<PathBuf>,
    #[arg(long)]
    force: bool,
    #[arg(long)]
    json: bool,
}
const EXAMPLE: &str = include_str!("../../../examples/startup-pitch.md");
fn read(path: &Path) -> Result<String> {
    let size = std::fs::metadata(path)?.len();
    if size > storyboard_core::project::MAX_PROJECT_BYTES as u64 {
        return Err("Input exceeds 16 MiB".into());
    }
    Ok(std::fs::read_to_string(path)?)
}
fn load(path: &Path) -> Result<Story> {
    let md = matches!(
        path.extension().and_then(|x| x.to_str()),
        Some("md" | "markdown")
    );
    if !md
        && !matches!(
            path.extension().and_then(|x| x.to_str()),
            Some("json" | "storyboard" | "story")
        )
    {
        return Err("Use .md, .story.md, .json, .story.json or .storyboard".into());
    }
    Ok(compile(&read(path)?, md)?)
}
fn input_theme(path: &Path, story: &Story) -> Result<Theme> {
    let text = read(path)?;
    if let Ok(value) = serde_json::from_str::<serde_json::Value>(&text)
        && value.get("project_version").is_some()
    {
        return Ok(storyboard_core::Project::parse(&text)?.theme);
    }
    Ok(Theme::named(&story.presentation.theme)?)
}
fn json(value: &impl Serialize) -> Result<String> {
    Ok(serde_json::to_string_pretty(value)?)
}
fn output(path: Option<&Path>, data: &str, force: bool) -> Result<()> {
    if let Some(path) = path {
        receipt::write_bytes(path, data.as_bytes(), force)?;
    } else {
        println!("{data}");
    }
    Ok(())
}
fn default_output(input: &Path, extension: &str) -> PathBuf {
    let parent = input.parent().unwrap_or(Path::new("."));
    let stem = input
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("presentation")
        .trim_end_matches(".story");
    parent.join(format!("{stem}.{extension}"))
}
fn render(args: RenderArgs) -> Result<()> {
    let mut story = load(&args.input)?;
    let theme = if let Some(brand) = args.brand {
        let kit: storyboard_core::theme::BrandKit = serde_json::from_str(&read(&brand)?)?;
        kit.theme.validate()?;
        if kit.logo.is_some() {
            return Err(
                "Brand logo placement is not yet supported; add an explicit local image block"
                    .into(),
            );
        }
        kit.theme
    } else {
        if let Some(name) = &args.theme {
            Theme::named(name)?
        } else {
            input_theme(&args.input, &story)?
        }
    };
    story.presentation.theme = theme.name.clone();
    let root = args.input.parent().unwrap_or(Path::new("."));
    let path = args
        .output
        .unwrap_or_else(|| default_output(&args.input, "pptx"));
    let r = storyboard_pptx::assets::export(&story, &theme, root, &path, args.force)?;
    if args.json {
        println!("{}", json(&r)?);
    } else {
        println!(
            "Built {} · {} editable slides · theme {}",
            path.display(),
            story.presentation.slides.len(),
            theme.name
        );
        println!(
            "Story: {}\nReceipt: {}",
            path.with_extension("story.json").display(),
            path.with_extension("receipt.json").display()
        );
        println!(
            "Doctor: {} findings. Run storyboard doctor {}",
            r.diagnostics.findings.len(),
            path.with_extension("story.json").display()
        );
    }
    Ok(())
}
fn preview_html(story: &Story, theme: &Theme, root: &Path) -> Result<String> {
    let layout = storyboard_core::resolve(story, theme)?;
    let mut slides = String::new();
    for i in 0..layout.slides.len() {
        slides.push_str(&format!(
            "<section class=\"slide\"{}>{}</section>",
            if i == 0 { "" } else { " hidden" },
            preview::svg(&layout, i, root)?
        ));
    }
    Ok(format!(
        r#"<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Storyboard preview</title><style>body{{margin:0;background:#101820;color:#e9f0f3;font:14px Carlito,system-ui}}header{{display:flex;gap:12px;align-items:center;padding:16px 24px;border-bottom:1px solid #304050}}button{{background:#263544;color:inherit;border:1px solid #536373;padding:8px 14px;border-radius:6px;cursor:pointer}}button:focus-visible{{outline:2px solid #9dd8c0}}main{{padding:24px;max-width:1400px;margin:auto}}svg{{width:100%;height:auto}}[hidden]{{display:none}}main.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}}section{{box-shadow:0 12px 48px #0005}}</style><header><strong>Storyboard Studio</strong><button id="previous" aria-label="Previous slide">←</button><span id="counter"></span><button id="next" aria-label="Next slide">→</button><button id="grid">Grid overview</button><button id="full">Fullscreen</button><span>Local preview · native text and shapes</span></header><main>{slides}</main><script>const slides=[...document.querySelectorAll('.slide')],main=document.querySelector('main');let index=0,grid=false;function show(){{slides.forEach((s,i)=>s.hidden=!grid&&i!==index);document.querySelector('#counter').textContent=`${{index+1}} / ${{slides.length}}`;main.classList.toggle('grid',grid)}}document.querySelector('#previous').onclick=()=>{{index=Math.max(0,index-1);show()}};document.querySelector('#next').onclick=()=>{{index=Math.min(slides.length-1,index+1);show()}};document.querySelector('#grid').onclick=()=>{{grid=!grid;show()}};document.querySelector('#full').onclick=()=>document.documentElement.requestFullscreen();document.onkeydown=e=>{{if(e.key==='ArrowRight')document.querySelector('#next').click();if(e.key==='ArrowLeft')document.querySelector('#previous').click()}};slides.forEach((s,i)=>s.onclick=()=>{{if(grid){{index=i;grid=false;show()}}}});show();</script></html>"#
    ))
}
#[derive(Serialize)]
struct Measurement {
    slides: usize,
    iterations: usize,
    compile_ms: f64,
    layout_ms: f64,
    pptx_ms: f64,
    pptx_bytes: usize,
}
fn benchmark(iterations: usize) -> Result<serde_json::Value> {
    if !(1..=100).contains(&iterations) {
        return Err("Iterations must be 1–100".into());
    }
    let base = compile(EXAMPLE, true)?;
    let theme = Theme::named("midnight")?;
    let mut measurements = Vec::new();
    for size in [10, 25, 50, 100, 250] {
        let mut story = base.clone();
        story.presentation.slides = (0..size)
            .map(|i| {
                let mut s = base.presentation.slides[i % base.presentation.slides.len()].clone();
                s.id = format!("bench-{i:03}");
                s
            })
            .collect();
        let input = json(&story)?;
        let (mut compilation, mut layout_time, mut pptx_time, mut bytes) = (0.0, 0.0, 0.0, 0);
        for _ in 0..iterations {
            let now = Instant::now();
            let parsed = compile(&input, false)?;
            compilation += now.elapsed().as_secs_f64() * 1000.0;
            let now = Instant::now();
            storyboard_core::resolve(&parsed, &theme)?;
            layout_time += now.elapsed().as_secs_f64() * 1000.0;
            let now = Instant::now();
            let deck = storyboard_pptx::render(&parsed, &theme, Path::new("."))?;
            pptx_time += now.elapsed().as_secs_f64() * 1000.0;
            bytes = deck.pptx.len();
        }
        measurements.push(Measurement {
            slides: size,
            iterations,
            compile_ms: compilation / iterations as f64,
            layout_ms: layout_time / iterations as f64,
            pptx_ms: pptx_time / iterations as f64,
            pptx_bytes: bytes,
        });
    }
    Ok(
        serde_json::json!({"version":storyboard_core::VERSION,"os":std::env::consts::OS,"architecture":std::env::consts::ARCH,"profile":if cfg!(debug_assertions){"debug"}else{"release"},"binary_bytes":std::fs::metadata(std::env::current_exe()?)?.len(),"measurements":measurements,"method":"Arithmetic mean of complete runs; PPTX includes layout, compression and semantic package validation. Process startup and peak RSS require external measurement."}),
    )
}
fn run(cli: Cli) -> Result<()> {
    match cli.command {
        Command::New { path, force } => {
            receipt::write_bytes(&path, EXAMPLE.as_bytes(), force)?;
            println!("Created {} · synthetic example", path.display());
        }
        Command::Compile {
            input,
            output: out,
            force,
        } => {
            let story = load(&input)?;
            output(out.as_deref(), &json(&story)?, force)?;
        }
        Command::Build(args) | Command::Render(args) => render(args)?,
        Command::Doctor {
            input,
            json: machine,
            markdown: _,
            fail_on_error,
        } => {
            let r = diagnose(&load(&input)?);
            println!("{}", if machine { json(&r)? } else { r.markdown() });
            if fail_on_error
                && r.findings
                    .iter()
                    .any(|f| f.severity == storyboard_core::Severity::Error)
            {
                return Err("Narrative Doctor found errors".into());
            }
        }
        Command::Inspect { input, layout } => {
            let story = load(&input)?;
            if layout {
                println!(
                    "{}",
                    json(&storyboard_core::resolve(
                        &story,
                        &input_theme(&input, &story)?
                    )?)?
                );
            } else {
                println!("{}", json(&story)?);
            }
        }
        Command::Verify {
            input,
            json: machine,
        } => {
            let r = receipt::verify(&input)?;
            if machine {
                println!("{}", json(&r)?);
            } else {
                println!(
                    "Verified story/PPTX hashes, package integrity and derived diagnostics.\n{}",
                    r.disclaimer
                );
            }
        }
        Command::Validate {
            input,
            json: machine,
        } => {
            let r = storyboard_pptx::validate::validate_file(&input)?;
            if machine {
                println!("{}", json(&r)?);
            } else {
                println!(
                    "Valid package · {} slides · {} parts · {} relationships\n{}",
                    r.slides, r.parts, r.relationships, r.scope
                );
            }
        }
        Command::Themes { json: machine } => {
            let themes = storyboard_core::themes();
            if machine {
                println!("{}", json(&themes)?);
            } else {
                for t in themes {
                    println!(
                        "{:<12}  #{}  #{}  title {}pt",
                        t.name, t.background, t.accent, t.title_size
                    );
                }
            }
        }
        Command::Examples => print!("{EXAMPLE}"),
        Command::Schema => println!("{}", json(&schemars_schema())?),
        Command::Diff {
            old,
            new,
            json: machine,
        } => {
            let (a, b) = (load(&old)?, load(&new)?);
            let mut changes = Vec::new();
            if a.presentation.title != b.presentation.title {
                changes.push("presentation.title".to_string());
            }
            if a.audience != b.audience
                || a.objective != b.objective
                || a.owner != b.owner
                || a.next_action != b.next_action
                || a.metadata != b.metadata
                || a.presentation.subtitle != b.presentation.subtitle
                || a.presentation.theme != b.presentation.theme
            {
                changes.push("story metadata/theme".into());
            }
            for s in &a.presentation.slides {
                match b.presentation.slides.iter().find(|v| v.id == s.id) {
                    None => changes.push(format!("removed {}", s.id)),
                    Some(v) if v != s => changes.push(format!("changed {}", s.id)),
                    _ => {}
                }
            }
            for s in &b.presentation.slides {
                if !a.presentation.slides.iter().any(|v| v.id == s.id) {
                    changes.push(format!("added {}", s.id));
                }
            }
            if a.presentation
                .slides
                .iter()
                .map(|s| &s.id)
                .collect::<Vec<_>>()
                != b.presentation
                    .slides
                    .iter()
                    .map(|s| &s.id)
                    .collect::<Vec<_>>()
            {
                changes.push("slide order".into());
            }
            if machine {
                println!("{}", json(&changes)?);
            } else {
                println!(
                    "{}",
                    if changes.is_empty() {
                        "No changes".into()
                    } else {
                        changes.join("\n")
                    }
                );
            }
        }
        Command::Preview {
            input,
            output: out,
            slide,
            svg,
            force,
        } => {
            let story = load(&input)?;
            let root = input.parent().unwrap_or(Path::new("."));
            let content = if svg {
                let deck = storyboard_core::resolve(&story, &input_theme(&input, &story)?)?;
                preview::svg(
                    &deck,
                    slide.checked_sub(1).ok_or("Slides are numbered from 1")?,
                    root,
                )?
            } else {
                preview_html(&story, &input_theme(&input, &story)?, root)?
            };
            let out =
                out.unwrap_or_else(|| default_output(&input, if svg { "svg" } else { "html" }));
            output(Some(&out), &content, force)?;
            println!("Preview: {}", out.display());
        }
        Command::Benchmark {
            iterations,
            output: out,
            force,
        } => output(out.as_deref(), &json(&benchmark(iterations)?)?, force)?,
        Command::Serve { input, port } => {
            let story = load(&input)?;
            let html = preview_html(
                &story,
                &input_theme(&input, &story)?,
                input.parent().unwrap_or(Path::new(".")),
            )?;
            let server = tiny_http::Server::http(("127.0.0.1", port)).map_err(|e| e.to_string())?;
            println!("Local preview: http://127.0.0.1:{port} · Ctrl+C to stop");
            for request in server.incoming_requests() {
                let response = if request.method() != &tiny_http::Method::Get {
                    tiny_http::Response::from_string("GET only").with_status_code(405)
                } else if request.url() == "/" {
                    tiny_http::Response::from_string(html.clone()).with_header(
                        tiny_http::Header::from_bytes("Content-Type", "text/html; charset=utf-8")
                            .map_err(|_| "Invalid header")?,
                    )
                } else {
                    tiny_http::Response::from_string("Not found").with_status_code(404)
                };
                request.respond(response)?;
            }
        }
    }
    Ok(())
}
fn schemars_schema() -> serde_json::Value {
    storyboard_core::schema()
}
fn main() {
    if let Err(e) = run(Cli::parse()) {
        eprintln!("error: {e}");
        std::process::exit(1);
    }
}
