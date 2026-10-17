"""Authoritative dash eligibility and swept village movement."""
import math
import time
import progression
import combat_environment as terrain


def reason(room,p,now=None):
    now=time.monotonic() if now is None else now
    if p.get('status')!='alive':return 'Stand up before dashing.'
    if p.get('rootUntil',0)>now:return 'You are rooted.'
    if progression.locked(room,p) or p.get('townInteraction')=='guild':return 'Close the conversation or service before dashing.'
    phases=('combat','town','stage_exit','chest','peace') if room.get('adventure') else ('combat',)
    if room.get('phase') not in phases:return 'Dashing is unavailable in this scene.'
    if p.get('townInterior'):return 'Leave the building before dashing.'
    return ''


def move(world,room,p,dx,dy):
    if room['phase']!='town':
        terrain.move(room,p,p['x']+dx,p['y']+dy)
        return
    # Use exactly the village movement footprint, sampled at <=6 world pixels.
    steps=max(1,math.ceil(math.hypot(dx,dy)/6))
    for _ in range(steps):
        nx,ny=max(28,min(932,p['x']+dx/steps)),max(30,min(510,p['y']+dy/steps))
        if world._town_walkable(room,nx,p['y']):p['x']=nx
        if world._town_walkable(room,p['x'],ny):p['y']=ny
