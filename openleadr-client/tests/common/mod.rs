use async_trait::async_trait;
use axum::body::Body;
use http_body_util::BodyExt;
use openleadr_client::{Client, ClientCredentials, ClientKind, HttpClient, ProgramClient};
use openleadr_vtn::{VtnConfig, data_source::PostgresStorage, state::AppState};
use openleadr_wire::program::ProgramRequest;
use reqwest::{Method, RequestBuilder, Response};
use sqlx::PgPool;
use std::{env::VarError, ops::Deref, sync::Arc};
use tower::{Service, ServiceExt};
use url::Url;

#[derive(Clone, Copy)]
#[allow(dead_code)]
pub enum AuthRole {
    Bl,
    Ven,
}

fn default_credentials(auth_role: AuthRole) -> ClientCredentials {
    let (id, secr) = match auth_role {
        AuthRole::Bl => ("bl-client", "bl-client"),
        AuthRole::Ven => ("ven-client-client-id", "ven-client"),
    };

    ClientCredentials::new(id.to_string(), secr.to_string())
}

// Do not silently fall back to another identity when an explicitly set secret is malformed.
fn credential_env(name: &str) -> Option<String> {
    match std::env::var(name) {
        Ok(value) => Some(value),
        Err(VarError::NotPresent) => None,
        Err(VarError::NotUnicode(_)) => {
            panic!("Invalid encoding for credential environment variable: {name}")
        }
    }
}

fn credential_policy(
    strict: bool,
    id: Option<&str>,
    secret: Option<&str>,
) -> Result<(), &'static str> {
    if !strict {
        return Ok(());
    }
    if id.map_or(true, |value| value.trim().is_empty()) {
        return Err("client ID");
    }
    if secret.map_or(true, |value| value.trim().is_empty()) {
        return Err("client secret");
    }
    Ok(())
}

fn external_vtn_credentials(auth_role: AuthRole) -> ClientCredentials {
    let (id_var, secret_var) = match auth_role {
        AuthRole::Bl => ("OPENLEADR_RS_BL_CLIENT_ID", "OPENLEADR_RS_BL_CLIENT_SECRET"),
        AuthRole::Ven => (
            "OPENLEADR_RS_VEN_CLIENT_ID",
            "OPENLEADR_RS_VEN_CLIENT_SECRET",
        ),
    };
    let legacy_id = credential_env("OPENLEADR_RS_CLIENT_ID");
    let legacy_secret = credential_env("OPENLEADR_RS_CLIENT_SECRET");
    let strict_external =
        std::env::var("OPENLEADR_RS_REQUIRE_EXTERNAL_VTN").as_deref() == Ok("1");
    let client_id = credential_env(id_var).or(legacy_id);
    let client_secret = credential_env(secret_var).or(legacy_secret);

    if strict_external {
        credential_policy(true, client_id.as_deref(), client_secret.as_deref()).unwrap_or_else(
            |missing| {
                panic!("External-only test mode requires non-empty {missing} (or legacy role credentials)")
            },
        );
        return ClientCredentials::new(client_id.unwrap(), client_secret.unwrap());
    }

    let client_id = client_id.unwrap_or_else(|| match auth_role {
        AuthRole::Bl => "bl-client".to_string(),
        AuthRole::Ven => "ven-client-client-id".to_string(),
    });
    let client_secret = client_secret.unwrap_or_else(|| match auth_role {
        AuthRole::Bl => "bl-client".to_string(),
        AuthRole::Ven => "ven-client".to_string(),
    });
    ClientCredentials::new(client_id, client_secret)
}

#[derive(Debug)]
pub struct MockClientRef {
    router: Arc<tokio::sync::Mutex<axum::Router>>,
}

impl MockClientRef {
    pub fn new(router: axum::Router) -> Self {
        MockClientRef {
            router: Arc::new(tokio::sync::Mutex::new(router)),
        }
    }

    pub fn into_client<K: ClientKind>(self, auth: Option<ClientCredentials>) -> Client<K> {
        Client::with_http_client(
            "https://example.com/".parse().unwrap(),
            "https://example.com/auth/token".parse().unwrap(),
            Box::new(self),
            auth,
        )
    }
}

#[async_trait]
impl HttpClient for MockClientRef {
    fn request_builder(&self, method: Method, url: Url) -> RequestBuilder {
        reqwest::Client::new().request(method, url)
    }

    async fn send(&self, req: RequestBuilder) -> reqwest::Result<Response> {
        let request = axum::http::Request::try_from(req.build()?)?;

        let response =
            ServiceExt::<axum::http::Request<Body>>::ready(&mut *self.router.lock().await)
                .await
                .unwrap()
                .call(request)
                .await
                .unwrap();

        let (parts, body) = response.into_parts();
        let body = body.collect().await.unwrap().to_bytes();
        let body = reqwest::Body::from(body);
        let response = axum::http::Response::from_parts(parts, body);

        Ok(response.into())
    }
}

fn enforce_external_only_guard() {
    if std::env::var("OPENLEADR_RS_REQUIRE_EXTERNAL_VTN").as_deref() != Ok("1") {
        return;
    }
    let external_url = std::env::var("OPENLEADR_RS_VTN_URL").or_else(|e| match e {
        VarError::NotPresent => std::env::var("OPENADR_VTN_URL"),
        other => Err(other),
    });
    match external_url {
        Ok(url) if !url.trim().is_empty() => {}
        Ok(_) => panic!("External-only test mode requires a non-empty external VTN URL"),
        Err(_) => panic!(
            "External-only test mode requires OPENLEADR_RS_VTN_URL or OPENADR_VTN_URL; refusing in-tree PostgreSQL fallback"
        ),
    }
}

fn fault_injection_enabled(value: Option<&str>) -> bool {
    value == Some("1")
}

pub fn should_inject_failure_after_create() -> bool {
    fault_injection_enabled(
        std::env::var("OPENLEADR_RS_INJECT_FAILURE_AFTER_CREATE")
            .ok()
            .as_deref(),
    )
}

pub struct TestContext<K> {
    pub client: Client<K>,
}

impl<K> Deref for TestContext<K> {
    type Target = Client<K>;
    fn deref(&self) -> &Self::Target {
        &self.client
    }
}

#[allow(unused)]
pub async fn setup<K: ClientKind>(auth_role: AuthRole) -> TestContext<K> {
    let _ = dotenvy::dotenv();
    enforce_external_only_guard();
    match std::env::var("OPENLEADR_RS_VTN_URL").or_else(|e| match e {
        VarError::NotPresent => std::env::var("OPENADR_VTN_URL"),
        other => Err(other),
    }) {
        Ok(url) => match url.parse() {
            Ok(url) => TestContext {
                client: setup_url_client_with_role(url, auth_role),
            },
            Err(e) => panic!("Could not parse URL: {e}"),
        },
        Err(VarError::NotPresent) => match std::env::var("DATABASE_URL") {
            Ok(db_url) => {
                let db = PgPool::connect(&db_url).await.unwrap();
                local_vtn_test_client(db, auth_role).await
            }
            Err(_) => panic!("Must either set DATABASE_URL or OPENLEADR_RS_VTN_URL env var"),
        },
        Err(VarError::NotUnicode(e)) => panic!("Could not parse URL: {e:?}"),
    }
}

async fn local_vtn_test_client<K: ClientKind>(db: PgPool, auth_role: AuthRole) -> TestContext<K> {
    let cred = default_credentials(auth_role);
    let storage = PostgresStorage::new(db).unwrap();

    let router = AppState::new(storage, &VtnConfig::from_env())
        .await
        .into_router();
    TestContext {
        client: MockClientRef::new(router).into_client(Some(cred)),
    }
}

// FIXME make this function independent of the storage backend
pub async fn setup_mock_client<K: ClientKind>(db: PgPool) -> Client<K> {
    let client_credentials =
        ClientCredentials::new("bl-client".to_string(), "bl-client".to_string());

    let storage = PostgresStorage::new(db).unwrap();

    let app_state = AppState::new(storage, &VtnConfig::from_env()).await;

    MockClientRef::new(app_state.into_router()).into_client(Some(client_credentials))
}

pub fn setup_url_client<K: ClientKind>(url: Url) -> Client<K> {
    setup_url_client_with_role(url, AuthRole::Bl)
}

pub fn setup_url_client_with_role<K: ClientKind>(url: Url, role: AuthRole) -> Client<K> {
    Client::with_url(url, Some(external_vtn_credentials(role)))
}

pub async fn setup_client<K: ClientKind>(db: PgPool) -> Client<K> {
    enforce_external_only_guard();
    match std::env::var("OPENLEADR_RS_VTN_URL").or_else(|e| match e {
        VarError::NotPresent => std::env::var("OPENADR_VTN_URL"),
        other => Err(other),
    }) {
        Ok(url) => match url.parse() {
            Ok(url) => setup_url_client(url),
            Err(e) => panic!("Could not parse URL: {e}"),
        },
        Err(VarError::NotPresent) => setup_mock_client(db).await,
        Err(VarError::NotUnicode(e)) => panic!("Could not parse URL: {e:?}"),
    }
}

#[allow(unused)]
pub async fn setup_program_client<K: ClientKind>(
    program_name: impl ToString,
    db: PgPool,
) -> ProgramClient<K> {
    let client = setup_client(db).await;

    let program_content = ProgramRequest {
        program_name: program_name.to_string(),
        interval_period: None,
        program_descriptions: None,
        payload_descriptors: None,
        attributes: None,
        targets: vec![],
    };

    client.create_program(program_content).await.unwrap()
}

#[allow(unused)]
pub async fn setup_client_with_role<K: ClientKind>(db: PgPool, role: AuthRole) -> Client<K> {
    enforce_external_only_guard();
    match std::env::var("OPENLEADR_RS_VTN_URL").or_else(|e| match e {
        VarError::NotPresent => std::env::var("OPENADR_VTN_URL"),
        other => Err(other),
    }) {
        Ok(url) => {
            let url = url.parse().expect("Invalid external VTN URL");
            return setup_url_client_with_role(url, role);
        }
        Err(VarError::NotPresent) => {}
        Err(VarError::NotUnicode(e)) => {
            panic!("Invalid external VTN URL environment variable: {e:?}")
        }
    }
    let cred = default_credentials(role);
    let storage = PostgresStorage::new(db).unwrap();
    let app_state = AppState::new(storage, &VtnConfig::from_env()).await;
    MockClientRef::new(app_state.into_router()).into_client(Some(cred))
}

#[cfg(test)]
mod credential_policy_tests {
    use super::{credential_policy, fault_injection_enabled};

    #[test]
    fn strict_external_rejects_missing_role_identity() {
        assert!(credential_policy(true, None, Some("secret")).is_err());
        assert!(credential_policy(true, Some("id"), None).is_err());
    }

    #[test]
    fn strict_external_rejects_whitespace_only_values() {
        assert!(credential_policy(true, Some("  "), Some("secret")).is_err());
        assert!(credential_policy(true, Some("id"), Some("  ")).is_err());
    }

    #[test]
    fn strict_external_accepts_explicit_identity() {
        assert!(credential_policy(true, Some("bl-1"), Some("secret")).is_ok());
    }

    #[test]
    fn non_strict_mode_preserves_local_defaults() {
        assert!(credential_policy(false, None, None).is_ok());
    }

    #[test]
    fn fault_injection_requires_exact_opt_in() {
        assert!(!fault_injection_enabled(None));
        assert!(!fault_injection_enabled(Some("true")));
        assert!(fault_injection_enabled(Some("1")));
    }
}
