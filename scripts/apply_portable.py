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

def change_checked_pattern(path, pattern, replacement, expected=1):
    """Permit harmless whitespace drift, but require exactly one known C# statement sequence.

    This is intentionally NOT a generic source rewriter: changed control flow or
    extra matching blocks must fail for source review rather than risk host state.
    """
    source = path.read_text(encoding='utf-8-sig')
    matches = list(re.finditer(pattern, source, re.MULTILINE))
    if len(matches) != expected:
        raise RuntimeError(
            f'{path}: expected {expected} matching audited statement sequence(s), '
            f'got {len(matches)}. Review upstream before changing.'
        )
    match = matches[0]
    # Keep replacement indentation aligned to the matched original statement.
    indent = match.group('indent')
    updated = source[:match.start()] + indent + replacement.replace('\n', '\n' + indent) + source[match.end():]
    path.write_text(updated, encoding='utf-8', newline='\n')


UNREGISTER_PATTERN = (
    r'^(?P<indent>[ \t]*)if[ \t]*\([ \t]*shell\?\.OpenSubKey\(KeyName\)[ \t]+is[ \t]+null[ \t]*\)[ \t]*\r?\n'
    r'(?:[ \t]*\r?\n)*[ \t]*continue;[ \t]*\r?\n'
    r'(?:[ \t]*\r?\n)*[ \t]*shell\.DeleteSubKeyTree\(KeyName\);'
)


def patch_shell_unregister(path):
    change_checked_pattern(path, UNREGISTER_PATTERN, """using var owned = shell?.OpenSubKey(KeyName);
if (owned is null) continue;
using var command = owned.OpenSubKey("command");
if (!string.Equals(command?.GetValue(null) as string,
    $"\\\"{_executablePath}\\\" --scan \\\"%1\\\"", StringComparison.OrdinalIgnoreCase))
    continue; // not our exact executable: preserve host owner
command?.Close();
owned.Close();
shell!.DeleteSubKeyTree(KeyName);""")


def patch_portable_security_tests(path):
    """Update one obsolete expectation and test explicit opt-in persistence.

    These are source-level portability changes, not a blanket test exclusion.
    Any upstream test drift must be reviewed instead of silently bypassed.
    """
    source = path.read_text(encoding='utf-8-sig')
    expected = 'Assert.True(settings.Security.RansomwareWatch);'
    if source.count(expected) != 1:
        raise RuntimeError(f'{path}: expected one upstream enabled-by-default expectation; '
                           f'found {source.count(expected)}. Review test contract.')
    # Require original test purpose and the documented defaults to be present.
    if ('A_settings_file_without_the_security_section_still_loads_its_defaults' not in source
            or 'Assert.True(settings.Security.BehaviourMonitoring);' not in source):
        raise RuntimeError(f'{path}: unexpected upstream settings migration test layout')
    # Bind the changed expectation to the ORIGINAL migration test, not a
    # future opt-in test that intentionally expects True.
    migration_pattern = (r'(Assert\.True\(settings\.Security\.BehaviourMonitoring\);\s*)'
                         r'Assert\.True\(settings\.Security\.RansomwareWatch\);')
    matching = list(re.finditer(migration_pattern, source))
    if len(matching) != 1:
        raise RuntimeError(f'{path}: expected one original migration-test assertion pair; found {len(matching)}')
    source = re.sub(migration_pattern,
                    lambda m: m.group(1) + 'Assert.False(settings.Security.RansomwareWatch); // Native portable: opt-in default',
                    source, count=1)
    marker = '    [Fact]\n    public void Sections_that_were_present_are_preserved()'
    if source.count(marker) != 1:
        raise RuntimeError(f'{path}: cannot safely insert opt-in persistence test')
    added = '''    [Fact]
    public void Native_portable_explicit_ransomware_watch_opt_in_is_preserved()
    {
        WriteLegacy("""{ "Security": { "RansomwareWatch": true } }""", "explicit-ransomware-opt-in.json");
        var settings = NewStore("explicit-ransomware-opt-in.json").Load();
        Assert.True(settings.Security.RansomwareWatch);
    }

'''
    source = source.replace(marker, added + marker)
    path.write_text(source, encoding='utf-8', newline='\n')


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
    # This source adaptation intentionally changes the security-module default.
    # Keep the original upgrade test meaningful by reflecting the portable
    # default; add a new test that explicit opt-in is retained across load.
    # Fail closed if the audited upstream test changes. No tests are skipped.
    patch_portable_security_tests(root/'tests/Nexus.Core.Tests/SettingsUpgradeTests.cs')
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
    patch_shell_unregister(shell)
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
