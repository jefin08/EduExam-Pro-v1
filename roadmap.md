# Roadmap

## Institutional Online Examination, Coding Assessment & Practice Platform

A phased build plan. Each phase should be shippable and usable on its own — later phases build on earlier ones rather than requiring a big-bang launch.

---

## Phase 0 — Foundations (pre-work)

Not user-facing, but everything else depends on it.

* Set up Core App Service, database schema, and auth (Admin/Teacher/Student roles).
* Institution → Class → Student data model and Admin-side enrollment tools.
* Teacher account creation (by Admin).
* Basic role-based login and dashboards (empty shells at this stage).

**Exit criteria:** an Admin can log in, create a class, create a teacher, and enroll a student. Nothing to grade yet.

---

## Phase 1 — MCQ Question Bank & Topics

* Teacher: create/edit MCQ questions (text, options, correct answer, marks, difficulty, tags).
* Teacher: create Topics, add MCQ questions to them, select which class(es) can see each topic.
* Student: see topics visible to their class (read-only at this stage — nothing to attempt yet).

**Exit criteria:** the topic-to-class visibility rule works end to end — a topic assigned to Class A is invisible to Class B.

---

## Phase 2 — Practice Mode (MCQ only)

* Teacher: build MCQ-only practice sets from a topic, assign to class(es), set solution-reveal rule.
* Student: attempt practice sets, unlimited attempts, immediate feedback, explanations after the configured reveal point.
* Student: basic personal practice dashboard (questions attempted, completion percentage).

**Exit criteria:** a student can practice MCQs end to end with no exam code involved, and their attempts are stored separately from any grade table (which doesn't exist yet).

---

## Phase 3 — Exam Mode (MCQ only)

* Teacher: build an exam from one or more topics, configure duration/schedule/randomization, generate an exam code.
* Student: join with exam code, timed session, auto-submit at timeout.
* Automatic MCQ grading, official grade record.
* Basic anti-cheating: tab-switch and copy-paste detection, logged and visible to the teacher.

**Exit criteria:** a full formal exam can run start to finish for MCQs, with grades that never touch the Phase 2 practice data.

---

## Phase 4 — Coding Question Bank & Judge Engine

* Teacher: create coding questions (description, I/O format, sample + hidden test cases, starter code, time/memory limits).
* Judge Service: sandboxed execution for Python, C++, Java (see `architecture.md`, Section 4).
* Browser-based code editor (syntax highlighting, run, submit, output console).
* Coding evaluation: compile error / runtime error / time-limit-exceeded detection, partial marking.

**Exit criteria:** a student can submit code against a standalone coding question and get an accurate pass/fail + partial score, independent of exams or practice sets.

---

## Phase 5 — Coding in Practice & Exam Modes

* Teacher: build coding-only and mixed (MCQ + coding) practice sets and exams.
* Combined scoring for mixed exams (MCQ + coding in one paper, one timer, one score).
* Coding-specific anti-cheating (copy-paste detection inside the code editor, activity logging) for exam mode.

**Exit criteria:** everything in the original project draft's "in scope" section works together — mixed exams, coding practice, judge-backed grading, all respecting the exam/practice data separation.

---

## Phase 6 — Analytics & Reporting

* Teacher dashboard: pass rate, common wrong answers, common coding failures, topic-wise difficulty, per-class practice heatmap, leaderboards.
* Student dashboard: progress, completed topics, streaks, time spent, recommended practice questions (rule-based).
* Admin dashboard: institution-wide reports across classes, subjects, and topics; platform usage stats.

**Exit criteria:** every role has the reporting view described in `working.md`, and it reflects real Phase 1–5 data.

---

## Phase 7 — Hardening & Polish

* Full anti-cheating pass: refine tab-switch/copy-paste detection, add activity logging groundwork for future plagiarism detection.
* Load-test the Judge Service and Exam Service independently for exam-day traffic spikes.
* Accessibility and responsive pass across all dashboards (not just the landing page).
* Security review of the sandbox (network isolation, resource limits, container lifecycle).

**Exit criteria:** the system is ready for a real institution to run a real graded exam on it.

---

## Explicitly Out of Scope (per project draft — not on this roadmap)

* Multi-institution SaaS platform
* Webcam proctoring
* Mobile applications
* AI-generated questions
* Essay evaluation
* Support for languages beyond Python, C++, and Java
* AI-based practice recommendations (noted in the draft as a future dashboard feature, not this build)
* Automated plagiarism detection (logging groundwork only — detection itself is future work)

---

## Suggested Sequencing Rationale

* **MCQ before coding** (Phases 1–3 before 4–5) because MCQ grading is simpler and lets the exam/practice separation, topic visibility, and monitoring features get proven out before the highest-risk component (the judge sandbox) is added.
* **Topics before anything else** (Phase 1) because both practice sets and exams depend on topic-to-class visibility as their gating mechanism — building either before topics exist would mean reworking them later.
* **Analytics last** (Phase 6) because it's a read-only layer over data that needs to actually exist first — building dashboards against fake data risks designing for the wrong shape of real usage.
