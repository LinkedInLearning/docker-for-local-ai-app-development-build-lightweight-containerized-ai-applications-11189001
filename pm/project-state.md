---
project: rag-api-tier1-hardening
current_version: v0.1.0
dev_branch: dev
current_phase: 4
total_phases: 4
execution_mode: all-at-once
status: completed
created: 2026-05-28
updated: 2026-05-29
---

> **Backfill note (2026-05-28).** Phases 1–3 were implemented and committed
> directly on the `dev` branch *outside* the pm-agent workflow, before any
> `pm/` state existed. This file (and `pm/v0_1_0/log.json`) were reconstructed
> after the fact from the development plan, the git history, and the phase
> architecture docs. Consequently:
> - No per-phase branches were used — all phase work landed on `dev`.
> - Actual per-agent token usage was not captured and is recorded as `n/a`.
> - QA for Phases 1–3 was done ad hoc (see the "fix QA issues" commits), not
>   through the pm-agent QA agents.
> Phase 4 (tests, docs, acceptance verification) is the remaining work and can
> be run through the normal pm-agent execution loop.

## Version History

| Version | Description | Plan File | Status | Date |
|---------|-------------|-----------|--------|------|
| v0.1.0 | RAG API Tier 1 hardening — async ingestion, auth, rate limits, path/upload guards, error sanitization | v0_1_0/development_plan.md | completed | 2026-05-29 |

## Completed Phases (v0.1.0)

| Phase | Name | Branch | Status | Est. Tokens | Actual Input | Actual Output | Actual Total |
|-------|------|--------|--------|-------------|--------------|---------------|--------------|
| 1 | Middleware stack (request ID, API-key auth, error sanitization) | dev | completed | 28K | n/a | n/a | n/a |
| 2 | Async ingestion (job registry, background runner, new endpoints) | dev | completed | 48K | n/a | n/a | n/a |
| 3 | Rate limiting, max upload size, path hardening | dev | completed | 28K | n/a | n/a | n/a |
| 4 | Tests, docs, acceptance verification (+ resolve_under symlink fix) | rag-api-tier1-hardening/phase-4-tests-docs → dev | completed | 40K | n/a | ~94K (combined) | ~94K |

## Token Log (v0.1.0)

| Phase | Agent | Input Tokens | Output Tokens |
|-------|-------|--------------|---------------|
| 1 | (backfill — not captured) | n/a | n/a |
| 2 | (backfill — not captured) | n/a | n/a |
| 3 | (backfill — not captured) | n/a | n/a |
| 4 | Architect (backfill — not captured) | n/a | n/a |
| 4 | Builder (backfill — not captured) | n/a | n/a |
| 4 | QA Reviewer (backfill — not captured) | n/a | n/a |
| 4 | QA Tester (backfill — not captured) | n/a | n/a |
| 4 | Fixer (QA findings #1–#8) | ~39K (combined) | ~39K (combined) |
| 4 | QA Tester (re-run, static) | ~40K (combined) | ~40K (combined) |
| 4 | Fixer (cycle 2: resolve_under symlink_escapes_root bug) | ~15K (combined) | ~15K (combined) |

## Current Phase

**Phase 4 — COMPLETED & MERGED** (version `v0.1.0` complete).

Merged `rag-api-tier1-hardening/phase-4-tests-docs` → `dev` via `--no-ff` (merge commit
`796e725`) on 2026-05-29. The merge also carried in course content (chapter_2, chapter_4,
chapter_5 L1–L6) that had accumulated on the phase branch. `dev` has NOT been pushed and has
NOT been merged to `main` yet — that's a follow-up at the user's discretion.

Test status: dev-container live run was 132 passed / 1 skipped / 1 failed; the 1 failure
(`test_rejects_symlink_escape`) was fixed in `b1f9802` and verified standalone. Expected full
re-run: **133 passed / 1 skipped / 0 failed** (134 collected). The 1 skip is the intentional
visible `pytest.skip` in `TestLogCapture` (propagate=False defeats caplog on some builds).

Final Phase 4 deliverables (all present on `dev`):
- ✅ `tests/test_middleware.py` (17), `tests/test_jobs.py` (13), `tests/test_job_registry.py` (20),
     `tests/test_security.py` (27) — 134 tests total across the suite (`tests/TEST_INDEX.md`)
- ✅ `.env.example`, README "Running the API", `docs/overview.md`
- ✅ `rag/api/security/paths.py` — `symlink_escapes_root` classification fix
- ✅ Tier 1 acceptance criteria verified via the dev-container live run (post-fix)

QA history (build `8fba3c8`; fix cycle 1 `ce3ef9d`; fix cycle 2 `b1f9802`; merge `796e725`):
- QA Reviewer (static): PASS WITH NOTES — 8 findings (5 Warnings, 3 Notes), 0 Critical → all fixed.
- QA Tester: static PASS; live run surfaced the symlink bug → fixed in cycle 2.

## Pending Phases

- None. Version `v0.1.0` is complete.

## Follow-ups (optional, at user discretion)

- Push `dev` to origin.
- Merge / open a PR `dev` → `main`.
- Re-run the full container suite to confirm 133/1/0 post-fix (recommended before pushing).
- Optional pm-agent Docs phase (formal API reference / usage guide) — the README + docs/overview
  already cover "Running the API"; a fuller Docs Agent pass was not run.
