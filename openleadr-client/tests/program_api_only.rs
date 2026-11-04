//! Opt-in, black-box Program lifecycle smoke test for Issue #53.
//!
//! Run against a disposable VTN with a client allowed to manage Programs:
//! OPENLEADR_RS_VTN_URL=http://127.0.0.1:3000 \
//! OPENLEADR_RS_CLIENT_ID=... OPENLEADR_RS_CLIENT_SECRET=... \
//! cargo test -p openleadr-client --test program_api_only -- --ignored
//!
//! The VTN must be a test instance. This test writes a Program and deletes it.
//! No PgPool, sqlx fixture, PostgresStorage, or in-process VTN is used here.
//! This is a first protocol-level smoke test, not a full conformance suite.

use openleadr_client::VirtualEndNode;
use openleadr_wire::program::ProgramRequest;
use serial_test::serial;
use uuid::Uuid;

mod common;

#[tokio::test]
#[serial]
#[ignore = "requires a disposable VTN at OPENLEADR_RS_VTN_URL"]
async fn program_create_read_delete_over_http() {
    let url = std::env::var("OPENLEADR_RS_VTN_URL")
        .expect("set OPENLEADR_RS_VTN_URL to a disposable test VTN");
    let url = url.parse().expect("invalid OPENLEADR_RS_VTN_URL");
    let client = common::setup_url_client::<VirtualEndNode>(url);

    // A unique name avoids collisions with existing Programs on a shared VTN.
    let name = format!("openleadr-api-only-{}", Uuid::new_v4());
    let expected = ProgramRequest {
        program_name: name,
        interval_period: None,
        program_descriptions: None,
        payload_descriptors: None,
        attributes: None,
        targets: vec![],
    };

    let created = client
        .create_program(expected.clone())
        .await
        .expect("failed to create Program through HTTP");

    // Always attempt API cleanup after creation, even when retrieval fails.
    let id = created.id().clone();
    let retrieved = client.get_program_by_id(&id).await;
    let cleanup = created.delete().await;

    // Check cleanup first, so a failed read does not conceal a failed delete.
    cleanup.expect("failed to delete test Program through HTTP");
    let missing = client.get_program_by_id(&id).await;
    assert!(
        matches!(missing, Err(ref error) if error.is_not_found()),
        "deleted Program still exists or could not be checked: {missing:?}"
    );

    let retrieved = retrieved.expect("failed to retrieve Program through HTTP");
    assert_eq!(retrieved.content(), &expected);
}
