# Chinese Local Web UI Design

Date: 2026-07-01

## Goal

Localize the existing local Poker LBS-Lite test panel into Chinese so a non-technical Chinese-speaking user can read and use the page comfortably.

## Scope

Only the visible browser UI changes:

- Page title.
- Section headings.
- Field labels.
- Select options.
- Preset buttons.
- Run-analysis button.
- Empty, loading, success, and error messages.
- Result metric labels.
- Strategy section labels.
- Action display labels.

## Internal Contract

Keep internal values unchanged:

- API route remains `/api/analyze`.
- JSON field names remain English, such as `known_hands`, `effective_stacks`, and `action_history`.
- Engine action keys remain English, such as `check`, `bet_33`, `bet_75`, `fold`, `call`, and `raise_3x`.
- Tests should assert Chinese visible text without changing engine behavior.

## Chinese Action Labels

Use these visible labels:

```text
check -> 过牌
bet_33 -> 下注 33%
bet_75 -> 下注 75%
fold -> 弃牌
call -> 跟注
raise_3x -> 加注 3x
```

## Non-Goals

This change does not implement:

- New strategy logic.
- New poker actions.
- Website data collection.
- Solver integration.
- Model training.
- Multi-player/team strategy.
- API schema changes.

## Testing

Update static page tests to verify:

- Chinese page title exists.
- Core Chinese labels and buttons exist.
- Chinese action labels exist.
- `/api/analyze`, `readState()`, `renderResult(result)`, and `renderError(message)` still exist.

Run the full test suite after implementation.

## Verification

After implementation:

1. Run all tests.
2. Refresh `http://127.0.0.1:8765/`.
3. Confirm the page shows Chinese labels.
4. Run the check preset and confirm a Chinese recommendation appears.
5. Run the bet preset and confirm the result panel updates.

## Self-Review

- Scope is limited to visible UI localization.
- Engine/API values stay stable.
- No new dependencies are required.
- No placeholders remain.
