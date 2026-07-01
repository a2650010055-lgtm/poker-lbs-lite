# Chinese Local Web UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the visible local Poker LBS-Lite test panel UI to Chinese while keeping API fields and strategy engine values unchanged.

**Architecture:** This is a static UI localization change. `app/ui/simple_test_panel.html` changes visible text only, while `readState()` continues to emit the same English JSON field names and action keys expected by `app.web_api` and `StrategyEngine`.

**Tech Stack:** Static HTML/CSS/JavaScript, Python pytest smoke tests.

---

## Scope

Modify only:

```text
app/ui/simple_test_panel.html
tests/unit/test_simple_test_panel.py
```

Do not modify:

```text
app/web_api.py
app/web_server.py
app/engine/
app/services/
app/schema/
```

## Task 1: Update Static UI Tests For Chinese Text

**Files:**
- Modify: `tests/unit/test_simple_test_panel.py`

- [ ] **Step 1: Write failing Chinese UI assertions**

Update the first test in `tests/unit/test_simple_test_panel.py` so it expects Chinese visible text while keeping id checks unchanged:

```python
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
```

Update the action-label test:

```python
def test_panel_uses_expected_action_display_labels():
    html = read_panel()

    assert 'check: "过牌"' in html
    assert 'bet_33: "下注 33%"' in html
    assert 'bet_75: "下注 75%"' in html
    assert 'fold: "弃牌"' in html
    assert 'call: "跟注"' in html
    assert 'raise_3x: "加注 3x"' in html
```

- [ ] **Step 2: Run the static page test and verify it fails**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_simple_test_panel.py -q
```

Expected: FAIL because the page still contains English labels.

- [ ] **Step 3: Commit nothing yet**

Do not commit after this task. Task 2 implements the matching UI change and both changes are committed together.

## Task 2: Localize The Static Panel

**Files:**
- Modify: `app/ui/simple_test_panel.html`
- Test: `tests/unit/test_simple_test_panel.py`

- [ ] **Step 1: Replace visible English UI text with Chinese**

Update `app/ui/simple_test_panel.html` visible strings:

```text
Poker LBS-Lite Test Panel -> 德州扑克 LBS-Lite 测试面板
Local API target: /api/analyze -> 本地接口：/api/analyze
State Inputs -> 状态输入
Hero Hand -> Hero 手牌
Card 1 -> 手牌 1
Card 2 -> 手牌 2
Board -> 公共牌
Flop 1 -> 翻牌 1
Flop 2 -> 翻牌 2
Flop 3 -> 翻牌 3
Stacks And Pot -> 底池和筹码
Pot -> 底池
Hero Stack -> Hero 筹码
Villain Stack -> 对手筹码
Facing Action -> 面对动作
Situation -> 当前情况
Check -> 过牌
Bet -> 下注
Bet Size -> 下注额
Check Preset -> 过牌预设
Bet Preset -> 下注预设
Run Analysis -> 开始分析
Analysis Result -> 分析结果
Run a preset or edit the state, then analyze. -> 选择预设或修改牌局状态，然后开始分析。
Debug JSON -> 调试 JSON
Preset loaded. Run analysis when ready. -> 预设已载入，确认后可以开始分析。
Recommendation -> 推荐动作
Confidence -> 置信度
Engine -> 引擎版本
Strategy Frequencies -> 策略频率
Action EV -> 动作 EV
Action -> 动作
EV -> EV
Reason Tags -> 判断依据
Analysis error -> 分析出错
Analyzing current state... -> 正在分析当前牌局...
REQUEST_FAILED -> 请求失败
ANALYSIS_FAILED -> 分析失败
NETWORK_ERROR -> 网络错误
Unknown error -> 未知错误
```

- [ ] **Step 2: Replace action display labels**

Update `ACTION_LABELS` in `app/ui/simple_test_panel.html`:

```javascript
const ACTION_LABELS = {
  check: "过牌",
  bet_33: "下注 33%",
  bet_75: "下注 75%",
  fold: "弃牌",
  call: "跟注",
  raise_3x: "加注 3x"
};
```

Keep `PRESETS`, `readState()`, JSON field names, and action key values unchanged.

- [ ] **Step 3: Run the static page tests**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_simple_test_panel.py -q
```

Expected: PASS.

- [ ] **Step 4: Run the full test suite**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add app\ui\simple_test_panel.html tests\unit\test_simple_test_panel.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: localize test panel to chinese"
```

## Task 3: Browser Verification

**Files:**
- No source changes expected.

- [ ] **Step 1: Refresh the running local page**

Open or refresh:

```text
http://127.0.0.1:8765/
```

Expected: visible page text is Chinese.

- [ ] **Step 2: Verify API still works**

Run:

```powershell
$body = @{
  mode = 'single'
  table_size = 2
  street = 'flop'
  position = 'BTN_vs_BB'
  current_actor = 'hero'
  hero_seat = 'hero'
  known_hands = @{ hero = @('Ah', 'Kh') }
  unknown_seats = @('villain')
  board = @('Kc', '8d', '3s')
  pot = 100
  effective_stacks = @{ hero = 900; villain = 900 }
  action_history = @(@{ player = 'BB'; action = 'check' })
  objective = 'actor_ev'
} | ConvertTo-Json -Depth 10
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8765/api/analyze' -ContentType 'application/json' -Body $body
```

Expected: response has `ok = True` and `result.recommend = bet_33`.

## Self-Review

Spec coverage:

- Chinese visible UI text: Task 2.
- Chinese action labels: Task 2.
- Internal API/engine values unchanged: Task 2 explicitly preserves `readState()` and action keys.
- Tests updated: Task 1 and Task 2.
- Browser/API verification: Task 3.

Gap scan:

- No unresolved gaps remain.

Type consistency:

- Test file remains `tests/unit/test_simple_test_panel.py`.
- UI file remains `app/ui/simple_test_panel.html`.
- `readState()`, `renderResult(result)`, and `renderError(message)` names remain unchanged.
