# Task 18: Academic Management UI

Plan: [Sistem Input & Rekap Nilai](2026-10-24-sistem-input-rekap-nilai.md), Task 18.

## Implemented

- Added protected course list/detail, class detail, and global student pages. Course/student searches run locally against existing list APIs. Dashboard course/class links and the shared navigation connect the new screens.
- Course reads now include courses created by a lecturer or assigned through their classes, without duplicates. Metadata writes still require the creator or a superadmin. Class lists remain scoped to the current lecturer; superadmins can assign lecturers through the existing user-list API.
- Class responses now include `has_finalized_grades`, calculated in a single additional batch query. Any finalized grade locks roster and component controls, including partially finalized classes. Class metadata remains editable under the existing rules. No migration is required.
- Added course/class/student create, edit, and confirmed deletion flows. Student email can be explicitly cleared with null; omitted email retains its value. The existing user changes restricting shared student edits/deletion to superadmins are preserved.
- Enrollment reuses stored records for known NIMs. New NIMs require a full name in the UI, with optional email. Duplicate enrollment and score-dependent deletion errors retain useful feedback.
- Component configuration is saved atomically with existing IDs preserved and explicit ordering. Initial UTS/UAS defaults use 50% each. Live validation uses integer hundredths, requires positive values and UTS/UAS, and blocks totals other than exactly 100%. Server score/finalization restrictions remain authoritative; failed writes retain the draft and Cancel restores server data.
- Added Base UI/shadcn dialogs, fields, tabs, tables, and feedback primitives. Management routes load lazily; account-specific query keys and mutation invalidation refresh academic data and dashboard summaries. No new package dependency was required.

## Verification and Resume Point

- RED to GREEN: three new contract tests initially failed for assigned-course visibility, missing class lock flags, and explicit-null email handling; all now pass.
- Full Linux/Pango backend suite: **154 passed**, one existing SlowAPI deprecation warning. Final run completed in 28.14 seconds using disposable PostgreSQL 18.
- `npm run build` and `rtk bypass npm run lint` passed. Only the existing `react(only-export-components)` warning in `components/ui/button.tsx` remains; route splitting avoids the large-bundle build warning.
- Real Edge smoke against a separate disposable database passed course/class/student CRUD and conflicts, lecturer assignment, new/existing NIM enrollment, required names, shared-student permissions, email clearing, precise decimal component weights, ID-preserving reorder, score protection, concurrent finalization, and denied foreign-class access.
- Browser verification also covered dashboard refresh/navigation, dialog autofocus, Tab containment, Escape/focus restoration, and 320/375px layouts. Desktop/mobile screenshots were inspected; no runtime errors were observed.
- Browser regression reproduced collapsed controls after component reorder. Disabling container-query containment specifically for movable field groups fixed the issue; reorder/save/delete was verified again without changing shared field behavior.
- A separate read-only review found no required changes. Existing user edits to the student router and class tests, plus untracked AGENTS.md and egg-info, are excluded from this task's commit.
- Next: **Task 19 — Grade entry grid UI**.
