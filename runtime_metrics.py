"""Bounded anonymous runtime measurements; no names, session IDs or save contents."""
from collections import defaultdict, deque
from contextlib import contextmanager
import threading
import time


class Metrics:
    def __init__(self):
        self.samples=defaultdict(lambda:deque(maxlen=600));self.lock=threading.Lock()

    def add(self,key,value):
        with self.lock:self.samples[key].append(round(float(value),4))

    @contextmanager
    def time(self,key):
        start=time.perf_counter()
        try:yield
        finally:self.add(key,(time.perf_counter()-start)*1000)

    def view(self):
        with self.lock:rows={k:sorted(v) for k,v in self.samples.items() if v}
        return {k:dict(count=len(v),mean=round(sum(v)/len(v),3),p50=v[len(v)//2],
                       p95=v[min(len(v)-1,int(len(v)*.95))],maximum=v[-1]) for k,v in rows.items()}


class MeasuredRLock:
    """Keep RLock semantics; measure only outermost acquisitions and holds."""
    def __init__(self,metrics):
        self.lock=threading.RLock();self.local=threading.local();self.metrics=metrics

    def acquire(self,*args,**kwargs):
        start=time.perf_counter();ok=self.lock.acquire(*args,**kwargs)
        if ok:
            depth=getattr(self.local,'depth',0)
            if not depth:
                self.metrics.add('lockWaitMs',(time.perf_counter()-start)*1000);self.local.start=time.perf_counter()
            self.local.depth=depth+1
        return ok

    def release(self):
        depth=getattr(self.local,'depth',0)
        if depth==1:self.metrics.add('lockHoldMs',(time.perf_counter()-self.local.start)*1000)
        self.lock.release();self.local.depth=depth-1

    def __enter__(self):self.acquire();return self
    def __exit__(self,*_):self.release()
