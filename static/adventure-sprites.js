// Adventure scenery follows public quest facts; animation never changes travel rules.
(() => {
  const root=document.currentScript?.dataset.spriteRoot || '/sprites/';
  const packs={},terrain={},layer=document.createElement('canvas');let revision=0,cache='';
  const reducedMotion=()=>Boolean(window.GauntletAudio?.visualSettings().reduced || window.matchMedia?.('(prefers-reduced-motion: reduce)').matches);
  const phase=(id,x,y)=>Array.from(id).reduce((n,c)=>n+c.charCodeAt(0)*17,Math.round(x*3+y*7));
  // Authored meandering routes, in compact coordinates; side paths hint at finds.
  const paths={
    brook:[[[960,270],[735,285],[470,300],[380,290]],[[470,300],[520,130],[480,0]],[[735,285],[710,230],[690,180]]],
    mill_trail:[[[480,540],[490,335],[570,230],[570,180]],[[490,335],[720,300],[960,270]]],
    yard:[[[480,0],[410,180],[480,370],[700,330],[960,270]]],
    hollow:[[[0,270],[330,270],[620,315],[680,270]],[[620,315],[500,440],[480,540]],[[620,315],[510,150],[480,0]],[[680,270],[780,160],[870,95]]],
    watch:[[[480,0],[450,170],[390,265],[590,310],[690,290]],[[390,265],[235,285],[0,270]]],
    network:[[[960,270],[745,300],[480,300],[245,270],[0,270]]],
    border:[[[480,0],[440,170],[530,360],[480,540]]],
    fields:[[[0,270],[275,280],[470,340],[520,440],[480,540]],[[275,280],[275,180],[565,200],[760,180]],[[470,340],[570,355],[740,290],[960,362]],[[565,200],[740,190],[960,173]]],
    eastern_threshold:[[[0,173],[270,210],[440,320],[640,330],[790,345]],[[640,330],[810,410],[960,420]]],
    mill:[[[480,0],[470,170],[480,225],[665,280],[960,270]],[[480,225],[390,325],[290,360]],[[665,280],[690,360]]],
    cellar:[[[0,270],[450,270],[570,290],[665,250]],[[450,270],[480,160],[480,0]]],
    caravan:[[[0,370],[330,360],[470,380],[660,340],[830,260],[832,120]]],
    road:[[[480,0],[455,160],[405,315],[650,335],[960,270]],[[650,335],[605,415],[480,540]],[[405,315],[275,320],[175,355]],[[650,335],[800,405],[960,421]],[[405,315],[170,360],[0,405]],[[455,160],[220,135],[0,130]]],
    crossroads:[[[0,270],[330,245],[490,275],[705,260],[960,270]],[[490,275],[410,375],[307,540]],[[490,275],[630,375],[691,540]]],
    camp:[[[480,0],[470,160],[540,270],[320,295],[0,270]],[[320,295],[400,305],[382,357]],[[540,270],[735,250],[960,270]],[[540,270],[520,420],[480,540]]],
    clearing:[[[0,270],[270,285],[480,315],[575,385],[480,540]],[[575,385],[625,365],[700,365]],[[575,385],[300,425],[0,421]],[[575,385],[730,445],[806,540]]],
    shrine:[[[288,0],[335,170],[480,265],[615,180],[701,0]]],
    bridge:[[[960,270],[740,260],[604,260],[480,275],[480,0]],[[740,260],[750,365],[740,540]],[[750,365],[850,345],[960,346]]],
    ruins:[[[480,0],[480,155],[486,225],[480,375],[480,540]],[[480,375],[650,310],[960,270]]],
    cave_entry:[[[0,270],[465,270],[960,270]],[[465,270],[450,390]]],
    cave_gallery:[[[0,270],[480,270],[960,270]],[[480,270],[480,0]]],
    cave_cache:[[[480,540],[510,350],[520,220]]],
    cave_heart:[[[0,270],[480,270],[960,270]],[[480,270],[380,400]]],
    tower_1:[[[0,270],[480,270],[480,0]],[[480,270],[480,540]]],
    tower_2:[[[480,0],[350,175],[350,365],[480,540]],[[480,0],[610,175],[610,365],[480,540]]],
    tower_3:[[[480,540],[480,270],[0,270]]]
  };
  const areas=['road','crossroads','camp','clearing','shrine','bridge','ruins','puzzle'];
  function field(area){
    if(!areas.includes(area))return null;
    if(!terrain[area]){const img=terrain[area]=new Image();img.onload=()=>{revision++;cache='';};img.src=root+'adventure-field-'+area+'-v1.png';}
    return terrain[area];
  }
  for(const key of ['landmarks','props','signals','npcs','discoveries']){
    const entry=packs[key]={image:new Image(),metadata:window.GauntletAdventureSpriteMetadata?.[key] || null};
    entry.path=root+'adventure-'+key+'-v1.png';entry.image.onload=()=>{revision++;};
    if(!entry.metadata)fetch(root+'adventure-'+key+'-v1.json').then(r=>r.ok?r.json():Promise.reject()).then(data=>{entry.metadata=data;revision++;}).catch(()=>{});
  }
  const dryLayers=new Map();
  function dryLand(ctx,room){
    const a=room.adventure,area=a.area,w=room.areaSize[0],h=room.areaSize[1],restored=a.chapter?.find(q=>q.id==='irrigation')?.found.includes('sluice_open');
    const key=[area,w,h,Boolean(restored)].join(':');let ground=dryLayers.get(key);
    if(!ground){ground=document.createElement('canvas');ground.width=960;ground.height=540;const g=ground.getContext('2d');
      const fade=g.createLinearGradient(0,0,960,0);fade.addColorStop(0,area==='fields'?'#71864b20':'#a89b6330');fade.addColorStop(.45,'#b5a26965');fade.addColorStop(1,'#c0a875a0');g.fillStyle=fade;g.fillRect(0,0,960,540);
      for(let i=0;i<85;i++){const x=100+(i*157)%835,y=50+(i*83)%450;g.strokeStyle='#65593a4a';g.lineWidth=1;g.beginPath();g.moveTo(x,y);g.lineTo(x+9,y+4);g.lineTo(x+7,y+10);g.moveTo(x+9,y+4);g.lineTo(x+16,y);g.stroke();}
      if(area==='eastern_threshold'){
        // The fixed shed footprint exactly matches the authoritative wood barrier.
        // The existing granary sheet is drawn below, over this stable ground layer.
        for(const [x,y] of [[200,120],[530,455],[880,120]]){g.strokeStyle='#514c35';g.lineWidth=5;g.beginPath();g.moveTo(x,y);g.lineTo(x,y-48);g.moveTo(x,y-24);g.lineTo(x-19,y-39);g.moveTo(x,y-30);g.lineTo(x+17,y-50);g.stroke();}
        for(let i=0;i<7;i++){g.fillStyle='#6a6343';g.fillRect(655+i*30,440,4,22);g.fillRect(655+i*30,447,33,3);}
        g.fillStyle='#554f38';g.fillRect(455,130,4,35);g.fillRect(441,140,32,4);g.fillStyle='#a48e5c';g.fillRect(449,126,15,12);
      }else if(restored){g.fillStyle='#718e4b66';g.fillRect(180,310,500,50);}
      dryLayers.set(key,ground);while(dryLayers.size>2)dryLayers.delete(dryLayers.keys().next().value);
    }
    ctx.drawImage(ground,0,0,w,h);
  }
  function stamp(ctx,id,x,y,{age=performance.now(),scale=1,animate=false,staticFrame=false}={}) {
    for(const entry of Object.values(packs)){
      const m=entry.metadata,row=m?.rows.find(r=>r.id===id),img=entry.image;
      if(row&&!entry.requested){entry.requested=true;img.src=entry.path;}
      if(!row||!img.complete||!img.naturalWidth)continue;
      const frame=animate&&!staticFrame?Math.floor(age/(id.startsWith('runner_walk')?145:220))%(m.frames||4):0;
      ctx.save();ctx.imageSmoothingEnabled=false;
      ctx.drawImage(img,frame*m.cell,row.row*m.cell,m.cell,m.cell,
        Math.round(x-m.anchor[0]*scale),Math.round(y-m.anchor[1]*scale),m.cell*scale,m.cell*scale);
      ctx.restore();return true;
    }
    return false;
  }
  function npc(ctx,kind,x,y,{moving=false,gesture=false,scale=1}={}) {
    const id=kind==='runner'?'runner_'+(moving?'walk':gesture?'gesture':'idle'):
      kind==='injured'?'hunter_injured':gesture?'hunter_gesture':'hunter_recovered';
    return stamp(ctx,id,x,y+18,{scale,animate:true});
  }
  function backdrop(ctx,room,w=960,h=540,puzzle=false) {
    const a=room.adventure;if(!a||a.area==='home')return false;
    if(!puzzle&&window.GauntletDungeonSprites?.floor(ctx,room,w,h))return true;
    if(window.GauntletWorldScenery?.floor(ctx,room,w,h,puzzle))return true;
    const area=puzzle?'puzzle':a.area,img=field(area);
    if(!img?.complete||!img.naturalWidth)return false;
    const key=[room.code,area,w,h,revision,JSON.stringify(a.exits)].join(':');
    if(key!==cache){
      layer.width=w;layer.height=h;const g=layer.getContext('2d');g.imageSmoothingEnabled=false;
      window.GauntletCamera.backdrop(g,img,w,h);
      if(!puzzle){
        // Native packed earth, softly blended into the authored woodland routes.
        const tile=document.createElement('canvas');tile.width=tile.height=20;const t=tile.getContext('2d');t.drawImage(terrain.camp?.naturalWidth?terrain.camp:img,235,133,20,20,0,0,20,20);
        g.lineJoin=g.lineCap='round';
        const authored=paths[area]||[];
        for(const [width,alpha] of [[50,.10],[40,.18],[30,.48]]){
          g.strokeStyle=g.createPattern(tile,'repeat');g.lineWidth=width;g.globalAlpha=alpha;
          for(const path of authored){g.beginPath();path.forEach(([x,y],i)=>g[i?'lineTo':'moveTo'](x*w/960,y*h/540));g.stroke();}
        }
        g.globalAlpha=1;
      }
      cache=key;
    }
    ctx.save();ctx.imageSmoothingEnabled=false;ctx.drawImage(layer,0,0,w,h);ctx.restore();return true;
  }
  function scenery(ctx,room) {
    const a=room.adventure;if(!a)return;
    window.GauntletRegionSprites?.scenery(ctx,room);
    if(a.dungeon&&!window.GauntletDungeonSprites?.scenery(ctx,room)){
      if(a.dungeon.type==='underground'){
        // Ground-level survey markings stay fixed. Stone rectangles own collision.
        ctx.save();ctx.fillStyle='#7b8669';
        const marks=a.area==='cave_gallery'?[[475,195],[475,135],[475,75]]:a.area==='cave_cache'?[[460,330],[500,365],[560,335]]:[[425,290],[455,315]];
        for(const [x,y] of marks){ctx.fillRect(x-5,y-2,10,3);ctx.fillRect(x+2,y+1,3,5);}
        ctx.fillStyle='#466354';for(let i=0;i<8;i++)ctx.fillRect(430+i*9,210+(i%3)*5,4,2);
        if(a.area==='cave_cache')stamp(ctx,'hunter_tracks',430,385,{scale:.6,staticFrame:true});
        ctx.restore();
      }
      // Solid footprint is supplied by the authoritative collision snapshot.
      for(const b of room.environment?.barriers||[]){
        if(b.material!=='stone')continue;
        ctx.fillStyle='#202b33';ctx.fillRect(b.x,b.y,b.width,b.height);
        ctx.fillStyle=room.region==='cavern'?'#4e626b':'#687166';ctx.fillRect(b.x+3,b.y+3,b.width-6,b.height-6);
        ctx.strokeStyle='#303f45';ctx.lineWidth=2;
        for(let y=b.y+16,row=0;y<b.y+b.height-4;y+=16,row++){
          ctx.beginPath();ctx.moveTo(b.x+3,y);ctx.lineTo(b.x+b.width-3,y);ctx.stroke();
          for(let x=b.x+10+(row%2)*15;x<b.x+b.width-4;x+=30){ctx.beginPath();ctx.moveTo(x,y-13);ctx.lineTo(x,y);ctx.stroke();}
        }
        ctx.fillStyle='#8e9c92';ctx.fillRect(b.x+3,b.y+3,b.width-6,3);
      }
    }
    if(a.area==='fields'||a.area==='eastern_threshold')dryLand(ctx,room);
    if(a.area==='bridge')bridge(ctx,room);
    if(['brook','mill_trail','yard','hollow','watch','network','border','fields','mill','eastern_threshold'].includes(a.area)){
      const w=room.areaSize?.[0]||960,h=room.areaSize?.[1]||540;ctx.save();ctx.scale(w/960,h/540);
      if(a.area==='brook'){
        const img=packs.landmarks.image;ctx.fillStyle='#267577';ctx.fillRect(295,205,120,65);
        if(img.complete&&img.naturalWidth)for(let y=205;y<270;y+=13)for(let x=295;x<415;x+=20)ctx.drawImage(img,112,145,28,26,x,y,20,Math.min(13,270-y));
        for(let i=0;i<12;i++){ctx.fillStyle=i%2?'#637e46':'#829456';const x=290+i*11;ctx.fillRect(x,201+(i%3),13,5);ctx.fillRect(x,269-(i%2),13,5);}
        ctx.fillStyle='#66894e';ctx.fillRect(290,205,5,65);ctx.fillRect(415,205,5,65);waterRipples(ctx,300,210,110,55,performance.now()+phase('brook',295,205));
      }
      if(a.area==='yard'){stamp(ctx,'camp_bench',380,260);stamp(ctx,'road_wagon',620,220,{scale:.75});campfire(ctx,480,350);}
      if(a.area==='hollow')stamp(ctx,'hunter_tracks',800,135,{scale:.7});
      if(a.area==='watch')stamp(ctx,'burned_watch',525,200,{scale:.65});
      if(a.area==='border')stamp(ctx,'road_wagon',690,260,{scale:.7});
      if(a.area==='fields'){const restored=a.chapter?.find(q=>q.id==='irrigation')?.found.includes('sluice_open');for(let row=0;row<7;row++)for(let col=0;col<18;col++){const x=190+col*28,y=115+row*31;ctx.fillStyle='#57492c55';ctx.fillRect(x,y,21,3);ctx.fillStyle=restored&&row>4?'#78a456':'#6d6844';ctx.fillRect(x+8,y-7,3,7);ctx.fillRect(x+4,y-5,10,2);}if(restored){ctx.fillStyle='#5c9695';ctx.fillRect(240,318,390,7);}}
      if(a.area==='eastern_threshold'&&!window.GauntletRegionSprites?.feature(ctx,{id:'empty_granary',x:660,y:190},a)){ctx.fillStyle='#756b45';ctx.fillRect(600,140,120,65);}
      if(a.area==='mill'){ctx.fillStyle='#435e5c';ctx.fillRect(290,385,400,10);}
      ctx.restore();
    }
    if(a.area==='road')stamp(ctx,'road_wagon',425*(room.areaSize?.[0]||960)/960,265*(room.areaSize?.[1]||540)/540);
    if(a.area==='crossroads')stamp(ctx,'leaf_waymarker',550*(room.areaSize?.[0]||960)/960,240*(room.areaSize?.[1]||540)/540);
    if(a.area==='clearing'){
      const f=a.features.find(f=>f.id==='watch');if(f)stamp(ctx,'burned_watch',f.x,f.y+18);
    }
    if(a.area==='camp'){
      stamp(ctx,'camp_tent',244,239);stamp(ctx,'camp_bench',382,357);campfire(ctx,400,305);
      if(!a.features.some(f=>f.id==='kit'))stamp(ctx,'repair_chest_empty',555,287,{staticFrame:true});
    }
    if(a.area==='ruins')stamp(ctx,'ruins_arch',486,270,{staticFrame:true});
    if(a.area==='shrine'&&a.shrineRestored){
      for(let i=0;i<12;i++){const angle=i*2.4,x=480+Math.cos(angle)*(72+i*3),y=280+Math.sin(angle)*55;
        ctx.fillStyle='#70a85d';ctx.fillRect(x,y,5,4);ctx.fillRect(x+3,y-4,3,5);ctx.fillStyle='#e9ce86';ctx.fillRect(x+1,y-5,2,2);}
    }
    if(a.area==='home'&&a.complete){stamp(ctx,'celebration_banner',380,96);stamp(ctx,'celebration_banner',580,96,{age:performance.now()+210});}
  }
  function campfire(ctx,x,y) {
    stamp(ctx,'camp_fire',x,y);
    if(reducedMotion())return;
    const age=performance.now()+phase('camp_fire',x,y),pulse=.12+.05*Math.sin(age/570);
    ctx.save();ctx.globalAlpha=pulse;ctx.fillStyle='#ffe38b';ctx.fillRect(x-3,y-30,5,9);ctx.restore();
    const cycle=age%4300;
    if(cycle<700){ctx.save();ctx.globalAlpha=.3*(1-cycle/700);ctx.fillStyle='#ecac55';ctx.fillRect(x+3,y-34-Math.floor(cycle/100),1,2);ctx.restore();}
  }
  function waterRipples(ctx,left,top,width,height,age) {
    if(reducedMotion())return;
    ctx.save();ctx.beginPath();ctx.rect(left,top,width,height);ctx.clip();
    const shift=Math.floor(age/170)%24;
    for(let y=top-24+shift,i=0;y<top+height;y+=24,i++){
      const x=left+8+(i%3)*7;
      ctx.fillStyle='#67c6bc99';ctx.fillRect(x,y,13,1);ctx.fillRect(x+13,y+2,5,1);
      ctx.fillStyle='#b1e1ca88';ctx.fillRect(x+3,y+4,8,1);
    }
    ctx.restore();
  }
  function bridge(ctx,room) {
    const a=room.adventure,b=a.bridgeLayout;if(!b)return;
    const img=packs.landmarks.image,meta=packs.landmarks.metadata;
    const ready=img.complete&&img.naturalWidth&&meta;
    const {left,right}=b.river,height=room.areaSize?.[1]||540,age=performance.now()+phase('bridge',b.sprite.x,b.sprite.y);
    // Fixed river/banks from the imported art. Only ripple highlights move.
    ctx.save();ctx.imageSmoothingEnabled=false;
    ctx.fillStyle='#176e77';ctx.fillRect(left,0,right-left,height);
    if(ready)for(let y=0;y<height;y+=26){
      ctx.drawImage(img,112,145,28,26,left+12,y,right-left-24,26);
      ctx.drawImage(img,91,144,12,26,left,y,12,26);
      ctx.drawImage(img,154,144,12,26,right-12,y,12,26);
    }
    waterRipples(ctx,left+12,0,right-left-24,b.crossing.top,age);
    waterRipples(ctx,left+12,b.crossing.bottom,right-left-24,height-b.crossing.bottom,age+300);
    if(!a.bridge)waterRipples(ctx,left+12,b.crossing.top,right-left-24,b.crossing.bottom-b.crossing.top,age+700);
    const id=a.bridge?'bridge_repaired':'bridge_broken';
    if(!stamp(ctx,id,b.sprite.x,b.sprite.y,{staticFrame:true})){
      ctx.fillStyle='#8b663c';ctx.fillRect(left-42,b.crossing.top,right-left+84,b.crossing.bottom-b.crossing.top);
      if(!a.bridge){ctx.fillStyle='#176e77';ctx.fillRect(left,b.crossing.top,right-left,b.crossing.bottom-b.crossing.top);}
    }
    // Water windows remain entirely inside frame zero's water; no timber,
    // rope, moss or bank pixels are taken from the wobbling alternate frames.
    const x=b.sprite.x-128,y=b.sprite.y-192;
    waterRipples(ctx,x+111,y+56,30,22,age);
    waterRipples(ctx,x+112,y+145,28,32,age+100);
    if(!a.bridge)waterRipples(ctx,x+113,y+99,27,26,age+50);
    if(!a.bridge){
      ctx.fillStyle='#17291fed';ctx.fillRect(left-46,b.crossing.bottom+17,164,25);
      ctx.fillStyle='#ffe095';ctx.font='bold 12px monospace';ctx.textAlign='center';
      ctx.fillText('BROKEN · REPAIR FIRST',left+36,b.crossing.bottom+34);
    }
    ctx.restore();
  }
  function feature(ctx,f,a,near) {
    if(window.GauntletRegionSprites?.feature(ctx,f,a))return true;
    if(f.id==='ridge_barrier')return stamp(ctx,'trail_locked',f.x,f.y+18,{staticFrame:true});
    if(window.GauntletDungeonSprites?.feature(ctx,f,a))return true;
    if(f.kind==='dungeon_story')return true;
    if(f.kind==='dungeon_treasure')return stamp(ctx,'repair_chest',f.x,f.y+18);
    if(f.kind==='dungeon_begin')return stamp(ctx,a.locked?'ruins_seal_awake':'ruins_seal',f.x,f.y+18);
    if(f.kind==='travel_shrine'){window.GauntletDungeonSprites?.stamp(ctx,'portal_shrine',f.x,f.y+18,{scale:.6});return true;}
    if(f.kind==='witness')return npc(ctx,'runner',f.x,f.y,{gesture:near});
    if(['brook_outlet','mill_wheel','watch_register','network_seal','pumping_register','dry_ditch','rooted_crop','empty_granary','field_restored','additive_ledger','channel_west','channel_east','sluice_open','cellar_begin','dry_spring','east_landmark','ridge_barrier'].includes(f.id))return stamp(ctx,f.id==='dry_spring'?'moss_cache':f.id.includes('channel')||f.id==='sluice_open'?'workbench_stocked':f.id==='cellar_begin'?'ruins_seal':'woodland_sign',f.x,f.y+18,{scale:.7});
    if(f.kind==='talk')return npc(ctx,'runner',f.x,f.y,{gesture:near});
    if(f.kind==='hunter')return npc(ctx,f.id==='hunter'?'injured':'recovered',f.x,f.y,{gesture:near && f.id!=='hunter'});
    if(f.id==='watch')return true; // Its arch/bench story landmark is drawn in scenery.
    const id={east_landmark:'woodland_sign',cache:'moss_cache',tracks:'hunter_tracks',sign:'woodland_sign',rootwater_sign:'woodland_sign',kit:'repair_chest',altar:a.shrineRestored?'shrine_restored':'shrine_corrupt',
      repair:a.bridge?'workbench_used':'workbench_stocked',seal:a.locked?'ruins_seal_awake':'ruins_seal'}[f.id];
    if(!id)return false;
    const drawn=stamp(ctx,id,f.x,f.y+18);
    if(drawn&&f.id==='altar'&&!reducedMotion()){
      const age=performance.now()+phase(id,f.x,f.y);
      ctx.save();ctx.globalAlpha=(near?.14:.035)+.015*Math.sin(age/1100);ctx.fillStyle=a.shrineRestored?'#b9ffd4':'#dfb8ff';
      ctx.beginPath();ctx.arc(f.x,f.y-58,8,0,Math.PI*2);ctx.fill();ctx.restore();
    }
    return drawn;
  }
  function trail(ctx,e,near=false,room=null) {
    if(window.GauntletDungeonSprites?.trail(ctx,e,room))return true;
    ctx.save();ctx.translate(e.x,e.y);ctx.rotate(({north:0,east:Math.PI/2,south:Math.PI,west:-Math.PI/2})[e.edge]||0);
    if(near&&!e.locked){ctx.shadowColor='#b6f599';ctx.shadowBlur=9;}
    const drawn=stamp(ctx,e.locked?'trail_locked':'trail_open',0,10); // Steady waystones; nearby glow is static.
    if(e.dungeonComplete){
      // A fixed green pennant distinguishes reopened passages without a pulsing effect.
      ctx.fillStyle='#162c25';ctx.fillRect(20,-18,3,28);
      ctx.fillStyle='#acd88d';ctx.fillRect(23,-18,13,10);ctx.fillRect(23,-8,8,4);
    }
    ctx.restore();return drawn;
  }
  function mapIcon(area,a={}) {
    area=({brook:'shrine',mill_trail:'road',yard:'camp',hollow:'clearing',watch:'clearing',network:'ruins',border:'road',dunmere:'home',fields:'camp',eastern_threshold:'road',mill:'ruins',cellar:'ruins'})[area]||area;
    if(!['road','crossroads','camp','clearing','shrine','bridge','ruins','home'].includes(area))area='road';
    const state=area==='bridge'&&a.bridge?'-repaired':area==='shrine'&&a.shrineRestored?'-restored':'';
    return root+'adventure-map-'+area+state+'-v1.png';
  }
  function featureBounds(f,a){
    const regional=window.GauntletRegionSprites?.bounds(f,a);if(regional)return regional;
    if(f.kind==='travel_shrine')return window.GauntletDungeonSprites?.bounds('portal_shrine',f.x,f.y+18,.6);
    const id={ridge_barrier:'trail_locked',east_landmark:'woodland_sign',kit:'repair_chest',cache:'moss_cache',tracks:'hunter_tracks',sign:'woodland_sign',rootwater_sign:'woodland_sign',altar:a.shrineRestored?'shrine_restored':'shrine_corrupt',repair:a.bridge?'workbench_used':'workbench_stocked',seal:a.locked?'ruins_seal_awake':'ruins_seal'}[f.id];
    if(!id)return null;
    for(const entry of Object.values(packs)){const m=entry.metadata,row=m?.rows.find(r=>r.id===id);if(!row||!entry.image.naturalWidth)continue;
      return window.GauntletWorldScenery?.spriteBounds(entry.image,0,row.row*m.cell,m.cell,m.cell,Math.round(f.x-m.anchor[0]),Math.round(f.y+18-m.anchor[1]),m.cell,m.cell);
    }return null;
  }
  function groundPaths(room,w,h){return (paths[room.adventure?.area]||[]).map(path=>path.map(([x,y])=>[x*w/960,y*h/540]));}
  window.GauntletAdventureSprites={stamp,npc,backdrop,scenery,feature,featureBounds,trail,mapIcon,groundPaths};
})();
