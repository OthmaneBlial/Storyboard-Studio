//! No requests occur until the caller explicitly approves sending the supplied text.
use reqwest::{Url, blocking::Client, redirect::Policy};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use std::{io::Read, time::Duration};
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum Provider {
    OpenaiCompatible,
    Gemini,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Config {
    pub provider: Provider,
    pub endpoint: String,
    pub model: String,
}
#[derive(Debug, thiserror::Error)]
#[error("{0}")]
pub struct Error(String);
impl Config {
    pub fn validate(&self) -> Result<Url, Error> {
        let url = Url::parse(&self.endpoint).map_err(|_| Error("Invalid provider URL".into()))?;
        let loopback = matches!(url.host_str(), Some("localhost" | "127.0.0.1" | "[::1]"));
        if !url.username().is_empty()
            || url.password().is_some()
            || url.query().is_some()
            || url.fragment().is_some()
            || url.host_str().is_none()
            || !(url.scheme() == "https" || (url.scheme() == "http" && loopback))
        {
            return Err(Error(
                "Use HTTPS, or HTTP on loopback; no credentials, query or fragment in the endpoint"
                    .into(),
            ));
        }
        if self.model.trim().is_empty()
            || self.model.len() > 200
            || self.model.chars().any(char::is_control)
        {
            return Err(Error(
                "Provider model is required and must be ≤200 characters".into(),
            ));
        }
        Ok(url)
    }
}
const INSTRUCTION: &str = "Draft a concise Markdown presentation: one # title, ## slides, ### optional cards, and Notes: speaker notes. Keep author-owned facts unchanged. Label assumptions. Never invent sources, evidence, customer results or endorsements. Include an explicit recommendation, owner and next action when supplied. Return Markdown only; no code fence.";
pub fn draft(
    config: &Config,
    input: &str,
    api_key: Option<&str>,
    approved: bool,
) -> Result<String, Error> {
    if !approved {
        return Err(Error(
            "Explicit approval to send this text to this endpoint is required".into(),
        ));
    }
    if input.trim().is_empty() || input.len() > 64 * 1024 {
        return Err(Error("Draft input must be nonempty and ≤64 KiB".into()));
    }
    let url = config.validate()?;
    let body = match config.provider {
        Provider::OpenaiCompatible => {
            json!({"model":config.model,"messages":[{"role":"system","content":INSTRUCTION},{"role":"user","content":input}],"temperature":0.3,"max_tokens":4096})
        }
        Provider::Gemini => {
            json!({"systemInstruction":{"parts":[{"text":INSTRUCTION}]},"contents":[{"role":"user","parts":[{"text":input}]}],"generationConfig":{"temperature":0.3,"maxOutputTokens":4096}})
        }
    };
    let client = Client::builder()
        .timeout(Duration::from_secs(60))
        .connect_timeout(Duration::from_secs(10))
        .redirect(Policy::none())
        .no_proxy()
        .build()
        .map_err(|_| Error("Provider HTTP client unavailable".into()))?;
    let mut request = client.post(url).json(&body);
    if let Some(key) = api_key.filter(|k| !k.is_empty()) {
        request = match config.provider {
            Provider::OpenaiCompatible => request.bearer_auth(key),
            Provider::Gemini => request.header("x-goog-api-key", key),
        };
    }
    let response = request
        .send()
        .map_err(|_| Error("Provider request failed; check connection and endpoint".into()))?;
    if !response.status().is_success() {
        return Err(Error(format!(
            "Provider returned HTTP {}",
            response.status().as_u16()
        )));
    }
    let mut bytes = Vec::new();
    response
        .take(4 * 1024 * 1024 + 1)
        .read_to_end(&mut bytes)
        .map_err(|_| Error("Cannot read provider response".into()))?;
    if bytes.len() > 4 * 1024 * 1024 {
        return Err(Error("Provider response exceeds 4 MiB".into()));
    }
    let response: Value = serde_json::from_slice(&bytes)
        .map_err(|_| Error("Provider returned invalid JSON".into()))?;
    let text = match config.provider {
        Provider::OpenaiCompatible => response
            .pointer("/choices/0/message/content")
            .and_then(Value::as_str)
            .map(str::to_owned),
        Provider::Gemini => response
            .pointer("/candidates/0/content/parts")
            .and_then(Value::as_array)
            .map(|parts| {
                parts
                    .iter()
                    .filter_map(|p| p.get("text").and_then(Value::as_str))
                    .collect::<Vec<_>>()
                    .join("\n")
            }),
    }
    .filter(|s| !s.trim().is_empty() && s.len() <= 64 * 1024)
    .ok_or_else(|| Error("Provider returned no bounded text draft".into()))?;
    Ok(text)
}
#[cfg(test)]
mod tests {
    use super::*;
    use std::{io::Write, net::TcpListener};
    #[test]
    fn opt_in_boundary_and_real_loopback_provider_roundtrip() {
        let server = TcpListener::bind("127.0.0.1:0").unwrap();
        let config = Config {
            provider: Provider::OpenaiCompatible,
            endpoint: format!(
                "http://{}/v1/chat/completions",
                server.local_addr().unwrap()
            ),
            model: "fixture".into(),
        };
        assert!(draft(&config, "source", None, false).is_err());
        let thread = std::thread::spawn(move || {
            let (mut stream, _) = server.accept().unwrap();
            stream
                .set_read_timeout(Some(Duration::from_secs(5)))
                .unwrap();
            let mut data = Vec::new();
            let mut chunk = [0u8; 4096];
            loop {
                let n = stream.read(&mut chunk).unwrap();
                data.extend_from_slice(&chunk[..n]);
                if let Some(split) = data.windows(4).position(|w| w == b"\r\n\r\n") {
                    let headers = String::from_utf8_lossy(&data[..split]).to_lowercase();
                    let size: usize = headers
                        .lines()
                        .find_map(|line| line.strip_prefix("content-length:"))
                        .unwrap()
                        .trim()
                        .parse()
                        .unwrap();
                    if data.len() >= split + 4 + size {
                        break;
                    }
                }
            }
            let text = String::from_utf8(data).unwrap();
            assert!(text.contains("author supplied brief"));
            assert!(
                text.to_lowercase()
                    .contains("authorization: bearer ephemeral-test-key")
            );
            let body = r##"{"choices":[{"message":{"content":"# Authored draft\n## Recommendation\nKeep the pilot bounded."}}]}"##;
            write!(stream,"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",body.len(),body).unwrap();
        });
        assert!(
            draft(
                &config,
                "author supplied brief",
                Some("ephemeral-test-key"),
                true
            )
            .unwrap()
            .starts_with("# Authored")
        );
        thread.join().unwrap();
        for endpoint in [
            "http://example.com/draft",
            "https://secret@example.com/draft",
            "https://example.com/draft?key=secret",
        ] {
            let bad = Config {
                endpoint: endpoint.into(),
                ..config.clone()
            };
            assert!(bad.validate().is_err());
        }
    }
}
