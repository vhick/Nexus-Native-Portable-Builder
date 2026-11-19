#!/usr/bin/env python3
"""Resolve 0xmortuex/Nexus to a stable official tag or an explicitly opted-in SHA.
Does not build untagged main on its own. Stdlib only; GitHub API failures are fatal.
"""
from __future__ import annotations
import argparse, json, os, re, sys, urllib.error, urllib.request

REPO='0xmortuex/Nexus'
API=f'https://api.github.com/repos/{REPO}'
SEMVER=re.compile(r'^v?(\d+)\.(\d+)\.(\d+)$')
SHA=re.compile(r'^[a-fA-F0-9]{40}$')
UA='Nexus-Native-Builder/1.0 (GitHub Actions)'

def get(path, *, missing_ok=False):
    headers={'Accept':'application/vnd.github+json','User-Agent':UA,'X-GitHub-Api-Version':'2022-11-28'}
    token=os.environ.get('GH_TOKEN','').strip()
    if token: headers['Authorization']=f'Bearer {token}'
    req=urllib.request.Request(API+path,headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code==404 and missing_ok: return None
        raise RuntimeError(f'GitHub API {path} HTTP {e.code}: {e.read(600).decode("utf-8","replace")}') from e

def stable(version):
    match=SEMVER.fullmatch(version)
    return tuple(map(int, match.groups())) if match else None

def resolve(requested, allow_untagged):
    if requested and SHA.fullmatch(requested):
        if not allow_untagged:
            raise RuntimeError('An untagged commit SHA requires allow_untagged=true. Never silently build main.')
        commit=get('/commits/'+requested)
        sha=commit.get('sha','').lower()
        if sha!=requested.lower(): raise RuntimeError('Commit SHA mismatch')
        return ('development-'+sha[:12],sha,'EXPLICIT_UNTAGGED_COMMIT')
    candidates=[]
    # Published releases first (may be empty; 404 on /releases/latest is not an error).
    for page in range(1,11):
        batch=get(f'/releases?per_page=100&page={page}')
        if not isinstance(batch,list): raise RuntimeError('Unexpected Releases response')
        for release in batch:
            tag=release.get('tag_name','')
            if not release.get('draft') and not release.get('prerelease') and stable(tag):
                candidates.append((stable(tag),tag))
        if len(batch)<100: break
    # Tags can be stable even without published GitHub Releases. Never infer stability from main.
    for page in range(1,11):
        batch=get(f'/tags?per_page=100&page={page}')
        if not isinstance(batch,list): raise RuntimeError('Unexpected Tags response')
        for t in batch:
            tag=t.get('name','')
            if stable(tag): candidates.append((stable(tag),tag))
        if len(batch)<100: break
    candidates=sorted(set(candidates), key=lambda item:item[0],reverse=True)
    if requested:
        candidates=[c for c in candidates if c[1]==requested or c[1].lstrip('v')==requested.lstrip('v')]
    if not candidates:
        raise RuntimeError('No suitable official stable semver tag found. Upstream has no published Releases as of audit. Provide an explicit 40-hex commit SHA and select allow_untagged, or wait for a stable upstream tag. No fallback to main.')
    tag=candidates[0][1]
    # Resolve tag to commit; annotated tags may point to tag objects.
    target=get('/git/ref/tags/'+tag)
    obj=target['object']
    for i in range(4):
        if obj['type']=='commit':break
        if obj['type']!='tag':raise RuntimeError('Unexpected tag type '+str(obj['type']))
        obj=get('/git/tags/'+obj['sha'])['object']
    if obj['type']!='commit' or not SHA.fullmatch(obj['sha']):
        raise RuntimeError('Cannot determine immutable commit for tag '+tag)
    return (tag,obj['sha'].lower(),'STABLE_TAG')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--version',default='')
    ap.add_argument('--allow-untagged',action='store_true')
    ap.add_argument('--github-output',default='')
    args=ap.parse_args()
    label,sha,kind=resolve(args.version.strip(),args.allow_untagged)
    data={'upstream_repo':REPO,'version':label,'commit':sha,'kind':kind}
    print(json.dumps(data,indent=2))
    if args.github_output:
        with open(args.github_output,'a',encoding='utf-8',newline='\n') as fp:
            fp.write(f'upstream_version={label}\nupstream_commit={sha}\nsource_kind={kind}\n')
if __name__=='__main__':
    try:main()
    except Exception as e:
        print('ERROR:',e,file=sys.stderr)
        sys.exit(1)
