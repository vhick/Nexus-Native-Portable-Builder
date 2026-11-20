NEXUS NATIVE PORTABLE — b1r10 HEADER-HOVER UI UPDATE
===================================================

Fixes: near-white mouse-hover backgrounds on table column HEADINGS
(e.g. Process, Rating, Command/path, Class, Message).
Previous list-row hover and right-click fixes remain unchanged.

1. Exit Nexus fully from its tray. Make a backup of the existing native app
   folder, especially Data. The b1r9/b1r7 backups are your rollback options.
2. Extract this BUILDER ZIP into your existing separate GitHub Desktop
   Nexus-Native-Portable-Builder repository, including .github.
3. Commit and push the changes.
4. GitHub > Actions > Nexus Native Portable - Source Build and Release > Run.
5. upstream_version: f5294a682565db62b01994ac12bf630a7f54b0d8
   allow_untagged: true
   package_revision: r10
6. On a successful Release, extract the built native ZIP, preserving the
   existing Data directory. Test table header hover and column width resizing
   on all five sections. Do not assume CI proved the GUI behavior.

GitHub Desktop summary:
Fix Nexus GridView column header hover b1r10

Description:
Add a shared dark GridViewColumnHeader template for all five table lists,
fix bright heading hover/pressed states, retain column resizing and existing
row/menu/command behavior, add fail-closed audits and regression tests.

Status: LOCAL STATIC CHECKS ONLY until Windows workflow and GUI verified.
