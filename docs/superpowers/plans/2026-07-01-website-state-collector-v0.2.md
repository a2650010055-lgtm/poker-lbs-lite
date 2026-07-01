# Website State Collector V0.2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local website-state collection bridge that loads check/bet sample website states, converts them into the existing LBS raw state, and fills the Chinese panel for analysis.

**Architecture:** Add a focused collector converter and sample-state source under `app/collector`. Expose a read-only local endpoint through `app/web_api.py` and `app/web_server.py`; update the browser panel so collection fills existing inputs while strategy analysis still uses `/api/analyze`.

**Tech Stack:** Python 3.12 stdlib, pytest, existing stdlib HTTP server, HTML/CSS/vanilla JavaScript.

---

## File Structure

- Create `app/collector/website_state.py`
  - Defines `CollectedStateError`.
  - Validates a website-style collected state.
  - Converts collected state into `RawCollectedState`.
- Create `app/collector/sample_website_states.py`
  - Stores the two V0.2 sample website states: `check` and `bet`.
  - Returns a deep copy so tests and UI calls cannot mutate shared sample data.
- Create `tests/unit/test_website_state_collector.py`
  - Unit tests for sample lookup and conversion.
- Modify `tests/unit/test_web_api.py`
  - Unit tests for the new API helper.
- Modify `app/web_api.py`
  - Adds `load_collected_state_payload(scenario)`.
- Modify `tests/unit/test_web_server.py`
  - HTTP tests for `GET /api/collected-state`.
- Modify `app/web_server.py`
  - Adds `GET /api/collected-state?scenario=check|bet`.
- Modify `tests/unit/test_simple_test_panel.py`
  - Static checks for the collection controls and fetch call.
- Modify `app/ui/simple_test_panel.html`
  - Adds the collection controls and JavaScript fill behavior.

Use this Python command for all test runs in this plan:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider
```

---

### Task 1: Website State Converter Tests

**Files:**
- Create: `tests/unit/test_website_state_collector.py`

- [ ] **Step 1: Write the failing converter tests**

Create `tests/unit/test_website_state_collector.py` with this content:

```python
import pytest

from app.collector.sample_website_states import get_sample_website_state
from app.collector.website_state import (
    CollectedStateError,
    convert_website_state_to_raw_state,
)


def test_check_sample_converts_to_raw_state():
    raw = convert_website_state_to_raw_state(get_sample_website_state("check"))

    assert raw == {
        "mode": "single",
        "table_size": 2,
        "street": "flop",
        "position": "BTN_vs_BB",
        "current_actor": "hero",
        "hero_seat": "hero",
        "known_hands": {"hero": ["Ah", "Kh"]},
        "unknown_seats": ["villain"],
        "board": ["Kc", "8d", "3s"],
        "pot": 100,
        "effective_stacks": {"hero": 900, "villain": 900},
        "action_history": [{"player": "BB", "action": "check"}],
        "objective": "actor_ev",
    }


def test_bet_sample_converts_to_raw_state():
    raw = convert_website_state_to_raw_state(get_sample_website_state("bet"))

    assert raw["known_hands"] == {"hero": ["Qh", "Jh"]}
    assert raw["pot"] == 150
    assert raw["effective_stacks"] == {"hero": 850, "villain": 850}
    assert raw["action_history"] == [
        {"player": "BB", "action": "bet", "size": 50}
    ]


def test_missing_required_field_returns_readable_error():
    state = get_sample_website_state("check")
    del state["hero_cards"]

    with pytest.raises(CollectedStateError, match="INVALID_COLLECTED_STATE: hero_cards"):
        convert_website_state_to_raw_state(state)


def test_unsupported_action_returns_readable_error():
    state = get_sample_website_state("check")
    state["facing_action"]["action"] = "all_in"

    with pytest.raises(
        CollectedStateError,
        match="UNSUPPORTED_COLLECTED_STATE: facing_action.action",
    ):
        convert_website_state_to_raw_state(state)


def test_unknown_sample_scenario_returns_readable_error():
    with pytest.raises(CollectedStateError, match="UNSUPPORTED_COLLECTED_SCENARIO"):
        get_sample_website_state("river")
```

- [ ] **Step 2: Run converter tests and verify they fail for missing modules**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_website_state_collector.py -q
```

Expected: FAIL with `ModuleNotFoundError` for `app.collector.sample_website_states` or `app.collector.website_state`.

---

### Task 2: Website State Converter Implementation

**Files:**
- Create: `app/collector/website_state.py`
- Create: `app/collector/sample_website_states.py`
- Test: `tests/unit/test_website_state_collector.py`

- [ ] **Step 1: Create the converter module**

Create `app/collector/website_state.py` with this content:

```python
from typing import Any, TypeAlias

from app.collector.base import RawCollectedState


WebsiteState: TypeAlias = dict[str, Any]


class CollectedStateError(ValueError):
    pass


REQUIRED_FIELDS = (
    "street",
    "position",
    "current_actor",
    "hero_cards",
    "board_cards",
    "pot",
    "stacks",
    "facing_action",
)


def convert_website_state_to_raw_state(state: WebsiteState) -> RawCollectedState:
    if not isinstance(state, dict):
        raise CollectedStateError("INVALID_COLLECTED_STATE: root")

    for field in REQUIRED_FIELDS:
        if field not in state:
            raise CollectedStateError(f"INVALID_COLLECTED_STATE: {field}")

    _require_value(state, "street", "flop")
    _require_value(state, "position", "BTN_vs_BB")
    _require_value(state, "current_actor", "hero")

    hero_cards = _require_card_list(state, "hero_cards", 2)
    board_cards = _require_card_list(state, "board_cards", 3)
    pot = _require_number(state, "pot")
    stacks = _require_mapping(state, "stacks")
    hero_stack = _require_number(stacks, "hero", "stacks.hero")
    villain_stack = _require_number(stacks, "villain", "stacks.villain")
    facing_action = _require_mapping(state, "facing_action")

    return {
        "mode": "single",
        "table_size": 2,
        "street": "flop",
        "position": "BTN_vs_BB",
        "current_actor": "hero",
        "hero_seat": "hero",
        "known_hands": {"hero": hero_cards},
        "unknown_seats": ["villain"],
        "board": board_cards,
        "pot": pot,
        "effective_stacks": {"hero": hero_stack, "villain": villain_stack},
        "action_history": [_convert_facing_action(facing_action)],
        "objective": "actor_ev",
    }


def _require_value(state: WebsiteState, key: str, expected: str) -> None:
    if state.get(key) != expected:
        raise CollectedStateError(f"UNSUPPORTED_COLLECTED_STATE: {key}")


def _require_mapping(
    state: dict[str, Any],
    key: str,
    error_key: str | None = None,
) -> dict[str, Any]:
    value = state.get(key)
    if not isinstance(value, dict):
        raise CollectedStateError(f"INVALID_COLLECTED_STATE: {error_key or key}")
    return value


def _require_card_list(state: WebsiteState, key: str, length: int) -> list[str]:
    value = state.get(key)
    if (
        not isinstance(value, list)
        or len(value) != length
        or any(not isinstance(card, str) or not card for card in value)
    ):
        raise CollectedStateError(f"INVALID_COLLECTED_STATE: {key}")
    return list(value)


def _require_number(
    state: dict[str, Any],
    key: str,
    error_key: str | None = None,
) -> int | float:
    value = state.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CollectedStateError(f"INVALID_COLLECTED_STATE: {error_key or key}")
    return value


def _convert_facing_action(action: dict[str, Any]) -> dict[str, Any]:
    player = action.get("player")
    if player != "BB":
        raise CollectedStateError("UNSUPPORTED_COLLECTED_STATE: facing_action.player")

    action_name = action.get("action")
    if action_name == "check":
        return {"player": "BB", "action": "check"}

    if action_name == "bet":
        size = _require_number(action, "size", "facing_action.size")
        if size <= 0:
            raise CollectedStateError("INVALID_COLLECTED_STATE: facing_action.size")
        return {"player": "BB", "action": "bet", "size": size}

    raise CollectedStateError("UNSUPPORTED_COLLECTED_STATE: facing_action.action")
```

- [ ] **Step 2: Create sample website states**

Create `app/collector/sample_website_states.py` with this content:

```python
from copy import deepcopy

from app.collector.website_state import CollectedStateError, WebsiteState


_SAMPLE_STATES: dict[str, WebsiteState] = {
    "check": {
        "table_id": "demo-table",
        "hand_id": "demo-check-001",
        "street": "flop",
        "position": "BTN_vs_BB",
        "current_actor": "hero",
        "hero_cards": ["Ah", "Kh"],
        "board_cards": ["Kc", "8d", "3s"],
        "pot": 100,
        "stacks": {
            "hero": 900,
            "villain": 900,
        },
        "facing_action": {
            "player": "BB",
            "action": "check",
            "size": 0,
        },
    },
    "bet": {
        "table_id": "demo-table",
        "hand_id": "demo-bet-001",
        "street": "flop",
        "position": "BTN_vs_BB",
        "current_actor": "hero",
        "hero_cards": ["Qh", "Jh"],
        "board_cards": ["Kc", "8d", "3s"],
        "pot": 150,
        "stacks": {
            "hero": 850,
            "villain": 850,
        },
        "facing_action": {
            "player": "BB",
            "action": "bet",
            "size": 50,
        },
    },
}


def get_sample_website_state(scenario: str) -> WebsiteState:
    if scenario not in _SAMPLE_STATES:
        raise CollectedStateError("UNSUPPORTED_COLLECTED_SCENARIO")
    return deepcopy(_SAMPLE_STATES[scenario])
```

- [ ] **Step 3: Run converter tests and verify they pass**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_website_state_collector.py -q
```

Expected: PASS for all tests in `test_website_state_collector.py`.

- [ ] **Step 4: Commit converter work**

Run:

```powershell
git add app\collector\website_state.py app\collector\sample_website_states.py tests\unit\test_website_state_collector.py
git commit -m "feat: add website state collector"
```

---

### Task 3: Web API Collection Helper

**Files:**
- Modify: `tests/unit/test_web_api.py`
- Modify: `app/web_api.py`

- [ ] **Step 1: Add API helper tests**

Append these tests to `tests/unit/test_web_api.py`:

```python
from app.web_api import load_collected_state_payload


def test_load_collected_state_payload_returns_converted_check_state():
    response = load_collected_state_payload("check")

    assert response["ok"] is True
    assert response["collected_state"]["hand_id"] == "demo-check-001"
    assert response["raw_state"]["known_hands"] == {"hero": ["Ah", "Kh"]}
    assert response["raw_state"]["action_history"] == [
        {"player": "BB", "action": "check"}
    ]


def test_load_collected_state_payload_returns_error_for_unknown_scenario():
    response = load_collected_state_payload("unknown")

    assert response == {
        "ok": False,
        "error": "UNSUPPORTED_COLLECTED_SCENARIO",
    }
```

- [ ] **Step 2: Run API helper tests and verify they fail for missing helper**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_web_api.py -q
```

Expected: FAIL with `ImportError` or `AttributeError` for `load_collected_state_payload`.

- [ ] **Step 3: Add the API helper**

Modify `app/web_api.py` so the imports at the top include:

```python
from app.collector.sample_website_states import get_sample_website_state
from app.collector.website_state import (
    CollectedStateError,
    convert_website_state_to_raw_state,
)
```

Add this function below `analyze_raw_payload`:

```python
def load_collected_state_payload(scenario: str) -> dict:
    try:
        collected_state = get_sample_website_state(scenario)
        raw_state = convert_website_state_to_raw_state(collected_state)
    except CollectedStateError as exc:
        return {"ok": False, "error": str(exc)}

    return {
        "ok": True,
        "collected_state": collected_state,
        "raw_state": raw_state,
    }
```

- [ ] **Step 4: Run API helper tests and verify they pass**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_web_api.py -q
```

Expected: PASS for all tests in `test_web_api.py`.

- [ ] **Step 5: Commit API helper work**

Run:

```powershell
git add app\web_api.py tests\unit\test_web_api.py
git commit -m "feat: expose collected state api helper"
```

---

### Task 4: Local Web Server Endpoint

**Files:**
- Modify: `tests/unit/test_web_server.py`
- Modify: `app/web_server.py`

- [ ] **Step 1: Add server endpoint tests**

Append these tests to `tests/unit/test_web_server.py`:

```python
def test_server_collected_state_endpoint_returns_sample_raw_state():
    server, thread = start_test_server()
    host, port = server.server_address

    try:
      connection = http.client.HTTPConnection(host, port, timeout=5)
      connection.request("GET", "/api/collected-state?scenario=bet")
      response = connection.getresponse()
      body = json.loads(response.read().decode("utf-8"))
    finally:
      stop_test_server(server, thread)

    assert response.status == 200
    assert body["ok"] is True
    assert body["collected_state"]["hand_id"] == "demo-bet-001"
    assert body["raw_state"]["action_history"] == [
        {"player": "BB", "action": "bet", "size": 50}
    ]


def test_server_collected_state_endpoint_returns_400_for_unknown_scenario():
    server, thread = start_test_server()
    host, port = server.server_address

    try:
      connection = http.client.HTTPConnection(host, port, timeout=5)
      connection.request("GET", "/api/collected-state?scenario=unknown")
      response = connection.getresponse()
      body = json.loads(response.read().decode("utf-8"))
    finally:
      stop_test_server(server, thread)

    assert response.status == 400
    assert body == {
        "ok": False,
        "error": "UNSUPPORTED_COLLECTED_SCENARIO",
    }
```

- [ ] **Step 2: Run server tests and verify the new endpoint fails**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_web_server.py -q
```

Expected: FAIL with HTTP 404 for `/api/collected-state`.

- [ ] **Step 3: Wire the endpoint into the server**

Modify the imports in `app/web_server.py`:

```python
from urllib.parse import parse_qs, urlparse

from app.web_api import analyze_raw_payload, load_collected_state_payload
```

Replace the start of `do_GET` with this structure:

```python
    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path in {"/", "/index.html"}:
            self._send_bytes(
                status=200,
                body=UI_PATH.read_bytes(),
                content_type="text/html; charset=utf-8",
            )
            return

        if parsed.path == "/api/collected-state":
            query = parse_qs(parsed.query)
            scenario = query.get("scenario", ["check"])[0]
            try:
                response = load_collected_state_payload(scenario)
            except Exception:
                self._send_json(
                    status=500,
                    payload={"ok": False, "error": "INTERNAL_ERROR"},
                )
                return

            status = 200 if response.get("ok") else 400
            self._send_json(status=status, payload=response)
            return

        self._send_json(status=404, payload={"ok": False, "error": "NOT_FOUND"})
```

- [ ] **Step 4: Run server tests and verify they pass**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_web_server.py -q
```

Expected: PASS for all tests in `test_web_server.py`.

- [ ] **Step 5: Commit server endpoint work**

Run:

```powershell
git add app\web_server.py tests\unit\test_web_server.py
git commit -m "feat: serve collected state samples"
```

---

### Task 5: Chinese Panel Collection Controls

**Files:**
- Modify: `tests/unit/test_simple_test_panel.py`
- Modify: `app/ui/simple_test_panel.html`

- [ ] **Step 1: Add static panel tests**

Extend `test_panel_contains_required_inputs_and_buttons` in `tests/unit/test_simple_test_panel.py` by adding these tokens to `required_tokens`:

```python
        "采集状态",
        "采集示例",
        "读取采集状态",
        'id="collectedScenario"',
        'id="loadCollectedState"',
```

Extend `test_panel_posts_to_analyze_endpoint_and_renders_result` with these assertions:

```python
    assert 'fetch("/api/collected-state?scenario=" + encodeURIComponent(scenario))' in html
    assert "function loadCollectedState()" in html
    assert "function applyRawState(rawState)" in html
```

- [ ] **Step 2: Run panel tests and verify they fail for missing controls**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_simple_test_panel.py -q
```

Expected: FAIL because `读取采集状态`, `loadCollectedState`, and `/api/collected-state` are not in the page yet.

- [ ] **Step 3: Add collection controls to the HTML**

In `app/ui/simple_test_panel.html`, add this CSS near the existing `.actions` rules:

```css
    .collector-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(140px, auto);
      gap: 10px;
      align-items: end;
    }
```

Add this responsive rule inside the existing `@media (max-width: 860px)` block:

```css
      .collector-row {
        grid-template-columns: 1fr;
      }
```

Add this HTML block above the existing preset/action button row:

```html
          <div class="field-group">
            <div class="field-group-title">采集状态</div>
            <div class="collector-row">
              <label for="collectedScenario">采集示例
                <select id="collectedScenario">
                  <option value="check">对手过牌</option>
                  <option value="bet">对手下注</option>
                </select>
              </label>
              <button id="loadCollectedState" type="button">读取采集状态</button>
            </div>
          </div>
```

- [ ] **Step 4: Add fill behavior to the page script**

In `app/ui/simple_test_panel.html`, replace `renderEmpty()` with:

```javascript
    function renderEmpty(message) {
      const panel = clearResultPanel();
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = message || "预设已载入，确认后可以开始分析。";
      panel.appendChild(empty);
    }
```

Add these functions after `applyPreset(name)`:

```javascript
    function applyRawState(rawState) {
      const hand = rawState.known_hands && rawState.known_hands.hero
        ? rawState.known_hands.hero
        : ["", ""];
      const board = Array.isArray(rawState.board)
        ? rawState.board
        : ["", "", ""];
      const stacks = rawState.effective_stacks || {};
      const history = Array.isArray(rawState.action_history)
        ? rawState.action_history
        : [];
      const lastAction = history.length ? history[history.length - 1] : {};

      byId("heroCard1").value = hand[0] || "";
      byId("heroCard2").value = hand[1] || "";
      byId("boardCard1").value = board[0] || "";
      byId("boardCard2").value = board[1] || "";
      byId("boardCard3").value = board[2] || "";
      byId("pot").value = rawState.pot || 0;
      byId("heroStack").value = stacks.hero || 0;
      byId("villainStack").value = stacks.villain || 0;

      if (lastAction.action === "bet") {
        byId("situation").value = "bet";
        byId("betSize").value = lastAction.size || 0;
      } else {
        byId("situation").value = "check";
        byId("betSize").value = 0;
      }
    }

    async function loadCollectedState() {
      const scenario = byId("collectedScenario").value;

      try {
        const response = await fetch("/api/collected-state?scenario=" + encodeURIComponent(scenario));
        const payload = await response.json().catch(function() {
          return {};
        });
        byId("debugJson").textContent = JSON.stringify(payload, null, 2);

        if (!response.ok || !payload.ok) {
          renderError(payload.error || "采集状态读取失败");
          return;
        }

        applyRawState(payload.raw_state || {});
        byId("debugJson").textContent = JSON.stringify({
          collected_state: payload.collected_state,
          raw_state: payload.raw_state
        }, null, 2);
        renderEmpty("采集状态已读取，可以开始分析。");
      } catch (error) {
        renderError(error && error.message ? error.message : "采集状态读取失败");
      }
    }
```

Add this event listener near the other button listeners:

```javascript
    byId("loadCollectedState").addEventListener("click", loadCollectedState);
```

- [ ] **Step 5: Run panel tests and verify they pass**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_simple_test_panel.py -q
```

Expected: PASS for all tests in `test_simple_test_panel.py`.

- [ ] **Step 6: Commit panel work**

Run:

```powershell
git add app\ui\simple_test_panel.html tests\unit\test_simple_test_panel.py
git commit -m "feat: load collected state in local panel"
```

---

### Task 6: Full Verification and Local Browser Check

**Files:**
- Verify all changed files.

- [ ] **Step 1: Run the full test suite**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests -q
```

Expected: exit code 0 and all tests pass.

- [ ] **Step 2: Check Git diff for whitespace errors**

Run:

```powershell
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 3: Start a local server for browser verification**

Run:

```powershell
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m app.web_server --host 127.0.0.1 --port 8766
```

Expected: server prints a local URL ending in `http://127.0.0.1:8766`.

- [ ] **Step 4: Verify the browser workflow**

Open `http://127.0.0.1:8766/` and verify:

- The page shows `采集状态`.
- The page shows `读取采集状态`.
- Select `对手过牌`, click `读取采集状态`, and confirm the hand fields become `Ah Kh / Kc 8d 3s`.
- Click `开始分析` and confirm a strategy result appears.
- Select `对手下注`, click `读取采集状态`, and confirm the hand fields become `Qh Jh / Kc 8d 3s` and bet size `50`.
- Click `开始分析` and confirm a strategy result appears.

- [ ] **Step 5: Push the completed implementation**

Run:

```powershell
git status --short --branch
git push origin main
```

Expected: branch is clean and `main` pushes to GitHub.

---

## Spec Coverage Self-Review

- Sample website state is covered by Task 2.
- Conversion into existing LBS raw state is covered by Tasks 1 and 2.
- `GET /api/collected-state?scenario=check|bet` is covered by Tasks 3 and 4.
- Chinese panel controls are covered by Task 5.
- Collection and analysis remain separate in Task 5.
- Existing `/api/analyze` flow is not changed.
- Real website DOM reading, OCR, browser extensions, batch testing, model training, team strategy, and full Solver work are outside this V0.2 plan.
- Verification is covered by Task 6.
