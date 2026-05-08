# Project 5 Retrospective — Financial Analytics Dashboard

> Process Agent artifact, IA Agents pipeline pattern. Engineer-to-engineer report. Read this before scoping Project 6.

**Date:** 2026-05-08
**Project:** financial-analytics-dashboard
**Stack:** FastAPI + asyncpg + PostgreSQL + Jinja2 + Chart.js
**Final state:** 13 feature commits, 36 / 36 pytest tests, 6 routes live, full portfolio docs

---

## Context

A solo build of a personal finance dashboard with KPIs, monthly trends, category breakdowns, budget tracking, transaction CRUD-lite (read + create), and CSV export. Server-rendered, session auth, no SPA. Project 5 of 6 in a backend portfolio Helio is finishing post-layoff.

Roughly 3 weeks active development, ~30 commits to `main` (13 feature + 1 fix + chore + docs).

---

## What worked

1. **SQL-first aggregation.** The mid-project pivot from pandas to pure SQL (window functions for percent-of-total, GROUP BY for breakdowns, COUNT(*) OVER () for paginated totals) paid off in three ways: better backend portfolio signal, fewer layers between query and template, and elegant code reviewers actually notice. `SUM(SUM(t.amount)) OVER ()` for percent-of-total in one query is the kind of detail that lands in interviews.

2. **Per-commit verification gates.** Every commit had explicit "do this before commit" steps in PROJECT_PLAN.md (curl checks, SQL spot-checks, regression on prior pages). Made every commit defensible without having to re-derive what to test.

3. **Living documentation.** PROJECT_PLAN.md and TESTS.md updated alongside code, in their own `chore(plan)` / `docs(tests)` commits. Never went stale. Anyone (including future-Helio cold-resuming) can read three files and know exactly where the project is.

4. **Conventional Commits with tight scopes.** `feat(overview): ...`, `feat(expenses): ...`, `chore(plan): ...`. Made the git log itself a navigable index of the project's lifecycle.

5. **Two-pattern test isolation.** Service-layer tests use savepoint rollback (fast, transparent); integration tests use TRUNCATE on both setup AND teardown. Recognizing that HTTP requests run in their own sessions (so savepoints aren't visible to the request handler) was the key insight — and the symmetric truncate solved the cross-pattern interference cleanly.

6. **One page = one commit.** Service + router + template + main.py wiring shipped as a single reviewable unit. Predictable cadence, easy mental model.

---

## What was friction

1. **Visual bugs slipped past automated tests.** Two real bugs (page-title block override broken because Jinja2 `{% block %}` inside `{% include %}` doesn't participate in the parent's hierarchy; bar chart 0-width because `.chart-canvas-wrap` had no explicit `width: 100%`) both passed every curl and SQL check. Only browser inspection caught them. Lesson: **HTTP-level tests are necessary but not sufficient for UI work.**

2. **ADR deferrals lingered too long.** ADR #10 said "revisit pandas at end of Phase 5". We kept the unused pandas dep for ~10 commits before finally dropping it. The deferral didn't add information — we knew the day SQL-first won. Lesson: **decide ADRs at commit time, not "revisit later".**

3. **Mid-project mode flip was disruptive.** The advisor → programmer flip in the middle of Phase 5 came after a low-motivation week, not from a clean architectural decision. CLAUDE.md had to be rewritten, scaffolds had to be retroactively cleaned, and the workflow rhythm changed. Lesson: **decide mode at project kickoff. If energy shifts mid-project, that's information about scope, not the right time to flip the framework.**

4. **Test infrastructure landed too late.** Foundation pytest fixtures came in Phase 8 (commit #9 of 13). By then, the manual verification load had been heavy — 35 curl-based checks done by hand. Several of those should have been automated when first run. Lesson: **add basic pytest fixtures in Phase 4 or 5, not Phase 8.**

5. **Cross-fixture interference wasn't caught until tests ran.** The `seeded_db` failure ("duplicate key violates users_username_key") because integration tests left committed data behind only surfaced when both test patterns existed and ran in alphabetic order. The fix was straightforward (TRUNCATE on teardown too), but spotting it required actually running the suite — design-time review wouldn't have caught it.

---

## Decisions made mid-flight

| Decision | Trigger | Outcome |
|---|---|---|
| Drop pandas, go SQL-first (ADR #10) | Realized halfway through Phase 5 service layer | Better portfolio signal; pandas dep finally removed in commit #13 |
| Mode flip: advisor → programmer | Low-motivation week + Helio's explicit ask | Unblocked velocity; cost was a CLAUDE.md rewrite + retroactive scaffold cleanup |
| Option A (cherry-pick agents) over full IA Agents pipeline integration | Pipeline assumes hexagonal + SQL Server + Lovable; project uses layered + Postgres + Jinja2 | Right call — full integration would have required pipeline updates we weren't prepared to make |
| Bug fix as separate commit (`e344024`) | Two visual bugs surfaced after Phase 5 commits already pushed | Kept feature commits clean; fix commit had its own focused scope and message |
| Move test entry "ta caro" to keep, not delete | Helio's call after the form's first manual test | Real evidence the feature works end-to-end; later deleted before final screenshots |

---

## Recommendations for Project 6

**Start:**
- Lock the agent mode (advisor vs programmer) at kickoff — write it in the project's CLAUDE.md, don't revisit
- Land basic pytest fixtures in the first or second phase (smoke tests, async client) — catch regressions early
- Add a "browser screenshot" step to any UI-touching commit's verification gate — catches visual bugs

**Stop:**
- "Revisit later" ADRs — decide at commit time
- Mixed isolation patterns without a shared rule — define the test-isolation strategy upfront, not when fixtures conflict
- Manual verification for things that cleanly automate (e.g., the SQL spot-check pattern was good — make it pytest from the start)

**Keep:**
- Per-page commit cadence (service + router + template + wiring per page commit)
- Living PROJECT_PLAN.md + TESTS.md in `docs/`
- Conventional Commits with scope (`feat(overview):`, `chore(plan):`, etc.)
- Per-commit verification gates with explicit success criteria
- TESTS.md tracker — historical record + pending checklist in one file

---

## Suggested IA Agents pipeline updates

These come back to the pipeline repo (`C:\Users\helio\Documents\GitHub\IA Agents`):

1. **Add an SSR + layered alternative track.** Current Backend Agent assumes hexagonal architecture, SQL Server, and a Lovable React frontend. For projects like this one (FastAPI SSR + Postgres + Jinja2), provide an alternative agent prompt that targets layer-based architecture and skips the `io_mapping.md` step.

2. **Consider a "Visual Verification" sub-role.** Current QA Agent focuses on logical/functional tests. The two visual bugs in Project 5 (page title, bar chart) escaped HTTP-level checks entirely. A dedicated browser-screenshot step in the QA agent's checklist would have caught both.

3. **Adopt the `TESTS.md` tracker pattern.** This project's `docs/TESTS.md` (manual verifications + pytest planned + actual results, all checkbox-able) was a high-leverage artifact. Worth adding to the pipeline's standard output set alongside `io_mapping.md` and `audit_log.md`.

4. **Decision-time, not deferred ADRs.** Add a Process Agent rule: "ADRs marked 'revisit later' must have a concrete trigger condition (e.g., 'after Phase X if Y is true'). Open-ended deferrals are an anti-pattern."

---

## Numbers

| Metric | Value |
|---|---|
| Feature commits | 13 |
| Bug fix commits | 1 |
| Doc/chore commits | ~16 |
| pytest tests | 36 (all passing) |
| Manual verifications captured | 35 |
| Bugs caught by tests | 2 (both visual, fixed in `e344024`) |
| Bugs caught in production | 0 (project never deployed beyond local Docker) |
| Lines of dashboard code | ~2,200 (app/) |
| Lines of tests | ~600 (tests/) |
| Lines of docs | ~1,000 (docs/ + README.md) |
| Average commit size | small (median 2-7 files, focused scope) |

---

## What I'd tell Project 6 me, in one paragraph

Lock the agent mode at kickoff and don't flip it mid-project. Decide ADRs when the decision is clear, not "revisit later". Add browser screenshots to the verification gate for any UI-touching commit. Land basic pytest fixtures in the first or second phase, not the eighth. Keep the per-page commit cadence and the living-docs rhythm — those were the project's spine and they kept it shippable. The work itself was fine; the framework around it is what compounded.
