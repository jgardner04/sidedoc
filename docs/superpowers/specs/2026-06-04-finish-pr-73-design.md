# Finish & ship PR #73 — design

**Date:** 2026-06-04
**Branch:** `claude/practical-maxwell-iefDU`
**PR:** #73 — `fix(#72): preserve bold/italic/underline/tabs across docx round-trip`
**Goal:** Resolve the open code-review findings and take PR #73 out of draft into a mergeable state — without scope creep beyond the PR's established philosophy ("fix the data-already-there bugs, track the rest").

## Context

PR #73 is fully implemented, tested (620 passing), and CI-green, sitting as a draft. It fixes 5 round-trip data-loss bugs from issue #72 and spun out 8 follow-up issues (#74–#81). A code review on the PR raised 5 findings. None block the core fixes; the task is to decide each finding's disposition, apply the small ones, and ship.

A key observation about review finding #1: the underline **position recording** in `extract.py` is *pre-existing* — this PR only adds `escape_markdown_inline` on top of it plus the new overlay consumer in `reconstruct.py`. The reviewer's own argument is self-undermining (they say mistune returns *unescaped* text, which would *re-align* raw-text positions, not drift them). Whether #1 is a real bug cannot be settled by argument; it must be settled by a test.

## Disposition of the 5 review findings

| # | Finding | Disposition | Rationale |
|---|---------|-------------|-----------|
| 1 | `inline_formatting` positions recorded against raw run text; `escape_markdown_inline` doubles markdown-special chars, so an underlined run containing `*`/`_`/`` ` ``/`[`/`]`/`\` may re-apply the underline at a shifted offset. | **Test-gated.** Write a TDD test: an underlined run whose text contains a literal `*`, round-tripped, asserting the underline lands on the correct characters. If it reproduces → fix here (this PR's new overlay code). If it does not → keep the test as a regression guard and note the result in the PR. | Potential *silent corruption introduced by this PR's new code*. We neither ship "probably fine" on silent data loss nor hand-fix an unreproduced bug. The test resolves it both ways and TDD is mandatory. |
| 2 | `w:tab` handled in `extract_paragraph_content` but **not** in `_extract_cell_text_with_formatting` → tabs in table cells still dropped. | **Defer** — open a new follow-up issue, add a one-line scope note to the PR description. | Consistent with how cell-level underline was already deferred to #79. Cells are a separate extraction path; out of scope for this PR. |
| 3 | `_add_runs_with_tabs` emits an empty `<w:r><w:t/></w:r>` for a `""` segment. | **Fix here** — add guard `if not text: return []` before `paragraph.add_run`. | One line, in code this PR introduced, keeps output XML clean. |
| 4 | `addnext` insertion order relies on `paragraph.add_run` appending at the end — works today, fragile to future python-docx changes. | **Comment only** — add a clarifying comment explaining the append-then-`addnext` ordering contract. No refactor. | Correct today; the refactor is speculative ("if python-docx ever…"). YAGNI. |
| 5 | `run.underline = True` always emits a single underline, losing `WD_UNDERLINE` variants (double/dotted/dashed). | **`# TODO` comment**, defer. | Pre-existing behavior; `is_formatting_enabled` returns a bool so the variant was never captured. Very minor. |

## Ship-level decisions

1. **Issue #72 linkage.** #73 fixes only 5 of ~13 reported losses (8 tracked as #74–#81). Change the PR linkage from `fix(#72)` (which auto-closes on merge) to `refs #72` / "partially addresses #72", so #72 stays open as the umbrella until the follow-ups close it out.
2. **Final verification before un-drafting.**
   - Re-run the reporter-file round-trip (`extract` → `build`) and confirm the measured deltas in the PR description still hold (asterisks=0, italic=14, bold≈46, tabs=10).
   - Run full `pytest` on the branch tip; confirm the only failures are the 2 pre-existing `test_error_paths.py` baseline failures (unrelated to this PR).
   - Mark the PR Ready for review.

## Out of scope

- Any of the 8 already-tracked follow-up issues (#74–#81).
- Refactoring the `addnext`/overlay mechanism beyond the clarifying comment in #4.
- Capturing richer underline types (#5 beyond the TODO).
- Cell-level tab extraction beyond opening the tracking issue (#2).

## Success criteria

- Finding #1 has a committed test that documents its true behavior (and a fix if it reproduced).
- Finding #3 fixed; findings #4 and #5 have explanatory comments.
- A new issue exists for cell-tab extraction (#2), referenced in the PR.
- PR linkage updated so #72 is not auto-closed.
- Verification run green (modulo the 2 known baseline failures); PR marked Ready.
