# Architecture Document (Django)

## Institutional Online Examination, Coding Assessment & Practice Platform

This version is written specifically for a **Django** implementation. Pair with `dataflow.md` (how data moves) and `database-schema.md` (once written, for exact models/fields).

---

## 1. Stack

| Layer | Choice | Why |
|---|---|---|
| Backend framework | **Django** + **Django REST Framework** | Admin site comes free (useful for internal ops), ORM maps cleanly to the Institution → Class → Student / Teacher → Topic → Question model, DRF gives you a clean API for the frontend |
| Frontend | React (or Django templates + HTMX if you want to stay all-Django) | React is better if the code editor and live exam timer need to feel app-like; HTMX is fine if you want to avoid a separate frontend build entirely |
| Code editor component | Monaco Editor or CodeMirror, embedded in the frontend | Standard choice regardless of backend |
| Auth | Django's built-in auth + `django-rest-framework-simplejwt` | Custom `User` model with a `role` field (Admin/Teacher/Student) or a `Profile` model with a OneToOne to `User` |
| Primary database | **PostgreSQL** | Works natively with Django's ORM, supports the constraints you'll want for the exam/practice separation rule (see Section 6) |
| Async task queue | **Celery** + **Redis** (as both broker and result backend) | Code judging must not block the request/response cycle — a submission gets queued, a worker picks it up, result comes back async |
| Real-time updates | **Django Channels** (WebSockets) | For the live exam monitoring view (teacher watching tab-switch events as they happen) and for pushing judge results back to the student without polling |
| Caching / session state | **Redis** (separate logical DB from the Celery broker, or a separate Redis instance) | Exam timer display state, rate limiting |
| Object storage | **django-storages** with an S3-compatible backend | Stores raw code submissions, judge run logs |
| Code sandbox | Docker containers invoked from Celery workers (not from the Django web process) | Isolates arbitrary user code away from the main app entirely |

---

## 2. Django App Structure

Organize as separate Django apps by domain, not by role — this keeps the exam/practice separation enforceable at the model layer.

```
project/
├── config/                  # settings, urls, wsgi/asgi, celery.py
│
├── accounts/                 # custom User model, roles, auth
│   ├── models.py             # User (role: admin/teacher/student), Institution, Class
│   └── ...
│
├── content/                  # question bank + topics (Teacher-owned)
│   ├── models.py             # Topic, TopicClassVisibility, MCQQuestion, CodingQuestion
│   └── ...
│
├── exams/                    # formal exam mode
│   ├── models.py             # Exam, ExamCode, ExamSchedule, OfficialGrade,
│   │                         # MonitoringEvent (tab-switch/copy-paste log)
│   ├── consumers.py          # Channels consumer for live monitoring
│   └── ...
│
├── practice/                 # practice mode
│   ├── models.py             # PracticeSet, PracticeSetClassAssignment, PracticeAttempt
│   └── ...
│
├── judge/                    # coding submission + sandbox orchestration
│   ├── models.py             # Submission, TestCaseResult
│   ├── tasks.py               # Celery tasks: run_submission()
│   ├── sandbox.py             # Docker invocation logic
│   └── ...
│
├── reporting/                 # read-only aggregation layer
│   ├── services.py            # queries that roll up by student/topic/class/institution
│   └── ...
│
└── api/                       # DRF viewsets/serializers, one module per app above
```

**Why split this way:** `exams` and `practice` are separate apps, each with their own attempt/grade model, so there is no shared table a bug could accidentally write both kinds of data into. `judge` doesn't know about exams or practice — it just judges a `Submission` and returns a result; `exams` and `practice` each create their own `Submission` records and read the result back.

---

## 3. Request Flow: MCQ Exam Submission

```
Student submits answers (DRF endpoint: POST /api/exams/{id}/submit/)
        │
        ▼
exams/views.py — validates: exam code matches, student in class,
                 within schedule window, attempt not already used
        │
        ▼
Grades MCQs synchronously (fast, no need for Celery)
        │
        ▼
Writes to exams.models.OfficialGrade
        │
        ▼
Response returned to student immediately
```

## 4. Request Flow: Coding Submission (Exam or Practice)

```
Student submits code (DRF endpoint, tagged with context=exam|practice)
        │
        ▼
judge/views.py creates a Submission row (status=queued)
        │
        ▼
Celery task judge.tasks.run_submission.delay(submission_id) is dispatched
        │
        ▼
API responds immediately with submission_id (status=queued) —
does NOT block the HTTP request on the sandbox run
        │
        ▼
Celery worker picks up the task, calls sandbox.py
        │
        ▼
sandbox.py spins up a Docker container:
   - no network
   - CPU/memory/time limits set at container level
   - runs compile step (if applicable), then sample + hidden test cases
   - container destroyed after run
        │
        ▼
Result written back to Submission (status=graded, per-test-case results)
        │
        ▼
Either:
   - Channels pushes the result to the student's open connection, or
   - Frontend polls GET /api/judge/submissions/{id}/ until status=graded
        │
        ▼
exams/services.py or practice/services.py reads the graded Submission
and writes the score into OfficialGrade or PracticeAttempt respectively
```

**Why Celery here specifically:** a code judge run can take anywhere from milliseconds to several seconds (compilation + multiple test cases), and Django's request/response cycle should never hold a worker thread open waiting on a Docker container. Queuing it also naturally handles exam-day spikes — submissions queue up rather than the web server falling over.

---

## 5. Live Exam Monitoring (Channels)

```
Student's browser: tab-switch / copy-paste event detected client-side
        │
        ▼
WebSocket message sent to exams/consumers.py (Channels consumer)
        │
        ▼
Consumer writes a MonitoringEvent row, then broadcasts to a
Channels group named exam_{exam_id}_monitor
        │
        ▼
Teacher's live monitoring dashboard (subscribed to that group)
receives the event and updates in real time — no polling
```

Django Channels needs an ASGI server (Daphne or Uvicorn) and Redis as the channel layer backend. This can run alongside the regular WSGI/ASGI Django app — Channels handles the WebSocket routes, standard DRF handles everything else.

---

## 6. Enforcing the Exam/Practice Data Separation at the Model Layer

This is the most important rule in the whole system (see `dataflow.md`, Section 8), and Django makes it enforceable, not just a convention:

* `OfficialGrade` lives only in the `exams` app, with a `ForeignKey` to `Exam` — there is no path for `practice` app code to write to it, because `practice` doesn't import `exams.models`.
* `PracticeAttempt` lives only in `practice`, with a `ForeignKey` to `PracticeSet` — same isolation in reverse.
* Both can share the *same* `MCQQuestion` / `CodingQuestion` from `content`, via `ForeignKey`, without either app depending on the other.
* If a future feature genuinely needs to compare practice and exam performance (e.g. "did practice improve exam scores"), that logic belongs in `reporting`, which is allowed to read from both — but never write to either.

---

## 7. Topic → Class Visibility (Django-specific)

```python
# content/models.py (illustrative, not final schema)

class Topic(models.Model):
    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    subject = models.CharField(max_length=120)
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)

class TopicClassVisibility(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    class_group = models.ForeignKey('accounts.Class', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('topic', 'class_group')
```

A student's visible topics is then a straightforward queryset:

```python
Topic.objects.filter(
    is_active=True,
    topicclassvisibility__class_group=student.class_group
).distinct()
```

This is the single query every practice-set listing, exam listing, and topic browse view filters through — because it's centralized, there's one place to get the visibility rule right rather than reimplementing it per view.

---

## 8. Deployment Shape

```
                 ┌───────────────┐
                 │   Nginx/LB      │
                 └───────┬───────┘
              ┌──────────┴──────────┐
     ┌────────▼────────┐   ┌────────▼─────────┐
     │  Django (ASGI)     │   │  Django Channels   │
     │  via Daphne/        │   │  (WebSocket routes, │
     │  Uvicorn — handles  │   │  same codebase,     │
     │  DRF API traffic    │   │  same deploy)        │
     └────────┬────────┘   └────────┬─────────┘
              │                      │
     ┌────────▼──────────────────────▼─────────┐
     │              PostgreSQL                    │
     └────────────────────────────────────────┘

     ┌───────────────────┐     ┌────────────────────┐
     │  Celery workers      │────▶│  Docker sandbox       │
     │  (judge queue)        │     │  (per-submission,      │
     │                       │     │   no network, resource  │
     │  Redis (broker +      │     │   limits enforced)       │
     │  result backend)      │     └────────────────────┘
     └───────────────────┘
```

* Web (ASGI) process and Celery workers are **separate deployments/processes** — a judge backlog should never slow down someone logging in or a teacher browsing the question bank.
* Celery workers are the only processes that talk to Docker — the web process never invokes the sandbox directly, keeping arbitrary-code-execution risk contained to a component that's easy to isolate, scale, and restart independently.
* Redis is used for two distinct purposes (Celery broker/results, and Channels layer) — use separate logical databases or separate Redis instances so a burst of judge traffic doesn't starve WebSocket message delivery.

---

## 9. Practical Django Notes

* Use Django's **custom User model** from day one (`AUTH_USER_MODEL`) with a `role` field — retrofitting this later is painful.
* Put exam-code validation and schedule-window checks in a **DRF serializer's `validate()`**, not in the view, so the same rule applies whether the request comes from the web frontend or a future API consumer.
* Use `select_related`/`prefetch_related` aggressively in `reporting/services.py` — the rollups (per-topic, per-class, per-institution) will be the most query-heavy code path in the app.
* Consider Postgres **`CheckConstraint`** or a `unique_together` on `(student, exam)` in `OfficialGrade` to make "one attempt only" enforceable at the database level, not just in application logic.
* Django's admin site is genuinely useful here for early-stage Admin tooling — you may not need to build a custom Admin dashboard for every operational task in Phase 0/1 of `roadmap.md`.
