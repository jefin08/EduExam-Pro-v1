# Data Flow Document

## Institutional Online Examination, Coding Assessment & Practice Platform

This document traces how data moves through the system — what gets created, by whom, what it triggers, and where it ends up. Read alongside `working.md`, which covers permissions and role responsibilities.

---

## 1. Core Entities

```
Institution
   └── Class
         └── Student  ───────────────┐
                                      │
Teacher                               │
   └── Topic ── (assigned to) ──> Class
         ├── MCQ Question             │
         └── Coding Question          │
                                      │
   ├── Practice Set (built from Topic, assigned to Class)
   │        └── Attempt (by Student)
   │
   └── Exam (built from Topic, assigned to Class, has Exam Code)
            └── Submission (by Student)
                     ├── MCQ Answers
                     └── Code Submission ── Judge Engine ── Test Case Results
```

Every question lives inside exactly one topic. Every topic is authored by one teacher and made visible to one or more classes. Practice sets and exams are both built by pulling questions out of one or more topics — they're two different "views" over the same underlying question data.

---

## 2. High-Level Flow

```
 ADMIN                TEACHER                        STUDENT
   │                     │                               │
   │ creates ──────────► Class                            │
   │ enrolls ──────────► Student ────── belongs to ───────┤
   │                     │                               │
   │                     │ creates Topic                  │
   │                     │ adds Questions to Topic         │
   │                     │ selects Class(es) for Topic ───►│ Topic becomes visible
   │                     │                               │
   │                     │ builds Practice Set from Topic  │
   │                     │ assigns to Class ──────────────►│ appears on practice dashboard
   │                     │                               │
   │                     │ builds Exam from Topic          │
   │                     │ generates Exam Code             │
   │                     │ schedules & assigns to Class ──►│ appears once code + schedule match
   │                     │                               │
   │                     │◄──── Submissions & Attempts ────│
   │                     │        (auto-graded)            │
   │                     │                               │
   │◄──── institution-wide reports ────┤◄──── class/topic reports ──┘
```

---

## 3. Topic Creation & Class Visibility Flow

This is the gating mechanism for everything downstream.

```
1. Teacher creates Topic
        │
        ▼
2. Teacher adds MCQ / Coding questions to Topic
        │
        ▼
3. Teacher selects Class(es) via multi-select picker
        │
        ▼
4. System writes Topic ↔ Class mapping
        │
        ▼
5. Visibility check runs on every student page load:
        "list topics WHERE class = student.class"
        │
        ├── Student's class IS in the mapping ──► Topic, its practice sets,
        │                                          and any exam built from it
        │                                          become visible
        │
        └── Student's class NOT in the mapping ──► Topic stays completely
                                                     hidden (no listing, no
                                                     search result, no
                                                     recommendation)
```

Editing the class list (adding/removing a class, or deactivating the topic) re-runs this check immediately — visibility is not cached per student session.

---

## 4. Exam Flow (data path of one exam)

```
Teacher                                System                              Student
   │                                     │                                    │
   │ builds Exam from Topic(s)  ────────►│ stores Exam definition             │
   │ sets duration/schedule/rules ──────►│                                    │
   │ generates Exam Code ───────────────►│ stores code, linked to Exam+Class  │
   │                                     │                                    │
   │                                     │◄──── Student enters Exam Code ─────│
   │                                     │  validates: code correct?          │
   │                                     │            student in class?       │
   │                                     │            within schedule window? │
   │                                     │                                    │
   │                                     │──── serves randomized question set ►│
   │                                     │     starts timer                    │
   │                                     │     begins monitoring (tab-switch,  │
   │                                     │      copy-paste logging)            │
   │                                     │                                    │
   │                                     │◄──── MCQ answers + code submissions │
   │                                     │      (on submit, or auto-submit     │
   │                                     │       at timer end)                 │
   │                                     │                                    │
   │                                     │ MCQ: graded instantly against key   │
   │                                     │ Code: sent to Judge Engine ───┐     │
   │                                     │                               │    │
   │                                     │◄── sandbox run, hidden test ──┘     │
   │                                     │    cases, partial marks             │
   │                                     │                                    │
   │                                     │ combines MCQ + coding score         │
   │                                     │ writes to Official Grade record     │
   │                                     │                                    │
   │◄──── monitoring log + submissions ──│──── result released ───────────────►│
   │      (flag review if needed)        │     (per teacher's release setting) │
```

Key rule: an exam attempt always writes to the **official grade** table — this is what keeps it separate from practice data.

---

## 5. Practice Flow (data path of one practice attempt)

```
Teacher                                System                              Student
   │                                     │                                    │
   │ builds Practice Set from Topic ────►│ stores Practice Set definition     │
   │ assigns to Class(es) ──────────────►│ stores Set ↔ Class mapping         │
   │ sets solution-reveal rule ──────────►│ (after 1st attempt / after N)      │
   │                                     │                                    │
   │                                     │◄──── Student opens Practice Set ────│
   │                                     │      (no code needed, visibility    │
   │                                     │       check same as Topic)          │
   │                                     │                                    │
   │                                     │──── serves questions ──────────────►│
   │                                     │                                    │
   │                                     │◄──── answer / code submission ──────│
   │                                     │                                    │
   │                                     │ MCQ: instant grade + feedback       │
   │                                     │ Code: Judge Engine run, feedback    │
   │                                     │                                    │
   │                                     │ writes to Practice Attempt record   │
   │                                     │ (kept fully separate from grades)   │
   │                                     │                                    │
   │                                     │──── explanation/solution shown ────►│
   │                                     │     once reveal rule is met         │
   │                                     │                                    │
   │                                     │ updates: attempt count, streak,     │
   │                                     │  time spent, topic mastery stats    │
   │                                     │                                    │
   │◄──── topic/class practice analytics │──────────────────────────► (own progress
```

A student can repeat this loop unlimited times per question; each attempt is logged individually for the "common wrong answers" and "common coding failures" analytics teachers see.

---

## 6. Coding Submission → Judge Engine (detail)

```
Student submits code
        │
        ▼
System queues submission (exam or practice, tagged accordingly)
        │
        ▼
Judge Engine picks up job
        │
        ├── compiles / prepares interpreter for the selected language
        │        │
        │        ├── compilation error ──► returned immediately, no test run
        │        │
        │        ▼
        ├── runs against sample test cases (visible to student)
        ├── runs against hidden test cases (not visible to student)
        │        │
        │        ├── per test case: pass / fail / runtime error / time limit exceeded
        │        │
        │        ▼
        ├── computes partial marks (marks per passed test case)
        ▼
Result returned to System
        │
        ├── Exam context ──► written to Official Grade, feeds monitoring log
        └── Practice context ──► written to Practice Attempt, feeds student feedback
```

---

## 7. Reporting Data Flow

```
Attempt / Submission records (exam + practice, kept separate)
        │
        ▼
Aggregation layer rolls up by:
   - Student  → personal dashboard (progress, streak, weak topics)
   - Topic    → pass rate, common failures, difficulty signal
   - Class    → class-level performance, engagement heatmap
   - Subject  → cross-topic trend
        │
        ├──► Teacher Dashboard (own topics/classes only)
        └──► Admin Dashboard (institution-wide, read-only on authored content)
```

---

## 8. Data Separation Rules (non-negotiable)

* **Exam data and practice data never merge.** Same student, same topic, same question bank — two separate attempt tables, two separate scoring paths.
* **Topic visibility is the single source of truth** for what a student can see. Practice sets and exams don't carry their own separate visibility list — they inherit it from the topic(s) they're built from, though a teacher can still narrow the class list further when assigning a specific practice set or exam.
* **Admins never author data**, only read it — so reporting queries for Admin are always read-only aggregates, never writes.
