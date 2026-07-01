from pathlib import Path


PANEL_PATH = Path(__file__).parents[2] / "app" / "ui" / "simple_test_panel.html"


def read_panel() -> str:
    return PANEL_PATH.read_text(encoding="utf-8")


def test_panel_contains_required_inputs_and_buttons():
    html = read_panel()

    required_tokens = [
        "德州扑克 LBS-Lite 测试面板",
        "状态输入",
        "Hero 手牌",
        "公共牌",
        "底池和筹码",
        "面对动作",
        "过牌预设",
        "下注预设",
        "开始分析",
        "分析结果",
        "调试 JSON",
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


def test_panel_uses_expected_action_display_labels():
    html = read_panel()

    assert 'check: "过牌"' in html
    assert 'bet_33: "下注 33%"' in html
    assert 'bet_75: "下注 75%"' in html
    assert 'fold: "弃牌"' in html
    assert 'call: "跟注"' in html
    assert 'raise_3x: "加注 3x"' in html
