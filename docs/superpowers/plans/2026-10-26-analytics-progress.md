# Task 20: Class and Student Performance Charts

Plan: [Sistem Input & Rekap Nilai](2026-10-24-sistem-input-rekap-nilai.md), Task 20.

## Implemented

- Added the `?tab=analytics` class tab with saved grade distribution and per-student stacked component contributions. The status selector isolates finalized rows from complete, valid drafts; zero scores count as complete. Incomplete drafts are reported as excluded, and missing legacy component values leave the breakdown unavailable instead of being treated as zero.
- Distribution uses stored final scores in the `0–<45`, `45–<60`, `60–<75`, `75–<85`, and `85–100` buckets. Contributions use `score / max_score * weight`, aggregate by Tugas/UTS/UAS/Kustom without intermediate rounding, and show stored final score separately.
- Added `/students/:studentId` identity and semester trend details. The trend groups finalized history by semester, sorts labels naturally, and computes a simple mean of authorized class results. Chart tooltips and expandable tables expose class counts and details; empty semesters do not create points.
- Linked student names from the student list and class roster. The class grade controller and navigation guard remain mounted across tab changes; analytics uses the existing account-scoped grade query and shows when local edits are unsaved.
- Charts load lazily, use explicit responsive sizes, category colors and a wrapping legend, and provide accessible chart labels, tooltips, and data tables. No backend or database changes.

## Verification

- Frontend suite: **37 tests passed**. Includes bucket boundaries, zeros, complete-draft filtering, normalization, fractional weights, legacy missing values, semester sorting/means, loading retry, empty history, single-semester trend, and draft guard retention while switching tabs.
- `npm run build` passed. `rtk bypass npm run lint` passed with the existing `button.tsx` Fast Refresh warning only.
- Edge smoke against disposable PostgreSQL/API data verified all five bucket labels at 320px, class SVG dimensions and tooltips, the draft filter, keyboard trend tooltip, lecturer history scoping versus superadmin visibility, and 320/375px layouts without document overflow or runtime exceptions. Screenshots and smoke script are in the ignored Task 20 workspace.
- Next: **Task 22 — Docker staging/prod profiles and nginx**.
