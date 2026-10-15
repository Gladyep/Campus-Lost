# CampusConnect — Backend Requirements Analysis

**Project:** CampusConnect — Smart Lost and Found Platform  
**Document:** Backend Requirements Analysis  
**Technology:** Python, Django, Django REST Framework, MySQL  
**Version:** 1.0  
**Date:** October 2026

## 1. Purpose

This document defines the backend requirements for CampusConnect. The Django backend exposes APIs to the React frontend and is responsible for authentication, authorization, item reporting, image handling, search, potential-match detection, claim verification, private messaging, notifications, administration, and data integrity.

## 2. Backend Objectives

- Provide secure and consistent REST APIs.
- Store and retrieve application data using MySQL.
- Enforce role-based and object-level permissions.
- Match lost reports with relevant found reports.
- Support claims and verification workflows.
- Protect private messages, contact details, and verification answers.
- Notify users about relevant matches and status changes.
- Provide moderation tools and auditable administrative actions.

## 3. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | Python | Backend application logic |
| Framework | Django | Models, authentication, admin, and business logic |
| API | Django REST Framework | REST endpoints, serializers, permissions, and pagination |
| Database | MySQL | Persistent relational data |
| Image storage | Django media storage in development; managed/private object storage in production | Store uploaded images |
| Background jobs | Optional task queue such as Celery with a message broker | Process matching and notification tasks asynchronously when needed |
| Testing | Django test framework / pytest, plus Postman | Unit, integration, and API testing |

## 4. Functional Requirements

| ID | Requirement | Description |
|---|---|---|
| BE-01 | Authentication | Support secure registration, login, logout, and session/token validation. |
| BE-02 | Authorization | Enforce role and object-level permissions for every protected operation. |
| BE-03 | User management | Manage user profiles, account status, and campus affiliation fields where needed. |
| BE-04 | Item reporting | Create, read, update, and close authorized lost/found reports. |
| BE-05 | Image management | Validate image uploads and store file references safely. |
| BE-06 | Search and filtering | Filter and paginate item reports by keyword, category, location, date, type, and status. |
| BE-07 | Matching engine | Score eligible lost/found report pairs and record potential matches. |
| BE-08 | Claims | Create claims and enforce permitted claim state transitions. |
| BE-09 | Verification | Store item-specific questions and claim answers with strict access controls. |
| BE-10 | Messaging | Authorize conversation participants and protect private message data. |
| BE-11 | Notifications | Generate and deliver match, claim, message, and status notifications. |
| BE-12 | Moderation | Flag suspicious activity and provide administrator review actions. |
| BE-13 | Audit logs | Record important administrative and claim decisions. |
| BE-14 | Reporting | Provide authorized aggregate statistics for the dashboard. |
| BE-15 | Data integrity | Use constraints, transactions, and validation to maintain consistent records. |

## 5. Proposed Data Model

The exact schema should be refined during implementation. Django's built-in user model can be extended or replaced with a custom user model.

### 5.1 `User`
Suggested fields:
- `id`
- `name`
- `email` (unique where required)
- Django-managed password hash
- `role` or permissions
- `is_active`
- timestamps and permitted campus profile fields

### 5.2 `Category`
Suggested fields:
- `id`
- `name`
- `description`

### 5.3 `Item`
Suggested fields:
- `id`
- `user` (foreign key to the reporter)
- `category` (foreign key)
- `title`
- `description`
- `item_type` (`LOST` or `FOUND`)
- `location`
- `event_date`
- `status`
- timestamps

### 5.4 `ItemImage`
Suggested fields:
- `id`
- `item` (foreign key)
- `image` or `image_path`
- `uploaded_at`

### 5.5 `Claim`
Suggested fields:
- `id`
- `item` (foreign key to the found item)
- `claimant` (foreign key to the user)
- `status`
- `submitted_at`
- `reviewed_at`
- `reviewed_by` (nullable user reference)
- `decision_reason` where appropriate

### 5.6 `VerificationQuestion`
Suggested fields:
- `id`
- `item` (foreign key)
- `question_text`
- `is_active`

### 5.7 `ClaimAnswer`
Suggested fields:
- `id`
- `claim` (foreign key)
- `question` (foreign key)
- `answer_text`
- timestamps

### 5.8 `Match`
Suggested fields:
- `id`
- `lost_item` (foreign key to an item with type `LOST`)
- `found_item` (foreign key to an item with type `FOUND`)
- `match_score`
- `status`
- timestamps

Enforce that the two references have opposite item types through application validation and, where feasible, database-level constraints.

### 5.9 `Conversation` and `Message`
Suggested fields:
- `Conversation`: `id`, `item`, optional `claim`, timestamps.
- Conversation participants should be represented explicitly or derived through a clearly enforced permission model.
- `Message`: `id`, `conversation`, `sender`, `message_text`, `sent_at`, `read_at`.

### 5.10 `Notification`
Suggested fields:
- `id`
- `user`
- `type`
- `message` or structured payload
- `is_read`
- `created_at`
- optional link to the relevant item, match, or claim

### 5.11 `Report` and `AuditLog`
- `Report`: reporter, reported user or item, reason, status, timestamps, and review fields.
- `AuditLog`: actor, action, entity type, entity ID, timestamp, and limited relevant metadata.

Avoid logging passwords, authentication tokens, or unnecessary private message and claim-answer content.

## 6. Relationships and Integrity

- One user can report many items.
- One category can be assigned to many items.
- One item can have many images.
- One found item can have multiple claims.
- One claim can have multiple answers.
- One lost item can have multiple potential matches with found items.
- One conversation can contain many messages and must have authorized participants.
- One user can receive many notifications.
- Administrative actions should create audit records.

Use foreign keys, suitable indexes, database transactions, and appropriate deletion policies. Keep historical records where needed for dispute resolution and accountability.

## 7. API Requirements

The following routes are proposed. Actual request/response formats and endpoint names should be documented in the implemented API.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register/` | Register a user |
| POST | `/api/auth/login/` | Authenticate a user |
| POST | `/api/auth/logout/` | End an authenticated session, if implemented |
| GET | `/api/items/` | List/search/filter reports |
| POST | `/api/items/` | Create a lost/found report |
| GET | `/api/items/{id}/` | Retrieve report details |
| PATCH | `/api/items/{id}/` | Update an authorized report |
| DELETE | `/api/items/{id}/` | Delete or deactivate a report according to policy |
| GET | `/api/matches/` | Retrieve permitted potential matches |
| POST | `/api/claims/` | Submit an ownership claim |
| GET | `/api/claims/{id}/` | Retrieve an authorized claim |
| POST | `/api/claims/{id}/answers/` | Submit verification answers |
| PATCH | `/api/claims/{id}/decision/` | Review a claim with strict authorization |
| GET | `/api/conversations/` | List conversations available to the current user |
| POST | `/api/conversations/` | Start an authorized conversation |
| GET | `/api/conversations/{id}/messages/` | Retrieve permitted messages |
| POST | `/api/conversations/{id}/messages/` | Send a message |
| GET | `/api/notifications/` | Retrieve user notifications |
| PATCH | `/api/notifications/{id}/` | Mark a notification as read |
| GET | `/api/admin/dashboard/` | Retrieve administrator statistics |
| GET | `/api/admin/flagged-claims/` | Retrieve claims requiring review |
| POST | `/api/admin/reports/{id}/decision/` | Record an authorized moderation decision |

## 8. Smart Matching Requirements

### 8.1 Matching process
1. Trigger matching when a report is created or relevant fields change.
2. Retrieve eligible reports of the opposite type.
3. Exclude closed, returned, invalid, or otherwise ineligible reports.
4. Compare category, text description, location, date, and optional visual attributes.
5. Calculate a configurable relevance score.
6. Store or update the match record without creating duplicates.
7. Notify appropriate users when a match meets the configured threshold.
8. Re-evaluate matches when reports change status or details.

### 8.2 Example scoring model

| Attribute | Illustrative weight |
|---|---:|
| Category similarity | 30% |
| Description similarity | 30% |
| Location proximity | 20% |
| Date proximity | 20% |
| Total | 100% |

These weights are starting values for evaluation, not validated accuracy figures. The algorithm should be tested on representative sample reports. A match score is only a recommendation and must never approve a claim automatically.

### 8.3 Duplicate prevention
- Use a database uniqueness constraint for the lost/found pair where appropriate.
- Update existing match records instead of repeatedly inserting the same pair.
- Track notification delivery to avoid sending duplicate alerts unnecessarily.

## 9. Claim Verification and Status Rules

Suggested claim states:
- `PENDING`
- `UNDER_VERIFICATION`
- `APPROVED`
- `REJECTED`
- `FLAGGED`
- `DISPUTED`

Suggested item states:
- `LOST`
- `FOUND`
- `CLAIM_PENDING`
- `UNDER_VERIFICATION`
- `RETURNED`
- `CLOSED`
- `DISPUTED`

Requirements:
- Validate every state transition on the backend.
- Only authorized finders or designated reviewers may make permitted claim decisions.
- An approved claim should allow a safe handover process; approval alone does not prove that handover occurred.
- Mark an item as returned only after the configured recovery-confirmation process.
- Repeated failed claims, suspicious patterns, or user reports may trigger review.
- A fraud flag should trigger investigation, not automatically establish misconduct.
- Preserve decision timestamps and reviewer identity for accountability.

## 10. Anonymous Messaging Requirements

- Keep personal email addresses and phone numbers hidden from other users by default.
- Authorize each conversation participant for every read and write request.
- Link conversations to a relevant item or claim.
- Validate message length and content.
- Apply rate limits and support blocking/reporting.
- Define when administrators may access conversation data for a legitimate moderation purpose.
- Do not treat anonymity as a replacement for moderation, auditability, or appropriate privacy controls.

## 11. Notification Requirements

Generate notifications for:
- A new potential match above the configured threshold.
- A claim being submitted.
- A claim moving to another state.
- A new message.
- A report being flagged or a dispute requiring action.
- A confirmed item return or closure.

Notifications can initially be stored in MySQL and shown in the frontend. Email or browser push can be added later. Background processing may be introduced when matching or delivery work becomes slow or needs retries.

## 12. Security Requirements

- Use Django's password hashing and established authentication mechanisms.
- Enforce authentication, role-based permissions, and object-level access checks.
- Validate all input on the server, including uploaded files.
- Configure allowed hosts, CORS, CSRF protection, secure cookies, and HTTPS appropriately for deployment.
- Store secrets outside source control.
- Use parameterized ORM queries and avoid unsafe raw SQL.
- Apply rate limits to login, claims, messages, and other abuse-prone endpoints.
- Protect private claim answers, messages, and personal details.
- Use transactions for critical operations and prevent conflicting claim decisions.
- Keep backups and establish a retention/deletion policy.
- Audit privileged actions without storing unnecessary sensitive content.

## 13. Non-Functional Requirements

| ID | Requirement | Description |
|---|---|---|
| BENFR-01 | Performance | Paginate list APIs, index common filters, and measure performance under a defined load. |
| BENFR-02 | Reliability | Return consistent API errors and handle database or delivery failures safely. |
| BENFR-03 | Security | Protect endpoints and data against unauthorized access. |
| BENFR-04 | Scalability | Separate matching and notification work so it can move to background processing when needed. |
| BENFR-05 | Maintainability | Separate models, serializers, views, permissions, services, and tests. |
| BENFR-06 | Integrity | Use database constraints and transactions for important state changes. |
| BENFR-07 | Observability | Log operational errors and monitor failed jobs without leaking secrets. |
| BENFR-08 | Compatibility | Use supported, compatible versions of Django, DRF, Python, and MySQL. |

## 14. Suggested Backend Structure

```text
backend/
├── manage.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── accounts/
│   ├── items/
│   ├── matching/
│   ├── claims/
│   ├── messaging/
│   ├── notifications/
│   └── moderation/
├── media/
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

Each Django app may contain `models.py`, `serializers.py`, `views.py`, `urls.py`, `permissions.py`, `services.py`, and tests as appropriate. Never commit real credentials in `.env`; include only placeholder variable names in `.env.example`.

## 15. Testing Requirements

| Test ID | Scenario | Expected result |
|---|---|---|
| BET-01 | Register and authenticate a valid user | Account and authentication work as configured. |
| BET-02 | Access a protected endpoint without authentication | Request is rejected. |
| BET-03 | User attempts to edit another user's report | Request is denied unless explicitly permitted. |
| BET-04 | Upload an invalid file | Backend rejects the file. |
| BET-05 | Filter item reports | API returns only matching results with valid pagination. |
| BET-06 | Create opposite-type similar reports | Matching service evaluates and records a potential match. |
| BET-07 | Submit the same claim twice | Duplicate handling follows the defined policy. |
| BET-08 | Unauthorized user reads claim answers | Access is denied. |
| BET-09 | Non-participant reads a conversation | Access is denied. |
| BET-10 | Regular user calls an admin endpoint | Access is denied. |
| BET-11 | Claim decision is recorded | Status, reviewer, and audit history remain consistent. |
| BET-12 | Notification task fails | Failure is handled and retry/recovery behavior follows the implementation. |
| BET-13 | Concurrent claim decisions occur | Conflicting state changes are prevented or handled consistently. |
| BET-14 | SQL-like text is submitted as input | Input is handled safely through validated ORM/API processing. |

## 16. Backend Acceptance Criteria

- APIs implement the documented request and response contracts.
- MySQL models, relationships, migrations, and constraints work correctly.
- Authentication and object-level authorization are enforced server-side.
- Reports and images are validated and stored safely.
- Search and filtering return correct, paginated results.
- Matching records are created without unintended duplicates.
- Claims and verification answers follow the permitted workflow.
- Messages and notifications are accessible only to authorized users.
- Administrators can review flagged activity and create auditable decisions.
- Functional, integration, security, and error-handling tests pass.

## 17. Implementation Sequence

1. Create the Django project and configure MySQL.
2. Configure the user model and authentication.
3. Build item and category models, serializers, permissions, and APIs.
4. Add image upload and search/filtering.
5. Implement claims and verification questions.
6. Add potential-match scoring and match persistence.
7. Implement private conversations and notifications.
8. Build moderation and admin APIs with audit logging.
9. Add tests, API documentation, deployment configuration, and monitoring.

## 18. Conclusion

The CampusConnect backend is responsible for the platform's data, business rules, security, and integrations. Django REST Framework provides the API layer, while MySQL stores structured application records. Smart matching, verification workflows, privacy-aware messaging, notifications, and administrative review work together to make lost-item recovery more organized and trustworthy.
