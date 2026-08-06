# Design Document

## EduExam Pro — Landing Page (Graded Paper Theme)

This document describes the structure and components of the landing page — what's on it, in what order, and why. Pair with `theme.md` for the color/type/motif tokens referenced throughout.

---

## 1. Design Goal

One landing page, one job: convince an institution evaluating exam software that this platform genuinely does two different things well — **formal, monitored MCQ exams** and **real coding assessment with a judge engine** — on the same gradebook, without letting practice and official grades mix. Every section exists to prove one part of that claim.

---

## 2. Page Structure (top to bottom)

```
Header / Nav
  └─ Hero
       └─ Headline + subhead + CTAs
       └─ Hero visual: Exam-sheet card + Judge-engine card (side by side)
  └─ [perforated divider]
  └─ Two Modes section  (Exam mode vs Practice mode, compared)
  └─ [perforated divider]
  └─ Roll Call section  (Admin / Teacher / Student, numbered like a register)
  └─ [perforated divider]
  └─ Coding Judge section  (language stamps + judge feature grid)
  └─ [perforated divider]
  └─ Analytics section  (four-stat tally row)
  └─ [perforated divider]
  └─ Final CTA
  └─ Footer
```

---

## 3. Section-by-Section Breakdown

### 3.1 Header / Nav
* Sticky, translucent-on-scroll background so it stays usable on a long page.
* Wordmark uses a small circular "A+" seal instead of a logo mark — first touch of the grading motif.
* Nav links jump to each section anchor; a single mono-styled CTA button ("Request a demo") sits on the right.

### 3.2 Hero
* Eyebrow line names the audience directly: "For institutions — exams and coding assessment."
* Headline states the core claim in one sentence, with a highlighted phrase ("multiple‑choice") instead of relying on color alone, so it also reads fine in grayscale/print.
* Two CTAs: a primary action (Request a demo) and a lower-commitment secondary action (See how a session runs) that anchors down to the Modes section rather than leaving the page.
* **Hero visual** is two cards side by side:
  - **Exam-sheet card** — live countdown timer, a sample MCQ with a red-pen circle marking the answer, and a footer line showing monitoring status (tab switches, auto-submit rule). This demonstrates Exam Mode.
  - **Judge-engine card** — a simulated terminal log showing a code submission compiling and running against sample and hidden test cases, ending in a score. This demonstrates the Coding Assessment Module.
  - Together they visually argue the platform's central claim before any text explains it.

### 3.3 Two Modes
* Direct side-by-side comparison table (Exam mode / Practice mode) across six rows: access, attempts, question order, monitoring, submission/feedback, grading.
* Deliberately uses the same row labels on both sides so the contrast is a straight read across, not two separate lists a visitor has to reconcile themselves.

### 3.4 Roll Call
* Three roles listed as numbered register rows (01 Admin, 02 Teacher, 03 Student) rather than icon cards — ties back to the "class register" idea and keeps the section visually calm after the busier hero.
* Each row: role name in serif, one bolded one-line summary, one supporting sentence. No feature lists here — that's intentional, this section is about *who*, not *what*.

### 3.5 Coding Judge
* Three "stamp" badges (Python / C++ / Java) as the first thing in the section — answers "which languages" immediately, before any prose.
* A 2×2 feature grid below covers the judge's actual mechanics: sandboxed execution, hidden test cases, time/memory limits, mixed exams. Each item is a left-bordered block (bold label + one supporting line), matching the "ledger row" visual language used elsewhere on the page.

### 3.6 Analytics
* Four flat stat cells, each a plain number (not a chart) with a mono label underneath. Kept intentionally simple — this section's job is to close the "is this a real system" case with concrete counts (2 modes, 3 languages, 3 roles, unlimited practice attempts), not to demo a dashboard (that's a separate future page).

### 3.7 Final CTA
* Repeats the same two-button pattern as the hero, but with a single-column, larger headline — a deliberate "last word" moment rather than a new pitch.

### 3.8 Footer
* Minimal: platform name + role summary line, mono type, no additional links — the page doesn't try to be a full site, just a landing page.

---

## 4. Components (reusable across sections)

| Component | Where used | Notes |
|---|---|---|
| `.card` | Hero (exam sheet, judge panel) | White surface, 1px border, small flat shadow, 4px radius |
| `.mode-col` | Two Modes | Same card treatment, plus a colored `.mode-tag` (red for exam, teal for practice) |
| `.roll-row` | Roll Call | Grid row: number / role / description, divided by thin rules |
| `.stamp` | Coding Judge | Rotated badge, teal outline, mono uppercase text |
| `.tally-cell` | Analytics | Flat stat card: large serif number + mono label |
| `.btn-primary` / `.btn-ghost` | Hero, Final CTA | Mono type; primary is solid ink (hovers red-pen), ghost is outline only |
| `.perf` | Between every major section | Perforated dot divider, replaces a plain `<hr>` |

---

## 5. Responsive Behavior

* Breakpoint at `760px`: hero visual, modes comparison, and judge feature grid collapse from two columns to one.
* Breakpoint at `820px`: nav links hide (only wordmark + CTA remain) to keep the header usable on tablets.
* Breakpoint at `640px`: roll-call rows collapse their grid so the description wraps under the role name instead of squeezing into a third column.
* Analytics tally goes from 4 columns → 2 columns at `760px`.

---

## 6. Accessibility Notes

* Color is never the only signal — the hero headline highlight uses an underline treatment, not color alone; mode tags pair color with an explicit text label ("Exam mode" / "Practice mode").
* All animation (timer, judge log reveal, scroll reveal, pulsing dot) is wrapped in a `prefers-reduced-motion` check and disabled entirely for users who request it.
* Interactive elements (nav links, buttons) have clear hover states with sufficient contrast against the light background.

---

## 7. Open Items / Not Yet Designed

* Student dashboard UI (practice progress, streaks, recommended questions)
* Teacher dashboard UI (topic-to-class assignment screen, live exam monitoring view)
* Admin reporting UI (institution-wide analytics)
* Coding editor screen itself (the actual in-browser code editor + run/submit flow), currently only represented as a simulated log on the landing page
