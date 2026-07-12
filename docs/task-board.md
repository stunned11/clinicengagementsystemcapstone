# Project Task Board

**Project:** Clinic Engagement System — Customer Health Scoring
**Last updated:** 2026-07-12 · **Release:** v1.0.0

This board tracks all agreed user stories and tasks. It is organized as a Kanban flow (**Backlog → In Progress → In Review → Done**) with MoSCoW priorities and story-point estimates. Epics A–F are delivered in v1.0.0; Epic G is post-v1 roadmap work.

## Board snapshot (Kanban)

| Backlog | In Progress | In Review | Done |
| --- | --- | --- | --- |
| G1, G2, G3, G4 | — | — | A1, A2, A3, B1, B2, B3, B4, B5, C1, C2, C3, C4, C5, C6, D1, D2, E1, E2, E3, E4, F1, F2 (+ tasks T1, T2) |

## Summary

| Status | Stories | Story points |
| --- | --- | --- |
| Done | 22 | 58 |
| Backlog (Epic G) | 4 | 26 |
| **Total** | **26** | **84** |

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
| C1 | C — Dashboard | Story | Portfolio KPI row | Should | 3 | S2 | ✅ Done |
| C2 | C — Dashboard | Story | Color-coded scorecard table | Must | 3 | S2 | ✅ Done |
| C3 | C — Dashboard | Story | Status filter (live) | Should | 2 | S2 | ✅ Done |
| C4 | C — Dashboard | Story | Health-score-by-account chart | Could | 2 | S2 | ✅ Done |
| C5 | C — Dashboard | Story | "Accounts needing attention" list | Should | 2 | S2 | ✅ Done |
| C6 | C — Dashboard | Story | Scoring-model transparency sidebar | Could | 1 | S2 | ✅ Done |
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
- **Sprint:** S1 Foundation & Engine · S2 Experience & Test Hardening · S3 Ship & Document.
- **Status:** ✅ Done · 🔄 In Progress · 👀 In Review · ⬜ Backlog.
- **Epic G** is documented roadmap work and is intentionally **not implemented** in v1.0.0.
