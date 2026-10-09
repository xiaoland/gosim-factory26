use reqwest::{Url, header::HeaderValue};
use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    net::SocketAddr,
    path::Path,
};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Config {
    pub run_id: String,
    pub listen: SocketAddr,
    pub catalog_sha256: String,
    pub routes_sha256: String,
    pub deployments: Vec<Deployment>,
    pub limits: Limits,
}

#[derive(Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Deployment {
    pub alias: String,
    pub order: usize,
    pub deployment_id: String,
    pub provider: String,
    pub plan: String,
    pub wire_model: String,
    pub base_url: String,
    pub credential_env: String,
    #[serde(default)]
    pub model_info: BTreeMap<String, serde_json::Value>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Limits {
    // Accept prior frozen configs during recovery; these retired quotas have no effect.
    #[serde(default, rename = "active_requests")]
    _legacy_active_requests: Option<usize>,
    #[serde(default, rename = "waiting_requests")]
    _legacy_waiting_requests: Option<usize>,
    #[serde(default, rename = "connections")]
    _legacy_connections: Option<usize>,
    #[serde(default, rename = "queue_ms")]
    _legacy_queue_ms: Option<u64>,
    pub connect_ms: u64,
    pub headers_ms: u64,
    pub body_ms: u64,
    pub stream_idle_ms: u64,
    pub total_ms: u64,
    pub shutdown_ms: u64,
    pub error_bytes: usize,
}

pub struct Route {
    pub deployment: Deployment,
    pub url: Url,
    pub auth: HeaderValue,
}

pub fn load(
    config_path: &Path,
    credentials_path: &Path,
) -> Result<
    (
        Config,
        BTreeMap<String, Vec<Route>>,
        String,
        Vec<String>,
        String,
    ),
    Box<dyn std::error::Error>,
> {
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        if fs::metadata(credentials_path)?.permissions().mode() & 0o777 != 0o600 {
            return Err("credentials must have mode 0600".into());
        }
    }
    #[derive(Deserialize)]
    #[serde(deny_unknown_fields)]
    struct Credentials {
        environment: BTreeMap<String, String>,
    }
    if fs::metadata(config_path)?.len() > 1024 * 1024
        || fs::metadata(credentials_path)?.len() > 65536
    {
        return Err("config or credentials exceed startup size limit".into());
    }
    let config_bytes = fs::read(config_path)?;
    let config_sha = format!("{:x}", Sha256::digest(&config_bytes));
    let config: Config = serde_json::from_slice(&config_bytes)?;
    let credentials: Credentials = serde_json::from_slice(&fs::read(credentials_path)?)?;
    let l = &config.limits;
    if !config.listen.ip().is_loopback()
        || config.run_id.is_empty()
        || config.run_id.len() > 200
        || l.error_bytes == 0
        || l.error_bytes > 16384
        || [
            l.connect_ms,
            l.headers_ms,
            l.body_ms,
            l.stream_idle_ms,
            l.total_ms,
            l.shutdown_ms,
        ]
        .iter()
        .any(|&v| v == 0 || v > 3_600_000)
        || l.total_ms < l.headers_ms
        || l.total_ms < l.body_ms
    {
        return Err("invalid loopback address, identity or resource limits".into());
    }
    let token = credentials
        .environment
        .get("FACTORY26_GATEWAY_TOKEN")
        .filter(|v| v.len() >= 32)
        .ok_or("missing local token")?
        .clone();
    let secrets = credentials.environment.values().cloned().collect();
    let mut routes: BTreeMap<String, Vec<Route>> = BTreeMap::new();
    // A deployment is a supplier identity.  The same supplier deployment may
    // legitimately serve several aliases; only duplicate entries within one
    // alias are ambiguous and must be rejected.
    let mut ids_by_alias: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();
    for d in &config.deployments {
        let ids = ids_by_alias.entry(d.alias.clone()).or_default();
        if d.alias.is_empty() || d.wire_model.is_empty() || !ids.insert(d.deployment_id.clone()) {
            return Err("invalid or duplicate deployment".into());
        }
        let mut url = Url::parse(&d.base_url).map_err(|_| "invalid deployment URL")?;
        if url.scheme() != "https"
            || url.host_str().is_none()
            || !url.username().is_empty()
            || url.password().is_some()
            || url.query().is_some()
            || url.fragment().is_some()
        {
            return Err("upstream URL must be HTTPS without credentials, query or fragment".into());
        }
        url.set_path(&format!(
            "{}/chat/completions",
            url.path().trim_end_matches('/')
        ));
        let key = credentials
            .environment
            .get(&d.credential_env)
            .filter(|v| !v.is_empty())
            .ok_or("missing selected upstream credential")?;
        let mut auth = HeaderValue::from_str(&format!("Bearer {key}"))
            .map_err(|_| "invalid credential bytes")?;
        auth.set_sensitive(true);
        routes.entry(d.alias.clone()).or_default().push(Route {
            deployment: d.clone(),
            url,
            auth,
        });
    }
    if routes.is_empty() {
        return Err("no active routes".into());
    }
    for chain in routes.values_mut() {
        chain.sort_by_key(|r| r.deployment.order);
        if chain.len() > 4
            || chain
                .iter()
                .enumerate()
                .any(|(i, r)| i != r.deployment.order)
        {
            return Err("each alias needs one to four consecutive ordered deployments".into());
        }
    }
    Ok((config, routes, token, secrets, config_sha))
}
