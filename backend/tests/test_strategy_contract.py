from routes.missing_apis import StrategicDecisionIn, StrategicMilestoneIn, TaskIn, TaskPatch


def test_milestone_contract_accepts_traceability_fields():
    milestone = StrategicMilestoneIn(
        title="Valider le positionnement de l’offre",
        pillar_id="croissance",
        time_window="now",
        expected_evidence="Positionnement validé par une page offre",
        project_id="project-1",
        decision_id="decision-1",
    )
    assert milestone.time_window == "now"
    assert milestone.project_id == "project-1"


def test_decision_and_mission_contract_share_milestone_reference():
    decision = StrategicDecisionIn(
        title="Choisir l’offre prioritaire",
        milestone_id="milestone-1",
        pillar_id="vision",
    )
    task = TaskIn(label="Préparer la proposition", strategic_milestone_id=decision.milestone_id)
    patch = TaskPatch(strategic_milestone_id="milestone-2")
    assert task.strategic_milestone_id == "milestone-1"
    assert patch.strategic_milestone_id == "milestone-2"
