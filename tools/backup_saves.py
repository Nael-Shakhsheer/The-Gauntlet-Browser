"""Copy and hash-verify private Gauntlet/Adventure saves before a local restart."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label',default='update')
    args=parser.parse_args()
    if not re.fullmatch(r'[a-z0-9-]+',args.label):parser.error('Use a short lowercase label.')
    data=Path(__file__).resolve().parents[1]/'data'
    backup=data/'backups'/('before-'+args.label+'-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(parents=True,exist_ok=False)
    entries=[]
    for category in ('checkpoints','adventures','adventure-backups'):
        source=data/category
        for path in sorted(source.glob('*.json')):
            path.resolve().relative_to(source.resolve())
            if not path.is_file():continue
            destination=backup/category/path.name
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(path,destination)
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            if hashlib.sha256(destination.read_bytes()).hexdigest()!=digest:
                raise RuntimeError('Save changed during backup; verify before restarting.')
            entries.append(dict(path=category+'/'+path.name,sha256=digest,bytes=path.stat().st_size))
    (backup/'manifest.json').write_text(json.dumps(entries,indent=2),encoding='utf-8')
    print(f'Verified {len(entries)} private save files in {backup.relative_to(data.parent)}',flush=True)


if __name__=='__main__':main()
