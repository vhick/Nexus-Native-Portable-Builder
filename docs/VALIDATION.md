# Verification matrix — b1r2

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
