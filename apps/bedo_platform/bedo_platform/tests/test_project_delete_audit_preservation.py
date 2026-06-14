from pathlib import Path


def test_project_delete_does_not_delete_security_events():
    source = Path(__file__).parents[1] / "services" / "project_service.py"
    text = source.read_text(encoding="utf-8")
    function_body = text.split("def delete_project_cascade", 1)[1].split("def _create_initial_workflow", 1)[0]

    assert '"BEDO Security Event"' not in function_body
