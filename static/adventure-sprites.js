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
    eastern_threshold:[[[0,173],[270,210],[440,320],[640,330],[790,345]],[[640,330],[810,410],[960,420]],[[440,320],[480,430],[480,540]]],
    irrigation_channels:[[[480,0],[460,240],[420,315],[730,260],[960,270]],[[730,260],[820,420],[960,421]]],
    farmstead:[[[0,270],[300,280],[500,320],[650,190]],[[500,320],[480,140],[480,0]],[[500,320],[680,410]]],
    pump_exterior:[[[480,540],[340,340],[520,250],[740,290],[960,270]]],
    sluice_entry:[[[0,270],[480,270],[960,270]],[[480,270],[450,390],[650,400]]],
    sluice_gallery:[[[0,270],[480,270],[960,270]],[[480,270],[480,0]],[[480,270],[480,365]]],
    sluice_alcove:[[[480,540],[510,330],[490,190]]],
    pump_chamber:[[[0,270],[480,270],[700,370]],[[480,270],[360,400],[0,432]]],
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
  function seeded(seed){let n=seed>>>0;return()=>{n=(Math.imul(n,1664525)+1013904223)>>>0;return n/4294967296;};}
  function traceRoute(g,points){
    g.moveTo(...points[0]);
    for(let i=1;i<points.length-1;i++)g.quadraticCurveTo(...points[i],(points[i][0]+points[i+1][0])/2,(points[i][1]+points[i+1][1])/2);
    g.lineTo(...points[points.length-1]);
  }
  function fieldPlot(g,x,y,w,h,restored,seed){
    const rng=seeded(seed),bed=document.createElement('canvas');bed.width=w;bed.height=h;const b=bed.getContext('2d');
    b.fillStyle=restored?'#7c80524a':'#75664d4d';b.fillRect(0,0,w,h);
    // Broken, shallow furrows follow the soil instead of outlining a rectangle.
    for(let yy=12;yy<h-5;yy+=12+Math.floor(rng()*3)){
      const start=5+Math.floor(rng()*10),end=w-5-Math.floor(rng()*12);
      for(let xx=start;xx<end;){const length=Math.min(end-xx,22+Math.floor(rng()*48));
        b.fillStyle=restored?'#52634250':'#4f493748';b.fillRect(xx,yy,length,1);
        b.fillStyle='#c3ac7e30';b.fillRect(xx+2,yy+2,Math.max(1,length-4),1);xx+=length+2+Math.floor(rng()*6);}
    }
    for(let i=0;i<w*h/85;i++){b.fillStyle=i%3?'#a5946820':'#514b3922';b.fillRect(Math.floor(rng()*w),Math.floor(rng()*h),2+Math.floor(rng()*5),1+Math.floor(rng()*2));}
    for(let i=0;i<w*h/1300;i++){const px=12+Math.floor(rng()*(w-24)),py=12+Math.floor(rng()*(h-24));b.fillStyle=restored?'#6c875a90':'#8c875b70';b.fillRect(px,py,1,3);b.fillRect(px-2,py,2,1);b.fillStyle=restored?'#a0ae6c80':'#b2a07360';b.fillRect(px+1,py-1,2,1);}
    // Soft alpha margins retain crisp small pixels, without boxed plot borders.
    b.globalCompositeOperation='destination-in';
    const horizontal=b.createLinearGradient(0,0,w,0);horizontal.addColorStop(0,'#0000');horizontal.addColorStop(.07,'#000');horizontal.addColorStop(.93,'#000');horizontal.addColorStop(1,'#0000');b.fillStyle=horizontal;b.fillRect(0,0,w,h);
    const vertical=b.createLinearGradient(0,0,0,h);vertical.addColorStop(0,'#0000');vertical.addColorStop(.12,'#000');vertical.addColorStop(.88,'#000');vertical.addColorStop(1,'#0000');b.fillStyle=vertical;b.fillRect(0,0,w,h);
    g.drawImage(bed,x,y);
  }
  function dryLand(ctx,room){
    const a=room.adventure,area=a.area,w=room.areaSize[0],h=room.areaSize[1],restored=a.chapter?.find(q=>q.id==='irrigation')?.found.includes('sluice_open');
    const key=[area,w,h,Boolean(restored)].join(':');let ground=dryLayers.get(key);
    if(!ground){ground=document.createElement('canvas');ground.width=960;ground.height=540;const g=ground.getContext('2d');
      const fade=g.createLinearGradient(0,0,960,0);fade.addColorStop(0,area==='fields'?'#71864b10':'#a89b6320');fade.addColorStop(.45,'#b5a26938');fade.addColorStop(1,'#c0a87560');g.fillStyle=fade;g.fillRect(0,0,960,540);
      // Field-scale passable soil plots, not additional barriers or implied water.
      const plots=area==='fields'?[[105,95,275,135],[510,80,320,140],[185,350,375,120]]:area==='farmstead'?[[100,105,310,130],[535,340,290,145]]:area==='irrigation_channels'?[[80,385,380,105],[565,75,265,115]]:[[105,95,260,115],[590,365,260,110]];
      for(const [x,y,pw,ph] of plots)fieldPlot(g,x,y,pw,ph,restored&&x<300,phase(area,x,y));
      // Feather the dry soil along the same curved paths as the base layer.
      // A single stroke per band keeps junctions free of darker overlapping wedges.
      g.save();g.globalCompositeOperation='destination-out';g.lineJoin=g.lineCap='round';g.strokeStyle='#000';
      for(const [width,alpha]of[[100,.06],[84,.08],[70,.12],[58,.18],[46,.28]]){g.lineWidth=width;g.globalAlpha=alpha;g.beginPath();for(const path of paths[area]||[])traceRoute(g,path);g.stroke();}g.restore();
      if(area==='eastern_threshold'){
        // The fixed shed footprint exactly matches the authoritative wood barrier.
        // The existing granary sheet is drawn below, over this stable ground layer.
        for(const [x,y] of [[200,120],[530,455],[880,120]]){g.strokeStyle='#514c35';g.lineWidth=5;g.beginPath();g.moveTo(x,y);g.lineTo(x,y-48);g.moveTo(x,y-24);g.lineTo(x-19,y-39);g.moveTo(x,y-30);g.lineTo(x+17,y-50);g.stroke();}
        for(let i=0;i<7;i++){g.fillStyle='#6a6343';g.fillRect(655+i*30,440,4,22);g.fillRect(655+i*30,447,33,3);}
        g.fillStyle='#554f38';g.fillRect(455,130,4,35);g.fillRect(441,140,32,4);g.fillStyle='#a48e5c';g.fillRect(449,126,15,12);
      }
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
    if(window.GauntletCampaignScenery?.floor(ctx,room,w,h))return true;
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
          g.beginPath();for(const path of authored)traceRoute(g,path.map(([x,y])=>[x*w/960,y*h/540]));g.stroke();
        }
        g.globalAlpha=1;
      }
      cache=key;
    }
    ctx.save();ctx.imageSmoothingEnabled=false;ctx.drawImage(layer,0,0,w,h);ctx.restore();return true;
  }
  function scenery(ctx,room) {
    const a=room.adventure;if(!a)return;
    if(window.GauntletCampaignScenery?.groundDecor(ctx,room))return;
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
    if(['fields','eastern_threshold','irrigation_channels','farmstead','pump_exterior'].includes(a.area))dryLand(ctx,room);
    if(['irrigation_channels','farmstead','pump_exterior'].includes(a.area)){
      ctx.save();ctx.scale(room.areaSize[0]/960,room.areaSize[1]/540);
      for(const b of room.environment?.barriers||[]){
        const x=b.x*960/room.areaSize[0],y=b.y*540/room.areaSize[1],w=b.width*960/room.areaSize[0],h=b.height*540/room.areaSize[1];
        if(b.material==='water')waterSurface(ctx,x,y,w,h,{seed:b.id});
        else if(!window.GauntletRegionSprites?.barrier(ctx,{...b,x,y,width:w,height:h},a.area)){
          if(b.material!=='stone'||!window.GauntletDungeonSprites?.barrier(ctx,{...b,x,y,width:w,height:h},false)){ctx.fillStyle=b.material==='wood'?'#675d41':'#58675f';ctx.fillRect(x,y,w,h);}
        }
      }
      if(a.area==='farmstead')stamp(ctx,'hunter_tracks',420,360,{scale:.7});ctx.restore();
    }
    if(a.area==='bridge')bridge(ctx,room);
    if(['brook','mill_trail','yard','hollow','watch','network','border','fields','mill','eastern_threshold'].includes(a.area)){
      const w=room.areaSize?.[0]||960,h=room.areaSize?.[1]||540;ctx.save();ctx.scale(w/960,h/540);
      if(a.area==='brook'){
        waterSurface(ctx,295,205,120,65,{seed:'brook'});
      }
      if(a.area==='yard'){stamp(ctx,'camp_bench',380,260);stamp(ctx,'road_wagon',620,220,{scale:.75});}
      if(a.area==='hollow')stamp(ctx,'hunter_tracks',800,135,{scale:.7});
      if(a.area==='watch')stamp(ctx,'burned_watch',525,200,{scale:.65});
      if(a.area==='border')stamp(ctx,'road_wagon',690,260,{scale:.7});
      if(a.area==='fields'&&a.chapter?.find(q=>q.id==='irrigation')?.found.includes('sluice_open'))waterSurface(ctx,240,318,390,7,{seed:'restored-fields',banks:false});
      if(a.area==='eastern_threshold'&&!window.GauntletRegionSprites?.feature(ctx,{id:'empty_granary',x:660,y:190},a)){ctx.fillStyle='#756b45';ctx.fillRect(600,140,120,65);}
      if(a.area==='mill')irrigationWater(ctx);
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
    if(a.area==='fields'&&a.campaignExtension?.facts?.includes('repair:dunmere_reserve')){
      const sx=(room.areaSize?.[0]||960)/960,sy=(room.areaSize?.[1]||540)/540;
      stamp(ctx,'workbench_used',300*sx,408*sy,{scale:.7});waterSurface(ctx,275*sx,417*sy,95*sx,8*sy,{seed:'dunmere-reserve',banks:false});
    }
    if(['home','dunmere'].includes(a.area)&&a.campaign){
      const c=a.campaign,npc=a.features.find(f=>f.id===(a.area==='home'?'edda':'tovin'));
      if(npc){ctx.save();const x=npc.x+42,y=npc.y+30;
        if(c.workers){ctx.fillStyle='#a08a58';ctx.fillRect(x,y,18,9);ctx.fillStyle='#d1bf83';ctx.fillRect(x+2,y+1,14,3);}
        if(c.letters&&a.area==='home'){ctx.fillStyle='#786447';ctx.fillRect(x+25,y-18,23,19);ctx.fillStyle='#e2d0a0';ctx.fillRect(x+29,y-14,7,8);ctx.fillRect(x+38,y-12,7,9);}
        if(c.seedDestination===(a.area==='home'?'oakvale':'dunmere')||c.pumpingRestored&&a.area==='dunmere')for(let i=0;i<5;i++){ctx.fillStyle='#695938';ctx.fillRect(x+i*8,y+17,7,9);ctx.fillStyle='#84ad62';ctx.fillRect(x+2+i*8,y+13,3,8);}
        if(a.area==='dunmere'&&c.relief){ctx.fillStyle=c.relief==='workers'?'#d5c69a':'#6ca2a1';ctx.fillRect(x+50,y+6,11,8);ctx.fillRect(x+64,y+6,11,8);}
        ctx.restore();}
    }
  }
  function campfire(ctx,x,y) {
    stamp(ctx,'camp_fire',x,y);
    if(reducedMotion())return;
    const age=performance.now()+phase('camp_fire',x,y),pulse=.12+.05*Math.sin(age/570);
    ctx.save();ctx.globalAlpha=pulse;ctx.fillStyle='#ffe38b';ctx.fillRect(x-3,y-30,5,9);ctx.restore();
    const cycle=age%4300;
    if(cycle<700){ctx.save();ctx.globalAlpha=.3*(1-cycle/700);ctx.fillStyle='#ecac55';ctx.fillRect(x+3,y-34-Math.floor(cycle/100),1,2);ctx.restore();}
  }
  const waterLayers=new Map();
  function waterSurface(ctx,x,y,width,height,{seed='water',banks=true}={}){
    const w=Math.max(1,Math.ceil(width)),h=Math.max(1,Math.ceil(height)),key=[seed,w,h,banks].join(':');let surface=waterLayers.get(key);
    if(!surface){surface=document.createElement('canvas');surface.width=w;surface.height=h;const g=surface.getContext('2d'),rng=seeded(phase(String(seed),w,h));
      const depth=g.createLinearGradient(0,0,0,h);depth.addColorStop(0,'#365e60');depth.addColorStop(.45,'#477b78');depth.addColorStop(1,'#355f62');g.fillStyle=depth;g.fillRect(0,0,w,h);
      // One continuous surface per channel, with quiet irregular current streaks.
      // No rectangular crop/tile borders or bright checkerboard foam.
      for(let i=0;i<w*h/85;i++){const px=Math.floor(rng()*w),py=Math.floor(rng()*h);g.fillStyle=i%3?'#719b8b18':'#173e4a18';g.fillRect(px,py,5+Math.floor(rng()*26),1+Math.floor(rng()*2));}
      if(banks){
        // Uneven moss/silt margins read as banks rather than a framed blue panel.
        for(let px=0;px<w;){const length=4+Math.floor(rng()*9),top=1+Math.floor(rng()*3),bottom=1+Math.floor(rng()*3);g.fillStyle='#61744d';g.fillRect(px,0,length,top);g.fillRect(px,h-bottom,length,bottom);g.fillStyle='#2b4f4780';g.fillRect(px,top,length,1);g.fillRect(px,h-bottom-1,length,1);g.fillStyle='#91a16b50';g.fillRect(px+1,0,Math.max(1,length-3),1);px+=length;}
        for(let py=0;py<h;){const length=4+Math.floor(rng()*7),left=1+Math.floor(rng()*3),right=1+Math.floor(rng()*3);g.fillStyle='#61744d';g.fillRect(0,py,left,length);g.fillRect(w-right,py,right,length);g.fillStyle='#2b4f4780';g.fillRect(left,py,1,length);g.fillRect(w-right-1,py,1,length);py+=length;}
        for(let i=0;i<w/38;i++){const px=5+Math.floor(rng()*(w-10)),py=rng()<.5?1:h-3;g.fillStyle='#82966c90';g.fillRect(px,py,1,3);g.fillRect(px+2,py+1,1,2);}
      }
      waterLayers.set(key,surface);while(waterLayers.size>16)waterLayers.delete(waterLayers.keys().next().value);
    }
    ctx.save();ctx.imageSmoothingEnabled=false;ctx.drawImage(surface,x,y,width,height);ctx.restore();
    waterRipples(ctx,x+4,y+4,width-8,height-8,performance.now()+phase(String(seed),x,y));
  }
  function irrigationWater(ctx){
    ctx.save();ctx.lineJoin=ctx.lineCap='round';
    const path=()=>{ctx.beginPath();traceRoute(ctx,[[290,385],[360,390],[435,385],[515,389],[600,384],[690,385]]);};
    for(const[width,color]of[[19,'#625f43'],[14,'#697751'],[9,'#487876']]){ctx.lineWidth=width;ctx.strokeStyle=color;path();ctx.stroke();}
    ctx.restore();waterRipples(ctx,295,382,390,10,performance.now());
  }
  function waterRipples(ctx,left,top,width,height,age) {
    if(reducedMotion()||width<8||height<3)return;
    ctx.save();ctx.beginPath();ctx.rect(left,top,width,height);ctx.clip();
    const rng=seeded(phase('ripples',Math.round(left),Math.round(top))),count=Math.min(14,2+Math.floor(width*height/2600));
    for(let i=0;i<count;i++){
      const x=Math.round(left+rng()*Math.max(1,width-18)+Math.sin(age/2300+i)*2),y=Math.round(top+rng()*Math.max(1,height-3));
      ctx.globalAlpha=.09+.04*Math.sin(age/1700+i*1.7);ctx.fillStyle='#b0cbb9';ctx.fillRect(x,y,5+Math.floor(rng()*12),1);
    }
    ctx.restore();
  }
  function bridge(ctx,room) {
    const a=room.adventure,b=a.bridgeLayout;if(!b)return;
    const {left,right}=b.river,height=room.areaSize?.[1]||540,age=performance.now()+phase('bridge',b.sprite.x,b.sprite.y);
    // Fixed river/banks from the imported art. Only ripple highlights move.
    ctx.save();ctx.imageSmoothingEnabled=false;
    waterSurface(ctx,left,0,right-left,height,{seed:'bridge-river'});
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
    if(window.GauntletCampaignArt?.feature(ctx,f,a,near))return true;
    if(window.GauntletCampaignScenery?.feature(ctx,f,a))return true;
    if(f.id==='sluice_survey'&&f.claimed)return window.GauntletDungeonSprites?.stamp(ctx,'survey_cache_open',f.x,f.y+18,{scale:.8});
    if(f.portrait&&window.GauntletTownSprites?.character(ctx,f.portrait,f.x,f.y,{scale:.85,phase:phase(f.id,f.x,f.y)}))return true;
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
    if(f.kind==='clue')return stamp(ctx,'woodland_sign',f.x,f.y+18,{scale:.55});
    if(f.kind==='mechanism')return stamp(ctx,f.id==='warden_begin'?'ruins_seal':f.id==='seed_supply'?'moss_cache':'workbench_stocked',f.x,f.y+18,{scale:.7});
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
    if(window.GauntletReleaseVisuals?.trail(ctx,e,near,room))return true;
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
    const campaign=window.GauntletCampaignScenery?.mapIcon(area,a);if(campaign)return campaign;
    // Reuse recognizable existing landmarks while the regional artwork is
    // authored. No runtime quest/item IDs depend on these cosmetic aliases.
    if(area?.startsWith('city_'))area=['city_refuge','city_homes'].includes(area)?'home':area==='city_approach'?'road':'ruins';
    else if(area?.startsWith('veil_'))area=area==='veil_haven'?'home':/sanct|siphon|grove|pools/.test(area)?'shrine':'clearing';
    else if(area?.startsWith('cinder_'))area=['cinder_foothills','cinder_ravine','cinder_upper','cinder_antechamber'].includes(area)?'camp':area==='cinder_lair'?'ruins':'road';
    area=({brook:'shrine',mill_trail:'road',yard:'camp',hollow:'clearing',watch:'clearing',network:'ruins',border:'road',dunmere:'home',fields:'camp',eastern_threshold:'road',mill:'ruins',cellar:'ruins'})[area]||area;
    if(!['road','crossroads','camp','clearing','shrine','bridge','ruins','home'].includes(area))area='road';
    const state=area==='bridge'&&a.bridge?'-repaired':area==='shrine'&&a.shrineRestored?'-restored':'';
    return root+'adventure-map-'+area+state+'-v1.png';
  }
  function featureBounds(f,a){
    const campaign=window.GauntletCampaignArt?.featureBounds(f,a);if(campaign)return campaign;
    const scenery=window.GauntletCampaignScenery?.featureBounds(f,a);if(scenery)return scenery;
    const regional=window.GauntletRegionSprites?.bounds(f,a);if(regional)return regional;
    if(f.kind==='travel_shrine')return window.GauntletDungeonSprites?.bounds('portal_shrine',f.x,f.y+18,.6);
    const id={ridge_barrier:'trail_locked',east_landmark:'woodland_sign',kit:'repair_chest',cache:'moss_cache',tracks:'hunter_tracks',sign:'woodland_sign',rootwater_sign:'woodland_sign',altar:a.shrineRestored?'shrine_restored':'shrine_corrupt',repair:a.bridge?'workbench_used':'workbench_stocked',seal:a.locked?'ruins_seal_awake':'ruins_seal'}[f.id];
    if(!id)return null;
    for(const entry of Object.values(packs)){const m=entry.metadata,row=m?.rows.find(r=>r.id===id);if(!row||!entry.image.naturalWidth)continue;
      return window.GauntletWorldScenery?.spriteBounds(entry.image,0,row.row*m.cell,m.cell,m.cell,Math.round(f.x-m.anchor[0]),Math.round(f.y+18-m.anchor[1]),m.cell,m.cell);
    }return null;
  }
  function groundPaths(room,w,h){return (paths[room.adventure?.area]||[]).map(path=>path.map(([x,y])=>[x*w/960,y*h/540]));}
  window.GauntletAdventureSprites={stamp,npc,backdrop,scenery,feature,featureBounds,trail,mapIcon,groundPaths,waterSurface};
})();
