"""Small authoritative Adventure conversations; object inspections stay separate."""
import copy
import time


def supported(d):
    import progression
    return d and d['kind'] in progression.PRESENTATIONS and (d['kind'].startswith('adventure_') or d['kind']=='caravan_aftermath')


def options(d):
    if d.get('topic'):return [('back','Back to the main topic'),('leave','Leave the conversation')]
    choices=[('region','What is happening in the woodland?'),('advice','What should I do next?'),
             ('steady','We will help. [encouraging]'),('skeptical','I need clearer answers. [skeptical]')]
    if d['kind']=='adventure_runner':
        actions=[(k,label) for k,label in [('accept','Accept the offered assignment'),('report','Report completed work')] if k in d.get('runnerActions',['accept','report'])]
        choices+=actions+[('assignments','Review assignments'),('leave','Not yet. Leave')]
    elif d['kind']=='adventure_caretaker':choices+=[('treat','Restore my HP and mana · 5 shared Runes'),('leave','Leave')]
    else:choices+=[('continue','Continue' if d['page']<d.get('lastPage',0) else 'Help the hunter' if d['kind']=='adventure_hunter' else 'Understood'),('leave','Not now. Leave')]
    return choices[4:]+choices[:4]


def decorate(p,view):
    d=p.get('dialogue')
    if not supported(d):return view
    d['lastPage']=view['total']-1
    if d.get('reaction'):view['text']=d['reaction']
    if d['kind']=='adventure_caretaker':view['serviceRevision']=__import__('cottage').record(p)['revision']
    view['revision']=d.get('revision',0)
    view['choices']=[dict(id=k,label=v) for k,v in options(d)]
    view['reply']=d.get('reply','What can you tell me?')
    return view


def choose(world,room,p,payload):
    import progression,adventure,chapter_flow
    d=p.get('dialogue');key=payload.get('choice')
    if not supported(d) or payload.get('id')!=d['id'] or payload.get('page')!=d['page'] or payload.get('revision')!=d.get('revision',0):raise ValueError('This response is stale. Choose from the current conversation.')
    if key not in dict(options(d)):raise ValueError('That response is unavailable.')
    before=copy.deepcopy(d);decisions=copy.deepcopy(p.get('dialogueDecisions'))
    record=p.setdefault('dialogueDecisions',dict(version=1,attitudes={},topics=[]))
    if key in ('region','advice'):
        topic=d['kind']+':'+key
        if topic not in record['topics'] and len(record['topics'])<32:record['topics'].append(topic)
        d.update(topic=key,reply=dict(options(d))[key],reaction=(
            'The dragon disrupted the watch, but the Minotaur holds our old ruins. Beyond them, Dunmere’s failing water and harvest point toward Ashen Ridge.' if key=='region' else
            'Accept the runner’s current assignment. Read tracks on the Southern road; Rootwater’s cave mouth is on its lower east edge. Ordinary Skills can be learned in Oakvale after closing this conversation. Beds choose recovery; export keeps a portable backup.'))
    elif key in ('steady','skeptical'):
        record['attitudes'][d['kind']]=key
        d.update(topic=key,reply=dict(options(d))[key],reaction='Thank you. Your choices will help people get home. Ask what you need, then take one assignment at a time.' if key=='steady' else 'Fair. Read the objective before committing. You can postpone assignments and retreat from ordinary trails; tower waves and awakened bosses seal their exits.')
    elif key=='back':
        for field in ('topic','reaction','reply'):d.pop(field,None)
    elif key in ('accept','report'):
        status='offered' if key=='accept' else 'ready-to-turn-in'
        q=next((q for q in chapter_flow.menu(room,p) if q['status']==status and q['actionable']),None)
        if not q:raise ValueError('No assignment is '+('available to accept.' if key=='accept' else 'ready to report.'))
        p['dialogue']=None
        try:chapter_flow.action(world,room,p,dict(action='chapterAccept' if key=='accept' else 'chapterReport',quest=q['id']))
        except Exception:
            p['dialogue']=before
            if decisions is None:p.pop('dialogueDecisions',None)
            else:p['dialogueDecisions']=decisions
            raise
        p['chapterMenu']=time.monotonic()
    elif key=='assignments':p['dialogue']=None;p['chapterMenu']=time.monotonic()
    elif key=='treat':
        __import__('cottage').treat(world,room,p,payload)
    elif key=='leave':p['dialogue']=None
    elif key=='continue':progression.advance(world,room,p,dict(id=d['id'],page=d['page']))
    if p.get('dialogue'):p['dialogue']['revision']=d.get('revision',0)+1
    p.update(dx=0,dy=0,attacking=False,reviving=None)


def validate(p):
    import progression
    s=p.get('dialogueDecisions')
    if s is None:return
    if not isinstance(s,dict) or set(s)!={'version','attitudes','topics'} or s['version']!=1:raise ValueError('Unsupported conversation record.')
    kinds={k for k in progression.PRESENTATIONS if k.startswith('adventure_') or k=='caravan_aftermath'}
    if not isinstance(s['attitudes'],dict) or any(k not in kinds or v not in ('steady','skeptical') for k,v in s['attitudes'].items()):raise ValueError('Invalid conversation attitude.')
    if not isinstance(s['topics'],list) or len(s['topics'])>32 or any(not isinstance(t,str) for t in s['topics']) or len(set(s['topics']))!=len(s['topics']) or any(t not in {k+':'+v for k in kinds for v in ('region','advice')} for t in s['topics']):raise ValueError('Invalid conversation topics.')
