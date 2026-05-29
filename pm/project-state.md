---
project: rag-api-tier1-hardening
current_version: v0.1.0
dev_branch: dev
current_phase: 4
total_phases: 4
execution_mode: all-at-once
status: in_progress
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
| v0.1.0 | RAG API Tier 1 hardening — async ingestion, auth, rate limits, path/upload guards, error sanitization | v0_1_0/development_plan.md | in_progress | 2026-05-28 |

## Completed Phases (v0.1.0)

| Phase | Name | Branch | Status | Est. Tokens | Actual Input | Actual Output | Actual Total |
|-------|------|--------|--------|-------------|--------------|---------------|--------------|
| 1 | Middleware stack (request ID, API-key auth, error sanitization) | dev | completed | 28K | n/a | n/a | n/a |
| 2 | Async ingestion (job registry, background runner, new endpoints) | dev | completed | 48K | n/a | n/a | n/a |
| 3 | Rate limiting, max upload size, path hardening | dev | completed | 28K | n/a | n/a | n/a |

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

**Phase 4 — Tests, documentation, acceptance checklist verification** (in progress —
build + QA + fix cycle complete; **PAUSED awaiting merge approval** — user is running the
live pytest suite in the dev container before merge; re-invoke `/pm` to resume at pre-merge
validation / merge).

Phase 4 work is on branch `rag-api-tier1-hardening/phase-4-tests-docs` (the pm-agent
default `dev/<project>/phase-N` scheme was not used — see backfill note).

Status of deliverables:
- ✅ `tests/test_middleware.py` — 17 tests (auth + request-ID + error sanitization + log capture)
- ✅ `tests/test_jobs.py` — 13 tests (`/ingest` 202 + polling + listing)
- ✅ `tests/test_job_registry.py` — 20 tests (unit + concurrency)
- ✅ `tests/test_security.py` — 27 tests (resolve_under + upload limits + rate limits + path hardening)
- ✅ `.env.example` — sample env vars (no real keys)
- ✅ `README.md` — "Running the API" section (curl, env setup, job polling)
- ✅ `docs/overview.md` — cross-link to the plan and the new API section
- ⏳ Verify Tier 1 acceptance criteria (development plan §10 / `docs/api_production_roadmap.md` §5)
      — deferred to dev-container live pytest run.

QA cycle (commit `8fba3c8` build; QA `ce3ef9d` fix; live-run fix `b1f9802`):
- QA Tester (dynamic): PASS on static checks; live pytest/coverage/lint deferred to dev container.
- QA Reviewer (static): PASS WITH NOTES — 8 findings (5 Warnings, 3 Notes), 0 Critical.
- Fixer (cycle 1): all 8 findings + TEST_INDEX off-by-one counts addressed (commit `ce3ef9d`, tests/ only).
- QA Tester (re-run, static): PASS — no regressions, no new issues, `rag/` source untouched.
- Dev-container live run: 132 passed, 1 skipped, **1 failed** — `test_rejects_symlink_escape`
  surfaced a real classification bug in `resolve_under` (the documented `symlink_escapes_root`
  reason was dead code; symlink escapes were mislabeled `outside_allowed_root`).
- Fixer (cycle 2): fixed `rag/api/security/paths.py` to classify in-root symlink escapes via a
  lexical (pre-symlink) abspath comparison (commit `b1f9802`); all 4 resolve_under reason
  scenarios verified standalone on host. Re-run of full suite in dev container pending to
  confirm 133 passed / 1 skipped / 0 failed.

## Pending Phases

- Phase 4 — pre-merge validation + dev-container live test run, then version completion (docs/final).
