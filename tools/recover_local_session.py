"""Offline owner recovery of a native save; never serves or logs credentials.

Existing proofs and source bytes are preserved. A genuinely proof-less record
requires an explicit NEW output copy; the owner installs that copy with the
server stopped, retaining the original. There is no public recovery endpoint.
"""
import argparse
import base64
import copy
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def validate_record(record):
    if not isinstance(record,dict) or record.get('version')!=1:raise ValueError('Unsupported native save; original preserved.')
    room=record.get('room',{});players=room.get('players',{})
    code=room.get('code','')
    if not isinstance(code,str) or len(code)!=5 or any(c not in 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789' for c in code):raise ValueError('Invalid room identity.')
    if not isinstance(players,dict) or not players:raise ValueError('No saved characters.')
    if record.get('kind')=='adventure':
        # Skill validation loads definitions from game, whose historical module
        # singleton opens storage. Redirect that import to disposable storage;
        # inspecting one explicitly selected save must not open all private data.
        if 'game' not in sys.modules:
            from unittest.mock import patch
            import run_storage
            original=run_storage.RunStorage.__init__
            with tempfile.TemporaryDirectory(prefix='recovery-validation-') as folder:
                with patch.object(run_storage.RunStorage,'__init__',lambda self,_:original(self,Path(folder))):
                    import game
                game.WORLD.storage=None
        import save_portability
        save_portability.validate(save_portability.project(record))
    elif record.get('kind') is not None or not room.get('checkpoint'):
        raise ValueError('Choose a native Adventure save or Gauntlet bed checkpoint.')
    return room


def recovery_link(record,player,origin='http://127.0.0.1:8000',allow_new_proof=False):
    room=validate_record(record);p=room['players'].get(player)
    if not isinstance(p,dict) or p.get('bot'):raise ValueError('Choose an existing human character.')
    url=urlsplit(origin)
    if url.scheme not in ('http','https') or not url.hostname or url.username or url.password or url.path not in ('','/') or url.query or url.fragment:raise ValueError('Origin must be the game HTTP(S) address without a path or credentials.')
    result=copy.deepcopy(record);saved=result['room']['players'][player]
    proof=saved.get('recoveryProof')
    changed=not isinstance(proof,str) or not 0<len(proof)<=128
    if changed:
        if not allow_new_proof:raise ValueError('This old record has no private proof. Supply --output for a new migrated copy. The original will remain unchanged.')
        proof=saved['recoveryProof']=secrets.token_urlsafe(32)
    session=dict(room=room['code'],player=player,recovery=proof)
    encoded=base64.b64encode(json.dumps(session,separators=(',',':')).encode()).decode()
    return origin.rstrip('/')+'/#recover='+encoded,result,changed


def recover_file(source,player,origin='http://127.0.0.1:8000',output=None):
    source=Path(source).resolve();target=Path(output).resolve() if output else None
    if target and (target==source or target.exists()):raise ValueError('Output must be a new file; originals and existing copies are never replaced.')
    record=json.loads(source.read_text(encoding='utf-8'))
    link,migrated,changed=recovery_link(record,player,origin,allow_new_proof=bool(target))
    if target:
        # Publish a complete NEW copy atomically without replacing an existing
        # path, even if another process creates it after the initial check.
        pending=None
        try:
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=target.parent,prefix='.recovery-',delete=False) as stream:
                pending=Path(stream.name);json.dump(migrated,stream,ensure_ascii=False)
                stream.flush();os.fsync(stream.fileno())
            os.link(pending,target)
        finally:
            if pending:pending.unlink(missing_ok=True)
    return link,changed


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record',type=Path);parser.add_argument('--player',required=True,help='Existing private native-save player key, not a name.')
    parser.add_argument('--origin',default='http://127.0.0.1:8000');parser.add_argument('--output',type=Path,help='NEW migrated native copy, required only when the record lacks a proof.')
    args=parser.parse_args()
    try:link,changed=recover_file(args.record,args.player,args.origin,args.output)
    except (ValueError,KeyError,TypeError,OSError) as error:parser.exit(1,str(error)+'\n')
    if changed:print('New copy prepared. Stop the server, back up the originals, then install the new copy at the original save path before using this link.')
    print('PRIVATE recovery link — do not share or include in reports:')
    print(link)


if __name__=='__main__':main()
