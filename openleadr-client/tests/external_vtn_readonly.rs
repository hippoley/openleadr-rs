//! External-VTN read-only interoperability probes.
//!
//! Run explicitly against a trusted independent OpenADR VTN:
//!
//! OPENLEADR_RS_VTN_URL=https://your-vtn.example/ \
//! OPENLEADR_RS_CLIENT_ID=... OPENLEADR_RS_CLIENT_SECRET=... \
//! cargo test -p openleadr-client --test external_vtn_readonly -- --ignored --nocapture
//!
//! No sqlx fixture, Postgres connection, in-process VTN, or mutating request.
//! Success is evidence of the specified requests only, not OpenADR certification.
//! Ignored tests are NOT successes; capture the test runner exit code and output.

use openleadr_client::{BusinessLogic, Filter};
use url::Url;

mod common;

fn validate_external_vtn_url(raw_url: &str) -> Result<Url, String> {
    let url: Url = raw_url
        .parse()
        .map_err(|e| format!("invalid external VTN URL: {e}"))?;
    if !matches!(url.scheme(), "http" | "https") {
        return Err("OPENLEADR_RS_VTN_URL must use HTTP or HTTPS".into());
    }
    // OAuth client secrets must not be sent over cleartext off-host.
    if url.scheme() == "http"
        && !matches!(url.host_str(), Some("localhost" | "127.0.0.1" | "[::1]"))
    {
        return Err("non-local external VTN URLs must use HTTPS".into());
    }
    if !url.username().is_empty() || url.password().is_some() {
        return Err("credentials must not be embedded in OPENLEADR_RS_VTN_URL".into());
    }
    if url.query().is_some() || url.fragment().is_some() {
        return Err("OPENLEADR_RS_VTN_URL must not contain query or fragment".into());
    }
    Ok(url)
}

fn configured_external_vtn() -> Url {
    let raw_url = std::env::var("OPENLEADR_RS_VTN_URL")
        .expect("external test NOT RUN: OPENLEADR_RS_VTN_URL must be set");
    validate_external_vtn_url(&raw_url).expect("invalid external VTN base URL")
}

#[tokio::test]
#[ignore = "external live VTN required; skipped does not count as conformance evidence"]
async fn external_vtn_can_list_programs_without_local_database() {
    let client = common::setup_url_client::<BusinessLogic>(configured_external_vtn());
    let programs = client
        .get_program_list(Filter::none())
        .await
        .expect("external VTN Program list request failed");
    eprintln!(
        "PROGRAM_LIST PASS: {} items; read-only, not full conformance",
        programs.len()
    );
}

#[tokio::test]
#[ignore = "external live VTN required; skipped does not count as conformance evidence"]
async fn external_vtn_can_list_events_without_local_database() {
    let client = common::setup_url_client::<BusinessLogic>(configured_external_vtn());
    let events = client
        .get_event_list(Filter::none())
        .await
        .expect("external VTN Event list request failed");
    eprintln!(
        "EVENT_LIST PASS: {} items; read-only, not full conformance",
        events.len()
    );
}

#[test]
fn rejects_embedded_authentication_and_ambiguous_base_urls() {
    for raw in [
        "https://user:secret@example.test/",
        "https://example.test/path?token=private",
        "https://example.test/path#fragment",
        "http://remote.example.test/openadr/",
    ] {
        assert!(validate_external_vtn_url(raw).is_err(), "must reject: {raw}");
    }
}

#[test]
fn accepts_clean_base_url() {
    assert!(validate_external_vtn_url("https://example.test/openadr/").is_ok());
    assert!(validate_external_vtn_url("http://127.0.0.1:3000/").is_ok());
}
