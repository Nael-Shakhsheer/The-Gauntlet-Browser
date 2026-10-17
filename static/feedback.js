/* Small confirmed impact marks. Existing attack warnings and silhouettes stay authoritative. */
(() => {
  let scene='',marks=[],shakeAt=-Infinity,shakeUntil=0;
  const colors={Knight:'#e1c58b',Rogue:'#c5ade0',Archer:'#e7d6a8',Wizard:'#b7a0ed',Druid:'#9ecb81',Cleric:'#f0da96',Bard:'#e5b89f',Healer:'#b2e4cc'};
  const settings=()=>window.GauntletAudio?.visualSettings() || {reduced:Boolean(window.matchMedia?.('(prefers-reduced-motion: reduce)').matches),shake:'off'};
  function observe(room){
    const key=window.GauntletAudio?.sceneKey(room) || [room.code,room.adventure?.area,room.stage,room.dungeon?.id,room.dungeon?.floor].join('|');
    if(scene!==key){scene=key;marks=[];shakeUntil=0;}
    const events=window.GauntletAudio?.drainVisuals() || [],now=performance.now();
    window.GauntletAcquisitions?.observe(room,events);
    for(const event of events){
      if(event.kind==='magic_acquired'){event.kind='magic_rune_effect';event.rarity='MAGIC RUNE';}
      if(!['magic_rune_effect','hit','hurt','heal','ward','revive','summon','loot','curse','repair','restore','discovery','quest','complete','material'].includes(event.kind))continue;
      const p=room.players?.find(p=>p.id===(event.ownerId||room.you));
      if(!Number.isFinite(event.x)){event.x=p?.x;event.y=p?.y;}
      if(!Number.isFinite(event.x)||!Number.isFinite(event.y))continue;
      const local=event.ownerId===room.you;
      // Dropped low-priority decoration must never evict local danger or rescue feedback.
      if(marks.length>=24){const index=marks.findIndex(m=>!['hurt','revive'].includes(m.kind));if(index<0)continue;marks.splice(index,1);}
      marks.push({...event,at:now-(event.age||0)*1000,duration:['magic_rune_effect','loot','quest','complete','repair','restore','discovery'].includes(event.kind)?850:420});
      if(event.kind==='hurt'&&event.heavy&&local&&now-shakeAt>900){shakeAt=now;shakeUntil=now+140;}
    }
    marks=marks.filter(m=>now-m.at<m.duration);
  }
  function offset(){
    const now=performance.now(),s=settings();
    if(s.shake==='off'||s.reduced||now>=shakeUntil)return [0,0];
    const fade=Math.max(0,(shakeUntil-now)/140),amplitude=s.shake==='normal'?3:1.25;
    return [Math.sin((now-shakeAt)*.12)*amplitude*fade,Math.sin((now-shakeAt)*.085)*amplitude*.6*fade];
  }
  function draw(ctx,room){
    const now=performance.now(),reduced=settings().reduced;
    let budget=reduced?24:64;
    for(const m of marks){
      const t=(now-m.at)/m.duration;if(t<0||t>=1)continue;
      const actor=['heal','ward','revive'].includes(m.kind)?room.players?.find(p=>p.id===m.ownerId):null;
      const x=actor?.x??m.x,y=actor?.y??m.y;
      ctx.save();ctx.globalAlpha=Math.min(.75,(1-t)*1.1);ctx.lineWidth=2;
      const elemental={Fire:'#e5ae7d',Ice:'#add5e1',Storm:'#c4d6e2',Nature:'#a9c58d',Arcane:'#b7a0ed'};
      const color=['heal','revive','restore'].includes(m.kind)?'#a9d8b3':m.kind==='ward'?'#abcddf':elemental[m.element]||colors[m.heroClass]||'#cbb88d';
      ctx.strokeStyle=color;ctx.fillStyle=color;
      if(['hit','hurt','material'].includes(m.kind)){
        const n=reduced?2:4;
        for(let i=0;i<n&&budget>0;i++,budget--){const a=i*Math.PI*2/n+(m.id%7),r=7+(reduced?0:t*14);ctx.fillRect(Math.round(x+Math.cos(a)*r),Math.round(y+Math.sin(a)*r-6),3,2);}
      }else if(['heal','revive'].includes(m.kind)){
        const lift=reduced?0:t*10;ctx.fillRect(x-1,y-43-lift,3,11);ctx.fillRect(x-5,y-39-lift,11,3);
      }else{
        const radius=m.kind==='summon'?24:20;
        ctx.beginPath();ctx.ellipse(x,y+12,radius+(reduced?0:t*8),8,0,Math.PI*1.08,Math.PI*2.92);ctx.stroke();
        if(['magic_rune_effect','loot','quest','complete','repair','restore','discovery'].includes(m.kind)){
          const rarity=String(m.rarity||'').toUpperCase();
          ctx.font='bold 11px monospace';ctx.textAlign='center';
          ctx.fillText(m.kind==='magic_rune_effect'?'MAGIC RUNE':m.kind==='loot'?(rarity||'LOOT'):m.kind==='complete'?'CLEARED':m.kind.toUpperCase(),x,y-44);
        }
      }
      ctx.restore();
    }
  }
  window.GauntletFeedback={observe,draw,offset,settings,diagnostics:()=>({marks:marks.length,shakeUntil})};
  document.addEventListener('visibilitychange',()=>{if(document.hidden){marks=[];shakeUntil=0;window.GauntletAcquisitions?.reset();}});
  window.addEventListener('blur',()=>{marks=[];shakeUntil=0;});
})();

/* One bounded, nonblocking notice at a time. No inventory polling inference. */
(() => {
 let scene='',queue=[],timer=null,current=null;
 const box=document.createElement('aside');box.id='acquisitionNotice';box.className='acquisition-notice hidden';box.setAttribute('role','status');box.setAttribute('aria-live','polite');document.body.append(box);
 function reset(){clearTimeout(timer);timer=null;current=null;queue=[];box.classList.add('hidden');}
 function show(){if(timer||!queue.length)return;current=queue.shift();box.replaceChildren();
  const e=current,isRune=e.kind==='magic_acquired';box.dataset.kind=isRune?'magic':'item';
  const icon=e.itemKey&&typeof createItemSprite==='function'?createItemSprite({key:e.itemKey,name:e.name}):null;
  if(icon){icon.alt='';box.append(icon);}else{const sig=document.createElement('span');sig.className='acquisition-sigil';sig.textContent=isRune?'★':'◇';box.append(sig);}
  const text=document.createElement('div'),title=document.createElement('strong'),detail=document.createElement('small');
  title.textContent=isRune?'Magic Rune acquired'+(e.quantity>1?' ×'+e.quantity:''):e.name+(e.quantity>1?' ×'+e.quantity:'');
  detail.textContent=isRune?'Personal balance: '+e.balance+' · shared Runes are separate':String(e.rarity||'common')+' · '+e.destination;text.append(title,detail);box.append(text);box.classList.remove('hidden');
  timer=setTimeout(()=>{timer=null;current=null;box.classList.add('hidden');show();},3200);
 }
 function observe(room,events){const key=room.code+'|'+room.you+'|'+room.feedback?.epoch;if(scene!==key){scene=key;reset();}
  for(const e of events){if(!['acquisition','magic_acquired'].includes(e.kind)||e.ownerId!==room.you)continue;
   const existing=queue.find(x=>x.kind===e.kind&&x.name===e.name&&x.destination===e.destination);
   if(existing){existing.quantity+=e.quantity||1;if(e.balance!==undefined)existing.balance=e.balance;}else if(queue.length<24)queue.push({...e});
  }show();
 }
 window.GauntletAcquisitions={observe,reset,diagnostics:()=>({queued:queue.length,showing:Boolean(current)})};
})();
