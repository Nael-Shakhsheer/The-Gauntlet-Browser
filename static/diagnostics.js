/* Local bounded performance samples. Visible only inside Technical details. */
(() => {
  const rows=new Map();let generation=0;
  function add(key,value,epoch=generation){if(epoch!==generation||!Number.isFinite(value))return;const values=rows.get(key)||[];values.push(value);if(values.length>600)values.shift();rows.set(key,values);}
  function view(){return Object.fromEntries([...rows].map(([key,values])=>{const v=[...values].sort((a,b)=>a-b);return [key,{count:v.length,mean:v.reduce((a,b)=>a+b,0)/v.length,p50:v[Math.floor(v.length*.5)],p95:v[Math.min(v.length-1,Math.floor(v.length*.95))],maximum:v.at(-1)}];}));}
  let last=null,receivedAt=null;
  // Receipt age measures polling gaps even while stationary. movement.age is
  // instead time since server movement integration; it is not network latency.
  function observeState(room){
    receivedAt=document.hidden?null:performance.now();
    if(Number.isFinite(room.movement?.age))add('movementSampleAgeMs',Math.max(0,room.movement.age)*1000);
  }
  function reset(){generation++;rows.clear();last=null;receivedAt=null;}
  function frame(now){
    if(!document.hidden && document.body.classList.contains('is-playing')){
      if(last!==null){add('frameMs',now-last);if(now-last>50)add('longFrameMs',now-last);}
      if(receivedAt!==null)add('receivedSnapshotAgeMs',Math.max(0,now-receivedAt));
      last=now;
    }else{last=null;if(document.hidden)receivedAt=null;}
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
  // Resource Timing records observed requests, not save/session contents. Aggregate
  // only same-origin static paths; query strings and private API URLs are excluded.
  function resources(){
    const assets=performance.getEntriesByType('resource').filter(e=>{try{const u=new URL(e.name);return u.origin===location.origin&&!u.pathname.startsWith('/api/');}catch{return false;}});
    return {requests:assets.length,encodedBytes:assets.reduce((n,e)=>n+(e.encodedBodySize||0),0),transferBytes:assets.reduce((n,e)=>n+(e.transferSize||0),0),
      assets:assets.map(e=>({path:new URL(e.name).pathname,bytes:e.encodedBodySize||0,transfer:e.transferSize||0,ms:Math.round(e.duration*100)/100}))};
  }
  let initialResources=null;
  document.addEventListener('pointerdown',()=>{initialResources=resources();},{once:true,capture:true,passive:true});
  function render(){const box=document.querySelector('#runtimeReadings');if(box?.closest('dialog')?.open)box.textContent=JSON.stringify({timings:view(),initialResources,resources:resources()},null,2);}
  setInterval(render,1000);
  window.GauntletDiagnostics={add,view,resources,observeState,reset,generation:()=>generation};
  fetch('/api/build',{cache:'no-store'}).then(r=>r.ok?r.json():Promise.reject(Error('Server update needed'))).then(build=>{
    const label=document.querySelector('#buildVersion');if(label)label.textContent='Build '+build.server.slice(0,6)+' / '+build.client.slice(0,6)+' · '+location.host;
    const details=document.querySelector('#runtimeBuild');if(details)details.textContent=location.origin+' · Python '+build.server+' · client '+build.client+' · '+build.storage;
  }).catch(()=>{const label=document.querySelector('#buildVersion');if(label)label.textContent='Older server · refresh after update';});
})();
