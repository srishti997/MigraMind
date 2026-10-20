# Frontend rendering investigation

A fresh Chrome session at http://127.0.0.1:5173/ rendered sign-in and, using a temporary synthetic account, Overview, Migraine diary, Calendar, Insights and Attack Mode without JavaScript errors. The Vite entry and insights modules and the proxied backend health endpoint returned HTTP 200. No insights import or routing exception was reproduced.

A separate reproducible startup defect was identified: browsers can expose BroadcastChannel while rejecting its constructor with SecurityError. Authentication installed a cross-tab observer without catching this exception, which unmounted the React tree. The observer and publisher now catch channel failures and fall back to storage events. Channel cleanup also cannot interrupt unmounting. No account identity or health information is included in these signals.

The unit regression fails against the original implementation and passes with the fix. The real-API browser regression restores an authenticated session with BroadcastChannel deliberately blocked, checks all five main screens, emergency access, mobile overflow and uncaught page errors. Synthetic test accounts are removed afterward.

The original user's browser state was not accessible, so this defect cannot conclusively be attributed as the cause of that specific reported tab. If it persists after reloading, capture the first console error and failed module request in that browser (without sharing tokens or health records). Do not delete the local database or clear account data as a troubleshooting step.

If both channel messaging and browser storage are blocked, immediate cross-tab notification is unavailable. Server-side session validation and session expiry handling remain enforced. Browser extensions and real-device call/SMS behavior require manual verification.

## Verification commands

- Frontend: `npm test` and `npm run build` in `frontend`.
- Backend: `.venv\Scripts\python -m pytest -q -p no:cacheprovider --basetemp .research/pytest-<unique-run-id>` in `backend`. Use a new path for each run: pytest manages its own temporary directory. This avoids an inaccessible shared Windows pytest temp directory without deleting local data.
- Browser: `npm run test:e2e` in `frontend`, with both local servers running. Avoid repeated real-account runs within the authentication rate-limit window. The application security settings are unchanged.
