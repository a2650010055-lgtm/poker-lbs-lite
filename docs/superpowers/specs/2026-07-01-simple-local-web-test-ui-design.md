# Simple Local Web Test UI Design

Date: 2026-07-01

## Goal

Build a simple local browser test version for the existing LBS-Lite poker strategy engine.

This version is for manual testing and demonstration. It lets the user open a local web page, enter a supported flop spot, run the current strategy engine, and see the recommended action, strategy frequencies, EV values, confidence, and reason tags.

## User-Facing Scope

The first test page supports only the current engine scope:

- Heads-up spot: BTN vs BB.
- Street: flop.
- Current actor: hero.
- Known hand: hero only.
- Position model: `BTN_vs_BB`.
- Objective: `actor_ev`.
- Two action situations:
  - BB checks to hero: legal actions are `check`, `bet_33`, `bet_75`.
  - BB bets into hero: legal actions are `fold`, `call`, `raise_3x`.

The test page does not connect to the poker website yet. It is a local control panel for proving the strategy loop works before adding website data collection.

## Non-Goals

This version does not implement:

- Real website data scraping.
- Browser extension packaging.
- Solver database lookup.
- Model training.
- Multi-known-hand team mode.
- Turn or river support.
- All-in support.
- Multiplayer table support.

Those remain later phases. The UI should not pretend those features are available.

## Recommended Approach

Use a Python local web service with no new external framework dependency.

Reasons:

- The project is already Python.
- The existing engine can be called directly in the same process.
- No install step is needed for Flask, FastAPI, Node, or frontend tooling.
- The page can be opened at a local URL such as `http://127.0.0.1:8765`.
- Later, the same boundary can be reused when the website collector sends collected state into the engine.

## Architecture

Add three small pieces:

```text
Browser test page
  -> POST /api/analyze
  -> app.web_api.analyze_raw_payload(payload)
  -> app.services.analysis_service.normalize_raw_state(raw)
  -> app.engine.analyze_hand.StrategyEngine.analyze_hand(state)
  -> JSON result
  -> Browser result panel
```

### Files

```text
app/web_api.py
app/web_server.py
app/ui/simple_test_panel.html
tests/unit/test_web_api.py
```

### `app/web_api.py`

Responsibility:

- Accept a raw state dictionary from the local test UI.
- Normalize it with `normalize_raw_state`.
- Analyze it with `StrategyEngine`.
- Convert `AnalysisResult` into JSON-safe data.
- Convert engine errors into predictable API error responses.

It should not contain HTML, CSS, or browser-specific logic.

### `app/web_server.py`

Responsibility:

- Start a local HTTP server.
- Serve `app/ui/simple_test_panel.html` on `GET /`.
- Handle `POST /api/analyze`.
- Return JSON for both success and failure.
- Default to host `127.0.0.1` and port `8765`.

It should stay thin. It should not calculate poker strategy itself.

### `app/ui/simple_test_panel.html`

Responsibility:

- Show a simple manual form.
- Let the user load preset examples.
- Send the current state to `/api/analyze`.
- Display the returned strategy result.

The page can be a single static HTML file with inline CSS and JavaScript for V0.1. If it grows later, it can be split into separate files.

## UI Design

The page is a practical test dashboard, not a marketing page.

Primary layout:

- Left side: input panel.
- Right side: result panel.
- Bottom or collapsible area: compact raw/debug result for development checks.

Input fields:

- Hero hand: two card inputs, for example `Ah`, `Kh`.
- Board: three flop card inputs, for example `Kc`, `8d`, `3s`.
- Pot size.
- Hero stack.
- Villain stack.
- Situation selector:
  - `BB check`
  - `BB bet`
- Bet size input only matters when `BB bet` is selected.

Preset buttons:

- Strong hand after BB check.
- Facing bet example.

Result display:

- Recommended action, with a display label:
  - `check` -> Check
  - `bet_33` -> Bet 33%
  - `bet_75` -> Bet 75%
  - `fold` -> Fold
  - `call` -> Call
  - `raise_3x` -> Raise 3x
- Strategy frequency bars.
- EV values.
- Confidence.
- Reason tags.
- Engine version.

## Data Contract

The browser sends a raw state shaped like the existing fixtures.

Example for BB check:

```json
{
  "mode": "single",
  "table_size": 2,
  "street": "flop",
  "position": "BTN_vs_BB",
  "current_actor": "hero",
  "hero_seat": "hero",
  "known_hands": {
    "hero": ["Ah", "Kh"]
  },
  "unknown_seats": ["villain"],
  "board": ["Kc", "8d", "3s"],
  "pot": 100,
  "effective_stacks": {
    "hero": 900,
    "villain": 900
  },
  "action_history": [
    {"player": "BB", "action": "check"}
  ],
  "objective": "actor_ev"
}
```

Example for facing a bet:

```json
{
  "mode": "single",
  "table_size": 2,
  "street": "flop",
  "position": "BTN_vs_BB",
  "current_actor": "hero",
  "hero_seat": "hero",
  "known_hands": {
    "hero": ["Qh", "Jh"]
  },
  "unknown_seats": ["villain"],
  "board": ["Kc", "8d", "3s"],
  "pot": 150,
  "effective_stacks": {
    "hero": 850,
    "villain": 850
  },
  "action_history": [
    {"player": "BB", "action": "bet", "size": 50}
  ],
  "objective": "actor_ev"
}
```

Success response:

```json
{
  "ok": true,
  "result": {
    "recommend": "bet_33",
    "strategy": {"check": 0.28, "bet_33": 0.43, "bet_75": 0.29},
    "ev": {"check": 14.04, "bet_33": 22.72, "bet_75": 15.6},
    "confidence": 0.65,
    "reason_codes": ["top_pair_top_kicker", "k_high", "rainbow", "dry"],
    "engine_version": "lbs-lite-0.1.0",
    "solver_reference": null
  }
}
```

Error response:

```json
{
  "ok": false,
  "error": "DUPLICATE_CARD"
}
```

## Error Handling

The UI should show a clear message instead of crashing when:

- A card is invalid.
- A card is duplicated.
- A required field is missing.
- The state is outside V0.1 support.
- The server cannot parse JSON.

The server should return:

- HTTP 200 with `ok: true` for successful analysis.
- HTTP 400 with `ok: false` for user input or unsupported state errors.
- HTTP 500 with `ok: false` only for unexpected internal errors.

## Testing

Add focused tests around the web API boundary.

Required tests:

- Check example returns a success response and includes `recommend`.
- Facing bet example returns only `fold`, `call`, `raise_3x` strategy keys.
- Duplicate card input returns an error response.
- Unsupported state returns an error response.

Run the existing test suite after implementation to confirm the local web layer did not change engine behavior.

## Verification

After implementation:

1. Run all tests.
2. Start the local web service.
3. Open the local URL in the browser.
4. Load the strong-hand preset and run analysis.
5. Load the facing-bet preset and run analysis.
6. Confirm the result panel updates without page reload errors.

## Future Extension Path

This local test UI prepares the later website integration:

```text
V0.1 local manual form
  -> V0.2 local page reads collected state sample
  -> V0.3 collector reads website state object or DOM
  -> V0.4 result panel shows live collected website strategy
```

The important boundary is `web_api.analyze_raw_payload(payload)`. The current manual form and the future website collector can both feed raw state into that same boundary.

## Self-Review

- No placeholders remain.
- Scope is limited to the current engine.
- The design does not require new dependencies.
- UI, server, API, and engine responsibilities are separate.
- The future website collector path is explicit but not included in this task.
