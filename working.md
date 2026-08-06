# System Working Document

## Institutional Online Examination, Coding Assessment & Practice Platform

This document describes how the full system works end to end, including the new **Topics** feature, and exactly what each role (Admin, Teacher, Student) can do and is responsible for.

---

## 1. New Feature: Topics with Class-based Visibility

### What a Topic is

A **Topic** is a container a teacher creates to organize content by subject area (e.g. "Binary Trees," "SQL Joins," "Thermodynamics — Unit 3"). A topic can hold both MCQs and coding questions, and both practice sets and exam questions can be pulled from it.

```
Subject
  └── Topic            (created by a teacher)
        └── Sub-topic   (optional, for finer grouping)
              └── Questions (MCQ / Coding)
```

### Who creates topics

Only **Teachers** create and manage topics. Admins can see all topics across the institution for reporting, but do not author them.

### Class-based visibility (the core rule)

When a teacher creates or edits a topic, they **select one or more classes** that should see it. A topic is invisible to every class not selected.

* A topic can be assigned to a single class, several classes, or all classes a teacher handles.
* A topic can be reassigned or unassigned later — visibility updates immediately for students.
* A student only ever sees topics whose class list includes their own class. There is no way for a student to browse topics outside their class.
* The same topic can be shared across multiple sections taught by the same teacher (e.g. "Binary Trees" assigned to both Class 10-A and 10-B) without duplicating the questions.

### What becomes visible once a topic is assigned to a class

For students in that class:

* Any **practice sets** built from the topic appear on their practice dashboard.
* Any **exam** that draws questions from the topic becomes eligible to appear for them (still gated by the exam code and schedule — topic visibility controls *content*, exam code controls *access*).
* Topic-level analytics (their own attempts, accuracy, time spent) start accumulating.

For students **not** in an assigned class, the topic and everything under it stays hidden — it won't appear in search, practice listings, or recommendations.

### Teacher-side controls

A teacher managing a topic can:

* Create the topic and give it a name, subject, and description.
* Add MCQ and/or coding questions to it, individually or by moving existing questions in from the question bank.
* Select or change which classes can see it (multi-select class picker).
* Mark it active/inactive without deleting it (inactive = hidden from all classes, but not lost).
* View per-class analytics for the topic (a class that struggles with "Binary Trees" shows up distinctly from one that doesn't).

### Admin-side view

Admins do not assign classes to topics, but they can:

* See a full list of topics across all teachers and subjects.
* See which classes each topic is visible to, for auditing.
* Pull institution-wide analytics per topic/subject.

---

## 2. Role-by-Role: What Each User Can Do

### 2.1 Admin

**Setup and account management**
* Create and deactivate teacher accounts.
* Create classes and enroll/remove students.
* Assign students to the correct class so topic and exam visibility resolves correctly.
* Configure system-wide settings (supported languages, session timeouts, grading rules).

**Oversight**
* View every exam scheduled or in progress across the institution.
* View every topic and its class assignments (read-only).
* Monitor flagged activity from anti-cheating logs (tab switches, copy-paste events) across all exams.

**Reporting**
* Institution-wide performance reports, by class, subject, or topic.
* Platform usage reports (active teachers, active students, exams run, practice attempts).
* Cannot author questions, topics, or exams — that stays with teachers.

---

### 2.2 Teacher

**Question and topic authoring**
* Build the MCQ question bank: question text, options, correct answer, marks, difficulty, tags.
* Build the coding question bank: description, input/output format, sample and hidden test cases, starter code, time/memory limits.
* Create topics, populate them with questions, and **select the classes each topic is visible to** (see Section 1).

**Exam management**
* Assemble an exam by pulling questions from one or more topics (MCQ-only, coding-only, or mixed).
* Configure duration, schedule, randomization, and number of allowed attempts.
* Generate a unique exam code and share it with the intended class(es).
* Monitor an exam while it's live: who has joined, who has submitted, tab-switch/copy-paste flags as they happen.
* Auto and manual grading review — MCQs and coding grade automatically; the teacher can review borderline coding submissions.

**Practice set management**
* Create practice sets (MCQ-only, coding-only, or mixed) from any topic they own.
* Assign practice sets directly to classes (this uses the same class-visibility model as topics).
* Decide whether solutions/explanations show after the first attempt or after a set number of attempts.

**Analytics**
* Per-topic and per-class analytics: pass rate, common wrong answers, common coding failure types, weak vs. strong topics.
* Student-level drill-down: attempts, time spent, improvement trend over weeks/months.
* Practice engagement dashboard: completion percentage, heatmap of activity, leaderboard.

---

### 2.3 Student

**Access model**
* Sees only the topics, practice sets, and exams visible to their assigned class.
* Joins a formal exam only with a valid exam code, within the scheduled window.
* Opens any practice set assigned to their class at any time — no code needed.

**Exam mode**
* Attends the exam within the timer; auto-submit triggers at time's end.
* Limited to the configured number of attempts (often one).
* Subject to monitoring: tab-switch detection, copy-paste detection, activity logging.
* Sees official results and grade once released by the teacher/system.

**Practice mode**
* Attempts any visible practice set an unlimited number of times.
* Gets immediate feedback per question, and explanations/reference solutions once unlocked.
* Uses the same browser-based code editor and judge engine as exam mode, but without monitoring.

**Progress tracking**
* Personal dashboard: completion percentage, topics attempted, average attempts, time spent, streak.
* Can review past attempts (both exam results and practice history, kept separate).
* Sees recommended practice questions based on weak topics (rule-based now, AI-based later).

---

## 3. How a Topic Flows Through the System (End to End)

1. **Teacher** creates a topic under a subject and adds MCQ/coding questions to it.
2. **Teacher** selects the class(es) this topic should be visible to.
3. **System** immediately updates visibility — students in those classes now see the topic; everyone else doesn't.
4. **Teacher** optionally builds a practice set from the topic and assigns it to the same (or a different) class list.
5. **Teacher** optionally builds an exam pulling questions from the topic, generates an exam code, and schedules it for the class.
6. **Students** in the assigned class see the topic's practice content immediately, and can join the exam once they have the code and the schedule opens.
7. **Students** outside the assigned class see none of it — not the topic, not the practice set, not the exam listing.
8. **Teacher** and **Admin** view analytics that roll up by topic, by class, and by individual student.

---

## 4. Permissions Summary

| Action | Admin | Teacher | Student |
|---|---|---|---|
| Create/manage teacher accounts | Yes | No | No |
| Create/manage classes & enroll students | Yes | No | No |
| Create topics | No | Yes | No |
| Assign classes to a topic | No | Yes | No |
| Add questions to a topic | No | Yes | No |
| View topics (read-only, all) | Yes | Own topics only | Assigned-class topics only |
| Create exams / generate exam codes | No | Yes | No |
| Join an exam | No | No | Yes (with code) |
| Create practice sets | No | Yes | No |
| Attempt practice sets | No | No | Yes (assigned class only) |
| View institution-wide reports | Yes | No | No |
| View own class/topic reports | Read-only, all | Yes, own | No |
| View own performance | No | No | Yes |
