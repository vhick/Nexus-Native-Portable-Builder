# Real Windows 10/11 x64 acceptance checklist (manual, supervised)

Perform on a disposable test VM or a machine with current backup and restore point. Nexus is an **administrator-level optimizer**; a successful compilation is not permission to enable all system tweaks. Test on a nonproduction account before a primary PC. Keep Windows Defender running.

1. Extract package to a **writable non-system** directory with Unicode and spaces, e.g. `D:\Portable Tests\Néxus Test\`. Confirm `Nexus.exe`, `Nexus.Scanner.exe`, `assets/`, empty `Data/`.
2. Launch `Nexus.exe` directly from File Explorer (no CMD/PowerShell wrapper), accept the expected UAC request. Confirm the WPF UI, correct tabs, tray icon and full Exit from tray. Close window separately and confirm it minimizes instead of terminating if upstream default still applies.
3. Change at least three settings, create a safe test per-process rule and a Game Mode profile. Exit from tray. Verify Data/settings.json, Data/rules.json, Data/games.json and Data/logs appear and retain changes after direct restart. Restart from a DIFFERENT working directory and user-writable path.
4. With Sysinternals Process Monitor or controlled before/after snapshots, filter by `Nexus.exe`, `Nexus.Scanner.exe`, any child process and registry operations. Record any **application-owned** writes under `%APPDATA%`, `%LOCALAPPDATA%`, `%PROGRAMDATA%`, `%TEMP%`, Desktop/Documents, Start Menu, task history, etc. Distinguish read-only access, OS-managed caches and explicitly opted-in host integration from unexplained persistence. Any unexpected app-owned write must block portable acceptance.
5. Run scanner's `--self-test`, then a benign disposable sample or upstream's documented test sample. Verify scanning reports real engine availability; no unbundled third-party YARA DLL required.
6. Keep ransomware watch OFF and confirm no fresh `___nexus-do-not-delete.*` files appear in Documents/Pictures/Videos/Music/Desktop. If you choose to test opt-in: first snapshot these folders, enable watch, confirm canaries, then disable/restore with upstream UI; inspect exactly which files were removed. **Do not test the reset blindly on a valuable folder**; upstream canary cleanup matches the filename prefix, not a full ownership manifest.
7. Opt-in context menu on the disposable profile. Verify `HKCU\Software\Classes\*\shell\Nexus.NativePortable.ScanWithNexus`, Directory and Drive are created only on request. Verify right-click scan opens Nexus UI, works when Nexus already running. Disable and verify only those three exact owned entries are removed. Create a pre-existing same-name test key (in a disposable profile), ensure registration refuses overwrite and removal preserves it.
8. Opt-in user login autostart on a test account. Confirm Task Scheduler task name `Nexus Native Portable-<id>`, exact path including Unicode/spaces, logon action, privilege level, no overwrite of `Nexus Optimizer`. Log out/in, disable and verify task removal. Relocate folder **only after disabling**, then enable again to exercise new path. Also test stale path behavior and safe failure. Note potential Task Scheduler OEM/Unicode XML encoding limitation.
9. Exercise only reversible controlled process rules with a disposable test app, never protected processes or security agents. Verify CPU affinity, restraint and restoration on exit. Test Game Mode entry/exit, chosen power plan restoration, and crash recovery with a rollback plan. Check any cloned plan GUID before deletion; never delete an unowned power plan.
10. Test resume, DPI scaling, monitor hotplug and Explorer restart; ensure tray reappears, no duplicated long-lived background process, no bad window focus. Verify no single-instance race after a second double-click.
11. Stop Nexus and scanner fully. Move the complete portable folder between two test drives, run directly again and confirm Data retention. Confirm any stored host-specific paths and quarantine records are handled without silently changing a second PC's host settings.
12. Upgrade: save Data backup, overwrite binaries/assets from newly extracted release **without deleting Data**. Restart, verify settings. Roll back only if new schema still works with previous binary; preserve a separate complete backup. Verify same-name installed Nexus (if present) maintains distinct profiles and registry integrations. If not, document incompatibility.

**Capture evidence:** before/after filesystem listing, ProcMon PML/CSV, registry export of affected keys, Task Scheduler task XML, screenshots of settings and tray, checksums of package, and Windows version/build. Mark each row passed/failed with actual date and application version. Do not mark MANUAL-WINDOWS-TESTED until the actions above were truly performed.

## b1r5 Windows acceptance: Process context menu and autostart

**Preparation:** Exit Nexus through its tray menu (closing the window only minimizes it). Back up the existing `Data` folder, then extract the new native build into the same directory while preserving Data.

1. In Processes, right-click a **non-protected ordinary user program** (not Nexus, csrss, winlogon, security software, or other protected system processes). Verify a dark popup and dark submenu with readable text and a visible highlight.
2. Right-click two different rows and confirm the newly right-clicked row becomes selected. Test one reversible action (for example, set a noncritical test program's priority to Above normal, then restore Normal). Check that the log identifies the correct process.
3. Before opting in to autostart, visit Settings and verify the status check does **not** issue `Cannot check owned task: ... (0x80070002)` on a computer with no existing owned portable task.
4. Opt in to Start with Windows. Verify success without an overwrite prompt, then inspect Task Scheduler: the root task name must start with `Nexus Native Portable-`, its executable action must point to this specific native Nexus.exe and run level is highest available.
5. Reopen Nexus and verify the checkbox accurately reflects the owned task. Disable autostart and confirm that **only** the owned task is removed. Existing installed Nexus or other entries must be untouched.
6. Re-enable, move the portable folder, and confirm a stale task is **not** silently redirected or overwritten. Return to the original folder to disable the recorded entry, then opt in again from the new folder only if desired.
7. Test restart and actual Windows login with the machine's normal UAC policy. Record whether the elevated app starts. Do not assume an unattended Actions test proves interactive login behavior.

If autostart still fails, capture the full Nexus log and **the `schtasks.exe` stderr shown in its Autostart warnings**, plus whether Windows Task Scheduler can list its root tasks. Do not delete third-party scheduled tasks as a workaround.


### b1r6 Processes menu acceptance

1. Right-click a regular user application row (for example Notepad). The parent popup must be completely dark, with **no white gutter** over the first letters.
2. Move across every item and its submenu. Text, arrows, separators and highlights remain readable and do not clip at 100% and 150% DPI.
3. Verify keyboard navigation (arrows, Enter, Escape) and click outside to dismiss.
4. Confirm a harmless priority action can be applied/reverted to an ordinary test process (do not test on Windows system processes).
5. Verify autostart status and login separately; b1r6 intentionally does not modify autostart code.


### b1r7 Processes hover and selection acceptance

1. Run the rebuilt native `Nexus.exe` on Windows 10/11. Open **Processes** in Advanced mode.
2. Move the pointer over several *unselected* rows: background should be muted dark blue-gray (`#FF2C374B`) and all process names/numbers should remain light and readable; no white bands.
3. Click a row: selected background should be a distinct darker blue (`#FF354664`). Hover it: selected+hover shade (`#FF405878`) should remain readable. Move the pointer away and confirm selection persists.
4. Navigate the list with keyboard arrow keys and verify focus highlight, column alignment, scrolling and virtualization on a long list.
5. Right-click a safe noncritical user process (e.g., Notepad); selected process must match right-clicked row and the b1r6 dark menu and submenu must still work. Test a reversible action and restore it.
6. Repeat at 100% and 150% DPI; check no row-height/layout regressions. Leave autostart and any unsafe system tweaks untouched unless testing them separately.

Source-validation, unit tests and XAML XML checks do NOT prove WPF compilation or Windows appearance.


### b1r8 all-category hover and interactive-cell acceptance

Before upgrading, close Nexus from its tray, make a copy of the last working **b1r7 full folder and Data**, and do not delete Data on upgrade. Extract new build app files over the application binaries/resources only. Do not change power plans or IRQ settings merely to test appearance.

1. **Processes:** confirm b1r7 dark hover, selected row, menus and commands remain unchanged; do not test on protected system processes.
2. **Game Mode:** hover saved games; rows must stay dark with readable game name/rating/checkbox labels. Verify all existing checkboxes still toggle, and Remove button is clickable (prefer a harmless dummy test entry).
3. **Tweaks → Startup Manager:** hover Task Scheduler entries, including those with long command paths; labels must stay readable. Do not toggle or disable Windows-critical startup tasks; use a safe test task if checking interaction.
4. **Latency & Hardware → Interrupt tuning:** hover device rows. Device names, state and checkbox should remain readable. Verify the Pin IRQ text field accepts typing and Set remains interactive **without applying an unsafe new IRQ configuration**.
5. **Log:** hover and select lines; the Time/Level/Category/Message cells must remain readable. Check filter typing, scrolling and long histories.
6. **Dashboard:** if Currently restrained has entries, hover rows. Text and row alignment must remain readable. The ListBox uses a separate ContentPresenter so its DataTemplate must still display.
7. Test normal, selected, selected+hover, focus and disabled appearances where available; repeat at 100% and 150% Windows display scaling.
8. Confirm application saves settings/logs under `Data` beside the running `Nexus.exe`. Confirm opt-in startup and other host integrations only if you already use them; never infer safety from successful compilation alone.
9. If any interactive control or list fails, **exit through tray and restore the backed-up b1r7 binaries with original Data preserved**, then attach build logs/screenshots.

These manual checks have NOT been performed for b1r8 by the kit author.


### b1r9 source inventory and cross-application visual acceptance

1. After successful GitHub Actions build, open `AUDITS/upstream.md` and `AUDITS/patched.md` from the native ZIP. Verify every XAML file appears, not only MainWindow. Confirm no selectable-layout blockers and review recorded `ItemsControl`, `ComboBox`, custom namespace and dynamic-C# candidates.
2. On a disposable Windows test account, open **every Nexus section and settings dialog**, checking selectable lists, repeated cards, dropdowns, menus and contextual popups for legible hover, selected, disabled and keyboard-focused states. Focus on Game Mode, Tweaks/Startup Manager, Latency & Hardware devices and Logs.
3. Test 100% and 150% scaling, keyboard arrow/Tab/Enter and mouse input. For fields within rows, verify controls remain editable without applying risky system modifications. Check list sorting/filtering and long list scrolling.
4. If any new or third-party UI is created dynamically, it is *not* proven by the static inventory. Inspect it manually and document its observed results before marking MANUAL-WINDOWS-TESTED.
5. Ensure that native `Nexus.exe` still starts directly, owned data remains under `Data/`, and previous b1r7 Processes menu and autostart behavior are not regressed. This b1r9 audit does not add any OS integration.

The audit's clean output cannot replace actual screenshots and Windows runtime acceptance.
