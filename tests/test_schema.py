from strudel_orchestrator.schema import validate_metadata, validate_pattern_code


def test_validate_metadata_minimal_ok():
    metadata = {
        "slug": "test-track",
        "title": "Test Track",
        "tempo": 120,
        "mood": "",
        "tags": [],
        "summary": "",
    }
    errors, warnings = validate_metadata(metadata)
    assert errors == []
    # mood/tags/summary are optional but recommended
    assert any("mood" in w for w in warnings)
    assert any("tags" in w for w in warnings)
    assert any("summary" in w for w in warnings)


def test_validate_pattern_code_requires_body():
    errors, warnings = validate_pattern_code("")
    assert "Pattern body is empty." in errors


def test_validate_pattern_warns_on_gain_over_one():
    code = "sound(\"bd\").gain(1.2)"
    errors, warnings = validate_pattern_code(code)
    assert not errors
    assert any("Gain literal" in w for w in warnings)

