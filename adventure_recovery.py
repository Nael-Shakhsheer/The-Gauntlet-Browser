"""Recovery API service. Preview is read-only; import commits a distinct world.

Bearer recovery proofs are never in a portable backup or public game state.
"""
import copy
import secrets
import time
import uuid
import adventure
import save_portability as portable


def proof_matches(value,expected):
    return isinstance(value,str) and isinstance(expected,str) and 0<len(value)<=128 and secrets.compare_digest(value.encode('utf-8'),expected.encode('utf-8'))


class Recovery:
    def __init__(self,world):self.world=world;self.previews={}

    def session(self,code,pid):
        room=self.world.rooms[code];p=room['players'][pid]
        return dict(room=code,player=pid,recovery=p.get('recoveryProof'))

    def read(self,payload,export=False):
        with self.world.lock:
            room,p=self.world.adventure_access(str(payload.get('room','')),str(payload.get('player','')))
            if export:
                # Capture latest live progress; report disk failure separately.
                record=adventure.snapshot(room)
                document=portable.project(record)
                portable.validate(document)
                return document
            return self.world.adventure_summary(room,p)

    def preview(self,document):
        try:document,migrated=portable.validate(document)
        except (KeyError,TypeError,AttributeError,OverflowError) as exc:raise ValueError('Malformed backup; original saves are unchanged.') from exc
        with self.world.lock:
            self.previews={k:v for k,v in self.previews.items() if v['expires']>time.monotonic()}
            if len(self.previews)>=32:raise ValueError('Too many pending imports. Please retry later.')
            token=secrets.token_urlsafe(32)
            self.previews[token]=dict(document=document,expires=time.monotonic()+900,result=None)
            return dict(preview=token,summary=portable.summary(document,migrated))

    def slots(self,payload,preview=False):
        with self.world.lock:
            room,p=self.world.adventure_access(payload.get('room',''),payload.get('player',''))
            if not proof_matches(payload.get('recovery'),p.get('recoveryProof')):raise ValueError('Private recovery proof required.')
            record=self.world.storage.adventure_backup(room['adventure']['worldId']) if self.world.storage else None
            if preview:
                if record is None:raise ValueError('No Adventure backup yet. It is created after the second confirmed save.')
                result=self.preview(portable.project(record))
                slot=next((i for i,c in enumerate(record['room']['players'].values()) if c.get('characterId')==p['characterId']),None)
                if slot is None:raise ValueError('This character is absent from the older backup.')
                result['character']=slot
                return result
            return dict(current=self.world.adventure_summary(room,p),backup=portable.summary(portable.project(record)) if record else None,
                        slots=['Current Adventure','Adventure Backup','Gauntlet Checkpoint'])

    def commit(self,payload):
        with self.world.lock:
            row=self.previews.get(str(payload.get('preview','')))
            if not row or row['expires']<time.monotonic():raise ValueError('Import preview expired. Select the backup again.')
            if row['result']:return row['result']  # Confirmation retry is idempotent.
            if payload.get('confirm') is not True:raise ValueError('Review the summary and confirm a new world.')
            document=row['document'];chars=document['progress']['characters']
            slot=payload.get('character')
            if not isinstance(slot,int) or not 0<=slot<len(chars) or chars[slot].get('bot'):raise ValueError('Choose your human character.')
            try:result=self.install(document,slot)
            except (KeyError,TypeError,AttributeError,IndexError) as exc:raise ValueError('Backup content could not be restored safely. Originals are unchanged.') from exc
            row['result']=result
            return result

    def install(self,document,slot,cloud=None):
        """Caller holds world lock. Never replace an existing world or file."""
        progress=copy.deepcopy(document['progress']);a=progress['world']
        code=self.world._new_code();wid=str(uuid.uuid4());players={};ids=[]
        for i,char in enumerate(progress['characters']):
            pid=secrets.token_urlsafe(18);ids.append(pid)
            char['characterId']=str(uuid.uuid4());char['recoveryProof']=secrets.token_urlsafe(32);char['strictSession']=True
            players[pid]=char
        a.update(worldId=wid,name=document['name'],creatorCharacter=players[ids[slot]]['characterId'],revision=0,savedAt=None)
        if cloud:
            a.update(worldId=cloud['worldId'],creatorCharacter=cloud['creatorCharacter'])
            for p,cid in zip(players.values(),cloud['characterIds']):p['characterId']=cid
        record=dict(version=1,kind='adventure',room=dict(code=code,host=ids[slot],world=a,players=players,
            difficulty=progress['difficulty'],runes=progress['runes'],runId=secrets.token_hex(8),runStats={},home={}))
        try:
            adventure.restore(self.world,record)
            room=self.world.rooms[code]
            # A restored object must also be playable through the public API.
            self.world.state(code,ids[slot])
            if not adventure.save(self.world,room):raise ValueError('New world could not be saved. Originals are unchanged; retry after fixing storage.')
        except Exception:
            self.world.rooms.pop(code,None)
            raise
        return self.session(code,ids[slot])

    def guest_invite(self,payload):
        """Creator can give a PRIVATE new-world character recovery link to a guest.

        A public room code is deliberately insufficient to claim existing gear.
        """
        with self.world.lock:
            room,p=self.world.adventure_access(payload.get('room',''),payload.get('player',''))
            if not proof_matches(payload.get('recovery'),p.get('recoveryProof')):raise ValueError('Private recovery proof required.')
            if p['characterId']!=room['adventure']['creatorCharacter']:raise ValueError('Only the world creator can share character recovery.')
            character=payload.get('character')
            target=next((p for p in room['players'].values() if p['characterId']==character and not p.get('bot')),None)
            if not target:raise ValueError('Character not found.')
            return self.session(room['code'],target['id'])
