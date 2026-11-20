## b1r9 — full-app static UI inventory

- The Windows workflow runs `scripts/audit_xaml_controls.py` twice against the checked-out exact upstream source, before and after the source adaptation, and stops safely on unreviewed selectable list controls or missing reviewed row templates.
- Its XML parser checks ALL `.xaml` files within `src/Nexus.App`, not just the five GridViews in MainWindow; its C# scan is heuristic and explicitly **not** a guarantee of complete runtime coverage.
- JSON/Markdown inventories are included in the native ZIP `AUDITS/` folder and checksummed. A brief summary is appended to GitHub Actions even if a build fails.
- The 61 local Python tests are fixture/static checks only. **b1r9 Windows compilation, manual WPF behavior and complete runtime portability have not been verified.**
- All b1r7/b1r8 functional/visual modifications remain unchanged.

# Verification matrix — b1r3

**Evidence vocabulary:** SOURCE-INSPECTED, STATIC-VALIDATED, WINDOWS-COMPILED, AUTOMATED-RUNTIME-TESTED, MANUAL-WINDOWS-TESTED, USER-CONFIRMED, NOT YET VERIFIED, FAILED/BLOCKED.

| Verification | As delivered (19 Nov 2026) | GitHub Actions acceptance | Manual Windows acceptance |
|---|---|---|---|
| Upstream repo / framework / file paths | SOURCE-INSPECTED on unpinned `main` | Validate actual resolved SHA and source anchors | Not needed |
| Stable release selection | Upstream releases page empty; tags NOT YET VERIFIED | Stable source semver tag or explicit opted-in SHA; fail otherwise | Not needed |
| Builder script syntax + resolver cases | STATIC-VALIDATED locally | Python compileall, unittest | Not needed |
| Source patch | Static checks against authored patch; NOT YET VERIFIED against checkout SHA | Actual source modifications and source checks must pass | Verify Data writes |
| Full .NET 8 upstream compile | NOT YET VERIFIED | `dotnet publish`, must pass | Confirm native EXE runs |
| Scanner worker PE + self-test | NOT YET VERIFIED | x64 PE structure + `--self-test`; must pass | Run a safe test scan |
| Direct GUI Nexus.exe launch | NOT YET VERIFIED | Cannot headlessly verify elevated WPF GUI | Mandatory manual test |
| Real portable Data containment | NOT YET VERIFIED | Recompiled Core storage read/write/restart probe; not WPF app | Mandatory ProcMon/filesystem test |
| Elevation/UAC, tray and descendant lifecycle | NOT YET VERIFIED | Manifest source reviewed | Mandatory manual test |
| Mutex/pipe isolation and installed-app coexistence | NOT YET VERIFIED | Source-level name checks | Test two copies and installed Nexus simultaneously |
| Autostart, owner-check, Unicode, relocation | NOT YET VERIFIED | Source compilation only | Mandatory manual test |
| Shell menus, installed-app coexistence | NOT YET VERIFIED | Source-level guards only | Mandatory manual test |
| Ransomware canaries opt-in/removal | NOT YET VERIFIED | Default-off source check | Mandatory manual test |
| Notification activation, Explorer restart | NOT YET VERIFIED | No valid headless test | Manual if feature used |
| Game Mode power/registry/CPU undo | NOT YET VERIFIED | Upstream pure-logic tests | Mandatory supervised manual test |
| Native ZIP staging and checksum | NOT YET VERIFIED until GitHub workflow | SHA, PE x64, assets and ZIP CRC tests | User extraction and startup |
| Shared publisher action behavior | SOURCE-INSPECTED at `@v1.1.1`, exact tag SHA NOT YET VERIFIED | Dry run then live publish on successful build | Verify Release page and SHA sums |
| Installer / PAF / TraceGuard / ShellGuard | NOT APPLICABLE — NATIVE | N/A | N/A |
| Upgrade/rollback and preserve empty dirs | NOT YET VERIFIED | ZIP preserves `Data` empty dirs | Manual user Data preservation |

### Strict build success boundary

An Actions green check means the checked-out source compiled, unit/scanner tests ran, package binary structure and ZIP integrity passed, and publisher recorded a GitHub Release. It **does not** establish Windows GUI usability, UAC behavior, hidden host writes, irreversible system changes, or installed-app coexistence.

### Security boundary

Build only upstream source at an immutable SHA; the current kit uses publisher `v1.1.1` action **tag** (action source and interface inspected, immutable tag hash not frozen). .NET SDK selected as 8.0.x to match upstream `global.json` roll-forward, which is current-patch floating rather than byte-identical SDK pinning. NuGet package lock must be reviewed and pinned for strict reproducibility. Never describe this as a fully deterministic binary rebuild.

## b1r3 observed CI evidence

- Source adapter and static inventory: **PASSED**, 69 candidate paths inventoried.
- Upstream Core tests on b1r2: **608 / 609 passed**, one test failed due deliberate `RansomwareWatch` default change.
- b1r3 updates that test expectation to its new native-portable default and adds an explicit opt-in persistence test; this adaptation and its four local Python fixture tests are **STATIC-VALIDATED**, not Windows-run.
- Build source identity used: `f5294a682565db62b01994ac12bf630a7f54b0d8`.
- .NET 8 runner SDK, compiled Nexus.exe, tray, GUI, scan, Data containment, ZIP and publishing: **NOT YET VERIFIED** on b1r3.

## b1r4 build log evidence (2026-11-19)

Uploaded `logs_120332019776.zip` shows source patch, source static validation, .NET 8 SDK check, 610/610 upstream Core tests, and compiled Nexus.Core Data write/read probe PASSED. Windows x64 WPF app publish FAILED with three `CS0103` diagnostics from the builder-created `NativePortableIdentity.cs` missing `using System.IO;`. b1r4 remedies the source import and adds static regression checks; these are **locally validated only**. No Windows x64 publish/EXE runtime/ZIP release has yet passed for b1r4.


## b1r7 WPF Processes row hover correction

- Source inspection: upstream `MainWindow.xaml` Processes tab `ListView`, and global `ListViewItem` theme in `Themes/Dark.xaml`.
- Static checks: XML parsing, scoped ItemContainerStyle, `GridViewRowPresenter`, WPF row hover/selection trigger order, unchanged context menu and right-click behavior.
- USER-CONFIRMED (subsequently): b1r7 source-built Nexus and its dark Processes hover/selection and context menu render correctly in Windows screenshot. Other machine integrations remain separately unverified.


## b1r8 all-list dark hover correction

- Verified via user screenshots: b1r7 Processes works; other GridView hover states remain nearly white.
- SOURCE-INSPECTED: audited `Themes/Dark.xaml` `ListViewItem` selected-only style and five `ListView` bindings in `MainWindow.xaml` at commit `f5294a682565db62b01994ac12bf630a7f54b0d8`.
- STATIC-VALIDATED: `patch_shared_dark_list_rows` fails closed if counts, DataContext bindings, GridView layout or existing list theme deviate. Two distinct templates validate as XAML XML: GridViewRowPresenter for tables and ContentPresenter for Dashboard restrained list. Checks include selected/hover/keyboard/disabled triggers, preservation of interactive cell XAML and existing process-specific style.
- Evidence: 42 passing local tests; Python compileall, YAML parsing, patch fixtures and archive integrity.
- NOT YET VERIFIED: full b1r8 Windows compilation, mouse hover/focus at multiple DPI settings, Game Mode toggle / Remove button, startup checkboxes, device Pin IRQ set action, Log sorting/filter, OS-managed shell behavior. These require Windows GUI testing.
