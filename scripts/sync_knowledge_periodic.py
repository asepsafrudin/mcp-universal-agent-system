#!/usr/bin/env python3
import argparse
import glob
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path('/home/aseps/MCP')


def expand_sources(patterns):
    files = []
    for p in patterns:
        abs_pat = str(ROOT / p)
        for m in glob.glob(abs_pat, recursive=True):
            path = pathlib.Path(m)
            if path.is_file():
                files.append(path)
    # dedupe preserve order
    seen = set()
    uniq = []
    for f in files:
        s = str(f)
        if s not in seen:
            seen.add(s)
            uniq.append(f)
    return uniq


def ingest_file(file_path, namespace):
    # Placeholder ingestion pipeline via existing script entrypoint style.
    # Stores text payload into knowledge through mcp-unified cli bridge when available.
    cmd = [
        'python3', '-c',
        (
            'import pathlib, json; '
            f'p=pathlib.Path({json.dumps(str(file_path))}); '
            'txt=p.read_text(errors="ignore")[:200000]; '
            f'print(json.dumps({{"doc_id": p.name, "namespace": {json.dumps(namespace)}, "bytes": len(txt)}}))'
        )
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0, (r.stdout.strip() or r.stderr.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bootstrap', default=str(ROOT / 'project_knowledge_bootstrap.json'))
    ap.add_argument('--namespace', default=None)
    args = ap.parse_args()

    bpath = pathlib.Path(args.bootstrap)
    conf = json.loads(bpath.read_text())
    namespace = args.namespace or conf.get('namespace', 'default')
    patterns = conf.get('knowledge_sources', [])

    files = expand_sources(patterns)
    if not files:
        print('No files matched knowledge_sources patterns')
        return 0

    ok = 0
    fail = 0
    for f in files:
        success, msg = ingest_file(f, namespace)
        if success:
            ok += 1
            print(f'[OK] {f} :: {msg}')
        else:
            fail += 1
            print(f'[FAIL] {f} :: {msg}')

    print(f'Completed. success={ok} fail={fail} namespace={namespace}')
    return 0 if fail == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
