# TODO v1.3

- [ ] **Backend hardening**
  - [ ] Verify SPA fallback and static serving strategy works in all environments
  - [ ] Add logging around mock mode and rate limiter events
  - [ ] Ensure JWT secret enforcement handles restart gracefully

- [ ] **UI features**
  - [ ] Make login screen prettier and add loading states
  - [ ] Add user menu with logout and profile link
  - [ ] Build `/users` and `/settings` placeholder pages

- [ ] **Chat improvements**
  - [ ] Display session history and allow clearing
  - [ ] Show loading spinner while waiting for responses
  - [ ] Handle error messages from backend gracefully

- [ ] **Security**
  - [ ] Add CSRF protections for state-changing requests
  - [ ] Rate-limit other sensitive endpoints (memory, logs)
  - [ ] Audit CORS origins and tighten for production

- [ ] **DevOps / deployment**
  - [ ] Dockerize backend with proper env configuration
  - [ ] Automate frontend build and static copy step
  - [ ] Add healthcheck endpoints for readiness/liveness
