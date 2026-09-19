import inspect

from routes.growth_copilote import work_request


def test_work_request_uses_authenticated_user_not_client_selected_id():
    """Une demande Collaborateur doit appartenir au JWT, jamais à une query string."""
    parameters = inspect.signature(work_request).parameters
    source = inspect.getsource(work_request)

    assert "user" in parameters
    assert "user_id" not in parameters
    assert "str(user.id)" in source
