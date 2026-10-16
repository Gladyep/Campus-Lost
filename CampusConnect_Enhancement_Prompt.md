# CampusConnect – Smart Lost & Found Platform
## Enhancement Prompt: Recovered Items and Contact Reporter

I have an existing **CampusConnect – Smart Lost & Found Platform** project built using **React for the frontend, Django and Django REST Framework for the backend, and MySQL for the database**.

I want to enhance my existing application by adding two major features: **Recovered Items** and **Contact Reporter**.

## Important Instructions
- First, analyze my existing project structure, code, database models, APIs, and UI.
- Do not rebuild the application from scratch.
- Do not delete or break any existing features.
- Preserve my existing design, layout, colors, components, naming conventions, and folder structure.
- Keep the current Everything, Lost, and Found filters.
- Integrate all new features with the existing Django backend and MySQL database.
- Implement actual working functionality, not just UI buttons or dummy data.
- Make necessary database changes through safe Django migrations without deleting existing data.
- Avoid unnecessary dependencies and code duplication.

## Feature 1: Recovered Items

Add a new **Recovered** filter alongside the existing Everything, Lost, and Found filters.

Requirements:
1. Add a suitable status field or extend the existing status model to support recovered items.
2. Add a “Mark as Recovered” action to eligible lost or found reports.
3. Allow only the report owner or an appropriately authorized user to update the recovery status.
4. Confirm the action before changing the status.
5. Update the status in the MySQL database through the Django REST API.
6. Display a green “Recovered” badge on recovered item cards.
7. Make the Recovered filter display only recovered reports.
8. Ensure recovered reports no longer appear as active lost/found reports where appropriate, but remain accessible in the Everything filter.
9. Show the recovery status consistently on the Discover page, My Reports page, and report details page.
10. Prevent unauthorized users from marking unrelated items as recovered.
11. Ensure the status remains correct after refreshing the page or signing out and signing back in.

## Feature 2: Contact Reporter

Add a working **Contact** button to each eligible lost or found item card and its details page.

Requirements:
1. Clicking Contact should open a clean contact interface.
2. Display the reporter's name and available, authorized contact information.
3. Prefer secure in-app messaging between signed-in users.
4. If the project does not already support messaging, inspect the existing Messages module and integrate with it instead of creating a duplicate messaging system.
5. If messaging is not currently implemented, create the necessary Django models, APIs, and React UI.
6. Store messages in MySQL and associate them with the sender, recipient, and relevant report.
7. Display conversation history and message timestamps.
8. Validate and sanitize user input on the backend.
9. Enforce authentication and permissions for conversations and messages.
10. Do not expose private phone numbers or email addresses publicly.
11. Show helpful loading, success, empty, and error states.
12. Ensure messages persist after refreshing the page.

## Feature 3: Backend and Database Integration

- Inspect the existing Django models, serializers, views, URLs, permissions, and authentication system before making changes.
- Reuse the existing report and user models wherever possible.
- Update the REST API to support the new recovered status, recovered-report filtering, and messaging.
- Apply appropriate authentication and authorization checks.
- Create safe Django migrations for schema changes.
- Preserve all existing user accounts and reports.
- Verify that API responses match the structure expected by the React frontend.
- Configure CORS correctly for the existing frontend development URL.
- Do not hardcode local machine paths, credentials, or personal information.

## Feature 4: Frontend UI

Maintain the current CampusConnect design and add:
- Everything
- Lost
- Found
- Recovered
- Contact button on report cards
- Recovered status badge
- Contact/message interface
- Appropriate success and error notifications
- Loading indicators and empty states

Make the new elements responsive and consistent with the existing design. Do not redesign the entire application.

## Feature 5: Testing and Verification

After implementation:
1. Verify that existing registration and login still work.
2. Verify that existing lost and found reports still load.
3. Test creating a report and marking it as recovered.
4. Verify that the Recovered filter returns the correct reports.
5. Test sending and receiving messages using two different user accounts.
6. Verify that users cannot modify unauthorized reports or access other users' private conversations.
7. Verify that all changes persist in MySQL.
8. Check browser console errors, failed API requests, and Django terminal errors.
9. Ensure that the application works on another computer after cloning the GitHub repository and following the setup instructions.

## Final Deliverables

After completing the work:
- List all files created or modified.
- Explain the database changes.
- Provide the exact commands to install dependencies, apply migrations, and run the backend and frontend.
- Explain how to test the new features step by step.
- Document any environment variables or setup requirements.
- Clearly identify anything that could not be implemented or verified.

**Start by inspecting the existing code. Make minimal, compatible changes and preserve all existing working functionality.**
