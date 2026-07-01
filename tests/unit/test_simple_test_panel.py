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
        "采集状态",
        "采集示例",
        "读取采集状态",
        "&#x7f51;&#x7ad9;&#x72b6;&#x6001; JSON",
        "&#x5bfc;&#x5165;&#x7f51;&#x7ad9;&#x72b6;&#x6001;",
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
        'id="collectedScenario"',
        'id="loadCollectedState"',
        'id="websiteStateJson"',
        'id="importWebsiteState"',
        'id="runAnalysis"',
        'id="resultPanel"',
    ]

    for token in required_tokens:
        assert token in html


def test_panel_posts_to_analyze_endpoint_and_renders_result():
    html = read_panel()

    assert 'fetch("/api/analyze"' in html
    assert 'fetch("/api/collected-state?scenario=" + encodeURIComponent(scenario))' in html
    assert 'fetch("/api/import-website-state"' in html
    assert "function readState()" in html
    assert "function loadCollectedState()" in html
    assert "function importWebsiteState()" in html
    assert "function applyRawState(rawState)" in html
    assert "Array.isArray(rawState.known_hands.hero)" in html
    assert 'button.disabled = true' in html
    assert 'select.disabled = true' in html
    assert 'button.textContent = "读取中..."' in html
    assert 'button.disabled = false' in html
    assert 'select.disabled = false' in html
    assert 'button.textContent = "读取采集状态"' in html
    assert "finally {" in html
    assert 'byId("loadCollectedState").addEventListener("click", loadCollectedState)' in html
    assert 'byId("importWebsiteState").addEventListener("click", importWebsiteState)' in html
    assert "采集状态已读取，可以开始分析。" in html
    assert "\\u7f51\\u7ad9\\u72b6\\u6001\\u5df2\\u5bfc\\u5165" in html
    assert "JSON \\u683c\\u5f0f\\u9519\\u8bef" in html
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
