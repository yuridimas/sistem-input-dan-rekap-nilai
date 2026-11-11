# API reference

## Base URLs and contracts

| Runtime | API base | Schema |
| --- | --- | --- |
| Local Docker | `http://localhost:18000` | `/openapi.json` |
| Host Uvicorn | `http://localhost:8000` | `/openapi.json` |
| Deployment | Frontend origin plus `/api` | `/api/openapi.json` on that origin |

Paths below are relative to the API base. UUID path parameters identify database records. JSON is used except for report downloads. Successful DELETE responses are empty. Decimal response values serialize as strings; clients should accept decimal strings rather than assuming JSON numbers.

FastAPI exposes direct Swagger at `/docs` and ReDoc at `/redoc`. Deployment Swagger currently requests the unprefixed schema path; use `/api/openapi.json` or direct API Swagger instead. See [deployment](deployment.md#reverse-proxy-dan-tls).

The inventory below covers all 43 application operations registered by [`main.py`](../backend/app/main.py). Named contracts correspond to [`app/schemas/`](../backend/app/schemas/) and OpenAPI components. Login and refresh read `Request` manually, so their accepted bodies are described here even though OpenAPI does not declare their request bodies.

## Authentication

`POST /auth/login` accepts JSON `{ "email": "...", "password": "..." }`; `username` is an alias for email. It also has form parsing support. JSON is the request format used in these examples. Login is limited to 30 attempts/minute per remote address.

`POST /auth/refresh` accepts JSON `{ "refresh_token": "..." }`, with `token` as an alias. It also supports query parameters, form input, and a raw token body. Send refresh tokens in the JSON body. Both operations return `TokenResponse`: `access_token`, `refresh_token`, and `token_type: "bearer"`.

Use `Authorization: Bearer <access_token>` for protected operations. Refresh rotates both tokens; default expiry is 15 minutes for access and seven days for refresh. The used-refresh list is per process, lost on restart, and not shared across API workers. Inactive accounts are rejected even if their token has not expired.

## PowerShell example setup

Run against an installed development/test instance. Login with your configured account:

```powershell
$apiBase = 'http://localhost:18000'
$credential = Get-Credential -Message 'Application login'
$loginPayload = @{
  email = $credential.UserName
  password = $credential.GetNetworkCredential().Password
}
$tokens = Invoke-RestMethod -Method Post -Uri "$apiBase/auth/login" `
  -ContentType 'application/json' -Body ($loginPayload | ConvertTo-Json)

function Invoke-GradeApi {
  param([string]$Method, [string]$Path, $Body)
  $request = @{
    Method = $Method
    Uri = "$apiBase$Path"
    Headers = @{ Authorization = "Bearer $($tokens.access_token)" }
  }
  if ($PSBoundParameters.ContainsKey('Body')) {
    $request.ContentType = 'application/json'
    $request.Body = ConvertTo-Json -InputObject $Body -Depth 10
  }
  Invoke-RestMethod @request
}
```

The tables use this helper, payload variables below, and IDs returned by your instance (`$userId`, `$courseId`, `$classId`, `$studentId`, `$enrollmentId`, `$componentId`, `$notificationId`). Each table command illustrates one operation; it is not a script to run every mutation in sequence. Admin-only examples require a superadmin token.

## Operation inventory

### Identity and health

| Method and path | Input | Success | Purpose and example |
| --- | --- | --- | --- |
| `GET /health` | None; public | 200: `{status, db, redis}` | Dependency flags: `Invoke-RestMethod "$apiBase/health"` |
| `POST /auth/login` | Email/username and password | 200: `TokenResponse` | Login example above |
| `POST /auth/refresh` | Refresh token | 200: `TokenResponse` | `$tokens = Invoke-GradeApi POST '/auth/refresh' @{refresh_token=$tokens.refresh_token}` |
| `GET /auth/me` | Bearer token | 200: `UserResponse` | `Invoke-GradeApi GET '/auth/me'` |

Health returns `status: ok` and HTTP 200 even if a dependency fails; require both booleans to be true.

### Accounts: superadmin only

| Method and path | Input | Success | Purpose and example |
| --- | --- | --- | --- |
| `POST /admin/users` | `UserCreate` | 201: `UserRead` | Create account: `Invoke-GradeApi POST '/admin/users' $userCreate` |
| `GET /admin/users` | Optional query `role`, `is_active` | 200: `UserRead[]` | `Invoke-GradeApi GET '/admin/users?role=lecturer&is_active=true'` |
| `GET /admin/users/{user_id}` | UUID | 200: `UserRead` | `Invoke-GradeApi GET "/admin/users/$userId"` |
| `PATCH /admin/users/{user_id}` | `UserUpdate` | 200: `UserRead` | `Invoke-GradeApi PATCH "/admin/users/$userId" $userUpdate` |
| `DELETE /admin/users/{user_id}` | UUID | 204 | Deactivate, retaining historical relations: `Invoke-GradeApi DELETE "/admin/users/$userId"` |

### Courses

| Method and path | Input | Success | Purpose and example |
| --- | --- | --- | --- |
| `POST /courses` | `CourseCreate` | 201: `CourseRead` | Creator is current user: `Invoke-GradeApi POST '/courses' $courseCreate` |
| `GET /courses` | None | 200: `CourseRead[]` | Admin: all; lecturer: created or assigned courses. `Invoke-GradeApi GET '/courses'` |
| `GET /courses/{course_id}` | UUID | 200: `CourseRead` | Creator/admin/assigned lecturer: `Invoke-GradeApi GET "/courses/$courseId"` |
| `PATCH /courses/{course_id}` | `CourseUpdate` | 200: `CourseRead` | Creator/admin: `Invoke-GradeApi PATCH "/courses/$courseId" $courseUpdate` |
| `DELETE /courses/{course_id}` | UUID | 204 | Creator/admin, subject to dependencies: `Invoke-GradeApi DELETE "/courses/$courseId"` |

### Classes and rosters

Both roles can call these operations. Access to an existing class requires its assigned lecturer or superadmin.

| Method and path | Input | Success | Purpose and example |
| --- | --- | --- | --- |
| `POST /classes` | `ClassCreate` | 201: `ClassRead` | `Invoke-GradeApi POST '/classes' $classCreate` |
| `GET /classes` | None | 200: `ClassRead[]` | Visible classes: `Invoke-GradeApi GET '/classes'` |
| `GET /classes/{class_id}` | UUID | 200: `ClassRead` | `Invoke-GradeApi GET "/classes/$classId"` |
| `PATCH /classes/{class_id}` | `ClassUpdate` | 200: `ClassRead` | `Invoke-GradeApi PATCH "/classes/$classId" $classUpdate` |
| `DELETE /classes/{class_id}` | UUID | 204 | Dependencies can block removal: `Invoke-GradeApi DELETE "/classes/$classId"` |
| `POST /classes/{class_id}/enrollments` | `EnrollmentCreate` | 201: `RosterEntryRead` | Reuse/create profile by NIM: `Invoke-GradeApi POST "/classes/$classId/enrollments" $enrollmentCreate` |
| `GET /classes/{class_id}/roster` | UUID | 200: `RosterEntryRead[]` | `Invoke-GradeApi GET "/classes/$classId/roster"` |
| `DELETE /classes/{class_id}/enrollments/{enrollment_id}` | Class/enrollment UUIDs | 204 | `Invoke-GradeApi DELETE "/classes/$classId/enrollments/$enrollmentId"` |

Superadmins must supply an active lecturer's `lecturer_id` on class creation. Lecturers may omit it and are assigned themselves; they cannot assign another lecturer. Roster mutations are blocked after release. Dependent grading data can also block enrollment removal.

### Student directory

| Method and path | Input | Success | Purpose and example |
| --- | --- | --- | --- |
| `POST /students` | `StudentCreate` | 201: `StudentRead` | Both roles: `Invoke-GradeApi POST '/students' $studentCreate` |
| `GET /students` | None | 200: `StudentRead[]` | Both roles: `Invoke-GradeApi GET '/students'` |
| `GET /students/{student_id}` | UUID | 200: `StudentRead` | Both roles: `Invoke-GradeApi GET "/students/$studentId"` |
| `PATCH /students/{student_id}` | `StudentUpdate` | 200: `StudentRead` | Admin only: `Invoke-GradeApi PATCH "/students/$studentId" $studentUpdate` |
| `DELETE /students/{student_id}` | UUID | 204 | Admin only; enrolled profiles conflict: `Invoke-GradeApi DELETE "/students/$studentId"` |

### Components, scores, and releases

These operations require assigned-class access or superadmin. Student history is scoped to released results visible to the caller.

| Method and path | Input | Success | Purpose and example |
| --- | --- | --- | --- |
| `GET /classes/{class_id}/components` | UUID | 200: `ComponentRead[]` | `Invoke-GradeApi GET "/classes/$classId/components"` |
| `POST /classes/{class_id}/components` | Nonempty `ComponentCreate[]` | 201: `ComponentRead[]` | Atomic batch: `Invoke-GradeApi POST "/classes/$classId/components" $componentCreate` |
| `PUT /classes/{class_id}/components` | Nonempty `ComponentWrite[]` | 200: `ComponentRead[]` | Full configuration: `Invoke-GradeApi PUT "/classes/$classId/components" $componentWrite` |
| `PATCH /components/{component_id}` | `ComponentUpdate` | 200: `ComponentRead` | `Invoke-GradeApi PATCH "/components/$componentId" $componentUpdate` |
| `DELETE /components/{component_id}` | UUID | 204 | Remaining configuration must be valid: `Invoke-GradeApi DELETE "/components/$componentId"` |
| `GET /classes/{class_id}/grades` | UUID | 200: `ClassGradesRead` | Full roster grid: `Invoke-GradeApi GET "/classes/$classId/grades"` |
| `PUT /enrollments/{enrollment_id}/scores` | Nonempty UUID-to-score/null map | 200: `GradeRead` | Partial update: `Invoke-GradeApi PUT "/enrollments/$enrollmentId/scores" $scorePatch` |
| `POST /classes/{class_id}/finalize` | No body | 202: `FinalizeRead` | Commit release then enqueue: `Invoke-GradeApi POST "/classes/$classId/finalize"` |
| `GET /classes/{class_id}/ranking` | UUID | 200: `RankingRead[]` | Stored rankings: `Invoke-GradeApi GET "/classes/$classId/ranking"` |
| `GET /students/{student_id}/history` | Student UUID | 200: `HistoryRead[]` | Released history: `Invoke-GradeApi GET "/students/$studentId/history"` |

Weights must total 100% and include UTS/UAS. PUT configuration retains existing IDs or omits IDs for new components. Individual PATCH/DELETE must also leave a valid full configuration. Finalized grades block score, roster, and component changes. A scored component cannot be deleted; its maximum cannot be lowered below saved scores.

For scores, omit IDs to preserve entries, send `null` to clear, and send zero for a real zero. Scores permit at most two decimal places and cannot exceed the component maximum. Finalization requires a nonempty roster and all scores. Ranking ties receive distinct positions ordered by NIM/name.

### Dashboard and notification audit

| Method and path | Input | Success | Purpose and example |
| --- | --- | --- | --- |
| `GET /dashboard/summary` | None | 200: `DashboardSummaryRead` | Both roles, scoped view: `Invoke-GradeApi GET '/dashboard/summary'` |
| `GET /admin/notifications` | Optional `status=queued`, `sent`, or `failed` | 200: `NotificationRead[]` | Admin only: `Invoke-GradeApi GET '/admin/notifications?status=failed'` |
| `POST /admin/notifications/{notification_id}/retry` | No body | 202: `NotificationRead` | Admin retry of unsent record: `Invoke-GradeApi POST "/admin/notifications/$notificationId/retry"` |

Retry rejects sent records, refreshes the student's email from the profile, and prepares a new dispatch generation. HTTP 202 does not confirm delivery.

### Downloads

These require assigned-class access or superadmin. Pass bearer headers and save binary content to a file.

```powershell
$downloadHeaders = @{Authorization = "Bearer $($tokens.access_token)"}
```

| Method and path | Input | Success | Example |
| --- | --- | --- | --- |
| `GET /reports/student/{enrollment_id}/pdf` | Finalized enrollment UUID | 200: PDF attachment | `Invoke-WebRequest "$apiBase/reports/student/$enrollmentId/pdf" -Headers $downloadHeaders -OutFile student.pdf` |
| `GET /reports/class/{class_id}/pdf` | Fully finalized class UUID | 200: PDF attachment | `Invoke-WebRequest "$apiBase/reports/class/$classId/pdf" -Headers $downloadHeaders -OutFile class.pdf` |
| `GET /reports/class/{class_id}/xlsx` | Fully finalized class UUID | 200: XLSX attachment | `Invoke-WebRequest "$apiBase/reports/class/$classId/xlsx" -Headers $downloadHeaders -OutFile class.xlsx` |

PDF uses `application/pdf`; XLSX uses `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`. Downloads set `Content-Disposition: attachment` and `Cache-Control: no-store`. Missing renderer dependencies return 503. Regenerate download headers if the token rotates.

## Payload examples

Use actual UUIDs from your server. These examples define payloads; submit the relevant one using the inventory above. For a new lecturer password, obtain a credential rather than storing it in the document:

```powershell
$newLecturer = Get-Credential -Message 'New lecturer email and password'
$userCreate = @{
  email = $newLecturer.UserName
  password = $newLecturer.GetNetworkCredential().Password
  full_name = 'Example Lecturer'
  role = 'lecturer'
}
$userUpdate = @{full_name = 'Updated Lecturer'; is_active = $true}
$courseCreate = @{code='IF101'; name='Algorithms'; credits=3; semester='Ganjil'}
$courseUpdate = @{name='Introduction to Algorithms'}
# For admin creation, use a lecturer ID returned by /admin/users.
$classCreate = @{course_id=$courseId; section='A'; academic_year='2026/2027'; lecturer_id=$lecturerId}
$classUpdate = @{section='B'}
$studentCreate = @{nim='2026001'; full_name='Example Student'; email='student@example.com'}
$studentUpdate = @{email=$null}
$enrollmentCreate = @{nim='2026001'; full_name='Example Student'; email='student@example.com'}
$componentCreate = @(
  @{name='Midterm'; category='uts'; weight='40.00'; max_score='100.00'; order_index=0}
  @{name='Final'; category='uas'; weight='60.00'; max_score='100.00'; order_index=1}
)
# Populate this from GET components so existing IDs are retained.
$componentWrite = @(Invoke-GradeApi GET "/classes/$classId/components" | ForEach-Object {
  @{id=$_.id; name=$_.name; category=$_.category; weight=$_.weight; max_score=$_.max_score; order_index=$_.order_index}
})
$componentUpdate = @{name='Renamed assessment'}
$scorePatch = @{}
$scorePatch[$componentId] = '80.00'
# To clear instead: $scorePatch[$componentId] = $null
```

`UserCreate` requires email, password (6–128 characters), and full name; role defaults to `lecturer` and can be `superadmin`. `CourseCreate` requires code, name, positive integer credits, and semester. `StudentCreate` requires NIM/name with optional email. Enrollment requires NIM and optionally name/email. For a new NIM, an omitted name falls back to NIM.

Course/class update `null` values retain old fields. Student update `email: null` clears the address. Component PATCH rejects explicit null and unknown fields; component names are at most 100 characters, weights are positive and at most 100, maxima positive, and decimal fields allow two places. See OpenAPI for all field lengths and numeric bounds.

## Response contracts

| Contract | Fields / composition |
| --- | --- |
| `UserResponse` | `id`, `email`, `full_name`, `role`, `is_active` |
| `UserRead` | User profile plus `created_at`, `updated_at`; no password hash |
| `CourseRead` | `id`, `code`, `name`, `credits`, `semester`, `created_by`, `created_at` |
| `ClassRead` | `id`, `course_id`, `section`, `lecturer_id`, `academic_year`, `created_at`, `has_finalized_grades` |
| `StudentRead` | `id`, `nim`, `full_name`, nullable `email`, `created_at` |
| `RosterEntryRead` | Enrollment `id`, `enrolled_at`, nested `student` |
| `ComponentRead` | `id`, `class_id`, `name`, `category`, `weight`, `max_score`, `order_index`, `created_at` |
| `GradeRead` | `id`, `enrollment_id`, `final_score`, `status`, nullable `finalized_at`, `finalized_by`, `release_notified_at` |
| `ClassGradesRead` | `class_id`, `components`, `grades`; each grade row has `enrollment_id`, `student`, score map, nullable `final_score`, and `status` |
| `FinalizeRead` | `finalized_count`, `notified` (accepted queue submissions) |
| `RankingRead` | `rank`, `enrollment_id`, `student`, `final_score` |
| `HistoryRead` | `grade_id`, `enrollment_id`, nested `course`, JSON key `class`, `final_score`, nullable `rank`/`finalized_at`, component details/scores |
| `DashboardSummaryRead` | `course_count`, `class_count`, `pending_class_count`, nested `courses`/classes, `recently_released` |
| `NotificationRead` | `id`, `grade_id`, nullable `student_email`, `status`, nullable `error_message`/`sent_at`, `created_at` |

Grade status is `draft` or `finalized`. Notification status is `queued`, `sent`, or `failed`. Dashboard class status is `pending` or `released`.

## Errors

| HTTP | Meaning |
| --- | --- |
| 401 | Missing/invalid token, inactive account, rejected login/refresh |
| 403 | Role or resource access denied |
| 404 | Unknown resource or enrollment outside the requested roster |
| 409 | Duplicate data, dependent records, finalized mutation, repeated release, or sent notification retry |
| 422 | Invalid schema, component configuration, out-of-range/missing scores, or missing credentials |
| 429 | Login limiter exceeded |
| 503 | Required report renderer unavailable |

Service failures normally use `{ "detail": "message" }`. Pydantic failures use an array of field errors under `detail`. Missing finalization scores return a structured detail:

```json
{
  "detail": {
    "message": "Nilai komponen belum lengkap",
    "missing": [{"student_nim": "2026001", "component_name": "Midterm"}]
  }
}
```

After a finalization timeout, read `/classes/{class_id}/grades` before retrying: loss of the response does not imply rollback. A successful release can coexist with enqueue/delivery failures, which are handled through notification audit/retry.
