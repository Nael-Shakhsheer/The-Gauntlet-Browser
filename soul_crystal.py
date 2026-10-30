"""Personal permanent travel tool. Receipts are bounded by authored enemy origins."""
import math
import re
import time

CAPACITY=10
PARTICIPATION_RANGE=450


def ensure(p):
    s=p.setdefault('soulCrystal',dict(version=2,charge=CAPACITY,receipts={}))
    if s['version']==1:
        s.update(version=2,charge=min(CAPACITY,s['charge']))
    return s


def grant(room,enemy):
    if not room.get('adventure') or __import__('opening').active(room) or enemy.get('friendly'):return
    origin=enemy.get('lifeOrigin',enemy['id']);generation=enemy.get('lifeGeneration',0)
    amount=5 if enemy.get('boss') else 3 if enemy.get('miniBoss') or enemy.get('elite') else 1
    for p in room['players'].values():
        if p.get('bot') or not p.get('connected',True) or p.get('townInterior'):continue
        if math.dist((p['x'],p['y']),(enemy['x'],enemy['y']))>PARTICIPATION_RANGE:continue
        if p['status']!='alive' and time.monotonic()-p.get('combatParticipationAt',0)>30:continue
        s=ensure(p)
        if s['receipts'].get(origin,-1)>=generation:continue
        if len(s['receipts'])>=1024 and origin not in s['receipts']:continue
        s['receipts'][origin]=generation;s['charge']=min(CAPACITY,s['charge']+amount)


def validate(p):
    s=p.get('soulCrystal')
    if s is None:return # Additive migration: old characters receive the initial full crystal.
    if not isinstance(s,dict) or set(s)!={'version','charge','receipts'} or s['version'] not in (1,2) or type(s['charge']) is not int or not 0<=s['charge']<=(20 if s['version']==1 else CAPACITY):raise ValueError('Invalid soul crystal.')
    if not isinstance(s['receipts'],dict) or len(s['receipts'])>1024 or any(not isinstance(k,str) or not re.fullmatch(r'[A-Za-z0-9_:-]{1,100}',k) or type(v) is not int or not 0<=v<=10**9 for k,v in s['receipts'].items()):raise ValueError('Invalid enemy-life soul receipts.')
