use axum::http::StatusCode;
use futures::FutureExt;
use openleadr_client::{BusinessLogic, Error, Filter, PaginationOptions, VirtualEndNode};
use openleadr_wire::{program::ProgramRequest, target::Target};
use serial_test::serial;
use sqlx::PgPool;
use std::{panic::AssertUnwindSafe, str::FromStr};

mod common;

fn default_content() -> ProgramRequest {
    ProgramRequest {
        program_name: "program_name".to_string(),
        interval_period: None,
        program_descriptions: None,
        payload_descriptors: None,
        attributes: None,
        targets: vec![],
    }
}

#[tokio::test]
#[serial]
async fn ven_role_cannot_create_program() {
    let ctx = common::setup::<BusinessLogic>(common::AuthRole::Ven).await;
    let content = ProgramRequest {
        program_name: format!("ven-must-not-create-program-{}", uuid::Uuid::new_v4()),
        ..default_content()
    };

    match ctx.create_program(content).await {
        Ok(program) => {
            let id = program.id().clone();
            let cleanup = program.delete().await;
            panic!(
                "VEN credentials unexpectedly created Program {id}; cleanup result: {cleanup:?}"
            );
        }
        Err(err) => assert!(
            matches!(
                err,
                Error::Problem(ref problem)
                    if problem.status == StatusCode::UNAUTHORIZED
                        || problem.status == StatusCode::FORBIDDEN
            ),
            "VEN Program creation must fail with 401/403, got: {err}"
        ),
    }
}

#[tokio::test]
#[serial]
async fn concurrent_program_runs_do_not_cross_delete() {
    let ctx = common::setup::<BusinessLogic>(common::AuthRole::Bl).await;
    let run_a = uuid::Uuid::new_v4();
    let run_b = uuid::Uuid::new_v4();

    let program_a = ctx
        .create_program(ProgramRequest {
            program_name: format!("isolation-a-{run_a}"),
            ..default_content()
        })
        .await
        .unwrap();
    let program_b = ctx
        .create_program(ProgramRequest {
            program_name: format!("isolation-b-{run_b}"),
            ..default_content()
        })
        .await
        .unwrap();

    let id_a = program_a.id().clone();
    let id_b = program_b.id().clone();

    program_a.delete().await.unwrap();

    assert!(
        ctx.get_program_by_id(&id_a).await.unwrap_err().is_not_found(),
        "run A resource must be deleted"
    );
    let surviving_b = ctx
        .get_program_by_id(&id_b)
        .await
        .expect("run A cleanup must not delete run B resource");
    assert_eq!(surviving_b.content().program_name, format!("isolation-b-{run_b}"));

    surviving_b.delete().await.unwrap();
    assert!(
        ctx.get_program_by_id(&id_b).await.unwrap_err().is_not_found(),
        "run B cleanup must delete only its own resource"
    );
}

#[tokio::test]
#[serial]
async fn program_crud() {
    let ctx = common::setup::<BusinessLogic>(common::AuthRole::Bl).await;
    let run_id = uuid::Uuid::new_v4();
    let original_name = format!("program-crud-test-{run_id}");
    let updated_name = format!("program-crud-test-updated-{run_id}");
    let mut created_id = None;

    let outcome = AssertUnwindSafe(async {
        let content = ProgramRequest {
            program_name: original_name.clone(),
            ..default_content()
        };
        let created = ctx.create_program(content.clone()).await.unwrap();
        created_id = Some(created.id().clone());
        // Opt-in fault injection: the outer catch_unwind must still remove
        // every resource created before this point.
        if common::should_inject_failure_after_create() {
            panic!("intentional post-create fault injection: verify remote cleanup");
        }
        assert_eq!(created.content(), &content);

        let err = ctx.create_program(content).await.unwrap_err();
        assert!(err.is_conflict());

        let mut program = ctx.get_program_by_id(created.id()).await.unwrap();
        assert_eq!(program.content(), created.content());

        program.content_mut().program_name = updated_name.clone();
        program.update().await.unwrap();
        let updated = ctx.get_program_by_id(program.id()).await.unwrap();
        assert_eq!(updated.content().program_name, updated_name);

        program.delete().await.unwrap();
    })
    .catch_unwind()
    .await;

    let cleanup_error = if let Some(id) = created_id {
        match ctx.get_program_by_id(&id).await {
            Ok(program) => program.delete().await.err(),
            Err(err) if err.is_not_found() => None,
            Err(err) => Some(err),
        }
    } else {
        None
    };

    if let Err(payload) = outcome {
        if let Some(err) = cleanup_error {
            eprintln!("cleanup after program_crud failure also failed: {err}");
        }
        std::panic::resume_unwind(payload);
    }
    if let Some(err) = cleanup_error {
        panic!("program_crud cleanup failed: {err}");
    }
}

#[sqlx::test(fixtures("users"))]
async fn delete(db: PgPool) {
    let client = common::setup_client::<VirtualEndNode>(db).await;

    let program1 = ProgramRequest {
        program_name: "program1".to_string(),
        ..default_content()
    };
    let program2 = ProgramRequest {
        program_name: "program2".to_string(),
        ..default_content()
    };
    let program3 = ProgramRequest {
        program_name: "program3".to_string(),
        ..default_content()
    };

    let mut ids = vec![];
    for content in [program1, program2.clone(), program3] {
        ids.push(client.create_program(content).await.unwrap());
    }

    let program = client.get_program_by_id(ids[1].id()).await.unwrap();
    assert_eq!(program.content(), &program2);

    let removed = program.delete().await.unwrap();
    assert_eq!(removed.content, program2);

    let programs = client.get_program_list(Filter::none()).await.unwrap();
    assert_eq!(programs.len(), 2);
}

#[sqlx::test(fixtures("users"))]
async fn update(db: PgPool) {
    let client = common::setup_client::<VirtualEndNode>(db).await;

    let program1 = ProgramRequest {
        program_name: "program1".to_string(),
        ..default_content()
    };

    let mut program = client.create_program(program1).await.unwrap();
    let creation_date_time = program.modification_date_time();

    let program2 = ProgramRequest {
        program_name: "program1".to_string(),
        ..default_content()
    };

    *program.content_mut() = program2.clone();
    program.update().await.unwrap();

    assert_eq!(program.content(), &program2);
    assert!(program.modification_date_time() > creation_date_time);
}

#[sqlx::test(fixtures("users"))]
async fn update_same_name(db: PgPool) {
    let client = common::setup_client::<VirtualEndNode>(db).await;

    let program1 = ProgramRequest {
        program_name: "program1".to_string(),
        ..default_content()
    };

    let program2 = ProgramRequest {
        program_name: "program2".to_string(),
        ..default_content()
    };

    let _program1 = client.create_program(program1).await.unwrap();
    let mut program2 = client.create_program(program2).await.unwrap();
    let creation_date_time = program2.modification_date_time();

    let content = ProgramRequest {
        program_name: "program1".to_string(),
        ..default_content()
    };

    *program2.content_mut() = content;

    let Error::Problem(problem) = program2.update().await.unwrap_err() else {
        unreachable!()
    };

    assert_eq!(problem.status, StatusCode::CONFLICT);
    assert_eq!(program2.modification_date_time(), creation_date_time);
}

#[sqlx::test(fixtures("users"))]
async fn create_same_name(db: PgPool) {
    let client = common::setup_client::<VirtualEndNode>(db).await;

    let program1 = ProgramRequest {
        program_name: "program1".to_string(),
        ..default_content()
    };

    let _ = client.create_program(program1.clone()).await.unwrap();
    let Error::Problem(problem) = client.create_program(program1).await.unwrap_err() else {
        unreachable!()
    };

    assert_eq!(problem.status, StatusCode::CONFLICT);
}

#[sqlx::test(fixtures("users"))]
async fn retrieve_all_with_filter(db: PgPool) {
    let client = common::setup_client::<VirtualEndNode>(db).await;

    let program1 = ProgramRequest {
        program_name: "program1".to_string(),
        ..default_content()
    };
    let program2 = ProgramRequest {
        program_name: "program2".to_string(),
        targets: vec![Target::from_str("group-2").unwrap()],
        ..default_content()
    };
    let program3 = ProgramRequest {
        program_name: "program3".to_string(),
        targets: vec![Target::from_str("group-1").unwrap()],
        ..default_content()
    };
    let program4 = ProgramRequest {
        program_name: "program4".to_string(),
        targets: vec![
            Target::from_str("group-1").unwrap(),
            Target::from_str("group-3").unwrap(),
        ],
        ..default_content()
    };

    for content in [program1, program2, program3, program4] {
        let _ = client.create_program(content).await.unwrap();
    }

    let programs = client
        .get_programs(Filter::none(), PaginationOptions { skip: 0, limit: 50 })
        .await
        .unwrap();
    assert_eq!(programs.len(), 4);

    // skip
    let programs = client
        .get_programs(Filter::none(), PaginationOptions { skip: 1, limit: 50 })
        .await
        .unwrap();
    assert_eq!(programs.len(), 3);

    // limit
    let programs = client
        .get_programs(Filter::none(), PaginationOptions { skip: 0, limit: 2 })
        .await
        .unwrap();
    assert_eq!(programs.len(), 2);

    let programs = client
        .get_programs(
            Filter::By(&["test"]),
            PaginationOptions { skip: 0, limit: 50 },
        )
        .await
        .unwrap();
    assert_eq!(programs.len(), 0);

    let programs = client
        .get_programs(
            Filter::By(&["group-1", "group-2"]),
            PaginationOptions { skip: 0, limit: 50 },
        )
        .await
        .unwrap();
    assert_eq!(programs.len(), 3);

    let programs = client
        .get_programs(
            Filter::By(&["group-1", "group-3"]),
            PaginationOptions { skip: 0, limit: 50 },
        )
        .await
        .unwrap();
    assert_eq!(programs.len(), 2);

    let programs = client
        .get_programs(
            Filter::By(&["group-2", "group-3"]),
            PaginationOptions { skip: 0, limit: 50 },
        )
        .await
        .unwrap();
    assert_eq!(programs.len(), 2);

    let programs = client
        .get_programs(
            Filter::By(&["group-3"]),
            PaginationOptions { skip: 0, limit: 50 },
        )
        .await
        .unwrap();
    assert_eq!(programs.len(), 1);

    let programs = client
        .get_programs(
            Filter::By(&["group-1"]),
            PaginationOptions { skip: 0, limit: 50 },
        )
        .await
        .unwrap();
    assert_eq!(programs.len(), 2);

    let programs = client
        .get_programs(
            Filter::By(&["group-2"]),
            PaginationOptions { skip: 0, limit: 50 },
        )
        .await
        .unwrap();
    assert_eq!(programs.len(), 1);

    let programs = client
        .get_programs(
            Filter::By(&["not-existent"]),
            PaginationOptions { skip: 0, limit: 50 },
        )
        .await
        .unwrap();
    assert_eq!(programs.len(), 0);
}
