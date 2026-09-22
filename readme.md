# FindBack - AI-Powered Lost & Found

FindBack is a responsive frontend for reporting lost and found items, browsing reports, reviewing AI-suggested matches, and managing ownership claims. AI results are presented as suggestions only; ownership must always be verified by people.

## Tech stack

- HTML5
- Tailwind CSS v4
- Vanilla JavaScript modules
- Font Awesome and Inter (loaded from CDNs)

This project does not use React, Bootstrap, or LocalStorage.

## Project structure

```text
frontend/
+-- index.html                 # Landing page
+-- pages/                     # Auth, dashboard, report, search, match, claim, and profile screens
+-- js/                        # Small browser modules and API/session adapters
+-- src/input.css              # Tailwind source stylesheet
`-- css/output.css             # Generated Tailwind stylesheet
```

## Frontend pages

| Page | Path |
| --- | --- |
| Landing page | `frontend/index.html` |
| Login / register | `frontend/pages/login.html`, `register.html` |
| Dashboard | `frontend/pages/dashboard.html` |
| Lost / found reports | `frontend/pages/report-lost.html`, `report-found.html` |
| Search and matches | `frontend/pages/search.html`, `matches.html` |
| Item details / claims / profile | `item-details.html`, `claims.html`, `profile.html` |

## Run locally

Install dependencies from the frontend directory:

```bash
cd frontend
npm install
```

Rebuild Tailwind after editing HTML or `src/input.css`:

```bash
npx @tailwindcss/cli -i ./src/input.css -o ./css/output.css
```

Serve `frontend/` through any static web server, then open `index.html`. For example, a VS Code Live Server extension or another local static server is suitable.

## Backend integration

The frontend intentionally does not assume API routes or a specific authentication implementation.

When the backend contract is ready, configure these files:

1. In `frontend/js/api.js`, set `API_BASE_URL` and update `API_REQUEST_OPTIONS` if the backend does not use cookie-based sessions.
2. In `frontend/js/auth.js`, set the `AUTH_ENDPOINTS` values for login, registration, logout, the current session user, and profile updates.
3. Align `getCurrentUser()` with the backend session response if it is not a user object or `{ user: ... }` envelope.
4. Connect the remaining TODOs in the item, search, match, claim, and dashboard modules to the agreed API contract.

The dashboard and profile load identity from `getCurrentUser()` on page load. Their name, avatar, contact fields, greeting, and counts are not stored in the browser and do not use a default user.

### Expected current-user fields

The existing adapter accepts `firstName`/`first_name`, `lastName`/`last_name`, `name`, `email`, `phone`/`phoneNumber`, and `avatarUrl`. Statistics may be nested in `statistics` or `stats`, or be present directly on the user object. The adapter recognizes:

- `lostReports`, `lost_reports`, or `lostItems`
- `foundReports`, `found_reports`, or `foundItems`
- `potentialMatches`, `potential_matches`, or `matches`
- `activeClaims`, `active_claims`, or `claims`

Adapt these mappings once the backend response schema is final.

## Notes

- Placeholder reports and images are solely for visual frontend development.
- Image-report forms are ready to be sent with `FormData` once upload endpoints are available.
- The generated stylesheet (`frontend/css/output.css`) is committed so the pages render without a build step.
