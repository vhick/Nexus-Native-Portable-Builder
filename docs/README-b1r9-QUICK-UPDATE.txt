NEXUS NATIVE PORTABLE BUILDER — b1r9 UI Inventory / Coverage Guard

WHAT'S NEW
- Scans every .xaml and .cs file in upstream src/Nexus.App, not only MainWindow.xaml.
- Reports ListViews, ListBoxes, ItemsControls, ComboBoxes, menus, tabs and custom XAML elements.
- Fails safely if a new selectable list might inherit the wrong shared row template.
- Records static source / patched inventories in native ZIP: AUDITS/upstream.md,
  AUDITS/upstream.json, AUDITS/patched.md, AUDITS/patched.json.
- Adds Actions run summary and report hashes in BUILD-IDENTITY.json.
- Keeps b1r8 UI changes and all b1r7 user-confirmed working features intact.
- Does NOT modify or auto-theme new ItemsControls, ComboBoxes, custom panels.

INSTALL
1. Extract ALL files from this ZIP into your existing builder repository root.
2. Overwrite previous builder files, including .github/workflows/build-native.yml.
3. GitHub Desktop summary: Add full-app Nexus XAML inventory guard b1r9
   Description: Audit all Nexus XAML and dynamic UI declarations, fail closed
   on new selectable controls, ship source/patch inventory reports, preserve
   b1r8 shared dark list styles and b1r7 Processes functionality.
4. Commit and Push origin. GitHub > Actions > Nexus Native Portable > Run workflow.
5. upstream_version: f5294a682565db62b01994ac12bf630a7f54b0d8
6. allow_untagged: true
7. package_revision: r9
8. On success, download the new native ZIP from Releases and inspect AUDITS/.
9. Exit Nexus through system tray, back up full existing application/Data, replace
   binary/resources only. NEVER delete or overwrite the existing Data folder.

VALIDATION
61 controlled Python/fixture regression tests passed in the authoring environment.
No new b1r9 Windows compilation or visual acceptance was performed here.
Last user-confirmed fully working baseline: b1r7. b1r8/b1r9 require Windows testing.
Full details: docs/XAML-INVENTORY.md and docs/WINDOWS-ACCEPTANCE.md.
