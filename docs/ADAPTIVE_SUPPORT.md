# Adaptive support assistance: baseline v1

MigraMind remains a single-user local prototype. This sprint adds support personalization, not a chatbot, medical triage, migraine prediction or clinically validated AI. No call, message or support-card transmission is automatic. Emergency access is independent of recommendations.

## Try it locally

Refresh http://127.0.0.1:5173/.

1. In **Trusted contacts**, save the people you want to reach. Demo numbers must be replaced before actual use.
2. In **Caregiver profile**, continue editing and saving what helps, what to avoid and communication notes. Under **Your support choices**, select a preferred contact/method, optional ordered action priorities, accessibility settings and an ordering policy. Feedback-based ordering is off unless you explicitly opt in. **Reset action and accessibility choices** resets only these structured choices, keeping caregiver notes and feedback.
3. Open **Attack Mode**. The chosen contact is selected and the first support option is prominent; all available call/SMS/card options remain accessible. **Why this order?** explains the decision. Missing contacts show setup while the support card remains usable. Saved choices and stable defaults provide a fallback if ranking is unavailable. Ranking stays stable during a visit and is refreshed when Attack Mode is opened again.
4. Exit and India 112 calling stay at the top in a sticky header, including when reading a long card. Simplified view collapses longer emergency guidance without hiding emergency calling. Large text and reduced motion are explicit preferences; device reduced-motion settings are always respected.
5. Open **My support card → Review card for sharing**. The preview uses saved notes and the saved communication method. It does not append structured contact lists, diary entries or feedback. Free-text caregiver notes may themselves contain private details; review them before sharing. Review/redact the editable preview, then explicitly choose **Copy card text** or **Open device share…**, if supported. Review alone does not copy or share. Nothing claims delivery. The browser/OS controls the final share destination. If saved choices cannot be loaded, sharing is disabled rather than inventing a preference.
6. Explicitly start/end a session. Only after ending it, an optional feedback invitation appears; **Skip feedback** records no rating. **Review support feedback** opens the ordinary page outside Attack Mode. Choose the ended session, action and Yes/No if you want to rate it. You may also visit **Support feedback** later. The form is hidden during any active session or when session status cannot be verified. Review/delete controls remain available for existing ratings.

Entering/leaving Attack Mode still does not start/end a session. Clicking a call/SMS link is not proof of completion or delivery. The optional prompt may remember the last action clicked in the current view, but the user explicitly chooses and submits the rating. No link-attempt telemetry is persisted.

## Explainable policy

Version `explicit-feedback-v1` operates on exactly three nonemergency actions: `call_contact`, `prepare_sms`, `support_card`.

1. Available actions come first. Calls/SMS need at least one saved contact; a card does not. Unavailable actions are retained in the API response with a setup explanation.
2. User-ordered action priorities are pinned in their saved order. A selected communication method is also pinned after those priorities. These choices always outrank feedback. If every action is pinned, feedback cannot reorder them.
3. For unpinned actions, feedback ordering is enabled only when the user opts in and chooses adaptive mode. With at least 3 ratings for an action, use `(helpful + 1) / (ratings + 2)`. Below 3, use a neutral internal score of 0.5. This smoothing score is **not** a clinical probability, confidence score or learned-model accuracy.
4. Ties use stable call, SMS, card order. Fixed mode preserves explicit priorities and then this stable order, ignoring feedback scores. The fixed query baseline uses the same preference/availability rules, so it compares adaptation without overriding consented preferences.
5. The preferred contact ID is used if valid. Otherwise the first saved contact is a visible deterministic fallback, never saved as an inferred preference. Deleting a preferred contact clears the reference.

No patient symptoms, severity, forecasting scores, menstrual information or other sensitive attributes are inputs. No symptom danger classifier exists. Feedback is interpreted only as self-reported action helpfulness, and never changes emergency access.

Limitations: three ratings are an engineering cold-start threshold, not evidence of effectiveness. Ratings are sparse, selected by the user, context dependent and potentially stale; the baseline does not model contact-specific outcomes or causal effects. Selective action exposure can bias ratings. Stable controls and explicit preferences may matter more than reordering. Ranking changes, task success and medical benefit need separate real-user evaluation. No AI-accuracy or usability-improvement result is claimed.

## Persistence and API

Additive Alembic migration **004** creates two tables without changing existing records:

- `support_preferences`: singleton structured contact/method/action priorities, large-text/reduced-motion/simplified-view choices, feedback opt-in and fixed/adaptive policy. Consent-sensitive feedback use defaults to false. Existing free-text caregiver profile remains unchanged.
- `support_feedback`: session ID, action ID, helpful boolean, UTC creation timestamp. References are validated; one rating per session/action is enforced by a database unique constraint. Actions are restricted to the nonemergency enum. No free-text health feedback or inferred completion is stored.

From backend, apply before starting:

```powershell
./.venv/Scripts/python -m alembic upgrade head
```

A data-losing downgrade is deliberately disabled pending export/review. Existing schema-3 JSON export is extended additively with `support_preferences` and `support_feedback`. Prior research snapshot contracts ignore those collections; they are not forecasting features. API responses use `Cache-Control: no-store`. SQL logging remains disabled and the documented backend command disables access logs. No private details are added to application logs.

Routes:

- GET/PUT `/api/support/preferences`.
- POST `/api/support/preferences/reset` (feedback and caregiver notes are preserved).
- GET `/api/support/recommendations`; optional `?policy=fixed` for the configured fixed baseline.
- GET/POST `/api/support/feedback`.
- DELETE `/api/support/feedback/{id}`.

Feedback creation requires an existing ended session and no other active session. Duplicate ratings return 409; invalid/emergency actions return 422. Delete a rating before replacing it. Deleting feedback removes its influence on subsequent recommendation requests without model retraining. Resetting choices turns adaptation off but does not delete ratings. Saved-preference loading failure blocks preference editing rather than overwriting unknown choices with defaults. Session loading failure blocks the feedback form.

## Evaluation foundation

`backend/research/support_evaluation.py` offers offline descriptive utilities, not automatic telemetry. The input is a list of explicitly collected, deidentified usability trials with:

- `source`: `simulated_test` or `real_user_study`; never guessed.
- `policy`: `fixed` or `adaptive`.
- `completed`: user/researcher-ascertained boolean or null. A link click is not completion.
- `interactions`: measured nonnegative integer or null; not invented from elapsed time.
- `chosen_action`, `explicit_first_choice`: nonemergency IDs or null.
- `order_before`, `order_after`: unique ordered nonemergency IDs.

Reports separate simulated and real groups and policies. They include completion rate over known outcomes, mean interactions over recorded counts, explicit preference alignment over known action/choice pairs, and top-recommendation change rate over comparable orders, with each denominator. Unknown measurements and absent groups yield null metrics, not fabricated zero success or failure. No real-user outcome records were collected or generated this sprint.

For an existing consented local trial file only:

```powershell
cd backend
./.venv/Scripts/python -m research.support_evaluation --input ../research-data/support-trials.json --output ../.research/support-usability/report.json
```

Do not relabel synthetic tests as real outcomes. Trial preparation must independently verify consent, provenance, observation definitions and measurement. There is no automatic action instrumentation, A/B assignment or evidence of improved outcomes. A real study still needs an agreed task-completion definition, interaction counting protocol, accessibility evaluation, controlled comparison and privacy review. All inputs/outputs stay in ignored local research directories.

## Verification and remaining manual checks

Tests use synthetic fixtures and inspect phone/SMS URI targets without activating them. Native sharing and clipboard are mocked in automated sharing checks. Tests cover preference persistence/reset, explicit-priority dominance, cold-start/default/fixed ranking, missing contacts, feedback consent/evidence thresholds, ended/active session rules, create/delete/export, sharing review, accessibility settings and emergency visibility. Existing diary, forecasting-research, keyboard, reduced-motion and responsive regressions remain included.

Actual OS dialer/SMS handoff, native share cancellation/destination behavior, screen readers, device text scaling, fatigue/light sensitivity and real-user helpfulness still require manual testing. PostgreSQL remains unverified without a running Docker daemon. Authentication, user isolation, production privacy protections and clinical validation are not included. The API stays on loopback; do not publish health records or claim a monitored service.

Final verification: 56 backend tests, 29 frontend tests and 6 browser tests passed; production build and dependency checks passed. Additive migration 004 is applied locally. Real-user usability/clinical outcomes were not collected. Native call/SMS/share behavior and assistive-technology comfort still require manual checks. The local frontend remains at http://127.0.0.1:5173/ with the backend on port 8000.
