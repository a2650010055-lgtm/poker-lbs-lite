# Real Website State JSON Import V0.3A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a manual website-state JSON import path so the user can paste real test-site state, convert it to LBS raw state, fill the local panel, and then run analysis.

**Architecture:** Reuse the V0.2 Python website-state converter. Add a web API helper and local POST route, then add a compact import area to the existing local panel that calls the route and reuses `applyRawState(rawState)`.

**Tech Stack:** Python 3.12 stdlib, pytest, existing stdlib HTTP server, HTML/CSS/vanilla JavaScript.

---

## File Structure

- Modify `app/web_api.py`
  - Add `import_website_state_payload(payload)`.
  - Reuse `convert_website_state_to_raw_state`.
- Modify `tests/unit/test_web_api.py`
  - Add tests for valid import, non-object payload, and converter errors.
- Modify `app/web_server.py`
  - Add `POST /api/import-website-state`.
  - Keep existing `POST /api/analyze` behavior.
- Modify `tests/unit/test_web_server.py`
  - Add HTTP tests for the import endpoint.
- Modify `app/ui/simple_test_panel.html`
  - Add the `websiteStateJson` text area and `importWebsiteState` button.
  - Add `importWebsiteState()` JavaScript that posts JSON and fills fields.
- Modify `tests/unit/test_simple_test_panel.py`
  - Add static checks for the new import controls and JavaScript hooks.

Use this Python command for all test runs in this plan:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider
```

---

### Task 1: Web API Import Helper

**Files:**
- Modify: `tests/unit/test_web_api.py`
- Modify: `app/web_api.py`

- [ ] **Step 1: Add failing API helper tests**

Modify the import in `tests/unit/test_web_api.py` to include the new helper:

```python
from app.web_api import (
    analyze_raw_payload,
    import_website_state_payload,
    load_collected_state_payload,
)
```

Append this helper and these tests to `tests/unit/test_web_api.py`:

```python
def make_website_state() -> dict:
    return {
        "table_id": "real-table-1",
        "hand_id": "real-hand-001",
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
    }


def test_import_website_state_payload_returns_converted_raw_state():
    payload = make_website_state()

    response = import_website_state_payload(payload)

    assert response["ok"] is True
    assert response["collected_state"]["hand_id"] == "real-hand-001"
    assert response["raw_state"]["known_hands"] == {"hero": ["Ah", "Kh"]}
    assert response["raw_state"]["board"] == ["Kc", "8d", "3s"]
    assert response["raw_state"]["action_history"] == [
        {"player": "BB", "action": "check"}
    ]


def test_import_website_state_payload_rejects_non_dict_payload():
    response = import_website_state_payload(["not", "a", "state"])

    assert response == {"ok": False, "error": "INVALID_PAYLOAD"}


def test_import_website_state_payload_returns_converter_error():
    payload = make_website_state()
    del payload["hero_cards"]

    response = import_website_state_payload(payload)

    assert response == {
        "ok": False,
        "error": "INVALID_COLLECTED_STATE: hero_cards",
    }
```

- [ ] **Step 2: Run API tests and verify the helper is missing**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_web_api.py -q
```

Expected: FAIL during import because `import_website_state_payload` is not defined.

- [ ] **Step 3: Add the API helper**

Add this function to `app/web_api.py` below `load_collected_state_payload`:

```python
def import_website_state_payload(payload: Any) -> dict:
    if not isinstance(payload, dict):
        return {"ok": False, "error": "INVALID_PAYLOAD"}

    try:
        raw_state = convert_website_state_to_raw_state(payload)
    except CollectedStateError as exc:
        return {"ok": False, "error": str(exc)}

    return {
        "ok": True,
        "collected_state": payload,
        "raw_state": raw_state,
    }
```

- [ ] **Step 4: Run API tests and verify they pass**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_web_api.py -q
```

Expected: PASS for all tests in `test_web_api.py`.

- [ ] **Step 5: Commit API helper work**

Run:

```powershell
git add app\web_api.py tests\unit\test_web_api.py
git commit -m "feat: add website state import api helper"
```

---

### Task 2: Local Server Import Endpoint

**Files:**
- Modify: `tests/unit/test_web_server.py`
- Modify: `app/web_server.py`

- [ ] **Step 1: Add failing server endpoint tests**

Append this helper and these tests to `tests/unit/test_web_server.py`:

```python
def make_website_state_payload():
    return {
        "table_id": "real-table-1",
        "hand_id": "real-hand-001",
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
    }


def test_server_import_website_state_endpoint_returns_raw_state():
    server, thread = start_test_server()
    host, port = server.server_address
    payload = make_website_state_payload()

    try:
      connection = http.client.HTTPConnection(host, port, timeout=5)
      connection.request(
          "POST",
          "/api/import-website-state",
          body=json.dumps(payload).encode("utf-8"),
          headers={"Content-Type": "application/json"},
      )
      response = connection.getresponse()
      body = json.loads(response.read().decode("utf-8"))
    finally:
      stop_test_server(server, thread)

    assert response.status == 200
    assert body["ok"] is True
    assert body["collected_state"]["hand_id"] == "real-hand-001"
    assert body["raw_state"]["known_hands"] == {"hero": ["Ah", "Kh"]}
    assert body["raw_state"]["action_history"] == [
        {"player": "BB", "action": "check"}
    ]


def test_server_import_website_state_endpoint_returns_400_for_invalid_json():
    server, thread = start_test_server()
    host, port = server.server_address

    try:
      connection = http.client.HTTPConnection(host, port, timeout=5)
      connection.request(
          "POST",
          "/api/import-website-state",
          body=b"{not-json",
          headers={"Content-Type": "application/json"},
      )
      response = connection.getresponse()
      body = json.loads(response.read().decode("utf-8"))
    finally:
      stop_test_server(server, thread)

    assert response.status == 400
    assert body == {"ok": False, "error": "INVALID_JSON"}


def test_server_import_website_state_endpoint_returns_400_for_invalid_state():
    server, thread = start_test_server()
    host, port = server.server_address
    payload = make_website_state_payload()
    del payload["hero_cards"]

    try:
      connection = http.client.HTTPConnection(host, port, timeout=5)
      connection.request(
          "POST",
          "/api/import-website-state",
          body=json.dumps(payload).encode("utf-8"),
          headers={"Content-Type": "application/json"},
      )
      response = connection.getresponse()
      body = json.loads(response.read().decode("utf-8"))
    finally:
      stop_test_server(server, thread)

    assert response.status == 400
    assert body == {
        "ok": False,
        "error": "INVALID_COLLECTED_STATE: hero_cards",
    }
```

- [ ] **Step 2: Run server tests and verify the endpoint returns 404**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_web_server.py -q
```

Expected: FAIL with HTTP 404 for `/api/import-website-state`.

- [ ] **Step 3: Wire the import endpoint into the server**

Modify the `app/web_server.py` import:

```python
from app.web_api import (
    analyze_raw_payload,
    import_website_state_payload,
    load_collected_state_payload,
)
```

Replace the start of `do_POST` in `app/web_server.py` with this structure:

```python
    def do_POST(self) -> None:
        if self.path not in {"/api/analyze", "/api/import-website-state"}:
            self._send_json(status=404, payload={"ok": False, "error": "NOT_FOUND"})
            return

        try:
            payload = self._read_json_body()
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            self._send_json(status=400, payload={"ok": False, "error": "INVALID_JSON"})
            return

        try:
            if self.path == "/api/import-website-state":
                response = import_website_state_payload(payload)
            else:
                response = analyze_raw_payload(payload)
        except Exception:
            self._send_json(status=500, payload={"ok": False, "error": "INTERNAL_ERROR"})
            return

        status = 200 if response.get("ok") else 400
        self._send_json(status=status, payload=response)
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
git commit -m "feat: serve website state imports"
```

---

### Task 3: Local Panel JSON Import UI

**Files:**
- Modify: `tests/unit/test_simple_test_panel.py`
- Modify: `app/ui/simple_test_panel.html`

Use HTML numeric entities for new visible Chinese labels in the HTML source. They render as Chinese in the browser and keep the source text ASCII-safe for Windows tools:

- `&#x7f51;&#x7ad9;&#x72b6;&#x6001; JSON` renders as `网站状态 JSON`.
- `&#x5bfc;&#x5165;&#x7f51;&#x7ad9;&#x72b6;&#x6001;` renders as `导入网站状态`.

Use JavaScript Unicode escapes for new Chinese runtime messages:

- `\u8bf7\u5148\u7c98\u8d34\u7f51\u7ad9\u72b6\u6001 JSON` renders as `请先粘贴网站状态 JSON`.
- `JSON \u683c\u5f0f\u9519\u8bef` renders as `JSON 格式错误`.
- `\u7f51\u7ad9\u72b6\u6001\u5bfc\u5165\u5931\u8d25` renders as `网站状态导入失败`.
- `\u7f51\u7ad9\u72b6\u6001\u5df2\u5bfc\u5165\uff0c\u53ef\u4ee5\u5f00\u59cb\u5206\u6790\u3002` renders as `网站状态已导入，可以开始分析。`.

- [ ] **Step 1: Add failing static UI tests**

Extend `test_panel_contains_required_inputs_and_buttons` in `tests/unit/test_simple_test_panel.py` by adding these tokens to `required_tokens`:

```python
        "&#x7f51;&#x7ad9;&#x72b6;&#x6001; JSON",
        "&#x5bfc;&#x5165;&#x7f51;&#x7ad9;&#x72b6;&#x6001;",
        'id="websiteStateJson"',
        'id="importWebsiteState"',
```

Extend `test_panel_posts_to_analyze_endpoint_and_renders_result` with these assertions:

```python
    assert 'fetch("/api/import-website-state"' in html
    assert "function importWebsiteState()" in html
    assert 'byId("importWebsiteState").addEventListener("click", importWebsiteState)' in html
    assert "\\u7f51\\u7ad9\\u72b6\\u6001\\u5df2\\u5bfc\\u5165" in html
    assert "JSON \\u683c\\u5f0f\\u9519\\u8bef" in html
```

- [ ] **Step 2: Run panel tests and verify they fail for missing UI**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_simple_test_panel.py -q
```

Expected: FAIL because `websiteStateJson`, `importWebsiteState`, and `/api/import-website-state` are not in the page yet.

- [ ] **Step 3: Add text area styling**

In `app/ui/simple_test_panel.html`, replace the existing `input, select` block with these two blocks:

```css
    input,
    select,
    textarea {
      width: 100%;
      border: 1px solid #c7d2d7;
      border-radius: 6px;
      background: #fbfdfd;
      color: var(--text);
      font: inherit;
      padding: 8px 10px;
      outline: none;
    }

    input,
    select {
      height: 40px;
    }
```

Add this textarea rule near the field styles:

```css
    textarea {
      min-height: 132px;
      resize: vertical;
      line-height: 1.45;
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
    }
```

Update the focus selector:

```css
    input:focus,
    select:focus,
    textarea:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(8, 127, 140, 0.14);
    }
```

- [ ] **Step 4: Add the import controls to the panel**

In `app/ui/simple_test_panel.html`, add this block below the existing V0.2 collection field group and above the existing `.actions` button row:

```html
          <div class="field-group">
            <div class="field-group-title">&#x7f51;&#x7ad9;&#x72b6;&#x6001; JSON</div>
            <label for="websiteStateJson">&#x7f51;&#x7ad9;&#x72b6;&#x6001; JSON
              <textarea id="websiteStateJson" autocomplete="off">{
  "table_id": "real-table-1",
  "hand_id": "real-hand-001",
  "street": "flop",
  "position": "BTN_vs_BB",
  "current_actor": "hero",
  "hero_cards": ["Ah", "Kh"],
  "board_cards": ["Kc", "8d", "3s"],
  "pot": 100,
  "stacks": {
    "hero": 900,
    "villain": 900
  },
  "facing_action": {
    "player": "BB",
    "action": "check",
    "size": 0
  }
}</textarea>
            </label>
            <button id="importWebsiteState" type="button">&#x5bfc;&#x5165;&#x7f51;&#x7ad9;&#x72b6;&#x6001;</button>
          </div>
```

- [ ] **Step 5: Add the import JavaScript**

In `app/ui/simple_test_panel.html`, add this function after `loadCollectedState()`:

```javascript
    async function importWebsiteState() {
      const button = byId("importWebsiteState");
      const rawText = byId("websiteStateJson").value.trim();

      if (!rawText) {
        renderError("\u8bf7\u5148\u7c98\u8d34\u7f51\u7ad9\u72b6\u6001 JSON");
        return;
      }

      let importedState;
      try {
        importedState = JSON.parse(rawText);
      } catch (error) {
        renderError("JSON \u683c\u5f0f\u9519\u8bef");
        return;
      }

      button.disabled = true;
      button.textContent = "\u5bfc\u5165\u4e2d...";

      try {
        const response = await fetch("/api/import-website-state", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(importedState)
        });
        const payload = await response.json().catch(function() {
          return {};
        });
        byId("debugJson").textContent = JSON.stringify(payload, null, 2);

        if (!response.ok || !payload.ok) {
          renderError(payload.error || "\u7f51\u7ad9\u72b6\u6001\u5bfc\u5165\u5931\u8d25");
          return;
        }

        applyRawState(payload.raw_state || {});
        byId("debugJson").textContent = JSON.stringify({
          imported_state: payload.collected_state,
          raw_state: payload.raw_state
        }, null, 2);
        renderEmpty("\u7f51\u7ad9\u72b6\u6001\u5df2\u5bfc\u5165\uff0c\u53ef\u4ee5\u5f00\u59cb\u5206\u6790\u3002");
      } catch (error) {
        renderError(error && error.message ? error.message : "\u7f51\u7ad9\u72b6\u6001\u5bfc\u5165\u5931\u8d25");
      } finally {
        button.disabled = false;
        button.textContent = "\u5bfc\u5165\u7f51\u7ad9\u72b6\u6001";
      }
    }
```

Add this event listener near the other button listeners:

```javascript
    byId("importWebsiteState").addEventListener("click", importWebsiteState);
```

- [ ] **Step 6: Run panel tests and verify they pass**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -p no:cacheprovider tests\unit\test_simple_test_panel.py -q
```

Expected: PASS for all tests in `test_simple_test_panel.py`.

- [ ] **Step 7: Commit panel import work**

Run:

```powershell
git add app\ui\simple_test_panel.html tests\unit\test_simple_test_panel.py
git commit -m "feat: import website state json in panel"
```

---

### Task 4: Full Verification and Browser Check

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

Expected: server accepts local requests at `http://127.0.0.1:8766`.

- [ ] **Step 4: Verify valid JSON import in the browser**

Open `http://127.0.0.1:8766/` and verify:

- The page shows `网站状态 JSON`.
- The page shows `导入网站状态`.
- The text area contains a valid website-state JSON sample.
- Click `导入网站状态`.
- Confirm fields become `Ah Kh / Kc 8d 3s`, pot `100`, stacks `900/900`, situation `check`.
- Confirm debug JSON contains `imported_state` and `raw_state`.
- Click `开始分析` and confirm a strategy result appears.

- [ ] **Step 5: Verify invalid JSON handling in the browser**

In the text area, enter:

```json
{not-json
```

Click `导入网站状态`.

Expected: result panel shows `JSON 格式错误`.

- [ ] **Step 6: Verify existing V0.2 and manual flows still work**

Still on `http://127.0.0.1:8766/`:

- Click `读取采集状态` for the check example and confirm fields fill.
- Click `开始分析` and confirm a strategy result appears.
- Click the existing check preset and confirm it still fills fields.
- Click the existing bet preset and confirm it still fills fields.

- [ ] **Step 7: Push the completed implementation**

Run:

```powershell
git status --short --branch
git push origin main
```

Expected: branch is clean and pushed to GitHub.

---

## Spec Coverage Self-Review

- Manual website-state JSON import is covered by Tasks 1, 2, and 3.
- Existing V0.2 converter reuse is covered by Task 1.
- `POST /api/import-website-state` is covered by Task 2.
- Browser UI import controls and field filling are covered by Task 3.
- Bad JSON and malformed website state errors are covered by Tasks 1, 2, and 4.
- Existing V0.2 collection examples and manual presets remain in scope through Task 4 verification.
- Automatic DOM reading, OCR, website-calls-API behavior, batch import, storage, model training, multi-person expansion, strategy-engine changes, and full Solver work remain outside this V0.3A plan.
