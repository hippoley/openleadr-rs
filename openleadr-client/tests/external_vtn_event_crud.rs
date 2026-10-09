//! Explicitly authorized external VTN Event lifecycle probe.
//! Run against a disposable VTN only. This test mutates remote state.
//! OPENLEADR_RS_ALLOW_MUTATION=I_UNDERSTAND must be set.
//! The test attempts child-before-parent cleanup even after assertion failures.

use openleadr_client::BusinessLogic;
use openleadr_wire::{event::EventRequest, program::ProgramRequest};
use uuid::Uuid;
use serial_test::serial;

mod common;
#[path = "external_mutation_guard.rs"]
mod external_mutation_guard;

#[tokio::test]
#[serial]
#[ignore = "destructive live VTN test; requires isolated server and explicit authorization"]
async fn event_lifecycle_without_local_database() {
    let url = external_mutation_guard::authorized_mutation_url();

    let client = common::setup_url_client::<BusinessLogic>(url);
    let name = format!("openleadr-event-probe-{}", Uuid::new_v4());
    let program = client.create_program(ProgramRequest::new(&name)).await
        .expect("create parent Program failed");
    let program_id = program.id().clone();

    let request = EventRequest::new(program_id.clone()).with_event_name(&name);
    // Do not return early after creating the parent.
    let event_creation = program.create_event(request.clone()).await;
    let mut event_id = None;
    let verification = match event_creation {
        Err(err) => Err(format!("create Event failed: {err:?}")),
        Ok(mut event) => {
            let id = event.id().clone();
            event_id = Some(id.clone());
            async {
                let read = client.get_event_by_id(&id).await
                    .map_err(|e| format!("read Event failed: {e:?}"))?;
                if read.content() != &request {
                    return Err("Event content roundtrip mismatch".to_owned());
                }
                event.content_mut().event_name = Some(format!("{name}-updated"));
                event.update().await
                    .map_err(|e| format!("Event update failed: {e:?}"))?;
                let updated = client.get_event_by_id(&id).await
                    .map_err(|e| format!("reread Event failed: {e:?}"))?;
                if updated.content().event_name != Some(format!("{name}-updated")) {
                    return Err("Event update not visible".to_owned());
                }
                Ok(())
            }.await
        }
    };

    let event_cleanup = if let Some(id) = event_id {
        match client.get_event_by_id(&id).await {
            Ok(event) => event.delete().await.map(|_| ()).map_err(|e| format!("{e:?}")),
            Err(err) => Err(format!("cannot fetch Event for cleanup: {err:?}")),
        }
    } else {
        Ok(())
    };
    let parent_cleanup = match client.get_program_by_id(&program_id).await {
        Ok(p) => p.delete().await.map(|_| ()).map_err(|e| format!("{e:?}")),
        Err(err) => Err(format!("cannot fetch parent for cleanup: {err:?}")),
    };

    assert!(
        event_cleanup.is_ok() && parent_cleanup.is_ok(),
        "CLEANUP FAILED; program={program_id:?} name={name}; Event={event_cleanup:?}, parent={parent_cleanup:?}, checks={verification:?}"
    );
    assert!(verification.is_ok(), "Event checks failed: {verification:?}");
    eprintln!("EVENT_CRUD PASS; Event and parent Program removed");
}
