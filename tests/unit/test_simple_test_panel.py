from pathlib import Path


PANEL_PATH = Path(__file__).parents[2] / "app" / "ui" / "simple_test_panel.html"


def read_panel() -> str:
    return PANEL_PATH.read_text(encoding="utf-8")


def test_panel_contains_required_inputs_and_buttons():
    html = read_panel()

    required_tokens = [
        "Poker LBS-Lite Test Panel",
        'id="heroCard1"',
        'id="heroCard2"',
        'id="boardCard1"',
        'id="boardCard2"',
        'id="boardCard3"',
        'id="pot"',
        'id="heroStack"',
        'id="villainStack"',
        'id="situation"',
        'id="betSize"',
        'id="loadCheckPreset"',
        'id="loadBetPreset"',
        'id="runAnalysis"',
        'id="resultPanel"',
    ]

    for token in required_tokens:
        assert token in html


def test_panel_posts_to_analyze_endpoint_and_renders_result():
    html = read_panel()

    assert 'fetch("/api/analyze"' in html
    assert "function readState()" in html
    assert "function renderResult(result)" in html
    assert "function renderError(message)" in html
