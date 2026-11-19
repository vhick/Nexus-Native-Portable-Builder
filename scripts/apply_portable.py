#!/usr/bin/env python3
"""Application-specific, fail-closed SOURCE changes to upstream Nexus. No wrapper/harvesting."""
from pathlib import Path
import argparse, re, sys

AUDITED_ANCHOR='Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "Nexus")'
PORTABLE_ANCHOR='Path.Combine(AppContext.BaseDirectory, "Data")'

def change(path,old,new,expected=1):
    src=path.read_text(encoding='utf-8-sig')
    found=src.count(old)
    if found==0 and new in src:
        raise RuntimeError(f'Already patched? refusing ambiguous input: {path}')
    if found!=expected:raise RuntimeError(f'{path}: expected {expected} occurrences of {old!r}, got {found}. Review upstream before changing.')
    path.write_text(src.replace(old,new),encoding='utf-8',newline='\n')

def apply(root):
    core=root/'src/Nexus.Core/Persistence/NexusPaths.cs'
    change(core,AUDITED_ANCHOR,PORTABLE_ANCHOR)
    change(core,'(%APPDATA%\\Nexus in production, a temp dir in tests)', '(Data beside Nexus.exe in native portable, a temp dir in tests)')
    # Separate portable-instance mutex and scan IPC from an installed upstream copy.
    identity=root/'src/Nexus.App/Services/NativePortableIdentity.cs'
    if identity.exists(): raise RuntimeError('Upstream already defines NativePortableIdentity; review collision risk')
    identity.write_bytes((Path(__file__).resolve().parent.parent/'patches/NativePortableIdentity.cs').read_bytes())
    main=root/'src/Nexus.App/App.xaml.cs'
    change(main,'@"Global\\NexusOptimizerSingleInstance"', '$@"Global\\Nexus.NativePortable.{NativePortableIdentity.Suffix}"')
    pipe=root/'src/Nexus.App/Services/ScanRequestChannel.cs'
    change(pipe,'$"Nexus.ScanRequest.{Environment.UserName}"', '$"Nexus.NativePortable.ScanRequest.{Environment.UserName}.{NativePortableIdentity.Suffix}"')
    app=root/'src/Nexus.App/Services/AutostartService.cs'
    if 'private const string TaskName = "Nexus Optimizer";' not in app.read_text(encoding='utf-8-sig'):
        raise RuntimeError('AutostartService changed upstream; refuse to overwrite until reviewed')
    # Version-specific replacement. Reviewed interface retained: IsEnabled/SetEnabled.
    app.write_bytes((Path(__file__).resolve().parent.parent/'patches/AutostartService.cs').read_bytes())
    settings=root/'src/Nexus.Core/Models/AppSettings.cs'
    change(settings,'public bool RansomwareWatch { get; set; } = true;',
                    'public bool RansomwareWatch { get; set; } = false; // Portable: canaries require explicit opt-in')
    # Class is left available and enabled by Settings: tradeoff explicitly documented.
    shell=root/'src/Nexus.App/Services/Security/ShellIntegrationService.cs'
    change(shell,'private const string KeyName = "Nexus.ScanWithNexus";',
                'private const string KeyName = "Nexus.NativePortable.ScanWithNexus";')
    # prevent editing existing user shell state, even when identical key already exists
    change(shell,'        try\n        {\n            foreach (var className in Classes)\n            {\n                using var key = Registry.CurrentUser.CreateSubKey(PathFor(className));',
        '''        try
        {
            // Fail closed: never overwrite any existing registration, even of the same name.
            foreach (var className in Classes)
                if (Registry.CurrentUser.OpenSubKey(PathFor(className)) is not null)
                    return "A portable Nexus menu entry already exists. Remove it only from its original Nexus copy.";
            foreach (var className in Classes)
            {
                using var key = Registry.CurrentUser.CreateSubKey(PathFor(className));''')
    change(shell,'                if (shell?.OpenSubKey(KeyName) is null)\n                    continue;\n                shell.DeleteSubKeyTree(KeyName);',
        '''                using var owned = shell?.OpenSubKey(KeyName);
                if (owned is null) continue;
                using var command = owned.OpenSubKey("command");
                if (!string.Equals(command?.GetValue(null) as string,
                    $"\\\"{_executablePath}\\\" --scan \\\"%1\\\"", StringComparison.OrdinalIgnoreCase))
                    continue; // not our exact executable: preserve host owner
                command?.Close();
                owned.Close();
                shell!.DeleteSubKeyTree(KeyName);''')
    # Hard gate: source already has opt-in menu; ensure all three keys must belong to same portable copy.
    change(shell,'                    if (key is null)\n                        return false;',
        '''                    if (key is null) return false;
                    using var command = key.OpenSubKey("command");
                    if (!string.Equals(command?.GetValue(null) as string,
                        $"\\\"{_executablePath}\\\" --scan \\\"%1\\\"", StringComparison.OrdinalIgnoreCase))
                        return false;''')
    # No portability wrapper. No installer. No lifecycle side effects from the kit.
    print('SOURCE PATCHED: NexusPaths, AutostartService, SecurityOptions, ShellIntegrationService, instance mutex, IPC')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('upstream');a=p.parse_args()
    try:apply(Path(a.upstream))
    except Exception as exc:
        print('PATCH FAILED:',exc,file=sys.stderr);sys.exit(1)
