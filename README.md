# Nexus NATIVE Portable Builder Kit (Windows x64) — b1r1

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
4. In GitHub Desktop, review changes. For the Summary enter `Add Nexus native portable source builder b1r1`. Suggested Description: `Add fail-closed source resolver, portable Data source patch, opt-in Windows integration protections, x64 .NET 8 workflow, scanner smoke checks, ZIP checksums, and pinned release publisher.` Click **Commit to main**, then **Push origin**.
5. On GitHub open your **builder** repository > **Actions** > **Nexus Native Portable - Source Build and Release** > **Run workflow**.
6. First try an empty upstream version (only works if upstream has a stable tag). If it fails with **no stable tag**, enter a verified 40-character upstream commit SHA and tick **allow_untagged** to authorize a development build.
7. Leave revision `r1` unless packaging changes. Inspect **Actions > latest workflow run > steps**. The source patch step deliberately stops on upstream incompatibility. When everything passes, open **Releases** in your builder repository to find the `Nexus-NativePortable-...zip` and publisher-generated `SHA256SUMS.txt`.
8. Download the ZIP. Check its SHA-256 against `SHA256SUMS.txt` with Windows PowerShell: `Get-FileHash '.\your-file.zip' -Algorithm SHA256`.
9. Extract into your own user-writable folder, e.g. `D:\Portable\Nexus-NativePortable\`; run `Nexus.exe` directly, accepting the normal administrator UAC prompt. **Do not run it from inside the ZIP.** Do not delete `Nexus.Scanner.exe` or `assets`.
10. Settings, rules, logs, backups, quarantine, crash journals, autostart metadata and security history live in `Data` beside Nexus.exe. **Never delete Data during update/reinstall.** Exit Nexus using the tray menu before replacing binaries. Keep a backup of `Data` and the previous full folder so you can roll back, subject to schema and Windows-state limitations.

## Output

One native package ZIP with top directory `Nexus-NativePortable-{source-version}-{sourceSHA12}-{revision}` containing `Nexus.exe`, `Nexus.Scanner.exe`, `assets/`, `Data/`, `LICENSES/`, `README.txt`, and `BUILD-IDENTITY.json`. The publisher adds `SHA256SUMS.txt` to its GitHub Release. Releases use `nexus-native-{version}-{sourceSHA12}-{builderSHA8}-{revision}`. No PortableApps-format deliverables exist.

## Evidence, acceptance and known limitations

See [AUDIT.md](docs/AUDIT.md), [VALIDATION.md](docs/VALIDATION.md), [WINDOWS-ACCEPTANCE.md](docs/WINDOWS-ACCEPTANCE.md), and [UPGRADE-ROLLBACK.md](docs/UPGRADE-ROLLBACK.md). The kit's local Python checks validate script syntax, resolver cases and source/ZIP contracts; **they do not prove the EXE compiled**. The Windows runner compiles and exercises only the scanner worker; full elevated Nexus GUI/tray, registry, app-owned storage containment, autostart and power settings require a real manual Windows test. This kit has **not been compiled or runtime-tested** as delivered here.

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
tests/StorageProbe/StorageProbe.csproj
tests/StorageProbe/Program.cs
docs/AUDIT.md
docs/VALIDATION.md
docs/WINDOWS-ACCEPTANCE.md
docs/UPGRADE-ROLLBACK.md
README.md
```
