# b1r9 — Application-wide Nexus XAML and list-style inventory

## What changed

New `scripts/audit_xaml_controls.py` scans **every `.xaml` file** and source `.cs` file under the checked-out upstream `src/Nexus.App` tree, including nested views, dialogs and resource dictionaries. It does not modify any source code or restyle additional controls.

The inventory uses only Python's standard library and runs twice in GitHub Actions:

1. **upstream:** after SHA-verified checkout and **before** applying native portability patches, the original source controls are inventoried; unknown selectable lists fail the build.
2. **patched:** after the working b1r8 dark-list styles and other portability adaptations have been applied, the same full scan checks that source selectors remain safe and theme markers are present.

The reports contain file and line, control type, `ItemsSource` binding where present, known style state, inline item-template status, and number of interactive button/checkbox/textbox cells. The script additionally reports custom XML namespace elements and C# dynamic UI creation/loading patterns for manual review.

## Coverage / fail-closed policy

The six selected controls previously source-inspected in `MainWindow.xaml` at upstream commit `f5294a682565db62b01994ac12bf630a7f54b0d8` are:

- `ListView`: `Processes`, `Games`, `StartupEntries`, `Devices`, `Entries` (all `GridView`-backed)
- `ListBox`: `Restrained`

A new `ListView`, `ListBox`, `DataGrid`, or `TreeView` anywhere in the XAML tree, duplicate known selector, unexpected binding, list without a compatible `GridView`, or a selectable list inside a template is an **automatic build blocker**. These controls must be reviewed before expanding the application-wide row template. This is deliberate: the b1r8 shared `ListViewItem` template uses a `GridViewRowPresenter` and cannot be presumed suitable for every possible future list.

`ItemsControl` often displays cards, labels, or checkboxes and does not have the built-in selectable row behavior of `ListView`. `ComboBox`, `ContextMenu`, `MenuItem`, `TabControl`, custom controls and C#-created interfaces are **reported**, not blindly patched. The inventory makes those surfaces discoverable; it does not promise dark hover appearance without real Windows testing.

The working b1r7 Processes-specific row template remains unchanged. The b1r8 shared dark hover/selection templates remain unchanged. **b1r9 changes only validation, workflow reporting, documentation, and package provenance.**

## How to read your report

On a successful GitHub Actions run, find these files inside the resulting **native** release ZIP, in the `AUDITS/` directory:

- `upstream.json` and `upstream.md`: source control inventory before modification
- `patched.json` and `patched.md`: source control inventory after modification

`BUILD-IDENTITY.json` includes their SHA-256 checksums. On failed runs, open the Actions step `Assert source identity and apply audited in-process portability patches` and check the `BLOCKER` messages. The always-run summary step shows counts and blockers on the GitHub Actions run's Summary page. No separate uploaded intermediate artifact or paid service is required.

Manual local diagnostic command (after downloading or checking out the actual upstream source):

```powershell
python scripts/audit_xaml_controls.py upstream --phase upstream --output-dir ui-audit
```

The optional `--no-enforce` is for troubleshooting/reporting only. The published workflow always **enforces** its selectors.

## What this does NOT verify

- A headless XAML XML parse **cannot** prove actual WPF rendering or mouse-hover text contrast.
- Runtime-generated controls, external libraries, Windows popup templates and dynamic content can escape simple static analysis. The C# scan is deliberately a source-pattern heuristic, not a complete runtime UI tree.
- The script does not certify that every `ItemsControl` card, `ComboBox` dropdown, context menu, nested checkbox or other custom control is dark or legible.
- Interactive Windows testing at 100%/150% DPI, mouse and keyboard selection, log scrolling, game controls, device fields and existing process menus remains required, as does native data containment testing.

This is an **automated application-wide source inventory**, not an automatic guarantee of application-wide visual correctness.
