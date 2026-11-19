## b1r6 — 2026-11-19

- User-confirmed b1r5 native application runs; Processes right-click menu and submenu are legible but a white vertical icon gutter overlaps leading command text in the parent menu.
- Scoped the missing WPF override to `ContextMenu.Template` (not an application-wide implicit style). New `patches/ProcessMenuSurface.xaml` keeps an `ItemsPresenter`, menu commands and popup behavior, but removes the system-default white gutter.
- Added three UI/template regression tests and source validation checks for the ContextMenu template. No changes to autostart, source storage, scanner, or Windows-host integration.
- Default revision `r6`. Windows compilation and live rendering of b1r6 not yet tested.

# Nexus Native Builder revisions

## b1r5 — 2026-11-19

- User confirmed Nexus b1r4 successfully builds and starts. Windows screenshot shows a near-white-on-white Processes menu and Autostart `0x80070002` first-run failure.
- Source-inspected WPF menu at upstream `f5294a682565db62b01994ac12bf630a7f54b0d8`: `ContextMenu` has no explicit dark style and is a separate visual tree; the `ProcessesViewModel` commands require its DataContext.
- Add scoped WPF context menu/submenu template with dark readable background, white text, focused and disabled states. Bind to `PlacementTarget.DataContext`, and select process under pointer on right click.
- Source-built autostart patch previously called COM `GetTask(TaskName)`, which can throw for a normally missing task. Replace with read-only COM enumeration of root tasks; preserve explicit ownership and path validation for disable and repair.
- Local parser/fixture tests cover the changed source patterns; no Windows runtime validation claimed.


## b1r4 — 2026-11-19

- Inspected uploaded Actions logs `logs_120332019776.zip` with selected upstream SHA `f5294a682565db62b01994ac12bf630a7f54b0d8`.
- **PASS:** source checkout/patch/static validation, .NET SDK 8 selection, all 610 upstream Core tests, `Nexus.Core` portable Data runtime probe.
- **FAIL:** Windows x64 WPF app publish: generated `src/Nexus.App/Services/NativePortableIdentity.cs` uses `Path` without importing `System.IO` (three `CS0103` diagnostics at lines 17–18).
- Added explicit `using System.IO;` to `patches/NativePortableIdentity.cs` (source template copied into the upstream tree by our patcher).
- Added fail-early static validation for this import and four regression tests to prevent recurrence.
- Set workflow default `package_revision: r4`; no change to upstream SHA or source architecture.
- **Not yet verified:** b1r4 Windows compilation, GUI/runtime, scanner test, ZIP packaging and release publishing.


## b1r3 — 2026-11-19

- Reviewed uploaded `logs_120321043195.zip` on upstream commit `f5294a682565db62b01994ac12bf630a7f54b0d8`. Source patch and source static check passed; upstream Core tests ran 608 passed / 1 failed.
- Root cause: upstream `SettingsUpgradeTests` asserts `RansomwareWatch=true` for legacy settings, while our intentional native-portable source patch changes its default to false to avoid creating host-folder canaries without opt-in.
- Fail-closed `patch_portable_security_tests` changes only the obsolete default expectation to false and adds an explicit opt-in persistence test. It does **not** skip tests or enable automatic canaries.
- Add root `global.json` matching the upstream .NET 8 SDK family; previous CI executed under SDK 10.0.403 because `dotnet` was invoked from the builder root without a policy file. Assert SDK 8 at test time.
- Add RID-specific restore before `win-x64 --no-restore` publishing to prevent runtime-identifier asset mismatch.
- Four local fixture regression tests added; default package revision r3. Compilation and live Windows runtime **still unverified** until GitHub Actions rerun.

## b1r2 — 2026-11-19

- Source: uploaded GitHub Actions log `logs_120310743662.zip`, exact upstream source commit `f5294a682565db62b01994ac12bf630a7f54b0d8`.
- Fix: C# ShellIntegrationService unregister patch no longer requires exact whitespace and no blank lines. It matches only the audited sequence `if (shell?.OpenSubKey(KeyName) is null)` -> `continue` -> `shell.DeleteSubKeyTree(KeyName)` and must find exactly one occurrence.
- Continue preserving installed profiles, foreign shell keys and separate native executable identity.
- New offline tests cover whitespace, CRLF, ambiguity and refusal to change altered semantics.
- Default package revision increased to `r2`.
- Verification: static Python tests passed locally; no Windows-native build, runtime or registry integration execution was performed here.

## b1r1 — 2026-11-19

- Initial native-only source adapter and CI pipeline.
- Discovered brittleness: exact-text shell unregister anchor failed on a real GitHub Actions checkout before compilation.
