import pytest
from pydantic import ValidationError

from routes.simulation import StartRequest, SubmitRequest


def test_campus_start_contract_keeps_the_declared_programme_and_level():
    request = StartRequest(
        programme_label="Reconversion — gestion de projet",
        diploma_level="bachelor",
    )
    assert request.programme_label == "Reconversion — gestion de projet"
    assert request.diploma_level == "bachelor"


def test_campus_feedback_requires_a_real_user_response():
    response = SubmitRequest(response_text="Je commencerais par clarifier le besoin du client.")
    assert response.response_text.startswith("Je commencerais")

    with pytest.raises(ValidationError):
        SubmitRequest(response_text="Oui")
