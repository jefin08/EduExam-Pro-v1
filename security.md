# Security Document

## Institutional Online Examination, Coding Assessment & Practice Platform

Covers authentication/authorization, exam integrity controls, and code-execution sandboxing. Written against the Django stack described in `architecture.md`.

---

## 1. Authentication

* Custom Django `User` model (`AUTH_USER_MODEL`) with a `role` field (`admin` / `teacher` / `student`) — set once at account creation, not user-editable.
* Passwords hashed with Django's default PBKDF2 (or upgrade to Argon2 via `django.contrib.auth.hashers`) — never store or log plaintext passwords.
* API auth via short-lived JWT access tokens + longer-lived refresh tokens (`djangorestframework-simplejwt`), so a leaked access token has a small blast-radius window.
* Teacher accounts are created only by Admins; students are enrolled only by Admins (or bulk import by Admin) — no public self-registration for either role, since this is an institutional platform, not an open one.
* Enforce password reset / first-login password change for accounts created with system-generated credentials.
* Rate-limit login attempts (per IP and per account) to blunt credential-stuffing and brute-force attempts.

---

## 2. Authorization

* Role checks enforced at the DRF permission-class level, not just hidden in the frontend — every endpoint declares which role(s) may call it.
* Object-level checks matter as much as role checks:
  * A Teacher can only edit Topics/Exams/Practice Sets **they authored** — not another teacher's.
  * A Student can only submit to an Exam/Practice Set **visible to their class** — validated server-side on every submission, not just when the list is first displayed.
  * An Admin can **read** everything institution-wide but has no write access to Topics, Exams, or grading — enforced the same way (permission class + queryset scoping), so it isn't just a UI restriction that a direct API call could bypass.
* Put exam-code and schedule-window validation in the DRF serializer's `validate()` method (see `architecture.md` Section 9) so it can't be skipped by hitting the API directly instead of the exam-join screen.

---

## 3. Exam Integrity

### 3.1 Server-authoritative timing
* The exam's end time is computed and stored server-side the moment a student's session starts (or from the exam's fixed schedule window) — the client-side countdown is a **display only**.
* Auto-submit is triggered by a server-side check against the stored end time, not by the client reporting "time's up." A client that stops sending heartbeat/keepalive signals still gets auto-submitted based on server time.
* Consider a scheduled Celery task (or a check-on-request pattern) that sweeps for exams past their end time and force-submits any session still marked "in progress."

### 3.2 Exam codes
* Generated server-side, sufficiently random (not sequential/guessable), scoped to a single exam and (optionally) a single class.
* Rate-limit code-entry attempts per account to prevent brute-forcing a code.
* Codes should expire outside the exam's scheduled window even if guessed correctly.

### 3.3 Monitoring (tab-switch / copy-paste detection)
* Client-side detection (`visibilitychange`, copy/paste event listeners) reports events to the server as they happen via the Channels WebSocket connection (see `architecture.md` Section 5) — not batched at the end, so a flag is visible even if the student never finishes.
* Treat all client-reported monitoring data as **advisory, not authoritative** — a sophisticated student can suppress client-side JS. Monitoring is a deterrent and a signal for teacher review, not a guarantee of integrity. Say this plainly to institutions rather than overselling it.
* Store monitoring events with timestamps, tied to the specific submission, so teachers reviewing a flagged exam see the full sequence, not just a count.
* One attempt per exam per student, enforced at the database level (`unique_together` or a `CheckConstraint` on `(student, exam)` in `OfficialGrade`) — not just checked in application logic, which could be bypassed by a race condition (e.g. two rapid duplicate requests).

---

## 4. Code Execution Sandbox (highest-risk component)

This is the one part of the system that runs arbitrary user-submitted content. Treat every submission as potentially hostile, regardless of who submitted it.

* **One container per submission, always fresh.** Never reuse a warm container across submissions or students.
* **No network access from inside the sandbox.** Prevents exfiltrating data, downloading additional payloads, or calling out to fetch answers/other services.
* **No access to the host filesystem or other containers.** Read-only mount for the language runtime; any writable scratch space is destroyed with the container after the run.
* **Hard resource limits enforced at the container/runtime level** (CPU time, wall-clock time, memory, output size, process count) — not just a `timeout` wrapped around the code from inside, which malicious code could subvert.
* **Celery workers are the only processes that ever invoke Docker.** The Django web process never directly executes user code — this keeps the highest-risk operation isolated to a component that can be scaled, restricted, and restarted independently of the main app (see `architecture.md` Section 8).
* **Disable dangerous language features where feasible** — e.g. restrict Python's ability to import `os`/`subprocess` isn't reliably enforceable from inside the interpreter, so rely on the container boundary (no network, read-only filesystem, resource limits) as the real control rather than trying to sandbox at the language level.
* **Cap output size** returned to the student/teacher — a submission that intentionally prints gigabytes of output shouldn't be able to exhaust memory or storage.
* **Log every submission's source code and result** to object storage (`django-storages`), both for grading disputes and as groundwork for future plagiarism detection (noted as a future feature in the project draft) — but treat stored source code as sensitive: access-controlled to the owning student, their teacher, and Admin, not broadly readable.

---

## 5. Data Protection

* All traffic over HTTPS/WSS — no plaintext HTTP or unencrypted WebSocket connections, especially given exam answers and monitoring events are in transit.
* Student PII (name, class, submissions) accessible only to: the student themselves, their teacher(s), and Admin — never exposed across institutions if the platform ever grows to multi-tenant (noted as out of scope for now, but worth designing data models so tenant isolation is addable later without a rewrite).
* Practice attempts and official grades are stored in **separate tables in separate apps** (`practice` vs `exams`) — this is a data-integrity measure as much as a security one, since it means there's no code path where a bug or a compromised account could leak or forge official grade data through the practice API.
* Database backups encrypted at rest; object storage (submissions, logs) encrypted at rest via the storage provider.
* Avoid logging full request bodies for endpoints that carry exam answers or code submissions in plaintext application logs — log metadata (submission ID, student ID, status) instead, and keep the actual content only in the intended storage location.

---

## 6. Operational Security

* Separate environments (dev/staging/production) with separate credentials and separate Redis/Postgres instances — never test against production student data.
* Admin actions with institution-wide impact (deleting a class, deactivating an account) should be logged with who/when, even if a full audit-log feature isn't built yet — a simple `django-simple-history`-style change log goes a long way.
* Dependency updates (Django, DRF, Celery, Docker base images) tracked and applied regularly — the sandbox's Docker base images in particular should be rebuilt periodically to pick up OS-level security patches, since they're the layer directly exposed to untrusted code.
* Secrets (DB credentials, JWT signing key, S3 keys) via environment variables or a secrets manager — never committed to the repo, never hardcoded in `settings.py`.

---

## 7. Explicitly Not Covered Yet

Per the project draft's "Out of Scope" section, these are acknowledged but intentionally not designed here:

* Webcam proctoring (would need its own privacy/consent handling if added later)
* Automated plagiarism detection (this document only covers logging groundwork for it)
* Multi-institution tenant isolation (single-institution model assumed for now; see Section 5 note on designing for addability)
