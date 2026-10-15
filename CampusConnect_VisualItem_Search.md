# CampusConnect — Visual Item Search Feature

## Project Context

CampusConnect is a college Lost & Found management system.

I want to **replace the existing Claims feature** with a new feature called **Visual Item Search**.

## Technology Stack

- **Frontend:** React.js with Vite
- **Backend:** Python Django
- **Database:** MySQL
- **Frontend–backend communication:** Axios and Django HTTP endpoints
- **Routing:** React Router DOM

## Important Instructions

My React + Vite frontend already exists. Do not create a new frontend project or replace my existing application.

First, inspect my existing project structure, frontend components, routing, Django backend configuration, and MySQL database setup. Reuse my existing code wherever possible.

Do not modify unrelated features such as Discover, My Reports, Matches, Messages, and Alerts.

---

## 1. Replace the Claims Navigation

Remove the existing **Claims** navigation item and replace it with **Visual Search**.

Requirements:
- Keep the existing CampusConnect branding and layout.
- Maintain the current navigation bar design.
- Use a suitable search or image icon.
- Ensure the new navigation item opens the Visual Item Search page.
- Remove the old Claims page from active navigation and routing if it is no longer needed.
- Do not delete existing database tables or claims data without checking whether other features depend on them.

## 2. Visual Item Search Page

Create a modern, responsive Visual Item Search page that lets students search for lost belongings using photographs.

The page should contain:

### A. Page heading
**Find Your Lost Item**

Description:
> Upload a photo of your lost item to discover visually similar items reported on campus.

### B. Image upload section
- Allow users to upload an image from their device.
- Support JPG, JPEG, PNG, and WEBP formats.
- Display an image preview before searching.
- Allow users to remove or replace the selected image.
- Set reasonable file-size and image-dimension limits.
- Validate file type and size on both frontend and backend.
- Display clear error messages for invalid files.

### C. Search button
- Add a button labelled **Find Similar Items**.
- Display a loading indicator while searching.
- Prevent duplicate submissions while a search is in progress.
- Show a helpful message if no similar items are found.

### D. Search filters
- Item category
- Campus location
- Date reported

### E. Search results
Display matching found-item reports as cards. Each card should show:
- Item photograph
- Item name
- Category
- General location where it was found
- Date reported
- Visual similarity percentage
- Current status, if available

Add a **View Details** button to each result card.

Allow students to view the full item report and use the existing contact, matching, or recovery workflow where appropriate.

Do not expose private information such as a reporter's phone number, email address, or student ID in public search results.

## 3. Visual Similarity Search

Implement actual image-based similarity matching. Do not simply compare filenames or return random results.

Inspect the existing project and choose an appropriate approach.

Preferred approach:
- Use Python with a pretrained computer-vision image-embedding model, such as CLIP, to convert images into numerical vectors.
- Compare the uploaded image embedding against embeddings generated from existing found-item photographs.
- Use cosine similarity to rank the most visually similar items.
- Return the top relevant results.
- Make the similarity calculation reusable and separate from Django views.

If a pretrained model is impractical for the current project, implement a modular baseline using image features and explain its limitations. Keep the design extensible so a stronger embedding-based solution can be added later.

Do not claim to provide AI-powered image similarity unless the backend actually implements image comparison.

Similarity scores must be described as **approximate visual similarity**, not as a guarantee that two images show the same item.

Only search records eligible to appear in existing found-item listings. Do not expose private, deleted, or restricted records.

## 4. Django Backend

Use Django to implement the backend APIs.

First inspect the existing Django project and reuse existing models and APIs where appropriate.

Create or update the necessary components, such as:
- Django models, if additional fields are required
- Serializers only if the project already uses Django REST Framework
- Views or API endpoints
- URL routing
- Image validation
- Image processing and similarity calculation
- Error handling

**Important:** Do not introduce Django REST Framework if it is not already installed, unless it is explicitly required by the existing architecture.

If Django REST Framework is not installed, use Django views that accept `multipart/form-data` and return JSON responses.

Implement an endpoint similar to:

`POST /api/visual-search/`

The endpoint should:
1. Accept an uploaded image.
2. Validate the image.
3. Apply the selected search filters.
4. Compare the image against eligible found-item images.
5. Calculate visual similarity scores.
6. Rank results from highest to lowest similarity.
7. Return relevant matching items as JSON.

Use appropriate HTTP status codes and meaningful error messages.

Do not place all image-processing or database logic inside the Django view. Keep the implementation modular and maintainable.

## 5. MySQL Database

Use the existing MySQL database configuration. Do not create a separate database unless necessary.

Inspect the existing models and database schema first. Reuse existing lost-item and found-item records wherever possible.

Store the necessary image information and item metadata in MySQL through Django models.

Store uploaded image files using Django's configured media storage rather than storing raw image files directly in MySQL.

If image embeddings need to be stored, choose an appropriate representation and explain the trade-offs. Do not assume MySQL supports a specialized vector index without verifying compatibility.

Use Django migrations for required schema changes. Do not delete or overwrite existing item records.

## 6. Connect React Frontend to Django

Use Axios to send the selected image to Django.

Requirements:
- Send the image using `FormData`.
- Include relevant search filters.
- Handle loading, success, empty-result, and error states.
- Render the results returned by Django.
- Handle expired authentication or unauthenticated requests according to the existing authentication system.
- Use the existing API base URL configuration if available.
- Configure Django CORS settings appropriately for the local React development server.
- Do not hardcode secrets or database passwords in frontend code.

Use React Router DOM to connect the new page to the navigation.

Follow the existing folder structure, component conventions, styling approach, and API service patterns.

Do not introduce an entirely new UI framework unless necessary.

## 7. User Interface Design

Match the existing CampusConnect design.

The current application uses a clean, minimal interface with:
- A light background
- Simple typography
- Spacious layouts
- Minimal decorative elements
- A clean navigation bar

Maintain this visual style. Do not redesign the entire application.

The Visual Search page should include:
- A clear page heading
- A drag-and-drop image upload area
- An image preview
- Search filters
- A prominent search button
- A responsive grid of result cards
- Loading and empty states
- Error messages
- Mobile-friendly layouts

Ensure the page is accessible, with appropriate labels, keyboard navigation, and image alt text.

## 8. Security and Validation

Implement:
- Server-side image validation
- File-size restrictions
- Safe image decoding and processing
- Appropriate authentication and authorization checks
- Protection against unauthorized access to private reports
- Safe handling of uploaded files
- Appropriate error handling
- No exposure of sensitive student information

Do not trust frontend validation alone.

## 9. Testing

Test the feature to verify that:
1. A student can upload a valid image.
2. An image preview appears before searching.
3. The frontend sends the image to Django.
4. Django processes the uploaded image successfully.
5. Django retrieves eligible found-item records from MySQL.
6. The system ranks items using actual visual similarity.
7. Search results appear in descending similarity order.
8. Filters work correctly.
9. Invalid files are rejected.
10. Empty search results are handled properly.
11. Network and backend errors are displayed clearly.
12. Existing CampusConnect features continue working.
13. The application works on desktop and mobile screens.

Add appropriate automated tests for the Django API and image-similarity logic where practical.

## 10. Implementation Instructions

Work with my existing codebase rather than generating an unconnected example.

Follow this sequence:

### Step 1
Inspect my project structure and identify the existing Claims component, navigation configuration, routes, Django backend, database models, and API configuration.

### Step 2
Briefly explain which existing files need to be modified and which new files need to be created.

### Step 3
Implement the React Visual Item Search interface.

### Step 4
Implement the Django image-search endpoint and similarity logic.

### Step 5
Integrate the feature with the existing MySQL database.

### Step 6
Connect React to Django using Axios.

### Step 7
Replace Claims with Visual Search in the navigation.

### Step 8
Run available tests and resolve errors caused by the changes.

### Step 9
Provide exact commands to install any required dependencies and run the frontend and backend.

### Step 10
Explain how to configure image uploads and test the feature locally.

Before installing packages, inspect existing dependencies. Avoid unnecessary dependencies and do not overwrite existing configuration files.

If any required information is missing, identify it before making assumptions.

Do not merely provide sample code or instructions. Implement the feature in the existing project files wherever the environment permits.

## Final Summary Required

At the end, summarize:
- Files created
- Files modified
- Database changes
- Dependencies added
- API endpoints created
- Commands to run the application
- Any remaining limitations

The final result should be a working Visual Item Search feature integrated into the existing CampusConnect application.
