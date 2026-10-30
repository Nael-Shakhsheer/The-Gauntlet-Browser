// Cosmetic world dressing. These objects never enter server collision or AI state.
(() => {
  const root=document.currentScript?.dataset.spriteRoot || '/sprites/';
  const regions=['woodland','ruins','cavern','frost'],ground={},art=new Image();
  const layers=new Map(),layouts=new Map(),alphaBounds=new WeakMap(),fades=new WeakMap(),broadGround=new WeakMap();let revision=0;
  function groundImage(region){
    if(!ground[region]){const img=ground[region]=new Image();img.onload=()=>{revision++;layers.clear();};img.src=root+'world-ground-'+region+'-v2.png';}
    return ground[region];
  }
  art.onload=()=>{revision++;};art.src=root+'world-scenery-v2.png';
  const cell=160,anchor=[80,140];
  const heights={woodland:[110,108,53,47],ruins:[111,108,49,65],cavern:[108,97,77,56],frost:[112,111,57,108]};
  const features={road:[[405,315],[175,355],[425,265]],crossroads:[[490,275],[550,240]],camp:[[244,239],[382,357],[400,305],[555,287]],clearing:[[480,315],[700,365]],shrine:[[480,265]],bridge:[[604,337],[718,335]],ruins:[[486,270],[480,375]]};
  function hash(text){let n=2166136261;for(const c of text)n=Math.imul(n^c.charCodeAt(0),16777619);return n>>>0;}
  function random(seed){let n=seed;return()=>{n=(n+0x6D2B79F5)|0;let t=Math.imul(n^n>>>15,1|n);t^=t+Math.imul(t^t>>>7,61|t);return((t^t>>>14)>>>0)/4294967296;};}
  function regionOf(room){return regions.includes(room.region)?room.region:'woodland';}
  function profile(room){
    if(room.adventure?.area==='caravan')return {id:'opening',cap:8,interior:0};
    if(['eastern_threshold','irrigation_channels','farmstead','pump_exterior'].includes(room.adventure?.area))return {id:'dry-threshold',cap:18,interior:0};
    if(room.adventure?.area==='fields')return {id:'dry-fields',cap:24,interior:.12};
    if(room.adventure)return {id:'exploration',cap:90,interior:1};
    if(room.phase==='town')return {id:'village',cap:50,interior:.6};
    if(room.phase==='routes'||room.phase==='peace')return {id:'route',cap:20,interior:.45};
    const boss=room.encounterType==='large_boss'||room.encounterType==='mini_boss'||room.enemies?.some(e=>e.boss||e.miniBoss);
    return boss?{id:'boss',cap:6,interior:0}:{id:'arena',cap:10,interior:.25};
  }
  function eligible(room){return !room.townInterior && room.phase!=='town' && room.phase!=='lobby' && room.adventure?.area!=='home';}
  function paths(room,w,h){
    const authored=room.adventure && window.GauntletAdventureSprites?.groundPaths(room,w,h);
    if(authored?.length)return authored.map(points=>({points}));
    const exits=room.adventure?.exits || (room.phase==='routes'?[...(room.routes||[]).map(r=>({x:r.x,y:r.y})),{x:480,y:520}]:room.phase==='peace'?[{x:480,y:30},{x:480,y:520}]:[]);
    return exits.map((e,i)=>{const x=w/2,y=h*.55,dx=e.x-x,dy=e.y-y,bend=Math.min(65,Math.hypot(dx,dy)*.12)*(i%2?1:-1);
      return {x,y,ex:e.x,ey:e.y,cx:x+dx*.52-(dy/Math.max(1,Math.hypot(dx,dy)))*bend,cy:y+dy*.52+(dx/Math.max(1,Math.hypot(dx,dy)))*bend};});
  }
  function along(p,t){const k=1-t;return [k*k*p.x+2*k*t*p.cx+t*t*p.ex,k*k*p.y+2*k*t*p.cy+t*t*p.ey];}
  function nearPath(x,y,path,radius){return path.some(p=>{
    if(p.points){for(let i=1;i<p.points.length;i++){const [ax,ay]=p.points[i-1],[bx,by]=p.points[i],dx=bx-ax,dy=by-ay,t=Math.max(0,Math.min(1,((x-ax)*dx+(y-ay)*dy)/Math.max(1,dx*dx+dy*dy)));
      if(Math.hypot(x-ax-dx*t,y-ay-dy*t)<radius)return true;}return false;}
    for(let i=0;i<=24;i++){const [px,py]=along(p,i/24);if(Math.hypot(px-x,py-y)<radius)return true;}return false;
  });}
  function paintPaths(g,room,w,h){
    const list=paths(room,w,h);if(!list.length)return;
    const region=regionOf(room),color={woodland:'#ad9970',ruins:'#bfb199',cavern:'#708496',frost:'#8cb4c4'}[region];
    const wide=w>960||h>540?70:48;
    const route=p=>{if(p.points){const points=p.points;g.moveTo(points[0][0]/2,points[0][1]/2);
      for(let i=1;i<points.length-1;i++)g.quadraticCurveTo(points[i][0]/2,points[i][1]/2,(points[i][0]+points[i+1][0])/4,(points[i][1]+points[i+1][1])/4);
      const last=points[points.length-1];g.lineTo(last[0]/2,last[1]/2);
    }else{g.moveTo(p.x/2,p.y/2);g.quadraticCurveTo(p.cx/2,p.cy/2,p.ex/2,p.ey/2);}};
    g.save();g.lineJoin=g.lineCap='round';
    // Several restrained edge bands blend the route into the material, on the native pixel grid.
    for(const [extra,alpha] of [[36,.025],[26,.035],[18,.045],[10,.06],[4,.08],[0,.12]]){g.strokeStyle=color;g.globalAlpha=alpha;g.lineWidth=(wide+extra)/2;
      // One joined path prevents dark overlaps where branches meet.
      g.beginPath();for(const p of list)route(p);g.stroke();}
    g.restore();
  }
  function floor(ctx,room,w,h,puzzle=false){
    if(!eligible(room))return false;
    const region=room.adventure&&(puzzle||room.adventure.area==='shrine')?'ruins':regionOf(room),img=groundImage(region);if(!img.complete||!img.naturalWidth)return false;
    const key=[region,room.adventure?.area || '',room.phase,puzzle,w,h,revision,JSON.stringify((room.adventure?.exits || room.routes || []).map(e=>[e.x,e.y]))].join(':');
    let layer=layers.get(key);
    if(!layer){
      layer=document.createElement('canvas');layer.width=Math.ceil(w/2);layer.height=Math.ceil(h/2);const g=layer.getContext('2d');g.imageSmoothingEnabled=false;
      // Mirrored macro tiles share their edge pixels; no cut-and-pasted perimeter strips.
      const tile=512;
      for(let y=0;y<layer.height;y+=tile)for(let x=0;x<layer.width;x+=tile){const flipX=(x/tile)%2,flipY=(y/tile)%2;
        g.save();g.translate(x+(flipX?tile:0),y+(flipY?tile:0));g.scale(flipX?-1:1,flipY?-1:1);g.drawImage(img,0,0,tile,tile);
        // A low-frequency copy reduces microcontrast while keeping native pixel edges.
        let broad=broadGround.get(img);if(!broad){broad=document.createElement('canvas');broad.width=broad.height=32;const b=broad.getContext('2d');b.imageSmoothingEnabled=true;b.drawImage(img,0,0,32,32);broadGround.set(img,broad);}
        g.globalAlpha=.34;g.drawImage(broad,0,0,tile,tile);g.globalAlpha=1;g.restore();}
      const mood={camp:['#b29964',.19],clearing:['#9caf7d',.07],shrine:['#233d39',.14],bridge:['#365d5b',.11],puzzle:['#253f38',.13]}[puzzle?'puzzle':room.adventure?.area];
      if(mood){g.fillStyle=mood[0];g.globalAlpha=mood[1];g.fillRect(0,0,layer.width,layer.height);g.globalAlpha=1;}
      if(!puzzle)paintPaths(g,room,w,h);
      if(layers.size>18)layers.clear();layers.set(key,layer);
    }
    ctx.save();ctx.imageSmoothingEnabled=false;ctx.drawImage(layer,0,0,w,h);ctx.restore();return true;
  }
  function layout(room,w,h){
    if(!eligible(room))return [];
    const region=regionOf(room),area=room.adventure?.area || '',puzzle=room.phase==='puzzle';
    const purpose=profile(room).id,settings=profile(room);
    const key=[room.code,room.stage,area,region,w,h,puzzle,purpose,JSON.stringify((room.environment?.obstacles||[]).map(o=>[o.id,o.x,o.y]))].join(':');
    if(layouts.has(key))return layouts.get(key);
    const rng=random(hash(key)),items=[],path=paths(room,w,h),row=regions.indexOf(region),large=w>960||h>540;
    const bossArena=area==='shrine'||area==='ruins'||room.enemies?.some(e=>e.boss);
    const reserved=(features[area]||[]).map(([x,y])=>[x*w/960,y*h/540]);
    for(const f of room.adventure?.features || [])reserved.push([f.x,f.y]);
    for(const e of room.adventure?.exits || [])reserved.push([e.x,e.y]);
    if(room.phase==='peace')reserved.push([480,250]);
    if(room.phase==='routes')reserved.push([480,178]);
    for(const o of room.environment?.obstacles||[])reserved.push([o.x,o.y]);
    for(const b of room.environment?.barriers||[])reserved.push([b.x+b.width/2,b.y+b.height/2]);
    if(room.objective)reserved.push([room.objective.x??w/2,room.objective.y??h/2]);
    function add(x,y,variant,scale=1){
      if(items.length>=settings.cap)return;
      const dryness=['eastern_threshold','irrigation_channels','farmstead','pump_exterior'].includes(area)?.65+.35*x/w:area==='fields'?x/w:0;
      if(dryness>.55&&variant<2&&rng()<.8)return;
      const tall=variant<2 || region==='frost'&&variant===3;
      if(puzzle&&tall)scale*=.6;
      const extent=(tall?105:60)*scale,height=heights[region][variant]*scale*1.65;
      if(x<25||x>w-25||y<55||y>h-14)return;
      if(nearPath(x,y,path,large?57:46))return;
      const river=room.adventure?.bridgeLayout?.river;
      if(river && x>river.left-extent*.65 && x<river.right+extent*.65)return;
      if(reserved.some(([px,py])=>Math.abs(x-px)<extent+65 && y>py-75 && y-height<py+70))return;
      // Keep the puzzle apparatus and boss commitment space legible.
      if((puzzle||bossArena)&&Math.abs(x-w/2)<180+extent&&y>h/2-155&&y-height<h/2+155)return;
      if(puzzle && x>90 && x<w-90)return;
      if(!room.adventure && ['arena','boss'].includes(purpose)){
        // Decoration, not tactical cover. Leave the entire central fighting lane
        // and southern arrival/revive area clear, including the visible canopy.
        if(x>160&&x<w-160&&y>h*.29&&y-height<h*.85)return;
        if(Math.abs(x-w/2)<150&&y>h-155)return;
      }
      items.push({x:Math.round(x),y:Math.round(y),variant,row,scale,depth:y,dry:dryness>.45,id:'scenery-'+items.length});
    }
    // Perimeter clusters leave entry corridors open. Interior islands fill expanded fields.
    for(let x=64;x<w-35;x+=146){if(Math.abs(x-w/2)>105){add(x+20*rng(),104+rng()*20,rng()<.65?0:1,.9+rng()*.18);add(x+20*rng(),h-24,rng()<.65?0:2,.9+rng()*.18);}}
    for(let y=210;y<h-80;y+=155){if(Math.abs(y-h/2)>90){add(56,y+25*rng(),rng()<.55?0:3,.9);add(w-65,y+25*rng(),rng()<.55?1:2,.9);}}
    const stepX=large?238:255,stepY=large?208:210;
    if(!puzzle)for(let y=220;y<h-95;y+=stepY)for(let x=190;x<w-120;x+=stepX){
      if(rng()>settings.interior)continue;
      const cx=x+(rng()-.5)*115,cy=y+(rng()-.5)*85,variant=rng()<.68?(rng()<.65?0:1):3;
      add(cx,cy,variant,.86+rng()*.23);add(cx+54+rng()*35,cy+18+rng()*30,2,.8+rng()*.22);
      if(large&&rng()<.62)add(cx-70,cy+46,3,.7+rng()*.18);
    }
    if(layouts.size>20)layouts.clear();layouts.set(key,items);return items;
  }
  let dryAtlas=null;
  function droughtArt(){
    if(dryAtlas)return dryAtlas;
    const canvas=document.createElement('canvas');canvas.width=640;canvas.height=160;
    const g=canvas.getContext('2d');if(!g.getImageData)return art;
    g.drawImage(art,0,0,640,160,0,0,640,160);const pixels=g.getImageData(0,0,640,160);
    for(let i=0;i<pixels.data.length;i+=4){const d=pixels.data;if(!d[i+3])continue;const l=d[i]*.3+d[i+1]*.5+d[i+2]*.2;d[i]=Math.min(255,l*1.05+20);d[i+1]=Math.min(255,l*.92+12);d[i+2]=Math.min(255,l*.58+12);}
    g.putImageData(pixels,0,0);dryAtlas=canvas;return canvas;
  }
  function drawObject(ctx,o){
    if(!art.complete||!art.naturalWidth)return;
    const scale=o.scale*1.65;ctx.save();ctx.imageSmoothingEnabled=false;
    ctx.drawImage(o.dry?droughtArt():art,o.variant*cell,o.dry?0:o.row*cell,cell,cell,Math.round(o.x-anchor[0]*scale),Math.round(o.y-anchor[1]*scale),cell*scale,cell*scale);ctx.restore();
  }
  function spriteBounds(img,sx,sy,sw,sh,x,y,width,height){
    if(!img?.complete||!img.naturalWidth)return {x,y,width,height};
    let cache=alphaBounds.get(img);if(!cache){cache=new Map();alphaBounds.set(img,cache);}
    const key=[sx,sy,sw,sh].join(':');let b=cache.get(key);
    if(!b){const c=document.createElement('canvas');c.width=sw;c.height=sh;const g=c.getContext('2d');g.drawImage(img,sx,sy,sw,sh,0,0,sw,sh);
      const pixels=g.getImageData(0,0,sw,sh).data;let left=sw,top=sh,right=0,bottom=0;
      for(let py=0;py<sh;py++)for(let px=0;px<sw;px++)if(pixels[(py*sw+px)*4+3]>48){left=Math.min(left,px);top=Math.min(top,py);right=Math.max(right,px+1);bottom=Math.max(bottom,py+1);}
      b=right>left?[left,top,right-left,bottom-top]:[0,0,0,0];cache.set(key,b);}
    return {x:x+b[0]*width/sw,y:y+b[1]*height/sh,width:b[2]*width/sw,height:b[3]*height/sh};
  }
  function bounds(o){const s=o.scale*1.65;return spriteBounds(art,o.variant*cell,o.row*cell,cell,cell,o.x-anchor[0]*s,o.y-anchor[1]*s,cell*s,cell*s);}
  const objectEntries=new WeakMap();
  function objects(room,w,h){
    const authored=window.GauntletRoomDesigns?.objects(room,w,h);if(authored)return authored;
    const campaign=window.GauntletCampaignScenery?.objects(room,w,h);if(campaign)return campaign;
    if(room.adventure?.dungeon)return [];
    const items=layout(room,w,h);let cached=objectEntries.get(items);
    if(!cached||cached.revision!==revision){cached={revision,entries:items.map(o=>({key:[room.code,room.adventure?.area,room.stage,o.id].join(':'),depth:o.depth,occluder:true,bounds:bounds(o),draw:ctx=>drawObject(ctx,o)}))};objectEntries.set(items,cached);}
    return cached.entries;
  }
  function renderDepth(ctx,entries){
    entries.sort((a,b)=>a.depth-b.depth);
    const hunters=entries.filter(e=>e.player),now=performance.now(),outlined=new Set();
    const reduced=Boolean(window.GauntletAudio?.visualSettings().reduced||window.matchMedia?.('(prefers-reduced-motion: reduce)').matches);
    let states=fades.get(ctx);if(!states){states=new Map();fades.set(ctx,states);}
    for(const entry of entries){
      const b=entry.visibleBounds?.()||entry.bounds,key=entry.key||[b?.x,b?.y,b?.width,b?.height,entry.depth].join(':'),previous=states.get(key);
      const margin=previous?.hidden?12:-3;
      const overlaps=entry.occluder&&b&&!entry.player?.local?hunters.filter(p=>p!==entry&&p.depth<=entry.depth&&
        p.bounds.x<b.x+b.width+margin&&p.bounds.x+p.bounds.width>b.x-margin&&p.bounds.y<b.y+b.height+margin&&p.bounds.y+p.bounds.height>b.y-margin):[];
      // Combat actors keep all attack/health information opaque. A light outline
      // reveals the hunter's silhouette without redrawing its body over actors.
      if(entry.actor||entry.player){for(const p of overlaps)outlined.add(p);ctx.save();entry.draw(ctx);ctx.restore();continue;}
      const state=previous||{alpha:1,hidden:false,last:now,lastOverlap:now};
      if(overlaps.length){state.lastOverlap=now;state.entered??=now;if(now-state.entered>=45)state.hidden=true;}
      else{state.entered=null;if(now-state.lastOverlap>180)state.hidden=false;}
      const target=state.hidden?.3:1,step=Math.min(1,Math.max(0,now-state.last)/180);
      state.alpha=reduced?target:state.alpha+Math.sign(target-state.alpha)*Math.min(Math.abs(target-state.alpha),step);
      state.last=now;states.set(key,state);ctx.save();ctx.globalAlpha*=state.alpha;entry.draw(ctx);ctx.restore();
    }
    for(const p of outlined){const b=p.bounds,x=b.x+b.width/2,y=b.y+5;ctx.save();ctx.strokeStyle=p.player.local?'#eee2bc':'#c6d9d4';ctx.globalAlpha=.55;ctx.lineWidth=1;
      // Small visibility notches identify an overlapped hunter without a shield-like oval.
      ctx.beginPath();for(const sign of [-1,1]){ctx.moveTo(x+sign*8,y);ctx.lineTo(x+sign*15,y);ctx.lineTo(x+sign*15,y+7);}ctx.stroke();ctx.restore();}
    for(const entry of entries)if(entry.after){ctx.save();entry.after(ctx);ctx.restore();}
    for(const [key,state]of states)if(now-state.last>2000)states.delete(key);
  }
  window.GauntletWorldScenery={floor,objects,renderDepth,layout,drawObject,bounds,spriteBounds,profile,revision:()=>revision};
})();
