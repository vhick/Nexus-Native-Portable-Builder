#!/usr/bin/env python3
"""Fail-closed checks on the exact Nexus portable source adaptation."""
from pathlib import Path
import argparse,sys,re,json

def check(root):
    p=root/'src/Nexus.Core/Persistence/NexusPaths.cs'
    t=p.read_text(encoding='utf-8')
    assert 'Path.Combine(AppContext.BaseDirectory, "Data")' in t, 'Native data root is not executable-relative'
    assert 'Environment.SpecialFolder.ApplicationData), "Nexus"' not in t, 'Host user profile data root still exists'
    assert 'public string QuarantineDirectory' in t and 'public string RegistryBackupDirectory' in t, 'Upstream storage contract changed'
    s=(root/'src/Nexus.Core/Models/AppSettings.cs').read_text(encoding='utf-8')
    assert 'public bool RansomwareWatch { get; set; } = false;' in s, 'Unconsented canary writes enabled'
    a=(root/'src/Nexus.App/Services/AutostartService.cs').read_text(encoding='utf-8')
    assert 'private static readonly string StateDirectory = Path.Combine(AppContext.BaseDirectory, "Data", "Integrations")' in a
    assert 'Nexus Native Portable-' in a and 'Owned(existing)' in a
    h=(root/'src/Nexus.App/Services/Security/ShellIntegrationService.cs').read_text(encoding='utf-8')
    assert 'Nexus.NativePortable.ScanWithNexus' in h
    assert 'never overwrite any existing registration' in h
    assert 'StringComparison.OrdinalIgnoreCase' in h
    w=(root/'src/Nexus.App/App.xaml.cs').read_text(encoding='utf-8')
    assert 'var paths = NexusPaths.Default();' in w, 'Upstream application composition changed'
    assert 'Global\\Nexus.NativePortable.{NativePortableIdentity.Suffix}' in w, 'Native instance mutex not unique'
    pipe=(root/'src/Nexus.App/Services/ScanRequestChannel.cs').read_text(encoding='utf-8')
    assert 'Nexus.NativePortable.ScanRequest.' in pipe, 'Scan IPC collides with installed Nexus'
    assert (root/'src/Nexus.App/Services/NativePortableIdentity.cs').is_file(), 'Missing in-process identity source' 
    assert 'new ScannerPool(' in w, 'Scanner integration changed'
    csproj=(root/'src/Nexus.App/Nexus.App.csproj').read_text(encoding='utf-8')
    assert '<AssemblyName>Nexus</AssemblyName>' in csproj
    assert 'Nexus.Scanner.exe' in csproj
    # Report possible extra direct absolute path calls; these are not automatically failures:
    # many are intentional read-only system inspection or explicitly consented system actions.
    hits=[]
    for f in sorted((root/'src').rglob('*.cs')):
        rel=f.relative_to(root).as_posix()
        for n,line in enumerate(f.read_text(encoding='utf-8-sig').splitlines(),1):
            if any(w in line for w in ('Environment.SpecialFolder.', 'Registry.CurrentUser.CreateSubKey',
                    'Registry.LocalMachine.CreateSubKey', 'File.WriteAllText(', 'File.Create(',
                    'Directory.CreateDirectory(', 'schtasks', 'File.Move(', 'File.Delete(')):
                hits.append({'file':rel,'line':n,'content':line.strip()[:200]})
    (root/'source-write-audit.json').write_text(json.dumps(hits,indent=2),encoding='utf-8')
    print(f'SOURCE STATIC CHECK PASSED; {len(hits)} source write/path candidates inventoried (not proven runtime-contained)')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('upstream');args=ap.parse_args()
    try:check(Path(args.upstream))
    except Exception as e:print('SOURCE CHECK FAILED:',str(e),file=sys.stderr);sys.exit(1)
