#!/usr/bin/env python3
"""Stage verified Nexus source-published binaries, preserving empty Data dirs; zip independently."""
from pathlib import Path
import argparse, hashlib, json, os, re, shutil, struct, sys, zipfile, subprocess

def pe_machine(p):
    with p.open('rb') as f:
        if f.read(2)!=b'MZ':raise ValueError(f'Not a PE executable: {p.name}')
        f.seek(0x3C); off=struct.unpack('<I',f.read(4))[0]
        if off<64 or off>=p.stat().st_size-6:raise ValueError(f'Bad PE offset: {p.name}')
        f.seek(off)
        if f.read(4)!=b'PE\0\0':raise ValueError(f'Bad PE header: {p.name}')
        return struct.unpack('<H',f.read(2))[0]

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def stage(source, out, upstream_root, version, commit, builder_sha, revision, source_kind):
    for name in ['Nexus.exe','Nexus.Scanner.exe']:
        p=source/name
        if not p.is_file() or p.stat().st_size<1024:raise ValueError('Missing substantive published binary: '+name)
        if pe_machine(p)!=0x8664:raise ValueError('Expected Windows x64 binary for '+name)
    if not (source/'assets/patterns.txt').is_file():
        raise ValueError('Sentinel detection asset is missing')
    if not revision or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]{0,25}',revision):raise ValueError('Invalid revision')
    name=f'Nexus-NativePortable-{version}-{commit[:12]}-{revision}'
    if not re.fullmatch('[A-Za-z0-9_.-]+',name):raise ValueError('Invalid package name')
    root=out/name
    if root.exists():raise ValueError('Staging exists; refusing to overwrite persistent data')
    root.mkdir(parents=True)
    for item in source.iterdir():
        if item.is_dir():shutil.copytree(item,root/item.name,symlinks=False)
        else:shutil.copy2(item,root/item.name)
    license_dir=root/"LICENSES"
    license_dir.mkdir(exist_ok=True)
    for original in ["LICENSE", "NOTICE.md"]:
        src=upstream_root/original
        if not src.is_file():raise ValueError("Missing upstream attribution: "+original)
        shutil.copy2(src,license_dir/original)
    # Always create portable dirs before user starts application.
    for d in ['Data','Data/logs','Data/backups/registry','Data/security','Data/quarantine','Data/Integrations']:
        (root/d).mkdir(parents=True,exist_ok=True)
    info={'upstream_repo':'https://github.com/0xmortuex/Nexus',
          'source_ref':version,'source_commit':commit,'source_type':source_kind,
          'builder_commit':builder_sha,'package_revision':revision,
          'nuget_lockfiles':{p.relative_to(upstream_root).as_posix():sha(p) for p in sorted(upstream_root.rglob('packages.lock.json'))},
          'dotnet_sdk':subprocess.check_output(['dotnet','--version'],text=True,encoding='utf-8').strip(),
          'entry_point':'Nexus.exe','data_root':'Data/','mode':'NATIVE',
          'checksums':{'Nexus.exe':sha(root/'Nexus.exe'),'Nexus.Scanner.exe':sha(root/'Nexus.Scanner.exe')}}
    (root/'BUILD-IDENTITY.json').write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8')
    (root/'README.txt').write_text(
        'Nexus NATIVE Portable (x64)\n\nRun Nexus.exe directly as Administrator. Windows UAC is expected.\n'
        'All NexusPaths settings, logs, backups, and security journals are in Data beside Nexus.exe.\n'
        'IMPORTANT: Per-process and system optimization intentionally affect the host while enabled.\n'
        'Optional opt-in Windows actions: autostart task, context menu, power plans, tweaks, Game Mode,\n'
        'ransomware tripwires (off by default in this portable build). Disable/undo before moving\n'
        'the folder to another PC. Keep Data when upgrading. Do not delete quarantine or backups.\n'
        'Closing the window minimizes to tray. Exit from tray before upgrading or relocating.\n'
        'The scanner Nexus.Scanner.exe and assets folder MUST remain beside Nexus.exe.\n'
        'The portable binary is not guaranteed to be code-signed; keep Windows Defender enabled.\n'
        'Interactive GUI, device-specific host behavior, and full storage containment require manual testing.\n',encoding='utf-8')
    # Preserve full attribution and upstream licensing from checked-out source files (added by caller)
    zip_path=out/(name+'.zip')
    with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for item in sorted(root.rglob('*')):
            rel=item.relative_to(out).as_posix()
            if item.is_dir():z.writestr(rel+'/',b'')
            elif item.is_file():z.write(item,arcname=rel)
            else:raise ValueError('Unsupported symlink or unexpected item '+str(item))
    with zipfile.ZipFile(zip_path) as z:
        bad=z.testzip()
        if bad:raise ValueError('Corrupt zip entry: '+bad)
        names=set(z.namelist()); prefix=name+'/'
        for req in ['Nexus.exe','Nexus.Scanner.exe','assets/patterns.txt','Data/','Data/quarantine/','BUILD-IDENTITY.json','README.txt','LICENSES/LICENSE','LICENSES/NOTICE.md']:
            if prefix+req not in names:raise ValueError('Missing zip entry '+req)
        if any(x.endswith('AppNamePortable.exe') or x.endswith('appinfo.ini') for x in names):
            raise ValueError('PortableApps contamination in NATIVE package')
    checksum=sha(zip_path)
    (out/'Nexus-Native-SHA256SUMS.txt').write_text(f'{checksum}  {zip_path.name}\n',encoding='utf-8')
    print(json.dumps({'zip':zip_path.as_posix(),'sha256':checksum,'identity':info},indent=2))
    return zip_path

if __name__=='__main__':
    a=argparse.ArgumentParser()
    for field in ['publish_dir','output_dir','upstream_root','version','commit','builder_sha','revision','source_kind']:
        a.add_argument('--'+field.replace('_','-'),required=True)
    args=a.parse_args()
    try:
        stage(Path(args.publish_dir),Path(args.output_dir),Path(args.upstream_root),args.version,args.commit,args.builder_sha,args.revision,args.source_kind)
    except Exception as e:print('PACKAGE FAILED:',e,file=sys.stderr);sys.exit(1)
