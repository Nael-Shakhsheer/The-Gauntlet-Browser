"""Atomic local checkpoint files and append-only balance observations."""
import json
import logging
import os
import uuid
import errno
from contextlib import contextmanager


@contextmanager
def locked_record(path):
    """OS-released lock, including a crashed writer; no stale lock sentinel."""
    with path.with_suffix('.lock').open('a+b') as lock:
        lock.seek(0,2)
        if lock.tell()==0:lock.write(b'0');lock.flush()
        lock.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:raise OSError(errno.EAGAIN,'Another save transaction is in progress.') from None
        try:yield
        finally:
            lock.seek(0)
            if os.name=='nt':msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
from pathlib import Path


class RunStorage:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.checkpoints = self.directory / "checkpoints"
        self.checkpoints.mkdir(parents=True, exist_ok=True)
        self.adventure_paths = {}
        from cloud_storage import Supabase
        self.cloud=Supabase(self.directory)

    def save(self, room):
        path = self.checkpoints / (room["code"] + ".json")
        temporary = path.with_suffix(".tmp")
        with temporary.open("wb") as stream:
            stream.write(json.dumps({"version":1,"room":room},ensure_ascii=False).encode('utf-8'))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)

    def load(self):
        rooms = []
        for path in self.checkpoints.glob("*.json"):
            try:
                document = json.loads(path.read_text(encoding="utf-8"))
                room = document["room"]
                if document["version"] != 1 or not room["players"] or not room["checkpoint"]:
                    raise ValueError("Unsupported or empty checkpoint")
                if room["code"] != path.stem or not all(c in "ABCDEFGHJKLMNPQRSTUVWXYZ23456789" for c in room["code"]):
                    raise ValueError("Invalid room code")
                rooms.append(room)
            except (ValueError, KeyError, TypeError, OSError):
                logging.exception("Could not load checkpoint %s; file preserved", path.name)
        return rooms

    def delete(self, code):
        (self.checkpoints / (code + ".json")).unlink(missing_ok=True)

    def save_adventure(self, record):
        """Separate versioned records; a durable provider can implement this interface."""
        directory = self.directory / "adventures"
        directory.mkdir(parents=True, exist_ok=True)
        room=record['room'];world_id=str(uuid.UUID(room['world']['worldId']))
        path = self.adventure_paths.get(world_id, directory / (world_id + '.json'))
        with locked_record(path):
            previous_record=None;previous_bytes=None
            if path.exists():
                if world_id not in self.adventure_paths:raise OSError(errno.EAGAIN,'An unloaded original save is preserved.')
                try:
                    previous_bytes=path.read_bytes()
                    previous_record=json.loads(previous_bytes.decode('utf-8'))
                    previous=previous_record['room']['world'].get('revision',0)
                except (OSError,ValueError,KeyError,TypeError):raise OSError(errno.EAGAIN,'An unreadable original save is preserved.') from None
                if previous!=room['world']['revision']-1:raise OSError(errno.EAGAIN,'Save revision conflict; newer progress preserved.')
            temporary = path.with_suffix('.tmp')
            # Encode once rather than thousands of Python-level fragment writes.
            # Same UTF-8 JSON, OS lock, revision check, fsync and atomic replace.
            with temporary.open('wb') as stream:
                stream.write(json.dumps(record,ensure_ascii=False).encode('utf-8'));stream.flush();os.fsync(stream.fileno())
            if previous_record is not None:
                backup=self.directory/'adventure-backups'/(world_id+'.json')
                backup.parent.mkdir(parents=True,exist_ok=True)
                pending=backup.with_suffix('.tmp')
                with pending.open('wb') as stream:
                    # Preserve the exact confirmed previous bytes in the backup.
                    stream.write(previous_bytes);stream.flush();os.fsync(stream.fileno())
                os.replace(pending,backup)
            os.replace(temporary,path)
        self.adventure_paths[world_id]=path
        self.cloud.queue(record)

    def adventure_backup(self, world_id):
        """Previous confirmed whole-party revision, never a partially-written save."""
        world_id=str(uuid.UUID(world_id))
        path=self.directory/'adventure-backups'/(world_id+'.json')
        if not path.exists():return None
        return json.loads(path.read_text(encoding='utf-8'))

    def load_adventures(self):
        records = []
        for path in (self.directory / "adventures").glob("*.json"):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                room = record["room"]
                if (record["version"] != 1 or record["kind"] != "adventure" or
                        room["world"]["version"] != 1 or not room["players"] or
                        (room["code"] != path.stem and room["world"].get('worldId') != path.stem) or len(room["code"]) != 5 or
                        not all(c in "ABCDEFGHJKLMNPQRSTUVWXYZ23456789" for c in room["code"])):
                    raise ValueError("Unsupported or invalid Adventure save")
                world_id=room['world'].get('worldId') or str(uuid.uuid5(uuid.NAMESPACE_URL,'gauntlet:legacy:'+room['code']))
                uuid.UUID(world_id)
                if world_id in self.adventure_paths:raise ValueError('Duplicate world identity; original preserved')
                self.adventure_paths[world_id]=path
                records.append(record)
            except (ValueError, KeyError, TypeError, OSError):
                logging.exception("Could not load Adventure %s; file preserved", path.name)
        return records

    def delete_adventure(self, code):
        (self.directory / "adventures" / (code + ".json")).unlink(missing_ok=True)

    def status(self, world_id):
        return self.cloud.status(world_id)

    def record(self, report):
        with (self.directory / "balance.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(report, ensure_ascii=False) + "\n")
