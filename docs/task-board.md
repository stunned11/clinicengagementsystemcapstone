# Project Task Board

**Project:** Clinic Engagement System — Customer Health Scoring
**Last updated:** 2026-07-12 · **Release:** v1.1.0

This board tracks all agreed user stories and tasks. It is organized as a Kanban flow (**Backlog → In Progress → In Review → Done**) with MoSCoW priorities and story-point estimates. Epics A–F are delivered in v1.0.0, with a v1.1.0 revision to Epic C (below); Epic G is post-v1 roadmap work.

## v1.1.0 — CSM-workflow revision (2026-07-12)

A CSM-perspective review of the v1.0.0 dashboard found that the most actionable content (the attention list) was rendered last, below the fold, and silently ignored the status filter. This revision re-scopes Epic C around that workflow:

- **C1** — KPI row reordered (Critical/At-Risk lead) and severity-colored.
- **C3** — status filter now consistently governs the table, chart, *and* attention list (previously a gap).
- **C4** — chart bars colored by Status to match the table; worst-to-best order.
- **C5** — attention list moved above the full scorecard, filtered, and ranked by status then plan tier.
- **C7** *(new)* — recent-vs-prior trend indicator per account.

See issues [#9](https://github.com/stunned11/clinicengagementsystemcapstone/issues/9), [#11](https://github.com/stunned11/clinicengagementsystemcapstone/issues/11), [#12](https://github.com/stunned11/clinicengagementsystemcapstone/issues/12), [#13](https://github.com/stunned11/clinicengagementsystemcapstone/issues/13), [#29](https://github.com/stunned11/clinicengagementsystemcapstone/issues/29) and commit `859301c`.

## Board snapshot (Kanban)

| Backlog | In Progress | In Review | Done |
| --- | --- | --- | --- |
| G1, G2, G3, G4 | — | — | A1, A2, A3, B1, B2, B3, B4, B5, C1, C2, C3, C4, C5, C6, C7, D1, D2, E1, E2, E3, E4, F1, F2 (+ tasks T1, T2) |

## Summary

| Status | Stories | Story points |
| --- | --- | --- |
| Done | 23 | 60 |
| Backlog (Epic G) | 4 | 26 |
| **Total** | **27** | **86** |

Tasks (implementation work under stories): 2, both Done.

## Backlog — all stories & tasks

| ID | Epic | Type | Item | Priority | Pts | Sprint | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | A — Data Foundation | Story | Auto-create & seed SQLite on first run (zero setup) | Must | 3 | S1 | ✅ Done |
| A2 | A — Data Foundation | Story | 5 clinics × 30 days deterministic telemetry | Must | 3 | S1 | ✅ Done |
| A3 | A — Data Foundation | Story | Normalized schema + integrity constraints | Should | 2 | S1 | ✅ Done |
| T2 | A — Data Foundation | Task | Add `.gitignore` + pinned `requirements.txt` (under A1) | — | — | S3 | ✅ Done |
| B1 | B — Scoring Engine | Story | Patient sync-compliance sub-score | Must | 2 | S1 | ✅ Done |
| B2 | B — Scoring Engine | Story | Triage responsiveness scored vs SLA (2h→100, 24h→0) | Must | 3 | S1 | ✅ Done |
| B3 | B — Scoring Engine | Story | Seat-utilization sub-score (zero-seat safe) | Must | 2 | S1 | ✅ Done |
| B4 | B — Scoring Engine | Story | Weighted composite (45/35/20) | Must | 3 | S1 | ✅ Done |
| B5 | B — Scoring Engine | Story | Categorize Stable / At-Risk / Critical (80 / 60) | Must | 2 | S1 | ✅ Done |
| C1 | C — Dashboard | Story | Portfolio KPI row (Critical/At-Risk lead, severity-colored) | Should | 3 | S2 | ✅ Done |
| C2 | C — Dashboard | Story | Color-coded scorecard table | Must | 3 | S2 | ✅ Done |
| C3 | C — Dashboard | Story | Status filter (live) — governs table, chart, and attention list | Should | 2 | S2 | ✅ Done |
| C4 | C — Dashboard | Story | Health-score-by-account chart, colored by Status | Could | 2 | S2 | ✅ Done |
| C5 | C — Dashboard | Story | "Accounts needing attention" list — top of page, plan-tier ranked | Should | 2 | S2 | ✅ Done |
| C6 | C — Dashboard | Story | Scoring-model transparency sidebar | Could | 1 | S2 | ✅ Done |
| C7 | C — Dashboard | Story | Recent-vs-prior trend indicator per account | Should | 2 | S4 | ✅ Done |
| D1 | D — Quality & Testing | Story | 10 boundary-value unit tests | Must | 5 | S1 | ✅ Done |
| D2 | D — Quality & Testing | Story | Framework-free engine (lazy imports) for fast tests | Should | 3 | S2 | ✅ Done |
| E1 | E — CI/CD & Deployment | Story | CI on push/PR across Python 3.10/3.11/3.12 | Must | 3 | S3 | ✅ Done |
| E2 | E — CI/CD & Deployment | Story | Current action versions (no deprecations) | Could | 1 | S3 | ✅ Done |
| E3 | E — CI/CD & Deployment | Story | Public live deployment (Streamlit Cloud) | Must | 3 | S3 | ✅ Done |
| E4 | E — CI/CD & Deployment | Story | Auto-redeploy (CD) on push to `main` | Should | 2 | S3 | ✅ Done |
| T1 | E — CI/CD & Deployment | Task | Create annotated `v1.0.0` release tag (under E4) | — | — | S3 | ✅ Done |
| F1 | F — Governance & Docs | Story | README (setup / run / deploy) | Must | 3 | S3 | ✅ Done |
| F2 | F — Governance & Docs | Story | Design & testing document | Must | 5 | S3 | ✅ Done |
| G1 | G — Interoperability (roadmap) | Story | Ingest telemetry as FHIR `Observation` via adapter | Won't (v1) | 8 | — | ⬜ Backlog |
| G2 | G — Interoperability (roadmap) | Story | Map entities to FHIR `Organization`/`Patient`/`Device`/`Practitioner` | Won't (v1) | 5 | — | ⬜ Backlog |
| G3 | G — Interoperability (roadmap) | Story | SMART-on-FHIR OAuth2/OIDC for EHR access | Won't (v1) | 8 | — | ⬜ Backlog |
| G4 | G — Interoperability (roadmap) | Story | HL7 v2 (ADT/ORU) legacy inbound feed adapter | Won't (v1) | 5 | — | ⬜ Backlog |

## Definition of Done
A story is Done only when: code merged to `main`, unit tests updated and passing, CI green on all supported Python versions, and documentation updated.

## Legend
- **Priority (MoSCoW):** Must / Should / Could / Won't (this release).
- **Sprint:** S1 Foundation & Engine · S2 Experience & Test Hardening · S3 Ship & Document · S4 CSM-Workflow Revision (v1.1.0).
- **Status:** ✅ Done · 🔄 In Progress · 👀 In Review · ⬜ Backlog.
- **Epic G** is documented roadmap work and is intentionally **not implemented** in v1.0.0.
