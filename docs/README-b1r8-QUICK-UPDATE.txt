NEXUS NATIVE PORTABLE BUILDER b1r8 - QUICK UPDATE
================================================
1. In GitHub Desktop, open your separate Nexus builder repository.
2. Extract this entire b1r8 kit into the repository root, including .github.
3. Commit: Fix Nexus shared list hover contrast b1r8
4. Push origin.
5. GitHub Actions > Nexus Native Portable - Source Build and Release > Run workflow.
   upstream_version: f5294a682565db62b01994ac12bf630a7f54b0d8
   allow_untagged: checked (this is a development source, not stable release)
   package_revision: r8
6. If compilation, tests and release succeed, get the native application ZIP
   from YOUR builder repository's Releases (not the upstream project's Releases).
7. Close Nexus completely via the tray. Back up the entire existing b1r7
   folder and Data. Replace ONLY application binaries/resources, never Data.
8. Test mouse hover in Processes, Game Mode, Tweaks Startup Manager, MSI Devices
   and Logs. Confirm checkboxes and buttons still work on harmless test entries.
9. If any issue occurs, exit Nexus and restore b1r7 binaries; preserve Data.

What changed: Shared Dark.xaml ListViewItem / ListBoxItem row templates only.
What was preserved: Native Data, scanner, processes, autostart, shell protections,
release workflow, and b1r7 Processes context menu/row template.

NOT VERIFIED: b1r8 Windows compile and GUI mouse/keyboard behavior.
42 local Python fixture tests and ZIP integrity checks passed.
