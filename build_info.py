"""Version fingerprints distinguish a running Python build from refreshed assets."""
import hashlib
import os
import secrets
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def fingerprint(paths):
    digest=hashlib.sha256()
    for path in sorted(paths):digest.update(path.name.encode());digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


SERVER=fingerprint(ROOT.glob('*.py'))
INSTANCE=secrets.token_urlsafe(16)


def view():
    return dict(server=SERVER,client=fingerprint([*(ROOT/'static').glob('*.js'),ROOT/'static/style.css',ROOT/'static/index.html']),
                storage='temporary hosted disk' if os.environ.get('RENDER') else 'local server disk',protocol=2,instance=INSTANCE)
