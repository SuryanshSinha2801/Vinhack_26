# MindTrail Figma offline handoff

Editable source: https://www.figma.com/design/mAkYxgZKAwnXOm54H4lEjF/MindTrail-%E2%80%94-Student-Wellbeing-App

## Current file structure

| Page | Figma node | Status |
| --- | --- | --- |
| `00 Foundations` | `0:1` | Foundation canvas complete (`5:2`) |
| `01 Components` | `4:4` | Partially complete (`5:29`) |
| `02 Product Screens` | `4:5` | Created; product screens still pending |

The implemented component canvas currently includes:

- Button component set (`6:9`)
- Choice card component set (`6:17`)
- Progress component (`6:19`)

## Local implementation sources

- Design tokens: [`../figma-tokens.json`](../figma-tokens.json)
- Frontend contract: [`../FRONTEND_HANDOFF.md`](../FRONTEND_HANDOFF.md)
- API contract: [`../API_CONTRACT.md`](../API_CONTRACT.md)
- Product requirements: [`../../PRD.md`](../../PRD.md)

These files are the offline, version-controlled source of truth for colors, spacing, typography, states, API payloads, and screen behavior.

## Editable `.fig` copy

Figma's **File → Save local copy…** action was invoked on 2026-09-18, but the Codex in-app browser did not expose the downloaded `.fig` file to the Windows filesystem. Therefore, no `.fig` binary is checked into this folder yet.

To finish the editable offline export manually:

1. Open the editable source link above.
2. Choose **Main menu → File → Save local copy…**.
3. Save the result as `MindTrail-Student-Wellbeing-App.fig` in this folder.
4. Re-open that file in Figma Desktop once to verify it imports successfully.

Do not treat PNG/PDF exports as the editable source; they are review snapshots only.
