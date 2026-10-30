"""One durable kill commit per locked action/tick; never asynchronous ACKs.

Capture lazily before the first lethal hit. Ordinary frames incur no room copy.
Purchases/reports retain their own transaction boundary outside combat.
"""
import copy
from contextlib import contextmanager


def before_lethal(room):
    batch=room.get('_killBatch')
    if batch is not None and batch['before'] is None:
        batch['before']=copy.deepcopy({k:v for k,v in room.items() if k not in ('_killBatch','_chapterProbe')})


def deferred(room):
    batch=room.get('_killBatch')
    if batch is None or batch['before'] is None:return False
    batch['dirty']=True;room['_saveAttempt']=room.get('_saveAttempt',0)+1
    return True


def rollback(room,batch,error=None):
    before=batch['before']
    if before is None:return
    players=room['players'];probe=room.get('_chapterProbe');attempt=room.get('_saveAttempt',0)
    for pid,p in before['players'].items():
        if pid in players:players[pid].clear();players[pid].update(p);before['players'][pid]=players[pid]
    room.clear();room.update(before);room['_saveAttempt']=attempt
    if probe is not None:room['_chapterProbe']=probe
    if error:
        room['adventure']['saveError']=error
        for pid in room['players']:room.setdefault('privateNotices',{})[pid]=error


@contextmanager
def kill_batch(world,room,*,raise_error=True):
    import adventure
    if not adventure.active(room) or not world.storage or '_killBatch' in room:
        yield;return
    batch=dict(before=None,dirty=False);room['_killBatch']=batch
    try:
        yield
    except Exception:
        rollback(room,batch);raise
    finally:
        room.pop('_killBatch',None)
    if batch['dirty'] and not adventure.save(world,room):
        error=room['adventure'].get('saveError','Combat save failed; defeated enemies and rewards were restored.')
        rollback(room,batch,error)
        if raise_error:raise ValueError('Combat rewards were not committed because storage failed. Enemies and rewards were restored; recharge already spent stays spent.')
