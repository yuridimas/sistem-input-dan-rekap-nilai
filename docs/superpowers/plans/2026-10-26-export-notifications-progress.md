# Task 21: Export UI and Notification Status

Plan: [Sistem Input & Rekap Nilai](2026-10-24-sistem-input-rekap-nilai.md), Task 21.

## Implemented

- Added authenticated report downloads using existing endpoints: student PDF per enrollment and class PDF/XLSX. Downloads use the server's attachment filename with a safe fallback, release temporary object URLs, and show API error details even when Axios returns a Blob.
- Added class report actions for classes with finalized grades and a per-enrollment PDF action in student grade history.
- Added a superadmin-only `/notifications` page and sidebar link. It defaults to failed deliveries, requests selected statuses from the API, can show all statuses, and retries failed sends; successful retries update the view to queued. Created and sent timestamps are labeled separately.
- No backend, schema, or dependency changes.

## Verification and Resume Point

- Frontend suite: **45 tests passed** across 6 files, including download headers/fallback/error parsing, class and student report actions, notification filtering/retry, and role protection.
- `npm run build` passed.
- `rtk bypass npm run lint` passed with the existing Fast Refresh warning in `src/components/ui/button.tsx`.
- `git diff --check` passed. UI behavior was exercised through React Testing Library; no live-browser or backend-connected smoke run was available in this session.
- Project plan complete after **Task 23**; see [final validation](2026-10-26-final-validation-progress.md).
