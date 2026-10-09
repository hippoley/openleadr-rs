//! Opt-in, read-only protocol smoke test for an independent OpenADR VTN.
//!
//! Example:
//! OPENLEADR_RS_VTN_URL=https://vtn.example.test/ \
//! OPENLEADR_RS_CLIENT_ID=... OPENLEADR_RS_CLIENT_SECRET=... \
//! cargo test -p openleadr-client --test external_vtn_readonly -- --ignored --nocapture
//!
//! The test is ignored by default because it needs a real external service.
//! It does not use a sqlx test fixture, initialize a local VTN, or mutate resources.
//! Passing proves one authenticated Program-list request, NOT full conformance.

use openleadr_client::{BusinessLogic, Filter};
use url::Url;

mod common;

#[tokio::test]
#[ignore = "requires OPENLEADR_RS_VTN_URL and a live, authorized third-party VTN"]
async fn external_vtn_can_list_programs_without_local_database() {
    let raw_url = std::env::var("OPENLEADR_RS_VTN_URL")
        .expect("set OPENLEADR_RS_VTN_URL to the third-party VTN address");
    let url: Url = raw_url
        .parse()
        .expect("OPENLEADR_RS_VTN_URL must be a valid URL");
    assert!(
        matches!(url.scheme(), "http" | "https"),
        "OPENLEADR_RS_VTN_URL must use HTTP or HTTPS"
    );
    let client = common::setup_url_client::<BusinessLogic>(url);
    // No database handle, local server, or destructive test fixtures.
    let programs = client
        .get_program_list(Filter::none())
        .await
        .expect("third-party VTN should support an authenticated Program list request");
    eprintln!(
        "external VTN Program list: success ({} programs; read-only; not a conformance certification)",
        programs.len()
    );
}
