# Human Release Verification Checklist

This checklist closes evidence that cannot be proven by source inspection or the
loopback smoke probe. Run it against the current local dashboard before changing
the readiness score. Do not capture raw prompts, model responses, credentials,
private full paths, or action tokens in screenshots.

## Session Record

- Evaluated revision and patch state:
- Dashboard command/profile:
- Browser and macOS version:
- Reviewer:
- Started at / completed at:

Record each check as `PASS`, `FAIL`, or `BLOCKED`. A pass requires direct
observation at the named viewport; a larger viewport is not proxy evidence for a
smaller one.

## Viewport Matrix

Inspect every route at `1440x900`, `1024x768`, and `390x844`:

- `/`
- `/lab`
- `/radar`
- `/inventory`
- `/runs`
- `/reviews`
- `/compare`
- `/reports`
- one real artifact detail page
- one real model detail page

For each route and viewport, verify:

- No text, control, badge, chart, or table overlaps another element.
- The page has one obvious primary status or next action.
- Long model and artifact identifiers wrap, truncate with a title, or remain in a
  deliberately scrollable data region without widening the page.
- Primary actions remain visible and usable without relying on hover.
- Empty, degraded, pending, failed, and disabled states explain the next step.
- Data tables expose a stable status/action summary; secondary evidence may use
  row details or a contained horizontal scroll region.
- Charts include units, evidence authority, exclusion counts, and a plain-language
  explanation of what decisions they support.

## Keyboard And Focus

Starting with the pointer idle:

1. Press `Tab`; confirm the skip link becomes visible and moves focus to main
   content when activated.
2. Traverse primary navigation, filters, row actions, disclosure controls, and
   forms using `Tab` and `Shift+Tab`.
3. Confirm every focused control has a visible focus indicator and no focus trap.
4. Activate buttons and links with `Enter`; activate native buttons and controls
   with `Space` where supported.
5. On `/reviews`, reach the underlying evidence before any confirmation control.
6. Confirm destructive or authoritative actions require acknowledgement and do
   not execute from an accidental key press.

## Core Journey Checks

### Review And Confirmation

- `/reviews` shows pending work in primary navigation when drafts exist.
- Agreement and disagreement states are visually distinct and explained.
- Capture-error, all-zero, label-only, and metric-disagreement rows expose the
  correct remediation without opening raw private content by default.
- Confirm, edit-and-confirm, reject, rerun, and retire are not presented as
  equivalent actions.
- No draft becomes confirmed without an explicit human acknowledgement.

### Compare And Decision

- Confirmed evidence is visually authoritative over draft or unscored evidence.
- Models missing throughput or RAM are excluded from the efficiency frontier and
  the exclusion reason/count is visible.
- A user can move from comparison to a keep, watch, retest, or remove decision
  without developer guidance.

### Recovery And Degraded States

- Stop either Qdrant or the selected model server, refresh Home and Lab, and
  confirm the affected service is reported without breaking unrelated views.
- Confirm remediation names the exact local command or setting without exposing
  credentials, query strings, private URL paths, or document content.
- Restore the service and confirm status recovers without restarting the dashboard
  unless the product explicitly says a restart is required.

## Sanitized Report Review

Have a second person who did not create the report answer these questions from a
fresh export:

1. Which model is recommended for each supported workload, and why?
2. Which conclusions are confirmed versus draft or incomplete?
3. Which runs are excluded from efficiency claims, and why?
4. What should the owner test, rerun, confirm, or remove next?
5. Does the report reveal a private path, prompt, response, token, or secret?

The report passes only when questions 1-4 are answerable without developer
guidance and question 5 is `No`.

## Evidence Log

For every failure, record:

- route and viewport
- concise observed behavior
- expected behavior
- severity (`P0`-`P3`)
- sanitized screenshot filename, if useful
- backlog owner and proposed exit evidence

Store approved screenshots under a dated readiness evidence directory. Keep raw
or unsanitized captures local and ignored.

## Gate Result

This verification passes only when:

- every route passes at all three viewports;
- keyboard/focus checks pass without a blocker;
- authoritative review actions remain explicitly human-controlled;
- degraded-state recovery is understandable and non-leaky; and
- the second-person report review passes.

Any unresolved privacy, data-integrity, hidden-action, or inaccessible-control
failure is release-blocking regardless of the weighted score.

## 2026-07-18 Evidence Update

- **Viewport matrix: PASS (automated inspection).** All ten required routes had
  no page-level horizontal overflow at `1440x900`, `1024x768`, or `390x844`.
  Dense charts and tables remained inside intentional scroll regions.
- **Keyboard and focus: PENDING.** Browser automation did not provide reliable
  focus traversal evidence, so this check is not represented as passed.
- **Sanitized report review: PASS.** An independent read-only reviewer correctly
  identified the confirmed workload leaders, incomplete portfolio decisions,
  all efficiency exclusion classes, and next actions. The reviewer found no
  private path, prompt, response, token, credential, or secret.
