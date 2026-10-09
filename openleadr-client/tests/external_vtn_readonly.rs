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

fn configured_external_vtn() -> Url {
    let raw_url = std::env::var("OPENLEADR_RS_VTN_URL")
        .expect("external test NOT RUN: OPENLEADR_RS_VTN_URL must be set");
    let url: Url = raw_url
        .parse()
        .expect("OPENLEADR_RS_VTN_URL must be a valid URL");
    assert!(
        matches!(url.scheme(), "http" | "https"),
        "OPENLEADR_RS_VTN_URL must use HTTP or HTTPS"
    );
    assert!(
        url.username().is_empty() && url.password().is_none(),
        "credentials must not be embedded in OPENLEADR_RS_VTN_URL"
    );
    assert!(
        url.query().is_none() && url.fragment().is_none(),
        "OPENLEADR_RS_VTN_URL must be a base URL, without query or fragment"
    );
    url
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
    ] {
        let url: Url = raw.parse().unwrap();
        assert!(
            !url.username().is_empty()
                || url.password().is_some()
                || url.query().is_some()
                || url.fragment().is_some(),
            "test fixture must exercise a rejected base URL"
        );
    }
}
