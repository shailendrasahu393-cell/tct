# Backend integration TODO

The frontend now uses the FastAPI backend for authentication, labs, and links.

1. Connect authentication endpoints using HttpOnly, Secure, SameSite cookie sessions.
2. Expand the database-backed lab and link endpoints as the data model evolves.
3. Enforce authentication, roles, ownership checks, input validation, password hashing, rate limiting, and audit logging on the server.
4. Derive the active lab from the authenticated session; never trust client-supplied lab IDs for write operations.
5. Implement server-side password reset and create-admin flows. Never return password hashes or secrets to this UI.
