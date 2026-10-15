# CampusConnect — Frontend Requirements Analysis

**Project:** CampusConnect — Smart Lost and Found Platform  
**Document:** Frontend Requirements Analysis  
**Technology:** React.js  
**Version:** 1.0  
**Date:** October 2026

## 1. Purpose

This document defines the requirements for the CampusConnect frontend. The React application provides the user interface through which students, faculty, staff, and administrators report lost or found items, search listings, manage claims, communicate privately, and receive notifications.

## 2. Frontend Objectives

- Provide a clear, responsive, and accessible user experience.
- Make reporting a lost or found item quick and straightforward.
- Help users discover relevant listings through search, filters, and potential matches.
- Guide owners through claim submission and verification.
- Support private, in-platform communication without exposing personal contact details.
- Give administrators a dedicated interface for reviewing suspicious activity and managing reports.

## 3. Users and Interfaces

### 3.1 Campus user
- Register, log in, and log out.
- View, search, and filter lost and found reports.
- Create and manage their own reports.
- View potential matches and notifications.
- Submit claims and track their status.
- Use private messaging and report suspicious activity.

### 3.2 Finder / claimant
- Review claims for items they reported finding, subject to permissions.
- Review or answer verification questions as permitted by the workflow.
- Communicate with claimants through the platform.
- Confirm the handover when the item is returned.

### 3.3 Administrator
- View dashboard summaries and queues for flagged claims, disputes, and reports.
- Review relevant claim and item details.
- Record moderation decisions and reasons.
- Manage users and inappropriate content according to assigned permissions.
- View audit information available to authorized administrators.

## 4. Functional Requirements

| ID | Requirement | Description |
|---|---|---|
| FE-01 | Authentication screens | Provide registration, login, logout, validation, and useful error messages. |
| FE-02 | User profile | Display and allow editing of permitted profile fields. |
| FE-03 | Dashboard | Show relevant listings, recent activity, potential matches, and notifications. |
| FE-04 | Lost-item form | Collect title, category, description, date, location, and optional photos. |
| FE-05 | Found-item form | Collect found-item details, discovery date/location, and photos. |
| FE-06 | Image upload preview | Preview selected photos and show file validation errors. |
| FE-07 | Search and filters | Search keywords and filter by category, date, location, item type, and status. |
| FE-08 | Item details | Show listing details while hiding private information and protected verification details. |
| FE-09 | Potential matches | Display suggested matching reports and a clear indication that a match is not proof of ownership. |
| FE-10 | Claim form | Allow a user to submit a claim and answer verification questions. |
| FE-11 | Claim tracking | Display pending, under-verification, approved, rejected, and disputed states as applicable. |
| FE-12 | Messaging | Provide item- or claim-related conversations without automatically revealing phone numbers or email addresses. |
| FE-13 | Notifications | Display match alerts, claim updates, messages, and status changes. |
| FE-14 | User reports | Let users report suspicious claims, users, or inappropriate content. |
| FE-15 | Admin dashboard | Show counts and queues for flagged claims, disputes, reports, and moderation actions. |
| FE-16 | Accessibility and responsiveness | Support keyboard navigation, readable contrast, clear labels, and mobile/tablet/desktop layouts. |

## 5. Proposed Pages and Components

| Page / Component | Main responsibilities |
|---|---|
| Login | Collect credentials and display authentication errors. |
| Registration | Collect required account information and validate input. |
| Main dashboard | Summarize recent listings, matches, and notifications. |
| Lost & Found listing page | Show searchable, filterable item cards. |
| Item details page | Show public item details, photos, status, and allowed actions. |
| Create/edit item form | Submit or update a report with validated fields and image previews. |
| My reports | List reports created by the current user and their statuses. |
| Matches page | Show potential lost/found matches and their relevance. |
| Claim form | Collect ownership evidence and verification answers. |
| Claims page | Show claims and their progress to authorized participants. |
| Messages | Show conversations and send/receive messages. |
| Notifications | List alerts and allow them to be marked as read. |
| Admin dashboard | Display review queues, statistics, and moderation controls. |
| Shared UI components | Navigation, protected routes, loading states, dialogs, alerts, pagination, and empty states. |

## 6. Frontend Validation and User Feedback

- Require mandatory fields before submission.
- Validate date formats and reject invalid or implausible values where applicable.
- Validate image file type and size on the client for usability; the backend must validate again.
- Display loading indicators during API requests.
- Show clear success and error messages.
- Confirm potentially destructive actions such as deleting or closing a report.
- Handle empty search results, expired sessions, network errors, and permission errors.
- Prevent duplicate submissions while a request is in progress.
- Do not rely on frontend checks alone for security or authorization.

## 7. API Integration Requirements

The frontend communicates with Django REST Framework through HTTP APIs.

| Method | Proposed endpoint | Frontend use |
|---|---|---|
| POST | `/api/auth/register/` | Register |
| POST | `/api/auth/login/` | Log in |
| POST | `/api/auth/logout/` | Log out, if implemented |
| GET | `/api/items/` | List and filter reports |
| POST | `/api/items/` | Create a report |
| GET | `/api/items/{id}/` | View a report |
| PATCH | `/api/items/{id}/` | Update an authorized report |
| GET | `/api/matches/` | View potential matches |
| POST | `/api/claims/` | Submit a claim |
| GET | `/api/claims/{id}/` | View an authorized claim |
| POST | `/api/claims/{id}/answers/` | Submit verification answers |
| GET | `/api/notifications/` | Retrieve notifications |
| PATCH | `/api/notifications/{id}/` | Mark notification as read |
| GET | `/api/conversations/` | Retrieve permitted conversations |
| POST | `/api/conversations/` | Start a permitted conversation |
| GET | `/api/admin/dashboard/` | Retrieve administrator summaries |
| GET | `/api/admin/flagged-claims/` | Retrieve flagged claims for review |

These endpoints are proposed and must be aligned with the implemented backend API.

## 8. Frontend State and Access Control

- Keep authentication state in an appropriate, secure implementation.
- Use protected routes to improve navigation and user experience.
- Render administrator pages only for users with the relevant role.
- Treat the backend as the source of truth for permissions.
- Avoid storing passwords or sensitive verification answers in browser storage.
- Handle session expiration and redirect users to sign in when necessary.
- Do not expose secrets in React environment variables; frontend environment variables are not private.

## 9. Non-Functional Requirements

| ID | Requirement | Description |
|---|---|---|
| FENFR-01 | Usability | Common actions should be easy to discover and complete. |
| FENFR-02 | Responsiveness | Layout should work on mobile, tablet, and desktop screens. |
| FENFR-03 | Performance | Use pagination and efficient rendering for large listing collections. |
| FENFR-04 | Accessibility | Use semantic HTML, labels, keyboard support, and suitable contrast. |
| FENFR-05 | Maintainability | Organize pages, reusable components, API calls, and styles into separate modules. |
| FENFR-06 | Reliability | Provide loading, empty, success, and error states for API-driven screens. |
| FENFR-07 | Privacy | Display only information the current user is authorized to view. |

## 10. Suggested Frontend Structure

```text
frontend/
├── public/
├── src/
│   ├── api/
│   │   ├── client.js
│   │   ├── auth.js
│   │   ├── items.js
│   │   ├── claims.js
│   │   ├── matches.js
│   │   ├── messages.js
│   │   └── notifications.js
│   ├── assets/
│   ├── components/
│   │   ├── layout/
│   │   ├── items/
│   │   ├── claims/
│   │   └── common/
│   ├── pages/
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   ├── Dashboard.jsx
│   │   ├── Items.jsx
│   │   ├── ItemDetails.jsx
│   │   ├── CreateItem.jsx
│   │   ├── Matches.jsx
│   │   ├── Claims.jsx
│   │   ├── Messages.jsx
│   │   ├── Notifications.jsx
│   │   └── AdminDashboard.jsx
│   ├── routes/
│   ├── hooks/
│   ├── context/
│   ├── styles/
│   ├── App.jsx
│   └── main.jsx
├── package.json
└── README.md
```

This is a suggested organization; actual file names can vary.

## 11. Frontend Testing Requirements

| Test ID | Scenario | Expected result |
|---|---|---|
| FET-01 | Submit invalid login details | Clear validation or authentication error is shown. |
| FET-02 | Submit a valid item form | User sees success feedback and the created report. |
| FET-03 | Filter by category | Only matching results are displayed. |
| FET-04 | Select an unsupported image | UI shows a validation error and prevents normal submission. |
| FET-05 | Open a protected page while signed out | User is prompted to authenticate. |
| FET-06 | Regular user opens admin route | Admin content is not exposed; backend also denies access. |
| FET-07 | Submit a claim | Claim status and next steps are displayed. |
| FET-08 | Receive a notification | Notification appears with appropriate read/unread state. |
| FET-09 | API request fails | UI displays a recoverable error state. |
| FET-10 | Use the interface on a small screen | Main workflows remain usable without broken layout. |

## 12. Frontend Acceptance Criteria

- All required pages are accessible through clear navigation.
- Users can submit and manage reports through API integration.
- Search, filters, claims, matches, messages, and notifications show backend data.
- Forms validate inputs and display useful feedback.
- Private information is not rendered to unauthorized users.
- The layout is responsive and accessible.
- Loading, empty, error, and session-expiration states are handled.
- Administrator functions are protected in both the frontend and backend.

## 13. Conclusion

The CampusConnect React frontend will provide the user-facing experience for reporting, finding, claiming, and recovering campus belongings. Its design should prioritize simplicity, privacy, accessibility, and clear status feedback while relying on Django for authoritative validation and access control.
