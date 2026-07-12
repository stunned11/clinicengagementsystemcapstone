# Software Design, Architecture, and Testing Document

**Project:** B2B2C Patient Remote Monitoring — Customer Health Scoring Engine
**Technology Stack:** Python · Streamlit · SQLite · GitHub Actions
**Program:** Quantic MSSE Capstone

### 1. Executive Summary & Business Case

In a B2B2C Remote Patient Monitoring (RPM) model, a platform vendor contracts with clinics (the B2B tier), whose clinicians in turn serve monitored patients (the B2C tier). Net revenue retention is consequently contingent upon two loosely coupled behavioral surfaces: patient-side device engagement and clinic-side operational responsiveness. This project delivers a Customer Health Scoring engine that reconciles these surfaces into a single, defensible metric. The engine ingests daily account telemetry and computes a normalized 0–100 composite health score as a weighted function of three key performance indicators: B2C patient sync compliance (45%), B2B alert-triage latency (35%), and licensed-seat utilization (20%). Each account is subsequently classified as Stable, At-Risk, or Critical against deterministic thresholds. The business case is grounded in the economics of churn mitigation: Customer Success capacity is finite and disproportionately valuable, so directing intervention toward empirically deteriorating accounts maximizes retained contract value per labor hour. By supplanting anecdotal account judgment with reproducible quantitative triage, the platform institutionalizes early-warning detection and converts raw operational logs into prioritized commercial action.

### 2. System Architecture & Design Patterns

The system is deliberately structured as a **layered 3-tier architecture** with strict separation of concerns, notwithstanding its single-file packaging. The **presentation tier** comprises the Streamlit rendering routines (`render_sidebar`, `render_kpis`, `render_attention`, `render_health_chart`, `render_dashboard`), responsible exclusively for user-facing composition and for surfacing at-risk accounts in priority order. The **application (logic) tier** houses the domain scoring engine—`score_sync`, `score_triage`, `score_seat_utilization`, `weighted_health_score`, and `categorize`—alongside the `build_scorecard` aggregation service that transforms persisted rows into analytic records. The **data tier** encapsulates persistence through `get_connection`, `init_db`, and `seed_db`, isolating all SQLite dialect concerns behind function boundaries.

This layering is reinforced by a **Model-View-Controller (MVC)** decomposition. The Model unifies persistence and domain computation; the View is the declarative Streamlit component tree; and the Controller is `main()`, which orchestrates the canonical cycle `ensure_database → build_scorecard → render`. Two mechanisms enforce tier isolation. First, deferred (lazy) imports of `pandas` and `streamlit` invert the dependency direction at the module boundary, ensuring the computational core remains framework-agnostic. Second, the `if __name__ == "__main__"` guard prevents view instantiation during importation, rendering the logic tier headlessly testable and satisfying the dependency-inversion and single-responsibility principles.

### 3. Database Schema & Data Dictionary (Describe 'clinics' and 'telemetry_logs' schemas)

Persistence is delegated to an embedded SQLite database, initialized and seeded idempotently at runtime. The relational model is normalized to Third Normal Form across two entities: `clinics` (the account dimension) and the telemetry log table—implemented as `telemetry`, functionally the `telemetry_logs` store—which records one immutable observation per account per day.

**`clinics`**

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Surrogate account key |
| name | TEXT | NOT NULL, UNIQUE | Clinic display name |
| plan_tier | TEXT | NOT NULL | Commercial tier (Enterprise/Growth/Starter) |
| licensed_seats | INTEGER | NOT NULL | Contracted clinician seats |

**`telemetry` (telemetry_logs)**

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Surrogate row key |
| clinic_id | INTEGER | NOT NULL, FK → clinics(id) | Owning account |
| metric_date | TEXT | NOT NULL | ISO-8601 observation date |
| patient_sync_compliance | REAL | NOT NULL | Patient sync rate (0–100) |
| alert_triage_hours | REAL | NOT NULL | Mean alert-triage latency (hours) |
| clinician_login_count | INTEGER | NOT NULL | Daily active clinician logins |

A composite `UNIQUE(clinic_id, metric_date)` constraint enforces the temporal grain and guarantees seeding idempotency, while the foreign key preserves referential integrity.

### 4. Software Engineering Methodology & Project Governance

Delivery adhered to an **Agile/Scrum** framework, adapted for single-developer execution: as the sole engineer on this capstone, sprint ceremonies were self-directed rather than distributed across a team, but the underlying discipline was preserved rather than abandoned. Work proceeded in short, time-boxed sprints, each producing a potentially shippable increment. The product backlog was decomposed into vertically sliced user stories—data seeding, scoring computation, dashboard visualization, automated verification, and documentation—prioritized by business value and technical risk. Each sprint concluded with an increment whose **Definition of Done** was operationalized as a passing continuous-integration pipeline, ensuring that "done" denoted verified, integrable functionality rather than nominal completion, independent of the absence of a second reviewer. Sprint planning established scope at the outset of each iteration; a daily self-review of the backlog substituted for a team standup in surfacing impediments; and periodic self-retrospection—reassessing completed increments against real-world usage patterns rather than assumed requirements—informed subsequent iterations. Two concrete examples: the reactive remediation of a Node.js runtime deprecation within the CI toolchain, and a post-v1.0 retrospective in which the dashboard was re-evaluated against a Customer Success Manager's actual triage workflow, surfacing a live defect (the status filter silently excluding the attention list from its scope) and motivating the v1.1.0 revision documented in the task board.

Progress was governed through a **Kanban** board partitioned into Backlog, In Progress, In Review, and Done columns, with explicit work-in-progress limits self-imposed to constrain context switching and expose bottlenecks. Version control served as the authoritative governance ledger: atomic, conventionally formatted commits provided a traceable audit trail, and scoped changes flowed through automated CI gates—the functional substitute for peer review in a single-developer context—before integration into `main`. This dual Scrum-Kanban discipline balanced iteration cadence with continuous flow, demonstrating that the value of these methodologies is not contingent on team size but on the rigor with which they are self-enforced.

### 5. Testing Strategy & Verification

Verification followed a **unit-testing** strategy executed through `pytest`, targeting the deterministic scoring engine, which—by design—carries no framework dependencies and is therefore rapidly and reproducibly exercisable in isolation. The suite comprises ten tests applying **boundary value analysis** and **equivalence partitioning** to the engine's decision surfaces. Classification boundaries are probed precisely at the cutoffs (a score of 80 yielding Stable, 79.99 yielding At-Risk, 60 yielding At-Risk, and 59.99 yielding Critical), while the sub-score normalizers are validated at their SLA extremities: triage latency at the two-hour target (100) and the twenty-four-hour ceiling (0), plus the thirteen-hour linear midpoint (50). Seat-utilization tests assert clamping under full and overflow conditions and confirm graceful handling of the zero-seat division edge case.

Verification is institutionalized through **continuous integration** on GitHub Actions, triggered on every push and pull request to `main`. The pipeline provisions runners via `actions/checkout@v7` and `actions/setup-python@v6`, installs pinned dependencies, and executes `pytest -q` across a Python 3.10/3.11/3.12 build matrix, thereby guaranteeing cross-version regression protection and gating integration on uniformly green results.

### 6. Future Scalability & Security Considerations

The present implementation optimizes for reproducibility and pedagogical clarity: an embedded SQLite store, in-process seeding, and synchronous, single-node execution. Evolving the platform toward production scale is nevertheless a bounded exercise, precisely because the layered isolation confines change to individual tiers.

**Scalability.** The data tier abstractions (`get_connection`, `build_scorecard`) permit substitution of SQLite with a client-server RDBMS such as PostgreSQL without perturbing the logic or presentation tiers. Anticipated telemetry growth is addressed through composite indexing on `(clinic_id, metric_date)`, temporal partitioning, and incremental materialized aggregation that supersedes full-table scans. Score computation—currently on-demand—should migrate to a scheduled ETL/batch pipeline that precomputes and caches account scores, decoupling analytic latency from interactive rendering. Horizontally, the stateless presentation tier can be containerized (Docker) and replicated behind a load balancer under an orchestrator (Kubernetes), with all session state externalized to the database or a Redis cache. Externalizing the scoring weights and KPI definitions into configuration further enables model evolution without redeployment.

**Security.** Because RPM operates adjacent to Protected Health Information, the system must assume a HIPAA-regulated posture: encryption in transit (TLS) and at rest, least-privilege database credentials, and secrets administered through a dedicated manager rather than source control. The existing use of parameterized queries mitigates SQL injection and must be preserved categorically. Production deployment additionally mandates authentication (OIDC/SSO), role-based authorization with strict multi-tenant scoping, comprehensive access audit logging, and supply-chain assurance via pinned dependencies, automated vulnerability scanning, and a Business Associate Agreement governing data custody.

**Interoperability (FHIR / HL7) — future.** Production ingestion would replace the mock SQLite seed with standards-based clinical data exchange. The `telemetry` entity maps directly onto the HL7 **FHIR** `Observation` resource, while `clinics`, patients, monitoring devices, and clinicians correspond to the `Organization`, `Patient`, `Device`, and `Practitioner` resources respectively; legacy sites can be accommodated through HL7 v2 (ADT/ORU) feed adapters. Authorized electronic health record access would follow the **SMART on FHIR** OAuth2/OIDC profile. Because the data tier is already isolated behind `get_connection` and `build_scorecard`, substituting a FHIR-backed ingestion adapter for the SQLite source is an additive change rather than a rewrite, leaving the scoring engine and presentation tier untouched. This interoperability track is scoped as post-v1 roadmap work and is not implemented in the current release.

**Conclusion.** The architecture's disciplined tier and pattern boundaries render these enhancements evolutionary rather than disruptive, substantiating the design's long-term maintainability and compliance readiness.
