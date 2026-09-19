from routes.missing_apis import DocumentIn, TaskIn, TaskPatch


def test_task_contract_keeps_movement_context_fields():
    task = TaskIn(
        label="Préparer le rendez-vous client",
        project_id="project-42",
        planned_for="2026-08-18",
        estimated_minutes=45,
        decision_id="decision-7",
        vision_pillar_id="stabilite",
        defer_reason="Attente du brief client",
    )
    payload = task.dict()
    assert payload["project_id"] == "project-42"
    assert payload["planned_for"] == "2026-08-18"
    assert payload["estimated_minutes"] == 45
    assert payload["defer_reason"] == "Attente du brief client"


def test_task_patch_and_resource_url_are_supported():
    patch = TaskPatch(project_id="project-42", planned_for="2026-08-19", estimated_minutes=30)
    document = DocumentIn(name="Brief client", url="https://example.test/brief")
    assert patch.dict(exclude_unset=True)["project_id"] == "project-42"
    assert patch.dict(exclude_unset=True)["estimated_minutes"] == 30
    assert document.url == "https://example.test/brief"
