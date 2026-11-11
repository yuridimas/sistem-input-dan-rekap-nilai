# Usage

Assume the application is running; see [installation](installation.md). Interface labels are Indonesian. [API examples](api.md) cover programmatic use.

## Sign in and prepare accounts

1. Open <http://localhost:15173> for local Docker.
2. Sign in with the configured bootstrap email/password.
3. Create lecturer accounts through `POST /admin/users` as superadmin. The `/users` page is currently a placeholder; account CRUD, password changes, and deactivation are available through the API.

The dashboard summarizes visible courses/classes, pending releases, and recent releases. Lecturers see assigned classes; superadmins see all. Students are profiles/recipients, not an application login role.

## Set up courses and classes

1. Open **Mata kuliah** (`/courses`) and create a course: code, name, credits, semester.
2. Open the course and create a class: section and academic year.
3. As superadmin, assign an active lecturer. As lecturer, the class is assigned to yourself.
4. Open `/classes/:classId` and its tabs: **Mahasiswa**, **Komponen Penilaian**, **Nilai**, **Analisis**.

Lecturers can list/read courses they created or teach through an assigned class. Updating/deleting course metadata requires its creator or superadmin. Class management is limited to the assigned lecturer or superadmin.

## Build the roster

On **Mahasiswa**, enroll by NIM with name and optional email. Existing NIM reuses the student profile. Supply a name for new students; the API otherwise falls back to the NIM. Duplicate enrollment returns a conflict.

The global `/students` directory supports creation/reading for both roles; update/delete requires superadmin. Enrolled profiles cannot be deleted, and removing an enrollment with dependent grading data can also be blocked.

Email is optional for academic entry, but missing/invalid recipients prevent successful delivery. After an admin corrects the profile email, retry an unsent notification to refresh its recipient.

## Configure assessment components

On **Komponen Penilaian**, enter names, categories, weights, maximum scores, and display order, then save the configuration.

| Example | Category | Weight | Maximum |
| --- | --- | --- | --- |
| Assignments | `tugas` | 20 | 100 |
| Midterm | `uts` | 30 | 100 |
| Final exam | `uas` | 50 | 100 |

Weights must total exactly 100% with at least one UTS/UAS. Weights/maxima are positive with at most two decimals. A component containing scores cannot be removed or reduced below a saved score. Valid configuration changes recalculate draft totals.

## Enter and save grades

1. Open **Nilai** and enter each student's component scores.
2. Observe save state and resolve validation/network errors before leaving.
3. Use save/retry controls if a request fails. Draft edits survive class-tab changes; navigation guards handle unfinished work.
4. Check totals and fill every missing component before release.

Totals use `sum(score / maximum * weight)`, half-up to two decimals. In the example configuration, scores 80, 75, 90 produce `83.50`. Missing draft scores contribute zero without redistributing weights. Blank differs from saved zero: blank blocks release, zero is complete. API `null` clears a score; an omitted component preserves it.

Pending edits are in memory. Wait for successful saves before reload/exit. If changed server configuration pauses the editor, reconcile using its reload controls; explicit reload discards local drafts.

## Finalize a class

1. Confirm roster and components.
2. Save every score, including explicit zeroes where appropriate.
3. Start finalization; the UI flushes saves and refreshes the snapshot before confirmation.
4. Review confirmation and release.
5. Inspect released results and queue counts.

Release requires a nonempty roster, valid configuration, and complete in-range scores. It blocks score edits and roster/component changes. The current application has no unfinalize flow.

Release counts indicate finalized students and accepted queue tasks, not email delivery. Broker failure may leave released grades with failed notifications. After an uncertain timeout, use the server-status check before retrying; a repeated release returns conflict.

## Analytics and reports

Use **Analisis** for class charts/rankings. Rankings are stored on release; ties are ordered by NIM/name with distinct positions.

Open `/students/:studentId` for released history/trends in your access scope. Drafts do not appear in released history. Individual PDF downloads identify an enrollment, not a global student profile.

Released classes offer PDF/XLSX controls. Individual PDFs require a final enrollment grade; class exports require all roster grades final. XLSX includes component scores, totals, ranks, and pass/fail labels with a threshold of 45. Set `INSTITUTION_NAME` for report branding.

## Notifications

As superadmin, open **Notifikasi** (`/notifications`). Filter `queued`, `sent`, or `failed`, inspect errors, and retry unsent records after fixing recipient/broker/worker/SMTP. Sent records reject retry.

Empty `SMTP_HOST` means mock transport: logging can result in `sent` without contacting SMTP. Real mail requires configured SMTP and a worker sharing the API's database/Redis.

## Common problems

| Symptom | Action |
| --- | --- |
| Changing seed password does not change login | Seed does not reset accounts; use the authorized account update API. |
| Configuration/save rejected | Check 100% weight, UTS/UAS, positive maxima, and score ranges. |
| Missing cells block release | Fill listed cells; blank is not zero. |
| Write returns 409 | Reload; data may be final, duplicate, or protected by dependencies. |
| Release result uncertain | Check server status before retry. |
| Report returns 409 | Confirm the enrollment/full roster is final. |
| PDF returns 503 | Use the backend image with renderer libraries/fonts. |
| Email queued/failed | Check worker, broker, recipient, SMTP, then admin retry. |
| Wrong browser API URL | Correct `VITE_API_URL`, restart/rebuild, and check CORS. |
