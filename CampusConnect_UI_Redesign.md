# GitHub Copilot Prompt — Redesign CampusConnect Interface

## Goal
Redesign the existing **CampusConnect Lost & Found** interface to match the visual style and layout of the supplied student-dashboard reference image, while **preserving all existing CampusConnect features and functionality**.

The reference image is inspiration for the visual design only. Do not turn CampusConnect into a course-management dashboard. Keep it as a campus lost-and-found application.

## Existing technology stack
- **Frontend:** React + Vite
- **Backend:** Django
- **Database:** MySQL
- Axios and React Router DOM are already installed in the frontend.

Do not replace this stack or introduce a new frontend framework. Reuse the existing project structure, routes, API calls, authentication logic, and components wherever possible.

## Visual direction
Create a polished, modern, spacious dashboard inspired by the reference:
- Warm ivory/cream page background.
- White or very light neutral content surfaces.
- Deep burgundy as the main brand/accent color, consistent with the existing CampusConnect identity.
- Soft pastel accent cards, such as pale mint, blush, and light lavender, used sparingly.
- Dark charcoal panels for important summary information.
- Rounded cards, subtle borders, gentle shadows, generous whitespace, and clear visual hierarchy.
- Clean typography, simple line icons, and restrained hover/focus transitions.
- A narrow left sidebar on desktop, with a compact logo at the top and clearly labeled navigation items.
- Main content area with a personalized greeting and organized dashboard sections.
- Responsive layout for desktop, tablet, and mobile.
- Avoid oversized hero banners that push the actual reports far down the page.

Do not copy the reference institution's logo, name, text, course cards, or branding. Use CampusConnect branding and lost-and-found content only.

## Personalized greeting
At the top of the main content, display a friendly greeting using the signed-in user's actual name, for example:

**Hey, {firstName}! 👋**

Under it, show a short contextual line such as:
“Let’s help your campus community reunite with what matters.”

Implementation requirements:
1. Read the name from the project's existing authenticated-user/profile state or existing API response.
2. Use the real signed-in user's name; do not hard-code a sample name.
3. If only a full name is available, derive a safe first-name display from it.
4. If the user is not signed in or the name is unavailable, show a neutral fallback such as **“Welcome to CampusConnect”** rather than displaying `undefined`, `null`, or a blank greeting.
5. Do not change authentication, registration, or session behavior just to support the greeting.

## Preserve these existing CampusConnect features
Keep all existing features and their routes/actions working. Retain the current feature set, including:

- **Discover / Recently Reported:** Browse lost and found items.
- **Search:** Search by item name, place, or details.
- **Filters:** Lost/Found tabs and category filtering.
- **Report an Item:** Create a lost/found item report.
- **My Reports:** View the signed-in user's reports.
- **Matches:** View potential matches between lost and found reports.
- **Claims:** Keep the existing claim feature and its current behavior.
- **Messages:** Keep existing conversations and messaging functionality.
- **Alerts:** Keep notifications/alerts and their existing behavior.
- **Sign in / Profile:** Preserve current authentication and profile navigation.
- **Existing report cards:** Keep item images, titles, categories, status, date, location, and descriptions wherever currently supported.

Do not remove, rename, or silently disable any existing feature. Do not replace real functionality with static mock data.

## Suggested dashboard structure

### 1. Desktop layout
Use a left sidebar and a main content area.

**Sidebar navigation**
- CampusConnect logo/wordmark
- Dashboard or Discover
- My Reports
- Matches
- Claims
- Messages
- Alerts
- Profile / Sign in

Use the existing routes and labels where possible. Highlight the current page clearly. If a route is not present, inspect the project and use the correct existing route rather than inventing a broken one.

At the bottom of the sidebar, optionally show a small community message such as:
“Helping our campus find its way back.”

### 2. Main dashboard header
At the top:
- Greeting: **“Hey, {firstName}! 👋”**
- Supporting text: “Here’s what’s happening in your campus community.”
- A prominent **Report an Item** button that opens the existing report form.
- A profile/avatar area if the project already supports user profiles.

### 3. Summary cards
Create compact, visually distinct summary cards using existing backend data where available:
- **My Reports** — number of reports submitted by the signed-in user.
- **Potential Matches** — count of relevant matches, if this data is available.
- **Unread Messages** — unread count, if available.
- **Items Reunited** — use only if the backend currently tracks successful recoveries.

Data rules:
- Fetch real data from the existing Django APIs when supported.
- Reuse existing API services and Axios configuration.
- Do not invent endpoint URLs or database fields without checking the current code.
- If a metric is not supported by the backend, omit that card or show a neutral empty state. Do not fabricate counts.

### 4. Quick actions
Create compact action cards or buttons for:
- Report a Lost Item
- Report a Found Item
- Browse Recently Reported Items
- Open Visual Item Search only if this feature already exists in the project or is being implemented separately.

Quick actions must navigate to existing pages/forms or open existing flows. Do not create nonfunctional buttons.

### 5. Recently reported items
Keep the familiar image-card grid from the current CampusConnect page, but style it to fit the new dashboard:
- Item image at the top.
- Lost/Found badge.
- Category.
- Item title.
- Location and report date when available.
- Short description if available.
- Clear action to view details.

Use consistent card heights, sensible image cropping, and a responsive grid. Keep the existing search input and category/status filters accessible on the Discover page. If useful, show a small “Recently reported” preview on the dashboard with a link to view all items.

### 6. Other pages
Apply the same design system to existing pages such as My Reports, Matches, Claims, Messages, and Alerts where practical:
- Consistent sidebar/navigation.
- Consistent background, typography, spacing, buttons, and cards.
- Clear page titles and useful empty states.
- Preserve each page's current functionality and data flow.
- Do not force every page into the same dashboard layout if it harms usability.

## Responsive behavior
- **Desktop:** Fixed or sticky left sidebar and spacious main content.
- **Tablet:** Narrow/collapsible sidebar.
- **Mobile:** Replace the sidebar with a compact menu or bottom navigation; keep the greeting, report button, search, filters, and item cards easy to use.
- Avoid horizontal overflow.
- Make buttons and touch targets comfortable on mobile.

## Accessibility and interaction
- Use semantic headings and buttons.
- Ensure sufficient text/background contrast.
- Provide visible keyboard-focus states.
- Add useful alt text to item images.
- Respect reduced-motion preferences.
- Use subtle transitions only; do not add distracting animations.
- Ensure forms and filters remain usable with a keyboard.

## Implementation instructions for GitHub Copilot
Before editing:
1. Inspect the existing React/Vite source structure and identify the current homepage, navigation, item-card components, authentication/user state, API services, and route definitions.
2. Identify how Django endpoints are currently called and how the signed-in user's name is obtained.
3. Reuse the existing code and styling conventions wherever possible.
4. Make a short plan of the files/components that need to change.

Then implement the redesign:
1. Build or refactor the shared layout/sidebar and dashboard header.
2. Add the personalized greeting using the real authenticated user's name and a safe fallback.
3. Restyle the summary cards and recently reported item cards.
4. Preserve all current navigation links, API integrations, forms, filters, and actions.
5. Apply responsive styles.
6. Check for broken imports, route errors, console errors, and CSS conflicts.
7. Run the existing frontend build/lint scripts if available and fix issues introduced by the changes.

## Strict constraints
- Do not rewrite the whole application unnecessarily.
- Do not change Django models, database schema, or API contracts unless absolutely required; ask before making backend/schema changes.
- Do not remove existing features, including Claims, Messages, Alerts, Matches, My Reports, Search, and Report an Item.
- Do not replace real backend data with mock data.
- Do not hard-code a user's name, counts, reports, or matches.
- Do not expose private user information.
- Do not copy the reference dashboard's institution branding or course-management content.
- Do not add a new UI library unless the project already uses it or there is a clear need.
- Keep the implementation compatible with the current React + Vite project.

## Acceptance checklist
- [ ] The interface has the reference's spacious, modern dashboard feel.
- [ ] CampusConnect's burgundy/cream identity is retained.
- [ ] A signed-in user sees “Hey, {firstName}! 👋” with their actual first name.
- [ ] Signed-out/unknown users see a safe fallback greeting.
- [ ] Existing features and routes still work.
- [ ] Search, status/category filters, and report submission still work.
- [ ] Item cards use real report data and remain responsive.
- [ ] No fake statistics or hard-coded user information are shown.
- [ ] Desktop, tablet, and mobile layouts work without horizontal overflow.
- [ ] No new console/build errors are introduced.
