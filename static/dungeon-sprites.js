// Authored dungeon art and ephemeral portal effects. Public room facts own all rules.
(() => {
  const root=document.currentScript?.dataset.spriteRoot || '/sprites/';
  const props=new Image(),materials=new Image(),effects=new Image();
  const pendingSheets=new Map([[props,root+'dungeon-props-v1.png'],[materials,root+'dungeon-materials-v1.png'],[effects,root+'portal-effects-v1.png']]);
  const ids=['cave_mouth','tower_door','stairs_up','stairs_down','watch_bell','cave_seal','survey_marker','supplies_closed','supplies_open','survey_cache_closed','survey_cache_open','portal_shrine'];
  const ready=img=>{const url=pendingSheets.get(img);if(url){pendingSheets.delete(img);img.src=url;}return img.complete&&img.naturalWidth>0;};
  const floors={},floorLayers=new Map();
  function floor(ctx,room,w,h){
    const a=room.adventure;if(!a?.dungeon)return false;
    const kind=a.dungeon.type==='tower'?'tower':'cave';
    if(!floors[kind]){const img=floors[kind]=new Image();img.src=root+'dungeon-floor-'+kind+'-v1.png';}
    const img=floors[kind];if(!ready(img))return false;
    const key=a.area+':'+w+':'+h;let layer=floorLayers.get(key);
    if(!layer){
      layer=document.createElement('canvas');layer.width=Math.ceil(w/2);layer.height=Math.ceil(h/2);const g=layer.getContext('2d');g.imageSmoothingEnabled=false;g.drawImage(img,0,0,layer.width,layer.height);
      const tint={cave_gallery:['#163b49',.07],cave_cache:['#304846',.06],cave_heart:['#102032',.12],tower_2:['#333d38',.05],tower_3:['#244959',.08]}[a.area];
      if(tint){g.globalAlpha=tint[1];g.fillStyle=tint[0];g.fillRect(0,0,layer.width,layer.height);g.globalAlpha=1;}
      g.lineCap=g.lineJoin='round';g.strokeStyle=kind==='cave'?'#728491':'#bdb695';
      for(const [width,alpha]of [[24,.035],[17,.05],[10,.055]]){g.lineWidth=width;g.globalAlpha=alpha;
        for(const path of window.GauntletAdventureSprites?.groundPaths(room,w,h)||[]){g.beginPath();path.forEach(([x,y],i)=>g[i?'lineTo':'moveTo'](x/2,y/2));g.stroke();}
      }
      if(floorLayers.size>14)floorLayers.clear();floorLayers.set(key,layer);
    }
    ctx.save();ctx.imageSmoothingEnabled=false;ctx.drawImage(layer,0,0,w,h);ctx.restore();return true;
  }
  const reduced=()=>Boolean(window.GauntletAudio?.visualSettings().reduced || window.matchMedia?.('(prefers-reduced-motion: reduce)').matches);
  function stamp(ctx,id,x,y,{scale=1,alpha=1}={}){
    const i=ids.indexOf(id);if(i<0||!ready(props))return false;
    ctx.save();ctx.imageSmoothingEnabled=false;ctx.globalAlpha*=alpha;
    ctx.drawImage(props,(i%4)*160,Math.floor(i/4)*160,160,160,Math.round(x-80*scale),Math.round(y-132*scale),160*scale,160*scale);ctx.restore();return true;
  }
  function bounds(id,x,y,scale=1){
    const i=ids.indexOf(id);if(i<0||!ready(props))return null;
    return window.GauntletWorldScenery?.spriteBounds(props,(i%4)*160,Math.floor(i/4)*160,160,160,Math.round(x-80*scale),Math.round(y-132*scale),160*scale,160*scale)||null;
  }
  const patterns=new WeakMap();
  function wall(ctx,b,tower){
    if(!ready(materials))return false;
    let p=patterns.get(ctx);
    if(!p){p=[];for(let i=0;i<4;i++){
      const c=document.createElement('canvas');c.width=c.height=128;const g=c.getContext('2d');g.imageSmoothingEnabled=false;
      g.drawImage(materials,(i%2)*128,Math.floor(i/2)*128,128,128,0,0,128,128);p.push(ctx.createPattern(c,'repeat'));
    }patterns.set(ctx,p);}
    const {x,y,width:w,height:h}=b,base=tower?2:0;
    ctx.save();ctx.imageSmoothingEnabled=false;ctx.translate(x,y);ctx.beginPath();ctx.rect(0,0,w,h);ctx.clip();
    ctx.fillStyle=p[base];ctx.fillRect(0,0,w,h);
    ctx.fillStyle=p[base+1];ctx.fillRect(0,Math.max(0,h-14),w,14);
    ctx.strokeStyle=tower?'#8f9470':'#697e91';ctx.lineWidth=2;ctx.strokeRect(2,2,w-4,h-4);
    ctx.fillStyle=tower?'#24322a':'#112131';ctx.fillRect(0,h-3,w,3);ctx.restore();return true;
  }
  function scenery(ctx,room){
    const a=room.adventure;if(!a?.dungeon)return false;
    for(const b of room.environment?.barriers||[])if(b.material==='stone'&&!wall(ctx,b,a.dungeon.type==='tower'))return false;
    if(a.area==='sluice_gallery'){ctx.save();ctx.fillStyle='#aeb29a';for(const y of [65,115,165]){ctx.fillRect(474,y,12,3);ctx.fillRect(470,y+4,5,3);ctx.fillRect(485,y+4,5,3);}ctx.restore();}
    if(a.area==='sluice_entry'&&!a.features.some(f=>f.id==='sluice_supplies'))stamp(ctx,'supplies_open',650,418,{scale:.8});
    // Spent props remain in their authored positions after the server removes their interaction.
    if(a.area==='cave_entry'&&!a.features.some(f=>f.id==='cave_supplies'))stamp(ctx,'supplies_open',450,408,{scale:.8});
    if(a.area==='cave_cache'&&!a.features.some(f=>f.id==='cave_survey'))stamp(ctx,'survey_cache_open',510,368,{scale:.8});
    if(a.dungeon.type==='tower'&&!a.features.some(f=>f.kind==='dungeon_begin'))stamp(ctx,'watch_bell',480,448,{scale:.8});
    return true;
  }
  function feature(ctx,f,a){
    if(!f.kind.startsWith('dungeon_'))return false;
    const id=f.kind==='dungeon_story'?'survey_marker':f.kind==='dungeon_begin'?(a.dungeon?.type==='tower'?'watch_bell':'cave_seal'):f.id==='cave_survey'?'survey_cache_closed':'supplies_closed';
    return stamp(ctx,id,f.x,f.y+18,{scale:f.kind==='dungeon_story'?.62:.8});
  }
  function trail(ctx,e,room){
    const a=room?.adventure;let id;
    if(e.dungeonEntrance)id=e.dungeonEntrance.type==='tower'?'tower_door':'cave_mouth';
    else if(a?.dungeon){
      if(a.dungeon.type==='tower')id=e.id.startsWith('tower_')?(Number(e.id.slice(-1))>Number(a.area.slice(-1))?'stairs_up':'stairs_down'):'tower_door';
      else id='cave_mouth';
    }
    if(!id)return false;
    const w=room?.areaSize?.[0]||960,h=room?.areaSize?.[1]||540;
    const x=Math.max(44,Math.min(w-44,e.x)),y=Math.max(88,Math.min(h-10,e.y+18));
    const drawn=stamp(ctx,id,x,y,{scale:.8});
    if(drawn&&e.locked)stamp(ctx,'cave_seal',x,y+3,{scale:.36});
    return drawn;
  }
  const points={sluice:{sluice_entry:[160,360],sluice_gallery:[475,360],sluice_alcove:[475,140],pump_chamber:[795,360]},cave:{cave_entry:[160,360],cave_gallery:[475,360],cave_cache:[475,140],cave_heart:[795,360]},tower:{tower_1:[230,405],tower_2:[485,265],tower_3:[730,135]}};
  function map(d,sealed=false){
    const ns='http://www.w3.org/2000/svg',el=(tag,attrs={})=>{const n=document.createElementNS(ns,tag);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,v);return n;};
    const svg=el('svg',{viewBox:'0 0 960 540',class:'dungeon-map','aria-label':d.name+' · discovered chambers',role:'img'});
    if(d.id==='mill_cellar'){
      svg.append(el('image',{href:root+'dungeon-map-cellar-v1.png',width:960,height:540,preserveAspectRatio:'none',style:'image-rendering:pixelated'}));
      const label=(x,y,text)=>{const t=el('text',{x,y,fill:'#f1e2bc','text-anchor':'middle','font-size':22});t.textContent=text;svg.append(t);};
      label(160,280,'Mill door');label(480,70,d.complete?'Field hatch open':'Field hatch sealed');label(550,290,d.complete?'Pump chamber cleared':sealed?'Overseer · sealed fight':'Pump chamber');
      if(d.current){svg.append(el('circle',{cx:480,cy:370,r:10,fill:'#ffe2a1'}));label(480,410,'PARTY IN CELLAR');}return svg;
    }
    const coords=points[d.id]||{},known=new Set(d.nodes.map(n=>n.id)),maskId='dungeon-fog-'+d.id,defs=el('defs'),mask=el('mask',{id:maskId,maskUnits:'userSpaceOnUse',x:0,y:0,width:960,height:540});
    mask.append(el('rect',{width:960,height:540,fill:'white'}));
    for(let y=0;y<540;y+=16)for(let x=0;x<960;x+=16){
      const closest=Object.entries(coords).reduce((best,[id,[px,py]])=>{const distance=(x+8-px)**2+(y+8-py)**2;return distance<best.distance?{id,distance}:best;},{distance:Infinity});
      if(known.has(closest.id))mask.append(el('rect',{x,y,width:17,height:17,fill:'black'}));
    }
    defs.append(mask);svg.append(defs,el('image',{href:root+'dungeon-map-'+d.id+'-v1.png',width:960,height:540,preserveAspectRatio:'none',style:'image-rendering:pixelated'}),el('rect',{width:960,height:540,fill:'#0c1727',mask:'url(#'+maskId+')'}));
    // Only discovered links get a route badge; illustration is cosmetic and never reveals a route.
    for(const link of d.links){if(!known.has(link.fromId)||!known.has(link.toId))continue;
      const from=coords[link.fromId],to=coords[link.toId];if(!from||!to)continue;
      const badges={'cave_entry|cave_gallery':[310,360],'cave_cache|cave_gallery':[475,295],'cave_gallery|cave_heart':[637,360],'tower_1|tower_2':[365,310],'tower_2|tower_3':[620,180]};
      const [x,y]=badges[[link.fromId,link.toId].sort().join('|')]||[(from[0]+to[0])/2,(from[1]+to[1])/2];
      const locked=link.locked||sealed&&d.nodes.some(n=>n.current&&(n.id===link.fromId||n.id===link.toId));
      const g=el('g',{'aria-label':locked?'Passage sealed':'Passage open'});
      g.append(el('rect',{x:x-12,y:y-12,width:24,height:24,fill:'#182c32',stroke:locked?'#db9b7b':'#a5d3b6','stroke-width':2}));
      if(locked)g.append(el('path',{d:`M ${x-4} ${y-1} v -5 a 4 4 0 0 1 8 0 v 5 M ${x-6} ${y-1} h 12 v 8 h -12 Z`,fill:'none',stroke:'#efba86','stroke-width':3}));
      else g.append(el('path',{d:`M ${x-6} ${y} l 4 4 l 8 -9`,fill:'none',stroke:'#b6e5bb','stroke-width':3}));svg.append(g);
    }
    for(const n of d.nodes){const p=coords[n.id];if(!p)continue;const [x,y]=p,labelY=Math.min(509,y+100),g=el('g');
      const name=n.name.split(' · ').at(-1).replace('Entrance chamber','Entrance'),text=el('text',{x,y:labelY,'text-anchor':'middle',class:'dungeon-map-label',fill:'#fff1ce','font-size':24});text.textContent=name;
      g.append(el('rect',{x:x-130,y:labelY-29,width:260,height:39,fill:'#13232cef',stroke:n.current?'#e9cb7a':n.cleared?'#91bfa0':'#7d8fa1','stroke-width':2}),text);
      const state=el('text',{x,y:labelY+29,'text-anchor':'middle',class:'dungeon-map-state',fill:n.current?'#ffe4a3':'#c2d7d8','font-size':16});state.textContent=n.current?'PARTY HERE':n.cleared?'CLEARED':n.visited?'EXPLORED':'CHARTED';g.append(state);
      if(n.current)g.append(el('path',{d:`M ${x-7} ${y-30} h 14 v 8 h -4 l -3 5 l -3 -5 h -4 Z`,fill:'#ffe2a1',stroke:'#162b32','stroke-width':2}));
      const title=el('title');title.textContent=n.name+' · '+state.textContent;g.append(title);svg.append(g);
    }
    return svg;
  }
  let scene='',epoch='',cursor=0,observedAt=0,channel=null,bursts=[];
  function observe(room){
    const now=performance.now(),key=room.code+'|'+(room.adventure?.area||room.stage),f=room.feedback;
    const live=observedAt>0&&now-observedAt<1800&&!document.hidden&&scene.split('|')[0]===room.code,changed=key!==scene;
    if(changed){bursts=[];channel=null;scene=key;}
    if(f){
      const changedEpoch=f.epoch!==epoch;
      for(const e of f.events||[]){
        if(e.kind!=='portal_arrive'||e.age>.8||!live||(!changedEpoch&&e.id<=cursor))continue;
        for(const p of e.participants||[])if(Number.isFinite(p.x)&&Number.isFinite(p.y))bursts.push({x:p.x,y:p.y,at:now-(e.age||0)*1000,kind:'arrive'});
      }
      epoch=f.epoch;cursor=f.cursor;
    }
    const c=room.adventure?.portals?.channel;
    if(channel&&!c&&!changed&&!reduced())for(const p of channel.positions)bursts.push({x:p.x,y:p.y,at:now,kind:'cancel'});
    channel=c?{...c,remaining:Number.isFinite(c.remaining)?c.remaining:null,at:now,positions:(room.players||[]).filter(p=>c.participants?.includes(p.id)&&!p.indoors).map(p=>({x:p.x,y:p.y}))}:null;
    if(channel&&!channel.positions.length&&c.anchor)channel.positions=[{x:c.anchor[0],y:c.anchor[1]}];
    observedAt=now;bursts=bursts.slice(-16);
  }
  function fx(ctx,row,frame,x,y,scale=.9,alpha=1){
    if(!ready(effects))return;ctx.save();ctx.imageSmoothingEnabled=false;ctx.globalAlpha*=alpha;
    ctx.drawImage(effects,frame*160,row*160,160,160,Math.round(x-80*scale),Math.round(y-144*scale),160*scale,160*scale);ctx.restore();
  }
  function portals(ctx,room){
    if(document.hidden||room.townInterior)return;const now=performance.now(),simple=reduced();
    if(channel&&scene===room.code+'|'+(room.adventure?.area||room.stage)&&now-channel.at<1500){
      const remaining=channel.remaining===null?null:Math.max(0,channel.remaining-(now-channel.at)/1000),progress=remaining===null?0:1-remaining/(channel.duration||3);
      for(const p of channel.positions){
        if(simple||remaining===null)fx(ctx,0,simple?3:0,p.x,p.y+14,.72,.7);
        else if(remaining<=.52)fx(ctx,2,Math.min(3,Math.floor((.52-remaining)/.13)),p.x,p.y+14);
        else {fx(ctx,0,Math.min(3,Math.floor(progress*4)),p.x,p.y+14,.72);if(progress>.2)fx(ctx,1,Math.floor(now/170)%4,p.x,p.y+14,.9,.65);}
      }
    }
    bursts=bursts.filter(b=>now-b.at<(b.kind==='cancel'?350:800));
    for(const b of bursts){const age=now-b.at;if(age<0)continue;
      if(simple)fx(ctx,0,3,b.x,b.y+14,.72,.65*(1-age/800));
      else fx(ctx,b.kind==='cancel'?2:3,b.kind==='cancel'?3:Math.min(3,Math.floor(age/200)),b.x,b.y+14,.9,b.kind==='cancel'?1-age/350:1);
    }
  }
  document.addEventListener('visibilitychange',()=>{channel=null;bursts=[];observedAt=0;});
  window.GauntletDungeonSprites={stamp,bounds,floor,scenery,feature,trail,map,observe,portals,barrier:wall};
})();
