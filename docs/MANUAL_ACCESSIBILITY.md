# Phase 3: manual accessibility and device verification

Assessment date: **2026-11-10 (Asia/Calcutta)**. Branch: `test/manual-accessibility`; baseline **`1b5da97`**, PR #18 merged. This is a test plan and bounded automated evidence, **not a completed human accessibility review or physical-device sign-off**. See the historical [release-readiness report](RELEASE_READINESS.md).

## Status and recording rules

- **Manual checks: NOT RUN.** No person has completed the checklist below in this phase; no screen-reader session, actual browser-menu zoom or physical Android/iOS test is claimed.
- Automated desktop-browser and emulation results are separate below. A viewport resize, user-agent string, DOM role or computed color is not a human/device accessibility pass.
- All observations use fictional fixtures. Do not enter personal credentials, patient information, real contacts or real medication details. Do not activate a real telephone/SMS handler, sharing sheet, clipboard or location provider.
- No backend, database, provisioning or migration is needed or permitted for this procedure. Do **not** use the README's demo initialization or `scripts/ci_browser.py` here: that harness migrates a disposable database, which is outside this phase's scope.
- Record each result as **NOT RUN**, **MANUAL PASS**, **MANUAL FAIL**, or **BLOCKED**, with tester, date/time/timezone, OS/browser version, actual device, input/assistive technology, zoom, viewport, fixture mode and evidence. A pass in one configuration does not fill another matrix cell.

## Safe human-review session

Prerequisites: Git, Python 3.13 for a read-only port check, Node 22/npm, and installed Chrome or Edge. The [existing Playwright configuration](../frontend/playwright.config.mjs) defaults to a Windows Chrome executable; `MIGRAMIND_BROWSER` can select installed Edge because both use the Chromium launcher. Do not point that variable at Firefox: the launcher/engine must also change for Firefox.

Use a new PowerShell terminal at the repository root. These commands create a new source copy outside the checkout. No `.env`, existing venv, `node_modules` or ignored user database is copied by Git archive. The Phase 3 test files and approved, uncommitted Daily Status fix are copied explicitly until committed. Stop if a command fails.

```powershell
$phase3Repo = (Get-Location).Path
$manualRoot = Join-Path ([IO.Path]::GetTempPath()) ('migramind-manual-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $manualRoot | Out-Null
Write-Output "Manual review directory: $manualRoot"
git archive --format=zip --output="$manualRoot/source.zip" HEAD
if ($LASTEXITCODE) { throw 'Archive failed' }
Expand-Archive -LiteralPath "$manualRoot/source.zip" -DestinationPath "$manualRoot/source"
Copy-Item frontend/test-fixtures/manual-accessibility.ts "$manualRoot/source/frontend/test-fixtures/manual-accessibility.ts"
Copy-Item frontend/e2e/manual-accessibility-fixture.pw.ts "$manualRoot/source/frontend/e2e/manual-accessibility-fixture.pw.ts"
Copy-Item frontend/src/DailyCheckin.tsx "$manualRoot/source/frontend/src/DailyCheckin.tsx"
Set-Location "$manualRoot/source/frontend"
$env:npm_config_cache=Join-Path $manualRoot 'npm-cache'
npm.cmd ci
if ($LASTEXITCODE) { throw 'Locked frontend installation failed' }
@'
import socket
for port in (15383, 15384):
    with socket.socket() as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        probe.bind(('127.0.0.1', port))
print('Review ports free; no existing service will be used')
'@ | python -I -
if ($LASTEXITCODE) { throw 'Choose unused review ports; do not stop an existing service' }
$env:VITE_API_URL=''
$env:VITE_DATA_MODE='local'
$env:MIGRAMIND_API_PROXY='http://127.0.0.1:15384'
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 15383 --strictPort
```

Vite must report `http://127.0.0.1:15383/`. Port 15384 deliberately has **no server**. The fixture intercepts every `/api/` request; the proxy never points at an existing data service. Keep this terminal open. No application backend is started.

In a second PowerShell terminal, set `$manualRoot` to the exact newly printed/created directory (never an existing installation), then create **only a temporary test file**:

```powershell
$manualRoot = '<the new migramind-manual directory from terminal 1>'
Set-Location "$manualRoot/source/frontend"
$env:MIGRAMIND_E2E_BASE_URL='http://127.0.0.1:15383'
$env:MIGRAMIND_BROWSER='C:/Program Files/Google/Chrome/Application/chrome.exe'
# For Edge instead:
# $env:MIGRAMIND_BROWSER='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
$manualSession = Join-Path $manualRoot 'source/frontend/e2e/manual-session.pw.ts'
if (Test-Path -LiteralPath $manualSession) { throw 'Use a new manual-session file/target' }
@'
import {test} from '@playwright/test';
import {installManualAccessibilityFixture} from '../test-fixtures/manual-accessibility';
test('paused fictional manual review',async({page,baseURL})=>{
 test.setTimeout(0); // Human session only; not a CI/automated performance result.
 await installManualAccessibilityFixture(page,{
  baseURL:baseURL!,anonymous:false,readOnly:false,delayMs:0,failPaths:[],
 });
 await page.goto('/');
 await page.pause();
});
'@ | Set-Content -Encoding UTF8 -LiteralPath $manualSession
node node_modules/@playwright/test/cli.js test e2e/manual-session.pw.ts --config playwright.config.mjs --headed --workers=1 --retries=0 --output "$manualRoot/manual-results"
```

Playwright opens a fresh browser profile and pauses at `page.pause()`. Leave Inspector paused while the **human** uses the application, browser menus and assistive technology. Resume only after recording results; completing the Playwright test does not itself mean the manual checklist passed. Close the Inspector/test and stop the owned Vite terminal with Ctrl+C when finished. Never attach a personal browser profile, bind a public interface or delete an ambiguous directory. The headed pause procedure is supplied for a human tester; it was **not performed as a human session by the agent**. See [Playwright debugging](https://playwright.dev/docs/debug#run-a-test-from-a-specific-point).

### Fixture modes and honest limits

The [manual fixture](../frontend/test-fixtures/manual-accessibility.ts) supplies a fictional account, one contact, one January episode, three daily statuses with creation-history snapshots, empty wellness/early-symptom/feedback lists, and the existing synthetic descriptive-pattern fixture. It uses **no database**. All page mutation requests return controlled **422**, unsupported API reads return **404**, and selected reads can return **503**; none falls through to a backend. Telephone/SMS/external-link activation is blocked; clipboard/share/geolocation are JS stubs (coordinates are fictional). UI text saying copied/shared is therefore not evidence of a native OS handoff. Routing applies to page requests, **not** direct curl or Playwright `APIRequestContext`; use only the UI/page-fetch checks described here, never a personal backend.

Change options in the **temporary session file**, restart that test, and record the mode:

| Mode | Options | Useful coverage / limits |
| --- | --- | --- |
| Editable UI, default | `anonymous:false, readOnly:false` | All 12 destinations, populated/empty states, dialogs, native validation and controlled submit errors. Valid submissions deliberately do not save. |
| Anonymous | `anonymous:true` | Login/registration labels, missing-field validation and synthetic server error. Cannot establish successful authentication/session expiry/recovery. |
| Read-only UI | `readOnly:true` | Disabled/absent editing controls and explanatory text. This mocked UI is not the separately locked SQLite demo or provenance/readiness verification. |
| Loading | `delayMs:3000` | Observe busy/loading status and keyboard stability. Delay is capped at 10 seconds; it is artificial, not a measured backend latency. |
| Read failure | `failPaths:['/api/insights','/api/pattern-insights']` | Persistent error/retry accessibility. The same requests remain failed; restarting with an empty list is a new session, **not proof of live retry recovery**. |

Successful persistence, corrections/deletion/consent receipts, session changes, positive exports and native downloads are not implemented by this fixture. Do not file its intentional 422/404 responses as product defects or point it at a real backend to make them succeed. Existing stateful mock tests cover some success behavior automatically; human success-flow sign-off remains pending a suitable database-free fixture or a separately authorized environment. Do not submit account deletion or final destructive confirmations, even in the manual session.

## Checklist for all 12 destinations

For **every row**, first run common checks K1–R3 below at 100%, 200% and 400% browser zoom, then the destination-specific tasks. Repeat in warm/dark themes where applicable and record device/browser/assistive technology. All human result cells currently remain **NOT RUN**, including rows with automated evidence.

| ID / destination | Practical tasks | Expected result / scope | Human result |
| --- | --- | --- | --- |
| D01 Overview | Use the skip link; navigate here by keyboard. Read the main heading, missing-data cards, research disclosures and warning text. In read-only mode use tour/research destinations and return. | One main landmark; meaningful heading/focus; missing days stay unknown; research information is distinguishable from a prediction. Expanded disclosure and navigation purpose are announced. Unsupported research API success is a fixture limit. | NOT RUN |
| D02 Daily status | Read unknown/no-migraine/migraine examples. Tab to **Edit 2026-01-03**, inspect status-select focus, change draft values, Cancel, reopen history and close it. Inspect timing disclosure and required/range errors. | Labels/units and revisions understandable; no focus loss on cancel/close; optional fields are not presented as required. **A11Y-01 is fixed with automated regression coverage; human confirmation remains required.** Mocked saves always fail; persistence/tombstones are not manually verified. | NOT RUN; automated fix verified |
| D03 Migraine diary | Open Log an episode; traverse optional details and medication draft rows. Submit empty/invalid required fields, then valid fictional fields for a controlled error. Escape/close and return to initiating control. | Dialog has a name; focus starts inside, wraps only within it, errors are perceivable; no background interaction; Escape returns context without a save. Do not enter real medication data. | NOT RUN |
| D04 Calendar | Navigate to January 2026 using month controls; select the fixture episode date and empty days using Tab/Enter. Read selected-date content and legend without relying on color. | Month/date controls have useful names; active date/details are understandable to a screen reader; empty is not migraine-free. Record excessive tab burden or absent selection announcements. This is not declared an ARIA grid, so do not assume custom arrow-key support. | NOT RUN |
| D05 Insights | Read sparse 30-day state; select 90 days for synthetic supported patterns; change timezone. Open chart data tables and timed-observation disclosures; traverse them at zoom. | Filters have labels; graphical information has a readable data alternative; unknown/missing values and non-causal wording remain clear. Any intentional table scrolling is local; surrounding text should reflow. Synthetic counts are not clinical evidence. | NOT RUN |
| D06 Wellness | Read empty state; open Daily check-in. Try missing date and out-of-range optional values, trigger controlled submit failure, then Escape. | Blank differs from zero; labels contain units/ranges; native and server errors are conveyed; dialog focus and initiating-control return work. | NOT RUN |
| D07 Early symptoms | Read separation from attacks/forecasting. Open Log early symptom; test missing symptom/time, optional notes, controlled submit error and close. | Required/optional fields clear; date/time context readable; no prediction claim; focus/error/close behavior works. | NOT RUN |
| D08 Trusted contacts | Read the synthetic contact and call-link name without calling. Open Add/Edit contact; use malformed phone text; check native error and controlled save failure; close. | Phone links have correct purposes; invalid inputs are identified; dialog loop and return work; no number/country/reachability guarantee inferred. Do not activate a real dialer or delete a record. | NOT RUN |
| D09 Caregiver profile | Enter via navigation and Attack Mode's Review or edit action; repeat from the same destination. Traverse long notes, support preferences and grouped controls; exercise controlled error. | Destination heading receives focus; forms/legends/labels readable; no unexpected refocus while typing. Saving/preferences success is deliberately unavailable in the fixture. | NOT RUN |
| D10 Support feedback | Read empty/active-session restrictions. Inspect labels/controls without final deletion. Use the existing stateful support test evidence for the success-flow boundary. | Optional feedback, timing restrictions and empty state clear; no forced feedback during an active session. Creating/ending sessions and successful feedback are not supplied by the static manual fixture. | NOT RUN / success-flow fixture gap |
| D11 Settings | Toggle warm/dark appearance; reload within the test profile. Inspect export purpose, private-data warning and controls at zoom. | Appearance remains consistent, focus visible, labels wrap and controls remain reachable. Export endpoint is intentionally not supplied; download/OS file handling is not a manual pass. | NOT RUN |
| D12 Account | Read prototype/privacy text; inspect display-name field, consent checkbox/labels and gated deletion fields. Trigger only non-destructive controlled name/login errors. | Groups and required fields understandable; notices/errors announced; destructive purpose unmistakable. **Do not submit final deletion or enter a real password.** Successful logout/consent/account changes are not established by this fixture. | NOT RUN |

### Common keyboard, focus and error checks

| ID | Procedure | Expected result | Human result |
| --- | --- | --- | --- |
| K1 | Start at login or a fresh workspace; use only Tab/Shift+Tab. Record the actual order, including skip link, navigation, headings, filters, disclosures and footer. | Order follows the task/reading structure; no required action needs a mouse; no unexplained jump, invisible stop or whole-page trap. Programmatic focus tests alone do not prove this. | NOT RUN |
| K2 | Use Enter on links and Enter/Space on buttons; operate native select/input/disclosure controls with the keyboard. | Native semantics respected; selection/toggle state perceivable. Space is not required to activate a native hyperlink. | NOT RUN |
| K3 | Enter/exit Attack Mode; open/close SOS and the support card; use contact setup/caregiver handoffs twice, including same-page revisits. | Heading focus on entry/navigation; entry focus on ordinary exit; SOS close returns to its button; the approved PR #18 fixes remain intact. | NOT RUN |
| K4 | For episode/contact/wellness/early-symptom dialogs, Tab and Shift+Tab at both boundaries, expand optional sections, dismiss with Escape/close. | Focus stays in the active modal, background is unavailable, and dismissing restores a connected opener or sensible fallback. No trap after closing. | NOT RUN |
| E1 | Submit missing required/range-invalid fictional values; read the label and error with the screen reader. | Invalid control identifiable and reachable; native validation communicated. Do not require an `aria-invalid` attribute where native semantics already expose invalidity. | NOT RUN |
| E2 | Submit otherwise valid fictional input for the fixture's 422; use loading/read-failure modes. | Error/loading/status announced without losing context or trapping focus; retry purpose clear; no false success. Fixture failure is intentional; real backend recovery remains unverified. | NOT RUN |

### Screen-reader checks

Use a human-operated screen reader in the matrix below; record its version and browse/focus mode. Role locators, aria snapshots, labels and live-region attributes are only structural evidence.

- **S1 Landmarks/headings:** one meaningful active main; navigation named; headings form a usable outline; page, research and SOS transitions announce context. Inspect icon-only buttons/SVG announcements.
- **S2 Forms:** label, required/optional status, units, help, group/legend, readonly/disabled state and invalid/error association are understandable. Check native date/time and numeric controls, not only plain text inputs.
- **S3 Dynamic states:** loading, server errors, saved/unsaved notices, expanding disclosures, selected date, correction/history and read-only restrictions are conveyed without rereading the whole page. Do not mark a role=`status`/`alert` as an auditory pass.
- **S4 Focus return:** browser/SR focus remains aligned after navigation, Escape, cancel, retries, login state changes and any safely stubbed external-handler interaction. Confirm the A11Y-01 fix with the actual screen reader and keyboard before accepting cancellation focus.

All S1–S4 results: **NOT RUN**. No NVDA, Narrator, TalkBack or VoiceOver session was performed by the agent.

### Zoom, contrast, reflow and motion

| ID | Human procedure | Expected result / distinction | Human result |
| --- | --- | --- | --- |
| Z1 | At 100% browser zoom record window/client dimensions and OS scaling. Use the browser's actual menu to choose **200%**, then repeat all destinations/forms. | Text/controls remain available and usable; labels/errors are not clipped or overlapped. Record actual zoom and `innerWidth`/`innerHeight`; screenshot scale is insufficient evidence. | NOT RUN |
| Z2 | Choose actual **400%** browser zoom with a window about 1280 CSS px wide at 100%; repeat at the resulting approximately 320 CSS px layout width. Inspect dialogs, overlays, calendar and charts. | Reading/operating normal content does not require whole-page two-axis scrolling. Local data-table scrolling may be justified; inspect cell readability and keyboard reachability. Record actual dimensions rather than assume equivalence. | NOT RUN |
| Z3 | Where supported, test 200% text-only enlargement, large system font/text spacing, and zoom while keyboard focus is near an edge. | No loss of control/label content or obscured focus. Page zoom, text-only enlargement, viewport resizing, DPR and pinch zoom are separate mechanisms. | NOT RUN |
| C1 | Inspect actual text, muted/helper/error/disabled/selected states, icons, boundaries and focus rings in warm, dark and Attack Mode. Use measured rendered colors/backgrounds, including overlays. | Sufficient contrast and distinguishable state/purpose throughout; do not extrapolate three token-pair checks to all content or claim certification. | NOT RUN |
| R1 | On actual intended phone/tablet: portrait/landscape, touch, large text, software keyboard, scroll into dialogs and focus near sticky/overlay content. | Reachable controls and visible text/focus; no keyboard-covering essential fields; comfortable target spacing. Desktop touch flags do not test these. | NOT RUN / device access pending |
| R2 | Enable OS reduced motion, reload, and open/close menus/dialogs/Attack Mode; repeat normal preference. | Nonessential motion suppressed without losing state or functionality. OS change is a human check; `emulateMedia` is automated emulation. | NOT RUN |
| R3 | Inspect saved larger-text/reduce-motion/simplified-view choices and meaningful error handling. | Labels/grouping clear; success/persistence requires a stateful success fixture. Static manual fixture rejects writes, so cannot certify saved preferences. | NOT RUN / fixture gap |

[W3C resize-text guidance](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html) discusses 200% text resizing; [reflow guidance](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) relates a 1280px starting width at 400% to 320 CSS px and explains exceptions. These are assessment references, not a conformance claim. Automated 640/320px checks below are **width stress tests with height held at 850px**, not actual 200%/400% browser zoom or a loss-of-content audit. [Playwright emulation](https://playwright.dev/docs/emulation) configures selected browser/device properties; it does not supply human or physical-device evidence.

## Browser/device matrix

| Target | Planned human input / AT | Automated evidence in this phase | Human / physical status |
| --- | --- | --- | --- |
| Windows Chrome **156.0.8078.79** | Keyboard/mouse, NVDA or Narrator; actual 100/200/400% zoom | Headless installed Chrome; existing selected tests and viewport/touch probes below | **NOT RUN** human/SR/actual zoom; same host only |
| Windows Edge **157.0.4341.42** | Keyboard/mouse, Narrator or NVDA; actual zoom/forced colors | Headless installed Edge through Chromium launcher; selected tests/probes below | **NOT RUN** human/SR/actual zoom; not an independent browser engine |
| Windows Firefox | Keyboard/mouse, NVDA; actual zoom/text-only resize | **NOT RUN**: Firefox not found in checked standard install locations/PATH; managed Playwright Firefox missing; base config selects Chromium and a Chromium executable | **BLOCKED** on appropriate browser/test-engine setup; do not point `MIGRAMIND_BROWSER` at Firefox |
| Android Chrome + TalkBack | Actual phone, touch, portrait/landscape, software keyboard, OS font size | Pixel 7 descriptor in **desktop Chrome/Edge Chromium**, both orientations; no Android OS | **NOT RUN** physical/TalkBack/native handling |
| Android Firefox + TalkBack, if supported | Actual phone and engine-specific checks | **NOT RUN** | **NOT RUN** / browser/device setup pending |
| iOS Safari + VoiceOver | Actual iPhone/iPad, touch/rotor, orientation, text size/pinch behavior, software keyboard | iPhone 13 descriptor in **desktop Chromium only**; managed WebKit missing | **NOT RUN** physical/Safari/VoiceOver. An iPhone UA in Chromium is not iOS Safari. |
| Desktop WebKit, optional diagnostic | Keyboard and platform-appropriate screen reader | **NOT RUN**: managed WebKit absent | Not a replacement for physical iOS verification |

Chrome/Edge are two installed desktop browser binaries, both Chromium-based. The default Playwright config has one worker, no multi-engine/device projects and a platform-specific executable fallback; CI supplies its own Chromium path. No browser or accessibility-scanner dependency was downloaded in this phase. axe/pa11y/Lighthouse is not installed/configured. Actual phones cannot reach this Windows loopback origin as their own `localhost`; a separately reviewed fixture/device access arrangement is required. Do not expose the app publicly, change bindings or relax the fixture origin guard in this phase.

## Historical pre-fix automated evidence

Source: clean `test/manual-accessibility` at PR #18 merge; runtime dependencies copied into a new `%TEMP%/migramind-phase3-9mx48795/source/` from the previously locked installation after matching `package-lock.json`. No fresh-install claim. All API responses were mocked; native telephone/external activation blocked. No backend, user data, provisioning, migrations or persistent writes.

| Check | Actual result |
| --- | --- |
| Frontend unit baseline | **82 passed / 14 files**, 43.12s (44.64s command wall time) |
| Existing mocked accessibility/responsive tests | **17 passed in Chrome**, 25.8s (31.24s wall); **17 passed in Edge**, 25.1s (25.91s wall); first invocations, default timeouts, no retries |
| Additional fixture/pattern checks | **6 passed in Chrome**, 10.7s (11.71s wall); **6 passed in Edge**, 6.1s (6.90s wall). Each batch contains the 3 new fixture-isolation tests plus 3 existing sparse/supported chart/timezone/wellness cases. Thus **23 distinct selected scenarios per browser**, across two batches, not a full unfiltered suite. |
| Reflow-width probes | Each browser: **48 screen observations** = 12 destinations × 640/320px × warm/dark; no page horizontal-overflow assertion failed. Heading/main checks passed for the inspected states. Viewport only, not real browser zoom. |
| Touch/UA emulation | Each browser: **48 screen observations** = 12 destinations × Pixel 7/iPhone 13 descriptors × portrait/landscape; no page horizontal-overflow assertion failed. Both contexts run in desktop Chromium. |
| Reduced motion / dialog | Each browser: emulated reduced-motion Exit control had animation `none`, transition `0s`; emergency/exit viewport assertions passed. Contact dialog initial focus, Tab/Shift+Tab wrap, native invalid-phone validation and Escape/return passed with synthetic input. |
| Defect observation | **A11Y-01: focus lost to BODY after Daily status Cancel correction**, reproduced in both browsers. Probe completion is **not a passing cancellation-focus result**. |
| Manual fixture verification | Final strict TypeScript check passed in **1.30s**, using existing JSX/Vite types. Three checked-in safety tests pass in each browser: all-destination fixture traversal and blocked persistence/unknown reads; synthetic anonymous login error; rejection of non-loopback origin before navigation. Initial two temporary smoke checks also passed but are not counted as new independent scenarios. |
| Network / data / cleanup | Both probes recorded zero page errors, external request attempts and API mutation requests. All browser suites used API fixtures; some existing tests simulate in-memory writes only. Owned Vite stopped, review port free; application/backend/config/lock/migration bytes preserved. |

The agent inspected actual Chrome daily-cancel and Edge dark Attack Mode screenshots at 320px. These are supporting automatically rendered images, **not human interaction or physical-device evidence**. Active-element and viewport assertions, rather than a full-page screenshot alone, underpin the focus/geometry observations.

The first standalone fixture type check reported a Node `process` global and missing JSX compiler context. The fixture now requires an explicit validated loopback `baseURL` instead of a Node global, and the check uses the existing JSX/Vite client typing context. No types/dependencies were installed. Initial diagnostics are retained; final result is below. This was test-tooling setup, not an application defect or flaky browser result. No new browser failure was silently retried. Phase 2's earlier timeout remains historical evidence in its report.

### Commands and artifacts

From the disposable copy's `frontend`, with `VITE_API_URL=''`, `VITE_DATA_MODE=local`, `MIGRAMIND_E2E_BASE_URL=http://127.0.0.1:15383`, and `MIGRAMIND_API_PROXY=http://127.0.0.1:15384`:

```text
node node_modules/vitest/vitest.mjs run --maxWorkers=1
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 15383 --strictPort
node node_modules/@playwright/test/cli.js test e2e/accessibility-fixes.pw.ts e2e/assistance.pw.ts e2e/sos.pw.ts e2e/support.pw.ts e2e/product-quality.pw.ts --config playwright.config.mjs --output <new-root>/<browser>-browser
node node_modules/@playwright/test/cli.js test e2e/manual-accessibility-fixture.pw.ts e2e/patterns.pw.ts --config playwright.config.mjs --output <new-root>/<browser>-extra
node node_modules/typescript/bin/tsc --noEmit --strict --skipLibCheck --target ES2022 --module ESNext --moduleResolution Bundler --jsx react-jsx --types vite/client --lib ES2022,DOM test-fixtures/manual-accessibility.ts
```

Set `MIGRAMIND_BROWSER` to the Chrome or Edge paths in the matrix before each browser run. The exact one-off viewport/dialog probe remains at `%TEMP%/migramind-phase3-probe.cjs`. To repeat it on this host while the isolated Vite is running, set `PHASE3_FRONTEND=<new-root>/source/frontend`, `PHASE3_ARTIFACTS=<new-root>`, `PHASE3_BROWSER_LABEL=chrome` or `edge`, plus the browser/base-URL variables above, then run `node <probe-path>`. It uses 640/320px viewports at height 850, emulated `reducedMotion:reduce`, Pixel 7/iPhone 13 descriptors and mocked snapshot data. This temporary probe is not added to CI; the checked-in fixture tests and existing Playwright cases are portable. Do not reuse an existing personal server/source environment.

Private artifact directory: `%TEMP%/migramind-phase3-9mx48795/`. Evidence includes `results.json`, unit/browser/extra/type-check logs, `chrome-probe.json`, `edge-probe.json`, screenshots and tracked-source hashes. The initial two fixture smoke checks and final checked-in tests are separate runs. The former are not extra independent application workflows. No full backend, data-dependent browser or built-SQLite-demo suite was run because it would require a backend/data setup excluded here.

## Approved Daily Status focus fix

Follow-up date: **2026-11-10 (Asia/Calcutta)**. A11Y-01 is fixed after explicit approval. The original historical evidence above remains valid for the old implementation.

**Cause and minimal correction:** Cancel clears editing and increments the keyed form's key. The focused Cancel button disappears; the previous effect only focused when entering editing. [DailyCheckin.tsx](../frontend/src/DailyCheckin.tsx) now remembers the actual initiating button (Edit, or Review yesterday when correcting an existing report). A one-shot cancellation intent restores that connected, enabled button after render, or the newly rendered **Migraine status** select when the opener is unavailable. The existing focus-on-edit rule remains; initial load, save, deletion, route and dialog focus rules are not changed. No timing delay, extra tab stop, focus trap, styling or API behavior was added.

**Regressions:** three new [unit cases](../frontend/src/DailyCheckin.test.tsx) cover repeated cancellation, untouched initial outside focus, unchanged saved values/no writes, ordinary Tab order, a removed opener and Review yesterday's initiating control. Two new [isolated browser cases](../frontend/e2e/manual-accessibility-fixture.pw.ts) cover repeated keyboard Enter/Tab interaction across different reports at **320px**, unchanged GET snapshots/no writes, and a **1280px** fallback when a mocked refresh removes the opener. The fallback uses an empty GET snapshot after a controlled history failure; no record is deleted. Both new browser cases failed on the original implementation in **both Chrome and Edge**, precisely at the expected focus assertions (2 failures per browser, no test-run timeout); they passed after the fix. These intentional negative controls are not flaky tests or retries until green.

All execution used a new `%TEMP%/migramind-daily-focus-34ho06qb/` source copy and a byte-identical previously locked dependency copy. No install, backend, database or migration was run. API requests are intercepted with fictional fixtures. Vite binds only `127.0.0.1:15385`; proxy target `127.0.0.1:15386` has no backend. Browser profiles and production output directories are temporary. Evidence includes `source-baseline.json`, `results.json`, per-command logs and the original failure contexts. The owning harness has bounded timeouts (60s readiness, 120s negative-control batches, 360s units, 180s/build, 300s/browser batch) and stops its own Vite process tree in `finally`.

| Check | Actual result |
| --- | --- |
| Original component / Chrome | Both new cases failed on focus, **25.28s** command wall time. |
| Original component / Edge | Both new cases failed on focus, **19.62s** command wall time. |
| Final frontend unit suite | **85 passed / 14 files**, **88.09s** suite, **89.62s** command wall time. |
| Local production build | TypeScript and Vite passed; **16.81s** command wall time, Vite **5.42s**. |
| Synthetic production build | TypeScript and Vite passed; **14.06s** command wall time, Vite **5.17s**. |
| Final Chrome selected suite | **25 passed**, **56.5s** suite, **58.46s** command wall time. |
| Final Edge selected suite | **25 passed**, **56.6s** suite, **58.27s** command wall time. |
| Cleanup and preservation | Owned Vite stopped; ports **15385/15386 free**. Tested component/test bytes match the checkout; baseline hashes confirm no other source, backend, migration, dependency-lock or configuration change. Existing user data/environments were not opened. |

From the new isolated copy's `frontend`, use the same environment and browser-selection procedure as above, substituting ports **15385/15386**. Overlay the current `DailyCheckin.tsx`, `DailyCheckin.test.tsx`, manual fixture and fixture-test files if starting from `git archive HEAD` before these changes are committed. The human-session setup above explicitly overlays the fixed component.

```text
node node_modules/vitest/vitest.mjs run --maxWorkers=1
node node_modules/@playwright/test/cli.js test e2e/manual-accessibility-fixture.pw.ts --grep "Daily Status cancellation" --config playwright.config.mjs --output <new-root>/<browser>-focused
node node_modules/@playwright/test/cli.js test e2e/accessibility-fixes.pw.ts e2e/assistance.pw.ts e2e/sos.pw.ts e2e/support.pw.ts e2e/product-quality.pw.ts e2e/patterns.pw.ts e2e/manual-accessibility-fixture.pw.ts --config playwright.config.mjs --output <new-root>/<browser>-after
```

For each production build, set `VITE_DATA_MODE=local` then `synthetic`, retain `VITE_API_URL=''`, and run `node "C:/Program Files/nodejs/node_modules/npm/bin/npm-cli.js" run build -- --outDir <new-root>/<mode>-dist`. Output directories must be new temporary targets. Vite's advisory that external output directories will not be emptied is expected; no existing output was removed. The focused command is supplied for reproduction; actual final validation ran the encompassing 25-case suite once per browser, not an extra independent focused batch. No final test failed, timed out or was retried. Non-fatal Node color-environment warnings were recorded.

**Remaining gates:** a human must repeat D02, K1-K4 and S4 with keyboard and actual screen-reader browse/focus modes, confirm visible focus/scroll context and announcements, then complete 200%/400% browser zoom, rendered contrast, responsive/reduced-motion checks and the outstanding browser/device matrix. No human, screen-reader, physical-device or Firefox/Safari validation is claimed. Backend/data-dependent/built-SQLite-demo tests were not rerun for this focus-only change. Existing historical Phase 2 flakiness and installation limitations remain documented; this follow-up adds none.

## Findings and release gates

| ID / priority | Evidence, reproduction and impact | Proposed correction / disposition |
| --- | --- | --- |
| **A11Y-01 / P2** | Historical pre-fix Cancel correction handler in [DailyCheckin.tsx](../frontend/src/DailyCheckin.tsx): Edit 2026-01-03 → status select gets focus → focus Cancel → Enter. Both Chrome and Edge then report `document.activeElement.tagName === 'BODY'`. Cancel replaces the keyed form and removes its focused button without restoring context. Keyboard/SR users can lose their place. No save/mutation occurs. | **Resolved in automated follow-up after explicit approval.** Cancel restores the connected, enabled initiating control, or the new status select if unavailable. See [approved Daily Status fix](#approved-daily-status-focus-fix). Human keyboard/screen-reader confirmation remains pending. |
| A11Y-02 / P3 historical | Literal `Caregiver guide ? saved personal preferences` separator remains in `SupportCard.tsx`, already recorded in Phase 2. | Copy polish deferred; not changed. |
| Gate / high priority | Human keyboard/SR checks, real 200/400% zoom, comprehensive rendered contrast, forced colors, real-device input and platform handler behavior **not performed**. | Remain **NOT RUN**, not failed merely because unavailable. Complete relevant matrix cells before broad accessibility claims. |
| Gate / fixture coverage | All success writes and unsupported research/export APIs intentionally blocked. No real authentication/persistence/recovery/native-delivery verification. | Record those cases as **BLOCKED** until a suitable approved test arrangement exists; never relax isolation to use personal data. |

No additional product defect was confirmed by the selected geometry/motion checks; they do not exclude clipping, inaccessible announcements or other human findings. Native handlers must be tested only with safely stubbed handlers or authorized non-emergency test arrangements; **never call a real emergency number for QA**. Public deployment, real health-data collection, research governance and clinical validation remain outside scope and blocked as before.

## Human sign-off record — leave unfilled until performed

```text
Tester / date / timezone:
Commit / fixture mode / URL:
OS / browser exact version / hardware:
Keyboard / touch / screen reader version and mode:
OS scaling / browser zoom / viewport / orientation:
Checklist IDs exercised:
Actual announcements / focus order / contrast measurements:
PASS / FAIL / BLOCKED per ID (do not copy automated status):
Synthetic screenshots or recording paths:
Defect IDs, exact reproduction, impact and proposed correction:
Retest after approved fixes / reviewer:
```

Current sign-off: **no human sign-off and no physical-device pass**. The initial phase changed test infrastructure/documentation only; the explicitly approved follow-up changes Daily Status cancellation focus and adds focused regressions. No commit, push, PR creation, merge, deployment, provisioning, database/migration/lock/secret or production-setting change is authorized or performed.
