# Score Entry Implementation Progress

Plan: [Sistem Input & Rekap Nilai](2026-10-24-sistem-input-rekap-nilai.md), Task 10.

## Completed

- Added `scores` and `grades` models, migration `0005_scores_grades`, and Indonesian comments on every new table and column.
- Added schemas, repositories, services, and routers for score entry and the class grade grid.
- Score updates retain row IDs and initial `entered_at`; `entered_by` and `updated_at` identify the latest write. Scores and the computed grade commit together.
- Class locks serialize score writes and component edits. Enrollment locks prevent removal during a save. Authorization is checked against the current class owner after locking.
- Component weight/maximum edits recalculate existing drafts in the same transaction. Removing scored components returns 409; lowering a maximum below a saved score returns 422. Finalized grades and their class components reject edits with 409.

## API Contract

`PUT /enrollments/{id}/scores` accepts a nonempty JSON object mapping component UUIDs to numeric scores:

```json
{
  "11111111-1111-4111-8111-111111111111": "80.00",
  "22222222-2222-4222-8222-222222222222": "70.00"
}
```

The response is the updated grade (`id`, `enrollment_id`, `final_score`, `status`, and release metadata). Omitted component scores remain unchanged. Invalid precision, negative/nonfinite scores, values above the component maximum, and components outside the enrollment's class return 422 without saving partial changes.

`GET /classes/{id}/grades` returns `{class_id, components, grades}`. Each grade row contains `enrollment_id`, `student`, a component-to-score map, `final_score`, and `status`. Rows follow roster order by NIM. Unscored students have an empty map, null final score, and draft status. A recorded zero remains present in the score map.

## Calculation Decisions

- Ruling: normalize each score by its component maximum: `score / max_score * weight`. With maximum 100 this matches the plan's example, `80 × 30% + 70 × 30% + 90 × 40% = 81`. This keeps final scores on a 0–100 scale for nonstandard maxima. Consumers should use that scale.
- Ruling: missing scores contribute zero during draft calculation without redistributing their weights. Missing entries stay absent so finalization can distinguish them from recorded zeros.
- Persisted/input numbers use Decimal. Normalized contributions use exact rational arithmetic internally and round only once, half up to two decimal places, returning Decimal. This prevents repeating divisions from turning an exact `0.055` into `0.05`.

## Verification and Resume Point

- RED → GREEN: missing score endpoint; reweighting drafts; invalid maximum changes; component immutability; exact half-up rounding.
- Backend suite: **71 passed**, with one existing SlowAPI deprecation warning.
- Includes real concurrent requests using separate database connections, transaction rollback on grade-save failure, access boundaries, cross-class components, zero/missing scores, audit timestamps, and database comments.
- `alembic upgrade head` succeeded; `alembic check` reports no new upgrade operations.
- Next: **Task 11 — Finalize + ranking**. No finalization or ranking endpoint is introduced by Task 10.
