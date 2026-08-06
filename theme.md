# Theme Document

## EduExam Pro — "Graded Paper" Theme

The theme is built around a single idea: the page should feel like a **graded exam paper** — clean, light, ink-and-paper, with a red-pen accent for grading and a teal accent for a correct/passed result. It replaces the earlier dark "chalkboard" theme with a plain, professional, paper-based look.

---

## 1. Color Tokens

| Token | Hex | Used for |
|---|---|---|
| `--bg` | `#FAF9F5` | Page background (flat, no texture) |
| `--paper` | `#FFFFFF` | Card and panel surfaces |
| `--rule` | `#E4E2D8` | Light dividers inside cards (table rows, dashed rules) |
| `--rule-strong` | `#D3D0C2` | Card borders, section dividers, perforation dots |
| `--ink` | `#1E2733` | Primary text, headings |
| `--ink-soft` | `#6B7280` | Secondary text, labels, captions |
| `--red-pen` | `#B23A2E` | Grading accent — timer, exam mode tag, correct-answer mark, hover state on primary button |
| `--pass-teal` | `#2E6E60` | Pass/correct accent — practice mode tag, judge "passed" lines, grade seal |
| `--gold` | `#B4842A` | Highlight accent — eyebrow labels, "running" state in judge panel |

**Usage rule:** red-pen is reserved for exam/grading/timer contexts, teal is reserved for pass/correct/practice contexts. They never swap roles — that consistency is what makes the accent color legible as a signal (red = official/at-stake, teal = safe/practice) rather than decoration.

---

## 2. Typography

| Role | Font | Notes |
|---|---|---|
| Headlines (h1, h2, mode titles, roll roles) | **Source Serif 4**, weight 600 | Gives the report-card / academic-document feel |
| Data, code, timers, labels, buttons | **IBM Plex Mono** | Used anywhere something reads as "system output" — timer, judge log, exam code, kicker/eyebrow text, nav CTA |
| Body copy, nav links, descriptions | **IBM Plex Sans** | Everything else |

Font sizes scale with `clamp()` on headings so the page stays readable from mobile up to a wide desktop without separate breakpoint overrides.

---

## 3. Motifs

These are the small physical details that carry the "paper" idea — remove them and the theme reverts to a generic light SaaS look:

* **Perforated dividers** (`.perf`) — a row of dots between major sections, like a tear-off line on a paper form.
* **Paperclip mark** (`.clip`) — a rotated bracket in the top-left corner of the exam-sheet card, as if a paper were clipped.
* **Grade seal** (`.stamp-grade`) — a circular "A+" stamp, rotated slightly, on the judge panel — ties the coding module back to the grading metaphor.
* **Red-pen circle** on the correct MCQ option, instead of a filled bubble — mimics how a teacher actually marks a paper.
* **Language stamps** (`.stamp`) — Python / C++ / Java shown as slightly rotated rubber-stamp badges rather than plain pills.
* **Dashed rules** inside cards (card header, footer lines) — echo a perforated/cut line at a smaller scale.

---

## 4. Surface & Depth

* Cards use a **1px solid border** (`--rule-strong`) plus a very subtle `2px` flat drop shadow — no blur-heavy shadows, no gradients. This keeps the surface reading as paper sitting slightly off the page, not glass or plastic.
* Border radius is small and consistent: `4px` on cards/panels, `2px` on buttons and stamps — sharp enough to still feel like a printed form, not a rounded app UI.

---

## 5. Motion

* **Countdown timer** in the hero exam card ticks down every second (loops for demo purposes).
* **Judge panel lines** reveal one at a time with staggered delay, simulating a live test run.
* **MCQ red-pen circle** fades in and out on a loop, drawing attention to the "correct answer" motif.
* **Scroll reveal** — sections fade/slide up into place as they enter the viewport (`IntersectionObserver`).
* All motion is disabled under `prefers-reduced-motion: reduce`.

---

## 6. What Changed From the Original (Chalkboard) Theme

| Aspect | Chalkboard theme | Graded-paper theme |
|---|---|---|
| Base mode | Dark (near-black/green) | Light (off-white) |
| Headline font | Newsreader (italic accents) | Source Serif 4 (solid weight, underline highlight instead of italic) |
| Grading accent | Ledger red `#C1443C` | Red-pen `#B23A2E` |
| Pass accent | Sage green `#7FB88F` | Deep teal `#2E6E60` |
| Signature motif | OMR bubble fill + terminal glow | Red-pen circle mark + rubber-stamp badges + paperclip |
| Background texture | Flat dark, no lines | Flat off-white, no lines *(ruled notebook-line texture was tried and removed)* |
