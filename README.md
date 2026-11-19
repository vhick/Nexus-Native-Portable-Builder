# Nexus NATIVE Portable Builder Kit (Windows x64) — b1r6

**Repository audited:** [0xmortuex/Nexus](https://github.com/0xmortuex/Nexus)  
**Build:** Actual upstream C#/.NET 8 WPF application from source. **Native mode ONLY.**  
**Release component:** `vhick/portable-release-publisher@v1.1.1` (verified `action.yml` and implementation)  
**No PortableApps launcher, PAF installer, source-fork, post-exit harvesting or mandatory manager.**

## Critical warning and verified current upstream status

Upstream's public GitHub Releases page showed **zero published releases** during the November 19, 2026 audit. The tag endpoint was not independently accessible in the audit environment. Consequently **the default latest-stable resolver will reject the build if there is no proper stable semver tag.** This is intentional. The script queries current Releases AND tags when GitHub Actions runs, sorts versions numerically and refuses to substitute `main`.

To build before the first upstream stable tag, you must explicitly supply an **exact 40-character upstream commit SHA**, select **allow_untagged=true** and understand that this is a *development-source build, not a stable-release build*. The workflow validates that SHA against GitHub and checks out that exact commit. The selected source may drift from the audited anchors; if so, source adaptation aborts rather than guessing. Obtain the commit SHA by opening **upstream Nexus > Commits > desired commit > Copy full SHA**.

## Why it is native portable

Upstream uses `NexusPaths.Default()` in `src/Nexus.Core/Persistence/NexusPaths.cs` to root settings, rules, profiles, backup journals, logs, security history, quarantine, and benchmarks under `%APPDATA%\Nexus`. The builder patches that **actual C# source** to `AppContext.BaseDirectory/Data` **before it is compiled**. `Nexus.exe` directly uses this class through `App.OnStartup`, so no external environment-preparation tool or launcher is involved.

Nexus's isolated `Nexus.Scanner.exe` worker and `assets/` detection data are preserved beside Nexus.exe. The existing `requireAdministrator` Windows manifest and WPF tray/UI are preserved. *No administrator prompt will appear in hosted CI because the UI is not launched there.* An administrator/UAC prompt is expected when a user starts the actual program.

## Host safety adaptations

- **Single-instance behavior:** replace the fixed `Global\NexusOptimizerSingleInstance` mutex and `Nexus.ScanRequest.{user}` pipe with app-folder-derived names, preventing a native copy from hijacking or blocking an installed copy. Two independent native folders can run alongside each other; duplicate launches in the same folder still share one identity.
- **Autostart:** upstream's fixed `Nexus Optimizer` task and unsafe `/Create /F`/unconditional delete are replaced by a unique, per-copy task name with ownership data under `Data/Integrations/`. Creation is opt-in; no overwrite of same-name tasks. Deletion verifies the recorded target. Moving the directory requires explicit disable/re-enable and may require manually removing an obsolete task if Windows task-XML encoding prevents verification. This behavior needs real Windows acceptance testing.
- **Context menu:** native portable uses a distinct `Nexus.NativePortable.ScanWithNexus` HKCU key; registration refuses existing keys, and removal verifies its exact target. This feature remains opt-in. Do not assume removal after changing folder paths; unregister before relocating.
- **Ransomware canaries:** upstream *normally enables* hidden files in Documents/Pictures/Videos/Music/Desktop; portable defaults **RansomwareWatch=false**. If you explicitly turn it on, the upstream detection feature writes these host-managed tripwires. **These are an explicitly enabled OS integration, not portable data.** Turn it off and use the app's restore/reset to remove the tripwires before relocating; inspect files carefully because upstream's reset implementation has broad name-based cleanup.
- **Power/CPU/registry/network/system tweaks:** intentionally affect Windows and are **not** made virtual, hidden, or silently undone by a wrapper. Changes rely on upstream's journal/undo implementations. Use the in-app Restore Defaults/Undo before moving to a different PC; the stored state alone cannot guarantee restore of another machine's system settings.
- **Scanner/YARA:** keep native worker beside EXE. Optional third-party YARA-X DLL/rules are **not** bundled, respecting separate provenance and license rules.

## Beginner-friendly GitHub Desktop setup

1. Sign in to GitHub. Create an **empty, separate** repository, for example `Nexus-Native-Portable-Builder`. Do not fork or modify the upstream repository. Choose **private** if you do not want your builds publicly accessible. Avoid including unrelated sensitive files.
2. Open **GitHub Desktop > File > Clone repository**, select your new repository, choose a convenient folder and clone.
3. Extract **all** builder-kit files into the root of your local repository. Ensure the hidden `.github/workflows/build-native.yml` folder is copied (Windows Explorer may hide names starting with a dot).
4. In GitHub Desktop, review changes. For the Summary enter `Remove Nexus process-menu light gutter b1r6`. Suggested Description: `Add fail-closed source resolver, portable Data source patch, opt-in Windows integration protections, x64 .NET 8 workflow, scanner smoke checks, ZIP checksums, and pinned release publisher.` Click **Commit to main**, then **Push origin**.
5. On GitHub open your **builder** repository > **Actions** > **Nexus Native Portable - Source Build and Release** > **Run workflow**.
6. First try an empty upstream version (only works if upstream has a stable tag). If it fails with **no stable tag**, enter a verified 40-character upstream commit SHA and tick **allow_untagged** to authorize a development build.
7. Use revision `r6` for this corrected patch set. Inspect **Actions > latest workflow run > steps**. The source patch step deliberately stops on upstream incompatibility. When everything passes, open **Releases** in your builder repository to find the `Nexus-NativePortable-...zip` and publisher-generated `SHA256SUMS.txt`.
8. Download the ZIP. Check its SHA-256 against `SHA256SUMS.txt` with Windows PowerShell: `Get-FileHash '.\your-file.zip' -Algorithm SHA256`.
9. Extract into your own user-writable folder, e.g. `D:\Portable\Nexus-NativePortable\`; run `Nexus.exe` directly, accepting the normal administrator UAC prompt. **Do not run it from inside the ZIP.** Do not delete `Nexus.Scanner.exe` or `assets`.
10. Settings, rules, logs, backups, quarantine, crash journals, autostart metadata and security history live in `Data` beside Nexus.exe. **Never delete Data during update/reinstall.** Exit Nexus using the tray menu before replacing binaries. Keep a backup of `Data` and the previous full folder so you can roll back, subject to schema and Windows-state limitations.

## Output

One native package ZIP with top directory `Nexus-NativePortable-{source-version}-{sourceSHA12}-{revision}` containing `Nexus.exe`, `Nexus.Scanner.exe`, `assets/`, `Data/`, `LICENSES/`, `README.txt`, and `BUILD-IDENTITY.json`. The publisher adds `SHA256SUMS.txt` to its GitHub Release. Releases use `nexus-native-{version}-{sourceSHA12}-{builderSHA8}-{revision}`. No PortableApps-format deliverables exist.

## Evidence, acceptance and known limitations

See [AUDIT.md](docs/AUDIT.md), [VALIDATION.md](docs/VALIDATION.md), [WINDOWS-ACCEPTANCE.md](docs/WINDOWS-ACCEPTANCE.md), and [UPGRADE-ROLLBACK.md](docs/UPGRADE-ROLLBACK.md). The kit's local Python checks validate script syntax, resolver cases and source/ZIP contracts; **they do not prove the EXE compiled**. The Windows runner compiles and exercises only the scanner worker; full elevated Nexus GUI/tray, registry, app-owned storage containment, autostart and power settings require a real manual Windows test. This kit has **not been compiled or runtime-tested** as delivered here.

## b1r5 fix for November 19 Windows x64 application compilation

The uploaded `logs_120332019776.zip` proves that **all 610 upstream Core tests passed**, source patch/validation passed, and the real Nexus.Core executable-relative storage probe passed. The next application publish failed with three identical `CS0103` errors in our generated `src/Nexus.App/Services/NativePortableIdentity.cs` because `Path` requires `using System.IO;` and the WPF temporary compilation did not make that namespace available automatically. This is not an upstream bug.

This revision adds that explicit import to the application-specific template, strengthens `scripts/validate_source.py` to reject missing imports before `dotnet publish`, adds four targeted offline regression tests, and defaults the workflow's package revision to `r4`. It does **not** skip upstream tests, alter persistence, change Nexus features, or introduce wrappers. The `win-x64` compile and runtime tests remain **NOT YET VERIFIED for b1r5** until the workflow runs again.

## b1r3 fix for Core settings-upgrade test failure

The previous run passed source patching and validation, but upstream Core tests reported **608 passed, 1 failed**. This is because the native portable source adapter deliberately defaults ransomware canaries **off** until consent, while the old upstream migration test still expected **on**. `scripts/apply_portable.py` now fail-closed patches that **single default expectation**, keeps the other settings assertions intact, and adds a C# regression test ensuring an explicit `RansomwareWatch=true` setting still loads as true. No whole test class is skipped. The test suite now contains 610 expected tests (up from 609), assuming upstream commit unchanged.

The prior Windows runner reported .NET SDK `10.0.403` despite installing .NET 8 because the CLI ran from the builder root. Root-level `global.json` now mirrors upstream's 8.0.100/`latestFeature` selection, and CI verifies the selected version. The app publish step performs explicit `win-x64` restore before `--no-restore` publish. The SDK package patch level still follows latest .NET 8 feature release, not a byte-for-byte pinned SDK.

These are authored fixes based on real logs and upstream tests, not a claim that Windows compilation, GUI use, system tweaking or release publication has passed. See `docs/CHANGELOG.md` and `docs/VALIDATION.md`.

## b1r2 fix for November 19 source-patch failure

- Diagnosed uploaded run against exact upstream commit `f5294a682565db62b01994ac12bf630a7f54b0d8`.
- The failure occurred **before compilation**, in `ShellIntegrationService.cs` ownership-sensitive context-menu unregister patch. The previous patch required an exact three-line whitespace layout and did not find it.
- `scripts/apply_portable.py` now matches only that audited three-statement C# sequence with controlled whitespace/blank-line tolerance, verifies **exactly one match**, retains the portable executable ownership check, and refuses changed or ambiguous code.
- `tests/test_shell_patch.py` checks CRLF/blank-line/indentation variants, repeated attempts, unexpected statements, and duplicate anchors.
- The exact upstream commit has **not** been compiled or source-patched in this authoring environment because repository downloads are not available here. The GitHub Actions checkout is still the required verification gate. No runnable Nexus.exe is included in this builder ZIP.

## Workflow design

- `workflow_dispatch` only; no automatic release on unrelated pushes.
- Native-only, single Windows job, concurrency prevention, `contents: write` exclusively because the publisher must create releases.
- Resolve stable semver tag or exact opted-in SHA -> upstream checkout by verified commit -> source patches -> static checks -> .NET 8 upstream Core tests + compiled executable-relative storage probe -> self-contained x64 `dotnet publish` -> scanner `--self-test` -> PE + ZIP checks -> publisher dry-run -> publisher live publish.
- The action tag `@v1.1.1` was inspected in `action.yml` and `scripts/publish.py`; its actual immutable Git commit was **not independently verified** in this authoring environment, so this remains a supply-chain limitation. Do not claim immutable pinning.
- The source has no observed checked-in `packages.lock.json`; the workflow creates restore lockfiles and records their SHA-256 identities in `BUILD-IDENTITY.json`, but does not pre-pin the restored graph but is not a byte-for-byte reproducible NuGet supply-chain lock. `Directory.Build.props` and .NET 8 project versions are verified; transitive NuGet integrity is governed by NuGet HTTPS package hashes. This limitation should be addressed before demanding strict rebuild reproducibility.

### Repository contents

```
.github/workflows/build-native.yml
.gitignore
scripts/resolve_source.py
scripts/apply_portable.py
scripts/validate_source.py
scripts/package_native.py
patches/AutostartService.cs
patches/NativePortableIdentity.cs
tests/test_resolver.py
tests/test_patch_logic.py
tests/test_shell_patch.py
tests/StorageProbe/StorageProbe.csproj
tests/StorageProbe/Program.cs
docs/AUDIT.md
docs/VALIDATION.md
docs/WINDOWS-ACCEPTANCE.md
docs/UPGRADE-ROLLBACK.md
README.md
```


## b1r5: Windows first-run corrections

- The Processes context menu now has an explicit dark popup/submenu template and binds commands to `ListView.DataContext` via `PlacementTarget`.
- Right-clicking selects the row under the mouse before a process action is invoked.
- Autostart task detection enumerates registered root tasks instead of calling `GetTask` for a task that normally does not exist on first run. 0x80070002 can no longer block the first enable via that lookup.
- Task names, action path, ownership description and recorded path protections remain enforced.
- Rebuild Nexus from the same selected upstream commit; replace only binaries/resources and retain existing `Data/`.

**Runtime limitation:** this kit was statically validated offline, not compiled on Windows. The next GitHub Actions run and manual Windows tests are required to confirm popup commands and actual autostart creation.


## b1r6: process right-click menu visual correction (2026-11-19)

A user screenshot of the successful b1r5 Windows build shows the context menu is
readable and submenus render correctly, but the light/white system-theme icon
gutter overlays the first characters of some commands. b1r5 provided only a
MenuItem template; the outer ContextMenu retained its system-theme template.

This patch adds an instance-scoped `ContextMenu.Template` with a dark
`Border` and `ItemsPresenter`; it removes the default icon-gutter without
changing command bindings, row selection, autostart logic, native data handling,
or package format. The separate submenu template remains in place.

Regression tests check XML shape, instance scoping, command retention and
existing autostart safeguards. **This revision has not yet been compiled or
visually tested on Windows.** The previously reported b1r5 startup success
is not evidence that b1r6's cosmetic change is rendered correctly.
