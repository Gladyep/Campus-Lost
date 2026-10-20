# CampusConnect — Complete Bug Fixes and Feature Implementation Prompt

## Instructions for GitHub Copilot

You are working on an existing CampusConnect application.

### Existing technology stack
- **Frontend:** React + Vite
- **Routing:** React Router DOM
- **HTTP requests:** Axios
- **Backend:** Django
- **Database:** MySQL
- **Important restriction:** Do **not** use Django REST Framework.

### Primary objective
Inspect the existing codebase and fix the reported bugs, then implement the requested features in the existing architecture. Do not simply redesign the UI or create mock demonstrations. The features must work with real data through the existing Django backend and MySQL database.

## Critical implementation rules

1. **Inspect before editing.** First inspect the repository structure, frontend routes/components, Axios configuration, Django settings/URLs/views/models, authentication/session implementation, MySQL configuration, report models, and any existing messaging/matching/notification logic.
2. Reuse existing components, models, routes, tables, and API conventions whenever suitable. Do not create duplicate models or tables for functionality that already exists.
3. Do not use Django REST Framework. Use ordinary Django views, URL patterns, Django ORM, and the project's existing request/response conventions.
4. Do not hardcode sample listings, fake matches, fake notifications, fake messages, or fake counters in normal application operation.
5. Do not silently fall back to example data when the API is unavailable. Show a clear loading, empty, or error state as appropriate.
6. Keep authentication and authorization secure. A user may access only their own private reports, conversations, messages, and notifications, except for fields intentionally made public in community reports.
7. Never expose passwords, session secrets, tokens, or unnecessary private user details.
8. Preserve the existing visual style, responsive layout, typography, colors, sidebar, and navigation unless a change is required by the feature.
9. Do not break existing Discover, My Reports, Matches, Visual Search, Messages, Alerts, sign-in, sign-out, or report-submission functionality.
10. Do not replace the authentication system or change unrelated features.
11. Validate input on the frontend and backend. Use Django ORM parameterized filtering rather than building SQL from user input.
12. If a requested behavior depends on infrastructure or a model that does not exist, implement it using the current architecture and clearly explain any required setup. Do not claim a feature is working unless it has been tested.

---

# Part 1 — Fix Shared Backend, API, and Authentication Problems

## Issue 1: Authenticated pages incorrectly ask users to sign in

### Observed problem
Messages, Alerts, and Matches sometimes display messages such as:
- “Sign in to see your activity.”
- “Connect to the CampusConnect API to load private updates.”

This happens even after a user has signed in.

### Required fixes
- Trace the existing sign-in flow and determine how the frontend stores or maintains authentication.
- Check whether Axios requests include the correct authentication credentials or authorization headers according to the existing setup.
- Check Django authentication, session/cookie configuration, CSRF handling where applicable, API URLs, allowed hosts, CORS settings if applicable, and frontend API base URL.
- Ensure authenticated API views identify the currently signed-in user correctly.
- Ensure frontend authentication state is refreshed and shared consistently across routes.
- Do not treat a failed API request as proof that the user is signed out.
- Handle `401`, `403`, network failures, and server errors distinctly.
- On an actual expired session, show a clear sign-in prompt. On a backend failure, show a backend connection error instead.
- Verify sign-in, refresh, navigation between pages, sign-out, and sign-in as a different account.

Do not weaken authentication or make private endpoints public to hide this error.

## Issue 2: Frontend displays example data while Django API is offline

### Observed problem
Discover displayed a notice similar to “Showing example listings while the Django API is offline.”

### Required fixes
- Find and remove development/mock-data fallbacks from normal production/user flows.
- Load community reports from the actual Django backend and MySQL database.
- Display a loading state while requests are pending.
- Display a useful empty state when the backend successfully returns zero results.
- Display a clear connection/error state when the API fails.
- Do not present example records as real reports.
- If mock data is needed for development, keep it explicitly behind a development-only setting and never use it to conceal API failures.

## Issue 3: Shared community data versus private account data

### Required behavior
All users should access the same community report collection, subject to the application's intended visibility rules. Private user information must remain private.

Example:
- User A submits a lost-item report.
- User B signs in and can see that report in the community feed.
- User B must not automatically gain access to User A's private messages or private account data.

### Required fixes
- Confirm every report has the correct reporter/owner relationship.
- Ensure community endpoints return appropriately visible reports from all relevant users, not just the currently signed-in user's reports.
- Ensure personal pages such as My Reports filter by the authenticated user.
- Ensure messages, conversations, and notifications are scoped to the authenticated user.
- Check for frontend local state, browser storage, or cached data that may cause one account's content to appear under another account.
- Clear or refresh user-specific client state on sign-out and account changes.
- Verify the behavior using at least two separate accounts.

---

# Part 2 — Fix Discover and Recent Reports

## Issue 4: Browse Recent Reports button does not work

### Required behavior
Clicking **Browse recent reports** should navigate to the relevant community feed or recent-reports section.

### Required fixes
- Inspect the button's click handler and route.
- Make it navigate to the existing Discover/recent-reports view.
- Ensure the destination loads real reports from Django/MySQL.
- Preserve the existing search, category filters, Lost/Found/Recovered tabs, and item cards.
- Ensure item cards and their action buttons work.
- Do not introduce a duplicate page if the existing Discover page can provide this functionality.

## Issue 5: Discover report list is not consistently connected to live data

### Required fixes
- Fetch real community reports from the backend.
- Support existing search, category, status, and other relevant filters.
- Show correct report details, image, item name, description, location, date, and status when available.
- Ensure reports submitted by one user can appear in the community feed for other users.
- Ensure the frontend uses the actual status values defined in the project.
- Avoid showing deleted, unauthorized, or incorrectly classified records.
- Confirm report submission updates the community feed after a successful response.

---

# Part 3 — Date Picker Improvements

## Issue 6: Date fields require manual typing

### Required behavior
Users should be able to choose dates using a calendar.

### Required fixes
- Inspect date fields in report forms and search/filter interfaces.
- Replace manually typed date fields with a suitable calendar picker, preferably the browser's native date input (`type="date"`) if no existing date-picker component is used.
- Preserve the project's expected date format and convert values correctly between frontend and backend.
- Validate dates on both frontend and backend.
- Do not allow an end date earlier than the start date in date-range filters.
- Ensure dates are stored and filtered consistently using the existing Django model field types.
- Test the fields in the target browser and at the expected display size.

---

# Part 4 — Messages and Private Conversations

## Issue 7: Messages do not appear or work after sign-in

### Required behavior
Messages should appear as a private, text-based conversation between the relevant users.

### Required fixes
- Inspect existing message and conversation models, views, URLs, and frontend components before creating anything new.
- Fix authentication/API integration so the Messages page loads conversations for the currently authenticated user.
- Implement or repair sending and retrieving messages using Django views and the existing MySQL database.
- Associate conversations with their participants and, when applicable, the related item report.
- Show sender, message text, and timestamp.
- Visually distinguish messages sent by the current user from messages received from the other participant.
- Update the conversation after sending a message and handle failed sends without falsely showing success.
- If there are no conversations, show a proper empty state rather than a sign-in prompt for an authenticated user.
- If the backend is unavailable, show an error state rather than fake messages.
- Enforce server-side authorization on every conversation and message request.
- A user must not be able to read or send messages in a conversation they do not participate in.
- Reuse an existing conversation when appropriate rather than creating duplicates.
- Do not expose private email addresses or other unnecessary personal details.

## Issue 8: Contact Reporter must open the correct conversation

### Required behavior
When a user clicks **Contact Reporter** on a report or match:
1. Identify the actual reporter associated with that report.
2. Open the existing conversation between the current user and that reporter for the relevant report, if one exists.
3. Otherwise, create a conversation using the existing data model and backend conventions.
4. Navigate to Messages and automatically select/open the correct conversation.
5. Allow the user to exchange messages.

### Additional requirements
- Prevent duplicate conversations for the same relevant report and participant pair where the current design expects a single conversation.
- Do not allow users to contact themselves.
- Verify that the report's reporter ID comes from trusted database data, not an arbitrary client-supplied identity.
- Handle deleted, unavailable, or unauthorized reports gracefully.

---

# Part 5 — Alerts as a Real Notification Centre

## Issue 9: Alerts page asks users to sign in and displays no notifications

### Required behavior
The Alerts page should function as a notification centre with persistent, user-specific notifications.

### Events that should create notifications
1. **New community reports:** Notify users when a new lost/found report is added to the community, according to the application's notification rules.
2. **New private messages:** Notify the recipient when another user sends a message.
3. **Potential matches:** Notify relevant users when a plausible match is created or identified.
4. **Report status updates:** Notify the report owner when their report status changes.
5. **Recovery updates:** Notify relevant participants when an item is marked recovered.

### Required implementation
- Inspect existing alert/notification models and reuse them if available.
- If no suitable model exists, add a Django model and migration for persistent notifications.
- Associate each notification with its recipient and, where relevant, the triggering user, item report, conversation, or match.
- Store notification type, readable message, creation timestamp, read/unread state, and relevant target reference as appropriate.
- Create notifications in the backend when the corresponding event occurs; do not rely solely on frontend state.
- Avoid creating duplicate notifications when an operation is retried.
- Ensure users can retrieve only their own notifications.
- Display notifications in chronological order, with unread notifications visually distinct.
- Allow users to mark one notification as read and, if practical, mark all as read.
- Clicking a notification should open the relevant report, message conversation, or match.
- Show a useful empty state when there are no notifications.
- Show an API error when loading fails instead of claiming the user is signed out.
- Ensure notifications remain available after page refresh and sign-out/sign-in.

### New-report notification consideration
Community-wide notifications can become noisy. Implement the requested behavior while following existing project expectations. If the app notifies users about every new report, do so deliberately and consistently. Do not send a notification to the person who created the report about their own report unless the existing product design explicitly requires it.

### Live updates
Use the simplest approach supported by the current architecture. Polling at a reasonable interval or refreshing on page focus is acceptable if real-time infrastructure is not configured. Do not add a new service just to simulate real-time updates. If WebSockets or another live-update mechanism already exists, reuse it.

---

# Part 6 — Matches and Potential Matches

## Issue 10: Matches page shows sign-in prompt or no relevant matches

### Required behavior
The Matches page should display actual possible connections between relevant lost and found reports and allow the user to contact the other reporter.

### Required fixes
- Inspect the current match implementation and its report-status conventions.
- Determine which reports are eligible for matching. Normally, compare lost reports with found reports and exclude recovered items from active matches.
- Compare available information such as item name, category, description, date, location, and image where supported.
- Use actual database records and the current authenticated user.
- Display relevant match cards with report images, names, descriptions, locations, dates, statuses, and a clear explanation that a match is only a suggestion.
- Include **View Details** and **Contact Reporter** actions.
- Contact Reporter must open the correct private conversation.
- Handle the absence of matches with an honest empty state.
- Do not display a hardcoded match count or fabricated matches.
- Avoid duplicate match records or repeated cards for the same connection.
- Recalculate or update matches when a relevant report is created or changed.

## Issue 11: Potential Matches counter on the dashboard is incorrect or always zero

### Required behavior
The dashboard counter should reflect real potential matches.

### Required fixes
- Inspect how the counter is currently calculated.
- Derive the count from persisted matches or the same matching logic used by the Matches page.
- Scope the count appropriately to the current user and the application's intended match rules.
- Ensure the count and displayed match cards use consistent data.
- Update the counter after relevant report or match changes.
- Never use a hardcoded value.

---

# Part 7 — Visual Search

## Issue 12: Visual Search does not find visually similar items

### Observed problem
A user uploaded a photo of a blue bag and selected the Bags category, but the application displayed “No similar items found” even though a similar bag report existed.

### Required behavior
Visual Search should find visually similar reported items, rather than relying only on exact item names or text descriptions.

### Required fixes
1. Inspect the current Visual Search page, upload flow, backend endpoint, image storage, report model, and current matching logic.
2. Confirm that uploaded images are actually sent to the backend and that existing report images can be retrieved or processed.
3. Implement genuine image-similarity comparison using an approach compatible with the current project and available environment. Do not pretend category filtering is visual recognition.
4. Compare the uploaded image against eligible community report images.
5. Return ranked similar results with a similarity score if the chosen approach provides a meaningful score.
6. Apply optional category, campus location, and date filters.
7. Clearly document any model, package, storage, or setup requirements.
8. Validate file type and size, handle missing/corrupt images, and report processing errors clearly.
9. Do not claim image recognition is working if only a placeholder or keyword search has been implemented.
10. If a full image-embedding model is not available in the project, first evaluate feasible options and explain any additional dependency or setup before relying on it.

### Results
Show actual matching reports with:
- Item image.
- Item name and category.
- Description.
- Location and date.
- Report status.
- A link to view details.
- A way to contact the reporter where appropriate.

Do not silently replace a failed visual search with fake results.

---

# Part 8 — New Feature: Lost Item Search

## Issue 13: Users need to search found-item reports without reporting their own lost item

### Purpose
A person may not realize that an item is missing until days later. Someone else may already have found and reported it. The owner should be able to search the community and contact the finder without creating a lost-item report first.

### Dashboard integration
- Add a new sidebar entry named **Lost Item Search** immediately below **Visual Search**.
- Give it its own React page and route.
- Preserve the existing Visual Search feature and all other sidebar options.
- Follow the existing CampusConnect UI design and responsive behavior.

### Search interface
Include:
- Page title: **Find Your Lost Item**
- A short explanation that users can search items reported as found.
- Keyword/item-name search.
- Start-date and end-date calendar fields.
- Optional category filter.
- Optional campus-location filter.
- Search and Clear Filters actions.

### Search rules
- Return **found-item reports only**.
- Exclude lost reports.
- Exclude recovered reports.
- Use the actual status values from the existing database/model.
- Search item names and descriptions case-insensitively where supported.
- Apply date, category, and location filters correctly.
- Validate date ranges.
- Perform authoritative filtering on the Django backend and validate results on the frontend as appropriate.
- Users must not have to submit a lost-item report to search.
- Search results must come from MySQL, not mock data.

### Results cards
Each result should display:
- Item image or a neutral placeholder if no image exists.
- Item name.
- Category.
- Description.
- Location where it was found.
- Date reported.
- Found-status badge.
- **View Details** button.
- **Contact Reporter** button.

### Details and messaging
- View Details should show the full public details available for the found report.
- Contact Reporter should open or create the appropriate private conversation.
- The conversation should be associated with the relevant report where the data model supports this.
- The reporter identity must come from the stored report, not be trusted from arbitrary frontend input.
- Apply the same authorization and privacy rules as the Messages feature.

### Suggested endpoint
Adapt this to the project's existing URL conventions rather than creating a duplicate endpoint if one already exists.

`GET /api/items/search-found/`

Possible query parameters:
- `q`
- `start_date`
- `end_date`
- `category`
- `location`

Example:
`/api/items/search-found/?q=headphones&start_date=2026-10-10&end_date=2026-10-20`

Use standard Django views and Django ORM. Do not use Django REST Framework.

### Search states
Implement:
- Loading state.
- Results state.
- No-results state.
- Invalid-date state.
- Authentication state consistent with the existing product.
- Backend/network error state.

Do not display fake results when the endpoint fails.

---

# Part 9 — Database, Migrations, and Data Integrity

## Issue 14: Reports, messages, matches, and notifications must use consistent MySQL data

### Required checks
- Inspect the existing MySQL database settings and current models before modifying the schema.
- Reuse existing report, user, conversation, message, match, and notification tables when possible.
- Ensure foreign keys and relationships correctly connect reports to their reporters and conversations to participants.
- Ensure report status and dates are represented consistently.
- Add migrations only when schema changes are necessary.
- Do not create a second database for these features.
- Do not delete or overwrite existing user data.
- Do not put database passwords or secret keys in source code.
- Provide exact migration commands and explain any required environment configuration.
- Handle invalid, missing, or deleted related records gracefully.

If the repository uses a database named `campus.connect`, inspect the actual configured database name and preserve the working configuration rather than assuming a different name. If the configured name is invalid for the local MySQL setup, explain the required correction rather than silently changing it.

---

# Part 10 — Frontend, API, Error Handling, and Accessibility

## Issue 15: Buttons, routes, and page states are inconsistent

### Required fixes
- Audit all relevant buttons, sidebar links, and navigation actions.
- Ensure each action has a working handler and correct route.
- Use the project's existing Axios client and base URL.
- Avoid duplicate requests and handle loading state correctly.
- Display useful error messages without exposing sensitive server details.
- Ensure forms prevent accidental duplicate submissions.
- Provide accessible labels for search/date fields and buttons.
- Ensure new pages work on desktop and smaller screens.
- Keep empty states, loading indicators, and error states visually consistent with the existing design.

---

# Part 11 — Suggested Implementation Order

Work through these stages in order so that features are built on a reliable foundation.

## Stage 1: Inspect and diagnose
- Map the project structure and existing architecture.
- Identify the current report, authentication, message, match, and notification models/endpoints.
- Trace why the API is considered offline.
- Record the files that need changes.
- Do not start by rewriting the entire project.

## Stage 2: Fix API connectivity and authentication
- Fix Axios configuration, Django routes, authentication, cookies/headers, CSRF/CORS where applicable, and error handling.
- Verify authenticated requests using two separate accounts.

## Stage 3: Fix community reports
- Fix live report retrieval.
- Fix Discover and Browse Recent Reports.
- Ensure reports are shared appropriately between accounts.
- Remove normal-flow mock-data fallbacks.

## Stage 4: Fix messaging
- Fix conversation retrieval and message sending.
- Fix Contact Reporter navigation and conversation selection.
- Enforce participant-only access.

## Stage 5: Implement Alerts
- Add or repair persistent notification storage.
- Create notifications for the specified events.
- Implement unread/read behavior and notification navigation.

## Stage 6: Fix Matches and dashboard counter
- Implement real matching logic using actual report data.
- Display potential matches and allow contact.
- Make the counter accurate.

## Stage 7: Fix Visual Search
- Trace image upload and existing report-image storage.
- Implement genuine image similarity and meaningful result ranking.
- Apply the supported filters.

## Stage 8: Add Lost Item Search
- Add sidebar entry, route, page, date filters, search endpoint, found-only results, details, and Contact Reporter integration.

## Stage 9: Date pickers and final UI checks
- Replace manual date entry in the relevant fields.
- Verify all buttons, routes, empty states, and responsive behavior.

## Stage 10: End-to-end testing
- Run the frontend and backend.
- Test the required scenarios below.
- Fix regressions before reporting completion.

---

# Part 12 — Required End-to-End Tests

Test with at least two separate user accounts and real records in MySQL.

### Test A: Authentication
1. Sign in as User A.
2. Open Messages, Alerts, and Matches.
3. Confirm that authenticated pages do not incorrectly request sign-in.
4. Refresh the page and navigate between sections.
5. Sign out and sign in as User B.
6. Confirm that private data from User A is not shown to User B.

### Test B: Shared reports
1. User A submits a lost-item report.
2. User B opens Discover.
3. Confirm that User B can see the public community report.
4. Confirm that User B cannot see User A's private account data.

### Test C: Browse Recent Reports
1. Click Browse Recent Reports.
2. Confirm navigation works.
3. Confirm actual database reports are displayed.

### Test D: Date picker
1. Open a relevant report form.
2. Select a date using the calendar.
3. Submit the report.
4. Confirm the date is stored and displayed correctly.

### Test E: Messaging
1. User A submits a report.
2. User B selects Contact Reporter.
3. Confirm the correct conversation opens.
4. Send a message from User B.
5. Sign in as User A and confirm the message is received.
6. Confirm unrelated users cannot access the conversation.

### Test F: Notifications
1. Create a new report and verify the applicable notification behavior.
2. Send a private message and verify the recipient notification.
3. Create or identify a potential match and verify relevant notifications.
4. Mark a notification as read.
5. Refresh the page and verify that the read/unread state persists.
6. Confirm notifications belong to the correct recipient.

### Test G: Matches
1. Create a lost-item report for a test item.
2. Create a corresponding found-item report.
3. Confirm a potential match appears when the reports satisfy the matching rules.
4. Confirm recovered items are excluded from active matches.
5. Confirm Contact Reporter opens the correct conversation.
6. Confirm the dashboard counter agrees with the displayed match data.

### Test H: Visual Search
1. Upload an image of a test item.
2. Search against real report images.
3. Confirm that visually similar eligible reports can be returned by the implemented image-similarity method.
4. Test category, location, and date filters.
5. Test invalid files and API failure.
6. Confirm the app never pretends a keyword-only filter is visual recognition.

### Test I: Lost Item Search
1. User B creates a found-item report for headphones.
2. User A does not create a lost-item report.
3. User A opens Lost Item Search and searches for headphones.
4. Confirm the found-item report appears.
5. Confirm lost and recovered reports do not appear.
6. Apply a date range using the calendar.
7. Open the report details.
8. Click Contact Reporter and send a message.
9. Confirm the conversation works for both users.

### Test J: API outage
1. Stop or make the backend temporarily unavailable in a controlled development test.
2. Confirm the UI displays a clear error state.
3. Confirm mock/example reports, matches, messages, and notifications are not presented as live data.
4. Restore the backend and confirm the app recovers.

---

# Final deliverables required from GitHub Copilot

After implementation:

1. List every file created or modified and briefly explain its purpose.
2. Explain the root cause of each original bug that was confirmed.
3. List any database migrations and the commands required to run them.
4. Provide exact commands to start the Django backend and React/Vite frontend.
5. Identify any environment variables, image-processing packages, or other dependencies that must be configured.
6. Summarize which end-to-end tests passed and which remain incomplete.
7. Clearly disclose any feature that could not be fully implemented or verified.
8. Do not claim that the application works end to end unless it has actually been tested.

**Start by inspecting the existing project. Implement changes incrementally, preserve working features, and verify each stage before proceeding to the next.**
