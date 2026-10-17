/* Public story facts drive presentation. No local timers can finish the battle. */
(() => {
  const retry=document.createElement('button');retry.id='openingRetry';retry.className='primary hidden';retry.textContent='Retry caravan · no Rune loss';$('#arenaPanel').append(retry);
  retry.onclick=async()=>{retry.disabled=true;try{await sendAction('openingRetry');refresh();}catch(e){notice($('#combatNotice'),e.message);}finally{retry.disabled=false;}};
  const reduced=()=>Boolean(window.GauntletAudio?.visualSettings().reduced||window.matchMedia?.('(prefers-reduced-motion: reduce)').matches);
  function update(room){const o=room.adventure?.opening;retry.classList.toggle('hidden',!o?.retry);
    $('#adventureMapButton').disabled=Boolean(o);$('#adventureMapButton').title=o?'Reach Oakvale to chart the woodland.':'';
    if(!o)return;
    $('#adventureStatus').textContent=o.retry?'Caravan checkpoint · retry available':'Caravan defence · '+(o.phase==='withdrawal'?'gather at gate':'keep the road clear');
    notice($('#combatNotice'),o.retry?'The road was overrun. Retry the unfinished encounter; completed steps and your Runes are kept.':o.objective+(o.remaining?' Crew '+(o.phase==='withdrawal'?'withdrawing':'working')+' · '+o.remaining+'s.':''));
  }
  function backdrop(ctx,room){const o=room.adventure?.opening;if(!o)return;
    const art=window.GauntletAdventureSprites;
    // Watch art is distant scenery; it never participates in the combat target set.
    art?.stamp(ctx,o.watch?'burned_watch':'ruins_arch',1000,150,{scale:.48});
    const [gx,gy]=o.muster;ctx.save();ctx.strokeStyle=o.phase==='withdrawal'?'#f3d58b':'#7e8c7c';ctx.lineWidth=3;
    ctx.beginPath();ctx.ellipse(gx,gy,95,43,0,0,Math.PI*2);ctx.stroke();
    ctx.font='bold 13px monospace';ctx.fillStyle='#f3dfaf';ctx.textAlign='center';ctx.fillText(o.phase==='withdrawal'?'SAFE MUSTER · GATHER HERE':'OAKVALE GATE · CREW EVACUATING',gx,gy+60);
    if(o.warning){ctx.strokeStyle='#f1ce86';ctx.lineWidth=3;const sites=o.phase==='first'?[[110,330],[240,600]]:[[820,80],[1160,430],[140,480]];
      for(const [x,y]of sites){ctx.beginPath();ctx.arc(x,y,36,0,Math.PI*2);ctx.stroke();ctx.fillText('INCOMING',x,y-43);}}
    if(o.watch){ctx.fillStyle='#687573';ctx.globalAlpha=.14;for(let i=0;i<4;i++){ctx.beginPath();ctx.arc(1000+(i%2)*10,83-i*14,12-i,0,Math.PI*2);ctx.fill();}ctx.globalAlpha=1;}
    if(o.eventAge!==null&&o.eventAge<8){
      const t=o.eventAge/8,x=reduced()?880:450+t*680,y=70+Math.sin(t*Math.PI)*20;
      ctx.save();ctx.globalAlpha=.63;ctx.translate(x,y);ctx.scale(.78,.78);drawImportedHero(ctx,{class:'',status:'alive',facingX:1,facingY:0},0,0,'Dragon');ctx.restore();
      if(!reduced())for(let i=0;i<3;i++){ctx.save();ctx.globalAlpha=.65;ctx.translate(970-t*220-i*28,195+i*13);ctx.scale(.4,.4);drawImportedHero(ctx,{class:'',status:'alive',moving:true,facingX:-1,facingY:0},0,0,'Wolf');ctx.restore();}
      if(o.eventAge<.55){ctx.fillStyle='#d8c6a0';ctx.globalAlpha=.2*(1-o.eventAge/.55);ctx.beginPath();ctx.arc(1000,90,45,0,Math.PI*2);ctx.fill();ctx.globalAlpha=1;}
    }ctx.restore();
  }
  function objects(ctx,room){const o=room.adventure?.opening;
    if(!o){if(room.adventure?.area!=='home'||!room.adventure?.openingComplete||room.townInterior)return [];
      const p=room.townPortal||{x:480,y:270};return [-1,1].map((side,i)=>{const x=p.x+side*95,y=p.y+70;return {actor:true,depth:y+12,occluder:true,bounds:{x:x-20,y:y-40,width:40,height:60},draw:()=>window.GauntletTownSprites?.character(ctx,'Villager0'+(i+3),x,y,{scale:.8,direction:'south',phase:i*431})};});}
    const result=[{key:room.code+':wagon',depth:438,occluder:true,bounds:{x:420,y:330,width:135,height:115},draw:()=>window.GauntletAdventureSprites?.stamp(ctx,'road_wagon',487,440)}];
    // Withdrawal positions are derived from the authoritative phase countdown,
    // never fragile escort pathfinding or a hidden NPC health objective.
    const t=o.phase==='withdrawal'?Math.min(1,(20-o.remaining)/20):0;
    for(let i=0;i<3;i++){const x=(i===0?650:565+i*40)*(1-t)+(1020+i*24)*t,y=(i===0?340:390+i*40)*(1-t)+(125+i*20)*t;
      result.push({actor:true,depth:y+12,occluder:true,bounds:{x:x-23,y:y-44,width:46,height:66},draw:()=>{
        if(i===0){ctx.save();ctx.translate(x,y);ctx.scale(.9,.9);drawImportedHero(ctx,{class:'',status:'alive',facingX:-1,facingY:0},0,0,'Knight');ctx.restore();}
        else window.GauntletTownSprites?.character(ctx,'Villager0'+(i+2),x,y,{direction:t?'north-east':'south',mode:t?'walk':'idle',scale:.9,phase:i*233});
      }});
    }return result;
  }
  window.GauntletOpening={update,backdrop,objects};
})();
