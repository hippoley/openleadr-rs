//! Explicit, destructive interoperability test for a dedicated external VTN.
//!
//! Run ONLY against a disposable VTN for which you have permission to create
//! and delete Programs. This is NOT a read-only test or conformance certificate.
//!
//! OPENLEADR_RS_ALLOW_MUTATION=I_UNDERSTAND \
//! OPENLEADR_RS_VTN_URL=https://isolated-vtn.example/ \
//! OPENLEADR_RS_CLIENT_ID=... OPENLEADR_RS_CLIENT_SECRET=... \
//! cargo test -p openleadr-client --test external_vtn_program_crud -- --ignored --nocapture
//!
//! If the process is killed, cleanup cannot be guaranteed. Resources use a
//! unique name so that a later operator can identify them.

use openleadr_client::BusinessLogic;
use openleadr_wire::program::ProgramRequest;
use uuid::Uuid;
use serial_test::file_serial;

mod common;
#[path = "external_mutation_guard.rs"]
mod external_mutation_guard;
#[path = "external_recovery_journal.rs"]
mod external_recovery_journal;


#[tokio::test]
#[file_serial(openleadr_external_vtn)]
#[ignore = "destructive external VTN test; explicit authorization required"]
async fn program_create_read_update_delete_without_pgpool() {
    let url = external_mutation_guard::authorized_mutation_url();
    let client = common::setup_url_client::<BusinessLogic>(url.clone());
    let original_name = format!("openleadr-interoperability-{}", Uuid::new_v4());
    let mut journal = external_recovery_journal::RecoveryJournal::begin("Program", &original_name, url.as_str())
        .expect("durable recovery journal required before remote CREATE");
    let original = ProgramRequest::new(&original_name);
    journal.record("PROGRAM_CREATE_ATTEMPT").expect("persist Program intent before POST");

    // A failed HTTP response does NOT prove CREATE was rolled back.
    // Preserve the unique name and VTN URL for operator reconciliation.
    let mut program = match client.create_program(original.clone()).await {
        Ok(program) => program,
        Err(error) => panic!(
            "PROGRAM CREATE OUTCOME UNKNOWN: name={original_name}; error={error:?}. \
             Inspect the dedicated VTN for this unique name before retrying or cleaning up."
        ),
    };
    let program_id = program.id().clone();
    journal.record(&format!("CREATED program_id={program_id:?}")).expect("journal CREATE outcome");
    eprintln!("PROGRAM_CREATED id={program_id:?} name={original_name}");

    // Collect a result rather than panicking so cleanup still runs on
    // ordinary assertion / transport failures.
    let verification = async {
        let fetched = client.get_program_by_id(&program_id).await
            .map_err(|e| format!("READ failed: {e:?}"))?;
        if fetched.content() != &original {
            return Err("READ returned unexpected Program content".to_owned());
        }
        let updated_name = format!("{original_name}-updated");
        program.content_mut().program_name = updated_name.clone();
        program.update().await
            .map_err(|e| format!("UPDATE failed: {e:?}"))?;
        let reread = client.get_program_by_id(&program_id).await
            .map_err(|e| format!("READ after UPDATE failed: {e:?}"))?;
        if reread.content().program_name != updated_name {
            return Err("UPDATE not visible on reread".to_owned());
        }
        Ok::<(), String>(())
    }.await;

    // Always attempt cleanup after successful CREATE, including when checks
    // failed. This does not protect against process termination.
    let cleanup = client.get_program_by_id(&program_id).await;
    let cleanup_result = match cleanup {
        Ok(resource) => resource.delete().await.map(|_| ()),
        Err(err) => Err(err),
    };
    if let Err(error) = cleanup_result {
        panic!(
            "CLEANUP FAILED for program {original_name} ({program_id:?}): {error:?}; verification={verification:?}"
        );
    }

    match client.get_program_by_id(&program_id).await {
        Err(e) if e.is_not_found() => (),
        other => panic!("POST-DELETE CHECK FAILED: program {original_name} {program_id:?} still observable or lookup failed: {other:?}"),
    }

    journal.record("CLEANUP_VERIFIED").expect("durably record completed cleanup");
    assert!(
        verification.is_ok(),
        "Program protocol checks failed after successful cleanup: {verification:?}"
    );
    eprintln!("PROGRAM_CRUD PASS; resource deletion verified");
}
