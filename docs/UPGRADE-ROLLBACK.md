# Native upgrade, rollback and host-recovery guide

## Safe upgrade

1. In Nexus, stop Game Mode and restore power/tweaks that should not remain on this Windows installation. Do not assume quitting automatically undoes every user-applied permanent tweak.
2. Use tray **Exit** and ensure no Nexus.exe/Nexus.Scanner.exe processes remain. Never update a running optimizer.
3. Make two backups: (a) copy of entire extracted Nexus portable folder, including `Data` and nested empty directories; (b) an independent `Data` backup in another folder. Do not merge with an installed Nexus AppData profile by name.
4. Download a newer released NATIVE ZIP; verify its SHA256 with the publisher Release `SHA256SUMS.txt` and check its identity file for upstream commit and builder revision.
5. Extract the new ZIP into a DIFFERENT temporary directory. Copy new `Nexus.exe`, `Nexus.Scanner.exe`, and `assets/` into the existing portable folder after backing up existing binaries. Do **not** overwrite `Data/`, security quarantine, logs, registry backups, journal files, autostart identity, or user-specific files. Keep LICENSES and README updated separately.
6. Launch `Nexus.exe` directly, inspect log and settings. Review any data schema changes. Do not assume older builds can read newer settings or recovery journals.

## Safe rollback

1. Exit Nexus from tray; confirm all scanner/optimizer processes stopped.
2. Retain newest Data as evidence; do not overwrite a changed schema with an older default. Restore pre-upgrade full backup only after reviewing any system changes made since backup.
3. Replace application binaries/assets with the last known-good release. Use the Data backup that matches the old binary if needed. Do not silently restore an old Game Mode or power-plan journal to a different Windows state.
4. Compare task ownership and context menu target with the actual running portable location. Disable/repair only through the user-approved integrations. Do not delete conventional `Nexus Optimizer` task (it may belong to the installed application).
5. If quarantine contains held files, restore them using the corresponding journal and user consent. **Never delete Data/quarantine independently of its journal.**

## Moving drives, computers or accounts

The Data path is relative to executable and moves with the folder. Windows settings, scheduled tasks, registered context-menu paths, power plan GUIDs, network and process state are **host-specific**. Before relocation: disable optional task and context menu; undo applied OS tweaks and restore prior power plan. Canary files in user document folders require deliberate cleanup. If registry/task state cannot be verified after a move, preserve it and perform manual recovery with backup evidence; do not delete foreign entries based only on name.

## Crash handling

Upstream's intended-state journal is retained under `Data/intended-state.json` for Game Mode crash recovery on the same machine. Security quarantine journal and files are retained. A missing or corrupt Data file must not trigger package reset/cleanup; preserve it for forensic recovery. A forced termination may leave host process/power state modified, so restart on the **same machine** to exercise documented upstream recovery before relocating.
