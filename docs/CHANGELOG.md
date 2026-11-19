# Nexus Native Builder revisions

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
