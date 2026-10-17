"""Opt-in disposable playtest observations, without names or recovery identities."""
import copy
import time


def resources(room):
    return [dict(slot=i,hero=p['class'],companion=bool(p.get('bot')),hp=round(p['hp'],1),maxHp=p['maxHp'],
                 mana=round(p['mana'],1),items=[x['key'] for x in p['inventory']],
                 position=[round(p['x'],1),round(p['y'],1)],
                 gear=[x['key'] if x else None for x in p['toolSlots']],
                 utilities=[x['key'] if x else None for x in p['utilitySlots']],
                 cooldowns={k:round(max(0,v-time.monotonic()),2) for k,v in p['abilityCooldowns'].items()})
            for i,p in enumerate(room['players'].values())]


def enable(room,label='ordinary stats'):
    room['_chapterProbe']=dict(label=label,started=time.monotonic(),area=(room.get('adventure')or{}).get('current'),
        entered=resources(room),last={p['id']:p['status'] for p in room['players'].values()},
        downings=0,events=[],reports=[],visits=[],visitStart=time.monotonic(),visitArea=(room.get('adventure')or{}).get('current'),baseline=copy.deepcopy(room.get('runStats',{})))


def travel(room,destination):
    log=room.get('_chapterProbe')
    if not log:return
    log['visits'].append(dict(location=log['visitArea'],seconds=round(time.monotonic()-log['visitStart'],2),resources=resources(room)))
    event(room,'travel',destination=destination,remainingEnemies=len(room['enemies']))
    log.update(visitArea=destination,visitStart=time.monotonic())


def tick(room):
    log=room.get('_chapterProbe')
    if not log:return
    for p in room['players'].values():
        if log['last'].get(p['id'])=='alive' and p['status']=='downed':log['downings']+=1
        log['last'][p['id']]=p['status']


def event(room,kind,**details):
    log=room.get('_chapterProbe')
    if log:
        log['events'].append(dict(kind=kind,seconds=round(time.monotonic()-log['started'],2),**details))
        if kind=='downing':
            log['downings']+=1
            for p in room['players'].values():log['last'][p['id']]=p['status']
        if kind=='wipe':log['beforeWipe']=resources(room)


def finish(room,outcome):
    log=room.get('_chapterProbe')
    if not log:return None
    import telemetry
    totals=[{field:value-log['baseline'].get(pid,{}).get(field,0) for field,value in row.items() if field in telemetry.OVERALL_FIELDS} for pid,row in room.get('runStats',{}).items()]
    report=dict(version=1,fixture=log['label'],source='automated or scripted observations; not human balance validation',
        location=log['area'],duration=round(time.monotonic()-log['started'],2),difficulty=room['difficulty'],
        partySize=len(log['entered']),classes=[p['hero'] for p in log['entered']],companion=any(p['companion'] for p in log['entered']),
        outcome=outcome,damage=sum(p['damageDealt'] for p in totals),damageTaken=sum(p['damageTaken'] for p in totals),
        downings=log['downings'],wipes=room['adventure']['wipeCount'],revives=sum(p['revives'] for p in totals),
        deaths=sum(p['deaths'] for p in totals),entry=log['entered'],completion=log.get('beforeWipe',resources(room)),events=copy.deepcopy(log['events']),
        remaining=[dict(kind=e['kind'],role=e.get('combatRole'),hp=e['hp'],position=[round(e['x'],1),round(e['y'],1)]) for e in room['enemies']])
    report['visits']=copy.deepcopy(log['visits'])+[dict(location=log['visitArea'],seconds=round(time.monotonic()-log['visitStart'],2),resources=resources(room))]
    log['reports'].append(report);return report
