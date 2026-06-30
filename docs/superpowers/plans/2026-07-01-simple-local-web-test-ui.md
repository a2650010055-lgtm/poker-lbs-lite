# Simple Local Web Test UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local browser test panel that sends manual poker state input to the existing LBS-Lite strategy engine and displays the strategy result.

**Architecture:** Add a thin Python web boundary around the current engine. The browser page posts raw state JSON to a local stdlib HTTP server, `app.web_api` normalizes and analyzes the state, and the page renders the returned recommendation, strategy frequencies, EV values, confidence, reason tags, and engine version.

**Tech Stack:** Python 3.11+, stdlib `http.server`, static HTML/CSS/JavaScript, pytest.

---

## Existing Context

The current engine already supports:

- `normalize_raw_state(raw)` in `app/services/analysis_service.py`.
- `StrategyEngine().analyze_hand(state)` in `app/engine/analyze_hand.py`.
- No-bet actions: `check`, `bet_33`, `bet_75`.
- Facing-bet actions: `fold`, `call`, `raise_3x`.
- Regression fixtures in `tests/fixtures/flop_btn_bb_unopened.json` and `tests/fixtures/flop_btn_bb_facing_bet.json`.

Do not change the strategy engine in this feature unless a test proves the web layer exposed an existing bug.

## File Map

Create:

```text
app/web_api.py
app/web_server.py
app/ui/simple_test_panel.html
tests/unit/test_web_api.py
tests/unit/test_simple_test_panel.py
tests/unit/test_web_server.py
```

Responsibilities:

- `app/web_api.py`: Converts raw payloads into JSON-safe API responses. No HTML or HTTP logic.
- `app/web_server.py`: Local HTTP server. Serves the page and handles `/api/analyze`.
- `app/ui/simple_test_panel.html`: Manual browser UI. No strategy logic.
- `tests/unit/test_web_api.py`: Verifies API boundary behavior.
- `tests/unit/test_simple_test_panel.py`: Verifies the static page contains the controls and endpoint hook.
- `tests/unit/test_web_server.py`: Verifies the local server serves the page and accepts analysis requests.

Use this Python command in verification steps:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider <test-path> -q
```

## Task 1: Web API Boundary

**Files:**
- Create: `tests/unit/test_web_api.py`
- Create: `app/web_api.py`

- [ ] **Step 1: Write the failing web API tests**

Create `tests/unit/test_web_api.py`:

```python
import json
from pathlib import Path

from app.web_api import analyze_raw_payload


FIXTURE_DIR = Path(__file__).parents[1] / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_analyze_raw_payload_returns_success_for_check_spot():
    response = analyze_raw_payload(load_fixture("flop_btn_bb_unopened.json"))

    assert response["ok"] is True
    result = response["result"]
    assert result["recommend"] in result["strategy"]
    assert set(result["strategy"]) == {"check", "bet_33", "bet_75"}
    assert set(result["ev"]) == {"check", "bet_33", "bet_75"}
    assert result["engine_version"] == "lbs-lite-0.1.0"


def test_analyze_raw_payload_returns_facing_bet_actions():
    response = analyze_raw_payload(load_fixture("flop_btn_bb_facing_bet.json"))

    assert response["ok"] is True
    result = response["result"]
    assert result["recommend"] in result["strategy"]
    assert set(result["strategy"]) == {"fold", "call", "raise_3x"}
    assert set(result["ev"]) == {"fold", "call", "raise_3x"}


def test_analyze_raw_payload_returns_duplicate_card_error():
    raw = load_fixture("flop_btn_bb_unopened.json")
    raw["board"][0] = "Ah"

    response = analyze_raw_payload(raw)

    assert response == {"ok": False, "error": "DUPLICATE_CARD"}


def test_analyze_raw_payload_returns_unsupported_state_error():
    raw = load_fixture("flop_btn_bb_unopened.json")
    raw["street"] = "turn"
    raw["board"] = ["Kc", "8d", "3s", "2c"]

    response = analyze_raw_payload(raw)

    assert response["ok"] is False
    assert "unsupported street" in response["error"]


def test_analyze_raw_payload_rejects_non_dict_payload():
    response = analyze_raw_payload(["not", "a", "state"])

    assert response == {"ok": False, "error": "INVALID_PAYLOAD"}
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_web_api.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.web_api'`.

- [ ] **Step 3: Implement the API boundary**

Create `app/web_api.py`:

```python
from dataclasses import asdict
from typing import Any

from app.engine.analyze_hand import StrategyEngine
from app.schema.result import AnalysisResult
from app.services.analysis_service import normalize_raw_state


def analyze_raw_payload(payload: Any) -> dict:
    if not isinstance(payload, dict):
        return {"ok": False, "error": "INVALID_PAYLOAD"}

    try:
        state = normalize_raw_state(payload)
        result = StrategyEngine().analyze_hand(state)
    except (KeyError, TypeError, ValueError) as exc:
        return {"ok": False, "error": _error_message(exc)}

    return {"ok": True, "result": serialize_analysis_result(result)}


def serialize_analysis_result(result: AnalysisResult) -> dict:
    return asdict(result)


def _error_message(exc: Exception) -> str:
    if isinstance(exc, KeyError):
        return f"MISSING_FIELD: {exc.args[0]}"
    message = str(exc)
    return message if message else exc.__class__.__name__
```

- [ ] **Step 4: Run the web API tests**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_web_api.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add app\web_api.py tests\unit\test_web_api.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: add web api analysis boundary"
```

## Task 2: Static Browser Test Panel

**Files:**
- Create: `tests/unit/test_simple_test_panel.py`
- Create: `app/ui/simple_test_panel.html`

- [ ] **Step 1: Write the failing static page smoke tests**

Create `tests/unit/test_simple_test_panel.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_simple_test_panel.py -q
```

Expected: FAIL with `FileNotFoundError` for `app/ui/simple_test_panel.html`.

- [ ] **Step 3: Create the static test page**

Create directory `app/ui`, then create `app/ui/simple_test_panel.html`:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Poker LBS-Lite Test Panel</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4f6f8;
      --panel: #ffffff;
      --text: #17202a;
      --muted: #637083;
      --line: #d8dee8;
      --accent: #0b7285;
      --accent-dark: #075866;
      --danger: #b42318;
      --ok: #0f7b45;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.45;
    }

    main {
      width: min(1180px, calc(100vw - 32px));
      margin: 24px auto;
    }

    header {
      margin-bottom: 16px;
    }

    h1 {
      margin: 0 0 4px;
      font-size: 26px;
      letter-spacing: 0;
    }

    .subtitle {
      margin: 0;
      color: var(--muted);
      font-size: 14px;
    }

    .layout {
      display: grid;
      grid-template-columns: minmax(320px, 440px) 1fr;
      gap: 16px;
      align-items: start;
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }

    h2 {
      margin: 0 0 12px;
      font-size: 18px;
      letter-spacing: 0;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }

    .grid.three {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    label {
      display: block;
      margin-bottom: 6px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }

    input,
    select,
    button {
      width: 100%;
      min-height: 42px;
      border-radius: 6px;
      font: inherit;
    }

    input,
    select {
      border: 1px solid var(--line);
      padding: 8px 10px;
      background: #fff;
      color: var(--text);
    }

    .section {
      margin-top: 16px;
    }

    .actions {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
      margin-top: 16px;
    }

    button {
      border: 0;
      padding: 8px 10px;
      background: #e7edf3;
      color: var(--text);
      cursor: pointer;
      font-weight: 700;
    }

    button.primary {
      background: var(--accent);
      color: #fff;
    }

    button:hover {
      filter: brightness(0.97);
    }

    button.primary:hover {
      background: var(--accent-dark);
    }

    .recommend {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 14px;
      padding: 14px;
      border: 1px solid #b8dce3;
      border-radius: 8px;
      background: #eaf7f9;
    }

    .recommend strong {
      font-size: 24px;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      padding: 4px 8px;
      border-radius: 999px;
      background: #edf2f7;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }

    .bar-row {
      margin: 12px 0;
    }

    .bar-meta {
      display: flex;
      justify-content: space-between;
      margin-bottom: 5px;
      color: var(--muted);
      font-size: 13px;
    }

    .bar-track {
      width: 100%;
      height: 12px;
      border-radius: 999px;
      background: #e8edf2;
      overflow: hidden;
    }

    .bar-fill {
      height: 100%;
      min-width: 2px;
      background: var(--accent);
    }

    .ev-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 14px;
      font-size: 14px;
    }

    .ev-table th,
    .ev-table td {
      border-bottom: 1px solid var(--line);
      padding: 8px 0;
      text-align: left;
    }

    .tags {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 14px;
    }

    .status {
      margin-top: 12px;
      color: var(--muted);
      font-size: 13px;
    }

    .error {
      color: var(--danger);
      font-weight: 700;
    }

    .ok {
      color: var(--ok);
      font-weight: 700;
    }

    pre {
      max-height: 220px;
      overflow: auto;
      margin: 16px 0 0;
      padding: 12px;
      border-radius: 6px;
      background: #101820;
      color: #e8eef5;
      font-size: 12px;
    }

    @media (max-width: 820px) {
      main {
        width: min(100vw - 20px, 720px);
        margin: 16px auto;
      }

      .layout,
      .grid,
      .grid.three,
      .actions {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Poker LBS-Lite Test Panel</h1>
      <p class="subtitle">Manual local test page for the current BTN vs BB flop strategy engine.</p>
    </header>

    <div class="layout">
      <section class="panel">
        <h2>Hand State</h2>

        <div class="grid">
          <div>
            <label for="heroCard1">Hero card 1</label>
            <input id="heroCard1" value="Ah" autocomplete="off">
          </div>
          <div>
            <label for="heroCard2">Hero card 2</label>
            <input id="heroCard2" value="Kh" autocomplete="off">
          </div>
        </div>

        <div class="section">
          <label>Flop board</label>
          <div class="grid three">
            <input id="boardCard1" value="Kc" autocomplete="off" aria-label="Board card 1">
            <input id="boardCard2" value="8d" autocomplete="off" aria-label="Board card 2">
            <input id="boardCard3" value="3s" autocomplete="off" aria-label="Board card 3">
          </div>
        </div>

        <div class="section grid">
          <div>
            <label for="pot">Pot</label>
            <input id="pot" type="number" min="0" step="1" value="100">
          </div>
          <div>
            <label for="betSize">BB bet size</label>
            <input id="betSize" type="number" min="0" step="1" value="50">
          </div>
        </div>

        <div class="section grid">
          <div>
            <label for="heroStack">Hero stack</label>
            <input id="heroStack" type="number" min="0" step="1" value="900">
          </div>
          <div>
            <label for="villainStack">Villain stack</label>
            <input id="villainStack" type="number" min="0" step="1" value="900">
          </div>
        </div>

        <div class="section">
          <label for="situation">Situation</label>
          <select id="situation">
            <option value="bb_check">BB checks to hero</option>
            <option value="bb_bet">BB bets into hero</option>
          </select>
        </div>

        <div class="actions">
          <button id="loadCheckPreset" type="button">Check preset</button>
          <button id="loadBetPreset" type="button">Bet preset</button>
          <button id="runAnalysis" class="primary" type="button">Analyze</button>
        </div>

        <div id="status" class="status">Ready.</div>
      </section>

      <section class="panel">
        <h2>Strategy Result</h2>
        <div id="resultPanel">
          <p class="subtitle">Run analysis to see the recommendation.</p>
        </div>
        <pre id="debugJson">{}</pre>
      </section>
    </div>
  </main>

  <script>
    const actionLabels = {
      check: "Check",
      bet_33: "Bet 33%",
      bet_75: "Bet 75%",
      fold: "Fold",
      call: "Call",
      raise_3x: "Raise 3x"
    };

    const fields = {
      heroCard1: document.getElementById("heroCard1"),
      heroCard2: document.getElementById("heroCard2"),
      boardCard1: document.getElementById("boardCard1"),
      boardCard2: document.getElementById("boardCard2"),
      boardCard3: document.getElementById("boardCard3"),
      pot: document.getElementById("pot"),
      heroStack: document.getElementById("heroStack"),
      villainStack: document.getElementById("villainStack"),
      situation: document.getElementById("situation"),
      betSize: document.getElementById("betSize")
    };

    function numberValue(input) {
      const value = Number(input.value);
      return Number.isFinite(value) ? value : 0;
    }

    function cardValue(input) {
      return input.value.trim();
    }

    function readState() {
      const situation = fields.situation.value;
      const actionHistory = situation === "bb_bet"
        ? [{ player: "BB", action: "bet", size: numberValue(fields.betSize) }]
        : [{ player: "BB", action: "check" }];

      return {
        mode: "single",
        table_size: 2,
        street: "flop",
        position: "BTN_vs_BB",
        current_actor: "hero",
        hero_seat: "hero",
        known_hands: {
          hero: [cardValue(fields.heroCard1), cardValue(fields.heroCard2)]
        },
        unknown_seats: ["villain"],
        board: [
          cardValue(fields.boardCard1),
          cardValue(fields.boardCard2),
          cardValue(fields.boardCard3)
        ],
        pot: numberValue(fields.pot),
        effective_stacks: {
          hero: numberValue(fields.heroStack),
          villain: numberValue(fields.villainStack)
        },
        action_history: actionHistory,
        objective: "actor_ev"
      };
    }

    function loadPreset(kind) {
      if (kind === "bet") {
        fields.heroCard1.value = "Qh";
        fields.heroCard2.value = "Jh";
        fields.boardCard1.value = "Kc";
        fields.boardCard2.value = "8d";
        fields.boardCard3.value = "3s";
        fields.pot.value = "150";
        fields.heroStack.value = "850";
        fields.villainStack.value = "850";
        fields.betSize.value = "50";
        fields.situation.value = "bb_bet";
        return;
      }

      fields.heroCard1.value = "Ah";
      fields.heroCard2.value = "Kh";
      fields.boardCard1.value = "Kc";
      fields.boardCard2.value = "8d";
      fields.boardCard3.value = "3s";
      fields.pot.value = "100";
      fields.heroStack.value = "900";
      fields.villainStack.value = "900";
      fields.betSize.value = "50";
      fields.situation.value = "bb_check";
    }

    async function runAnalysis() {
      setStatus("Analyzing...", "ok");
      const state = readState();
      document.getElementById("debugJson").textContent = JSON.stringify(state, null, 2);

      try {
        const response = await fetch("/api/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(state)
        });
        const payload = await response.json();

        document.getElementById("debugJson").textContent = JSON.stringify(payload, null, 2);

        if (!payload.ok) {
          renderError(payload.error);
          setStatus("Analysis failed.", "error");
          return;
        }

        renderResult(payload.result);
        setStatus("Analysis complete.", "ok");
      } catch (error) {
        renderError(error.message);
        setStatus("Server request failed.", "error");
      }
    }

    function renderResult(result) {
      const panel = document.getElementById("resultPanel");
      const label = actionLabels[result.recommend] || result.recommend;
      const confidence = Math.round(result.confidence * 100);

      panel.innerHTML = `
        <div class="recommend">
          <div>
            <div class="subtitle">Recommended action</div>
            <strong>${escapeHtml(label)}</strong>
          </div>
          <span class="badge">${confidence}% confidence</span>
        </div>
        ${renderStrategyBars(result.strategy, result.ev)}
        ${renderEvTable(result.ev)}
        <div class="tags">
          ${result.reason_codes.map(tag => `<span class="badge">${escapeHtml(tag)}</span>`).join("")}
        </div>
        <p class="status">Engine version: ${escapeHtml(result.engine_version)}</p>
      `;
    }

    function renderStrategyBars(strategy, ev) {
      return Object.entries(strategy).map(([action, frequency]) => {
        const percent = Math.round(frequency * 100);
        const label = actionLabels[action] || action;
        const value = Number(ev[action] || 0).toFixed(2);
        return `
          <div class="bar-row">
            <div class="bar-meta">
              <span>${escapeHtml(label)}</span>
              <span>${percent}% | EV ${value}</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill" style="width: ${percent}%"></div>
            </div>
          </div>
        `;
      }).join("");
    }

    function renderEvTable(ev) {
      const rows = Object.entries(ev).map(([action, value]) => {
        const label = actionLabels[action] || action;
        return `
          <tr>
            <td>${escapeHtml(label)}</td>
            <td>${Number(value).toFixed(2)}</td>
          </tr>
        `;
      }).join("");

      return `
        <table class="ev-table">
          <thead>
            <tr><th>Action</th><th>EV</th></tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      `;
    }

    function renderError(message) {
      document.getElementById("resultPanel").innerHTML = `
        <p class="error">${escapeHtml(message || "Unknown error")}</p>
      `;
    }

    function setStatus(message, kind) {
      const status = document.getElementById("status");
      status.textContent = message;
      status.className = `status ${kind || ""}`;
    }

    function escapeHtml(value) {
      return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }

    document.getElementById("loadCheckPreset").addEventListener("click", () => loadPreset("check"));
    document.getElementById("loadBetPreset").addEventListener("click", () => loadPreset("bet"));
    document.getElementById("runAnalysis").addEventListener("click", runAnalysis);
  </script>
</body>
</html>
```

- [ ] **Step 4: Run the static page tests**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_simple_test_panel.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add app\ui\simple_test_panel.html tests\unit\test_simple_test_panel.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: add local strategy test panel"
```

## Task 3: Local HTTP Server

**Files:**
- Create: `tests/unit/test_web_server.py`
- Create: `app/web_server.py`

- [ ] **Step 1: Write the failing server tests**

Create `tests/unit/test_web_server.py`:

```python
import http.client
import json
import threading

from app.web_server import create_server


def start_test_server():
    server = create_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def stop_test_server(server, thread):
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def test_server_serves_index_page():
    server, thread = start_test_server()
    host, port = server.server_address

    try:
      connection = http.client.HTTPConnection(host, port, timeout=5)
      connection.request("GET", "/")
      response = connection.getresponse()
      body = response.read().decode("utf-8")
    finally:
      stop_test_server(server, thread)

    assert response.status == 200
    assert response.getheader("Content-Type") == "text/html; charset=utf-8"
    assert "Poker LBS-Lite Test Panel" in body


def test_server_analyze_endpoint_returns_strategy_json():
    server, thread = start_test_server()
    host, port = server.server_address
    payload = {
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

    try:
      connection = http.client.HTTPConnection(host, port, timeout=5)
      connection.request(
          "POST",
          "/api/analyze",
          body=json.dumps(payload).encode("utf-8"),
          headers={"Content-Type": "application/json"},
      )
      response = connection.getresponse()
      body = json.loads(response.read().decode("utf-8"))
    finally:
      stop_test_server(server, thread)

    assert response.status == 200
    assert body["ok"] is True
    assert body["result"]["recommend"] in body["result"]["strategy"]


def test_server_returns_400_for_invalid_json():
    server, thread = start_test_server()
    host, port = server.server_address

    try:
      connection = http.client.HTTPConnection(host, port, timeout=5)
      connection.request(
          "POST",
          "/api/analyze",
          body=b"{not-json",
          headers={"Content-Type": "application/json"},
      )
      response = connection.getresponse()
      body = json.loads(response.read().decode("utf-8"))
    finally:
      stop_test_server(server, thread)

    assert response.status == 400
    assert body == {"ok": False, "error": "INVALID_JSON"}
```

- [ ] **Step 2: Run the server tests to verify they fail**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_web_server.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.web_server'`.

- [ ] **Step 3: Implement the local HTTP server**

Create `app/web_server.py`:

```python
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app.web_api import analyze_raw_payload


UI_PATH = Path(__file__).resolve().parent / "ui" / "simple_test_panel.html"


class StrategyRequestHandler(BaseHTTPRequestHandler):
    server_version = "PokerLBSLite/0.1"

    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            self._send_bytes(
                status=200,
                body=UI_PATH.read_bytes(),
                content_type="text/html; charset=utf-8",
            )
            return

        self._send_json(status=404, payload={"ok": False, "error": "NOT_FOUND"})

    def do_POST(self) -> None:
        if self.path != "/api/analyze":
            self._send_json(status=404, payload={"ok": False, "error": "NOT_FOUND"})
            return

        try:
            payload = self._read_json_body()
        except json.JSONDecodeError:
            self._send_json(status=400, payload={"ok": False, "error": "INVALID_JSON"})
            return

        try:
            response = analyze_raw_payload(payload)
        except Exception:
            self._send_json(status=500, payload={"ok": False, "error": "INTERNAL_ERROR"})
            return

        status = 200 if response.get("ok") else 400
        self._send_json(status=status, payload=response)

    def _read_json_body(self) -> object:
        length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(length).decode("utf-8")
        return json.loads(body)

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(status=status, body=body, content_type="application/json")

    def _send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


def create_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), StrategyRequestHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local LBS-Lite test panel.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    server = create_server(args.host, args.port)
    host, port = server.server_address
    print(f"Serving Poker LBS-Lite Test Panel at http://{host}:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the server tests**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_web_server.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add app\web_server.py tests\unit\test_web_server.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: serve local strategy test ui"
```

## Task 4: Full Verification And Local Launch

**Files:**
- No source file changes unless verification exposes a defect.

- [ ] **Step 1: Run the complete test suite**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests -q
```

Expected: all tests pass.

- [ ] **Step 2: Start the local server**

Run:

```powershell
$workspace = (Get-Location).Path
$process = Start-Process -WindowStyle Hidden -FilePath 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -ArgumentList '-m','app.web_server','--host','127.0.0.1','--port','8765' -WorkingDirectory $workspace -PassThru
$process.Id
```

Expected: prints a process id.

- [ ] **Step 3: Verify the server responds**

Run:

```powershell
Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8765/' | Select-Object -ExpandProperty StatusCode
```

Expected:

```text
200
```

- [ ] **Step 4: Verify the analyze endpoint responds**

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

Expected: response has `ok = True` and `result.recommend` is present.

- [ ] **Step 5: Open and inspect the browser page**

Open:

```text
http://127.0.0.1:8765/
```

Verify manually:

- The page loads without a browser error.
- The check preset can run analysis.
- The bet preset can run analysis.
- The right panel updates with recommendation, frequency bars, EV values, reason tags, confidence, and engine version.
- Invalid duplicate cards display an error message.

- [ ] **Step 6: Commit any verification fix**

If a defect required a source change, run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add app tests
& 'C:\Program Files\Git\cmd\git.exe' commit -m "fix: stabilize local web test ui"
```

If no source change was needed, do not create a verification-only commit.

- [ ] **Step 7: Push final branch**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' push
```

Expected: GitHub `main` contains the local web test UI commits.

## Self-Review

Spec coverage:

- Local Python web service: Task 3.
- Manual browser form: Task 2.
- `/api/analyze` boundary: Task 1 and Task 3.
- Existing engine reuse: Task 1.
- Check and facing-bet action situations: Task 1 tests and Task 2 presets.
- Error handling: Task 1 API errors, Task 3 invalid JSON, Task 2 UI error rendering.
- Testing and verification: Tasks 1 through 4.

Gap scan:

- The plan contains concrete file paths, commands, test code, implementation code, and expected results.
- No unresolved gaps remain.

Type consistency:

- The public API function is consistently named `analyze_raw_payload`.
- The result serializer is consistently named `serialize_analysis_result`.
- The server factory is consistently named `create_server`.
- The UI posts to `/api/analyze`, matching the server route.
