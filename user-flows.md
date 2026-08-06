# User Flows

## Institutional Online Examination, Coding Assessment & Practice Platform

Step-by-step flows for the actual application (not the landing page). Each flow lists the screens involved and, where useful, the underlying API/service touched — see `architecture.md` for the Django app names.

---

## 1. Admin Flows

### 1.1 Onboard a new institution (first-time setup)
1. Admin logs in (superuser or first Admin account created via Django management command/seed).
2. Admin → **Create Class** — names the class/section (e.g. "Grade 10 - A").
3. Admin → **Create Teacher Account** — enters teacher's name/email, system sends credentials.
4. Admin → **Enroll Students** — adds students individually or via bulk CSV upload, assigning each to a class.
5. Done — the institution now has classes, at least one teacher, and enrolled students. Nothing to grade yet.

### 1.2 Monitor a live exam (oversight, not authoring)
1. Admin → **Live Exams** view — lists every exam currently in progress across the institution.
2. Admin selects an exam → sees the same monitoring feed the owning teacher sees (read-only): who has joined, submitted, and any flagged tab-switch/copy-paste events.
3. Admin can drill into a flagged student's event log but cannot alter grading or the exam itself — that stays with the teacher.

### 1.3 Pull institution-wide reports
1. Admin → **Reports** → selects scope (institution / class / subject / topic).
2. System (via `reporting` app) returns aggregated pass rates, engagement, and usage stats.
3. Admin can export to CSV/PDF for institutional record-keeping.

---

## 2. Teacher Flows

### 2.1 Build a Topic and assign visibility
1. Teacher → **Topics** → **New Topic** — names it, picks a subject.
2. Teacher adds questions: either writes new MCQ/coding questions inline, or pulls existing ones from their question bank.
3. Teacher → **Visibility** tab on the topic → multi-select the class(es) that should see it.
4. Save. Topic is now live for the selected classes — no further action needed for it to appear on those students' dashboards.

### 2.2 Create a Practice Set
1. Teacher → **Practice Sets** → **New Practice Set**.
2. Picks a source Topic (or several), selects which questions from it to include (MCQ, coding, or mixed).
3. Sets the solution-reveal rule (after 1st attempt / after N attempts).
4. Assigns to class(es) — defaults to the topic's class list but can be narrowed.
5. Publish. Set appears immediately on assigned students' practice dashboards.

### 2.3 Create and run an Exam
1. Teacher → **Exams** → **New Exam**.
2. Picks source Topic(s), selects specific questions or lets the system randomize from the pool.
3. Configures: duration, schedule (start/end window), number of attempts allowed, randomization on/off.
4. System generates a unique **Exam Code**.
5. Teacher shares the code with the class (manually, or via a "notify class" action if built).
6. **During the exam window:** Teacher → **Live Monitoring** — sees who has joined, current progress, and real-time tab-switch/copy-paste flags (via Channels, see `architecture.md` Section 5).
7. **After the exam closes:** Teacher → **Results** — reviews auto-graded scores, spot-checks any flagged submissions, releases results to students.

### 2.4 Review coding submissions and analytics
1. Teacher → selects a coding question → **Submissions** tab.
2. Sees per-student results: pass/fail per test case, runtime, common failure patterns (e.g. most students fail the same hidden test case).
3. Teacher → **Analytics** on a Topic → pass rate, weak sub-topics, per-class comparison.

---

## 3. Student Flows

### 3.1 Join a formal exam
1. Student → **Exams** tab → enters the exam code shared by the teacher.
2. System validates: code correct, student's class matches, current time within the scheduled window, attempt not already used.
3. If valid → exam starts: timer begins, questions load (randomized if configured), monitoring begins client-side.
4. Student answers MCQs and/or writes and runs code in the embedded editor (Run against sample test cases as many times as they like before submitting).
5. Student clicks **Submit**, or the timer expires and auto-submit triggers.
6. Student sees a confirmation screen ("submitted, awaiting release") — actual score appears once the teacher releases results, per the teacher's setting.

### 3.2 Attempt a Practice Set
1. Student → **Practice** tab → sees only practice sets assigned to their class.
2. Opens a set, no code required — starts immediately.
3. Answers a question → gets immediate feedback (correct/incorrect for MCQ, pass/fail per test case for coding).
4. Can retry the same question immediately, or move to the next.
5. Explanation/reference solution unlocks once the teacher's reveal rule is met (e.g. after first attempt).
6. Student can exit and resume later — progress is saved per question, not per session.

### 3.3 Submit code (either mode)
1. Student writes code in the embedded editor, selects language (Python/C++/Java).
2. Clicks **Run** — tests against visible sample cases only, fast feedback loop, doesn't count as a graded submission.
3. Clicks **Submit** — this is the graded attempt: goes to the Judge Service queue, runs against sample + hidden test cases.
4. Student sees a "judging…" state, then results stream back (via Channels) or the page polls until graded: pass/fail per test case, runtime, and a final score.
5. In exam mode, submission also respects the exam timer — if time runs out mid-judge, the last submitted version before timeout is what gets graded.

### 3.4 Review progress
1. Student → **Dashboard** — sees completion percentage, topics attempted, streak, time spent.
2. Student → **History** — separate tabs for **Exam Results** and **Practice History** (never merged, per the data separation rule).
3. Student sees recommended practice questions based on weak topics (rule-based recommendation, e.g. lowest pass rate topic surfaces first).

---

## 4. Cross-Role Flow: A Topic's Full Lifecycle

Ties the above together into one continuous story:

```
Teacher creates Topic → adds questions → assigns to Class A
        │
        ├──► Teacher builds Practice Set from Topic → assigns to Class A
        │         │
        │         └──► Student in Class A sees it on Practice tab, attempts freely
        │
        └──► Teacher builds Exam from Topic → generates code → schedules for Class A
                  │
                  └──► Student in Class A joins with code during the window,
                       completes it under monitoring, gets an official grade
        │
Admin (throughout) → sees institution-wide rollups of both, but authors neither
```

---

## 5. Error / Edge-Case Flows Worth Designing For

* **Student loses connection mid-exam:** timer is server-authoritative (see `architecture.md` Section 5), so reconnecting resumes with correct remaining time; last auto-saved answers are preserved.
* **Student tries to join with an expired/wrong exam code:** clear inline error, no partial session created.
* **Coding submission times out in the sandbox:** reported as "Time Limit Exceeded" distinctly from a wrong answer, both to the student (practice) and in the teacher's submission view.
* **Teacher edits a topic's class list mid-exam-cycle:** visibility changes take effect immediately for practice/browsing, but an exam already in progress for a student is not retroactively hidden mid-session.
* **Admin deactivates a student mid-exam:** should be handled as a hard stop with a logged reason, not a silent lockout — teacher should see why the student's session ended.
