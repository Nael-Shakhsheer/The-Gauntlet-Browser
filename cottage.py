"""Paid personal restoration using the shared pool; no bed or recharge mutation."""
import copy
import re

PRICE=5


def record(p):return p.setdefault('cottageReceipts',dict(version=1,revision=0,lastRequest=None,lastCost=0))


def treat(world,room,p,payload):
    import adventure
    if not adventure.active(room) or room['adventure']['current'] not in __import__('region_content').HUBS or p.get('townInterior')!='cottage' or p['status']!='alive':raise ValueError('Visit Mara inside the village cottage while standing.')
    if __import__('math').dist((p['x'],p['y']),(480,220))>70:raise ValueError('Move closer to Mara for treatment.')
    s=record(p);key=payload.get('requestId');revision=payload.get('serviceRevision')
    if not isinstance(key,str) or not re.fullmatch('[A-Za-z0-9_-]{16,80}',key) or type(revision) is not int:raise ValueError('Review the treatment price before confirming.')
    if key==s['lastRequest'] or revision<s['revision']:return
    if revision!=s['revision']:raise ValueError('Treatment changed. Review the current price and try again.')
    cost=0 if p['hp']>=p['maxHp'] and p['mana']>=p['maxMana'] else PRICE
    if room['runes']<cost:raise ValueError('Treatment costs 5 shared ordinary Runes. Your party has '+str(room['runes'])+'.')
    before=(room['runes'],p['hp'],p['mana'],copy.deepcopy(s))
    room['runes']-=cost;p.update(hp=p['maxHp'],mana=p['maxMana']);s.update(revision=s['revision']+1,lastRequest=key,lastCost=cost)
    if not adventure.save(world,room) and world.storage:
        room['runes'],p['hp'],p['mana'],p['cottageReceipts']=before
        raise ValueError('Treatment could not save. No Runes spent.')
    __import__('feedback').restored(room,p,'rest')
    d=p.get('dialogue')
    if d:d.update(topic='treated',reaction='Both resources are full. '+('5 shared ordinary Runes paid.' if cost else 'No treatment needed; no charge.')+' Cooldowns, crystal and inn recovery point are unchanged.',serviceRevision=s['revision'])


def validate(p):
    s=p.get('cottageReceipts')
    if s is None:return
    if not isinstance(s,dict) or set(s)!={'version','revision','lastRequest','lastCost'} or s['version']!=1 or type(s['revision']) is not int or not 0<=s['revision']<=10**9 or s['lastCost'] not in (0,5) or (s['lastRequest'] is not None and (not isinstance(s['lastRequest'],str) or not re.fullmatch('[A-Za-z0-9_-]{16,80}',s['lastRequest']))):raise ValueError('Invalid cottage receipt.')
