# Task 16: Auth Pages and Protected Layout

Plan: [Sistem Input & Rekap Nilai](2026-10-24-sistem-input-rekap-nilai.md), Task 16.

## Implemented

- Added Indonesian login with field validation, error feedback, and return-to-requested-page behavior.
- Persisted access and refresh tokens in Zustand while loading the current profile from `/auth/me`.
- Added single-flight access-token refresh and retry on 401; invalid refresh clears the session.
- Added protected routes, superadmin-only user routing, role-specific course navigation, responsive sidebar, logout, and dashboard/future-page placeholders.
- Set Indonesian document language, page title, and shared app-shell styling.

## Verification and Resume Point

- `npm run build` passed.
- `rtk bypass npm run lint` passed with one existing `react(only-export-components)` warning in `src/components/ui/button.tsx`.
- Real-browser smoke passed for invalid login, superadmin and lecturer menus, deep-link login redirect, mobile navigation and keyboard focus, logout, protected routes, and access-token refresh rotation. Refresh rotation was verified in a full smoke run after the one-minute access token expired.
- No backend files were changed for this task. Task 17 is implemented; see [dashboard progress](2026-10-25-dashboard-progress.md). Next: **Task 18: Courses/Classes/Students/Components management UI**.
