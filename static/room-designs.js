// Authored passable floor compositions and cosmetic canopy masses. No collision.
(() => {
 const plans=window.GauntletRoomDesignData||{},layers=new Map(),legacyLayouts=new Map();let homes=null;const errors=new Set();
 function sceneImage(){if(!homes){homes=new Image();homes.onerror=()=>errors.add('release-aurelian-homes-v5.png');homes.src='/sprites/release-aurelian-homes-v5.png';}return homes;}
 function sceneBounds(frame,x,y,width){const m=window.GauntletReleaseSceneData?.homes,b=m?.frames[frame]?.bounds;if(!b)return null;const height=width*b[3]/b[2];return{x:x-width/2,y:y-height,width,height};}
 function sceneProp(g,frame,x,y,width){const m=window.GauntletReleaseSceneData?.homes,b=m?.frames[frame]?.bounds;if(!b)return false;const img=sceneImage(),d=sceneBounds(frame,x,y,width);if(img.complete&&img.naturalWidth){g.save();g.imageSmoothingEnabled=false;g.drawImage(img,frame*128+b[0],b[1],b[2],b[3],Math.round(d.x),Math.round(d.y),d.width,d.height);g.restore();}return true;}
 function landmark(g,area,b){if(area!=='city_homes')return false;return sceneProp(g,b.y<250?0:1,b.x+b.width/2,b.y+b.height,Math.min(225,b.width));}
 let defenses=null;
 function defenseImage(){if(!defenses){defenses=new Image();defenses.onerror=()=>errors.add('release-aurelian-defenses-v5.png');defenses.src='/sprites/release-aurelian-defenses-v5.png';}return defenses;}
 function defenseProp(g,frame,x,y,width){const m=window.GauntletReleaseSceneData?.defenses,b=m?.frames[frame]?.bounds;if(!b)return;const img=defenseImage();if(!img.complete||!img.naturalWidth)return;const height=width*b[3]/b[2];g.save();g.imageSmoothingEnabled=false;g.drawImage(img,frame*128+b[0],b[1],b[2],b[3],Math.round(x-width/2),Math.round(y-height),width,height);g.restore();}
 function solidBounds(area,b){
  if(!['city_barracks','city_square','city_observatory'].includes(area))return null;
  defenseImage();return{x:b.x,y:b.y-b.width*.45,width:b.width,height:b.height+b.width*.45};
 }
 function solid(g,area,b){
  if(area==='city_barracks'){defenseProp(g,b.y<300?0:1,b.x+b.width/2,b.y+b.height,b.width);return true;}
  if(area==='city_square'){const count=Math.ceil(b.height/(b.width*.52));for(let i=0;i<count;i++)defenseProp(g,2,b.x+b.width/2,b.y+(i+1)*b.height/count,b.width);return true;}
  if(area==='city_observatory'){defenseProp(g,3,b.x+b.width/2,b.y+b.height,b.width);return true;}
  return false;
 }
 function feature(g,f,a){return f.id==='defense:city_infirmary'&&a.area==='city_archive'?sceneProp(g,2,f.x,f.y+18,135):false;}
 function featureBounds(f,a){return f.id==='defense:city_infirmary'&&a.area==='city_archive'?sceneBounds(2,f.x,f.y+18,135):null;}
 function poly(g,p,fill){g.fillStyle=fill;g.beginPath();p.forEach(([x,y],i)=>g[i?'lineTo':'moveTo'](Math.round(x),Math.round(y)));g.closePath();g.fill();}
 const tones={aurelian:['#a69c83','#777b73','#cfbea0','#4c5555'],verdant:['#4f6350','#344f48','#85916b','#344841'],cinder:['#5d5a54','#363b41','#897d6b','#292e35'],dunmere:['#98865a','#706347','#b09a6d','#555441'],woodland:['#65734b','#405b41','#a09064','#394d3e'],ruins:['#747569','#4d5852','#a49a80','#394a47'],cavern:['#515e62','#334951','#788581','#263d47']};
 const floorImages=new Map();
 const floorFiles={city_square:'release-city-square-floor-v5.png',city_homes:'release-city-homes-floor-v5.png',city_barracks:'release-city-barracks-floor-v5.png',city_archive:'release-city-archive-floor-v5.png',city_observatory:'release-city-observatory-floor-v5.png',veil_glades:'release-veil-glades-floor-v5.png',veil_grove:'release-veil-grove-floor-v5.png',veil_pools:'release-veil-pools-floor-v5.png',cinder_lava_road:'release-cinder-causeway-v5.png'};
 function floorImage(id){const file=floorFiles[id];if(!file)return null;let img=floorImages.get(id);
  if(!img){img=new Image();img.onerror=()=>errors.add(file);img.src='/sprites/'+file;floorImages.set(id,img);while(floorImages.size>4)floorImages.delete(floorImages.keys().next().value);}
  else{floorImages.delete(id);floorImages.set(id,img);}return img;
 }
 function ground(g,r,w,h){
  const p=plans[r.adventure?.area];if(!p||r.devTools?.arena||r.townInterior||r.phase==='town'||p.id==='caravan')return false;
  const authoredFloor=floorImage(p.id);
  if(authoredFloor?.complete&&authoredFloor.naturalWidth){
   g.save();g.imageSmoothingEnabled=false;g.drawImage(authoredFloor,0,0,w,h);
   if(p.id==='veil_glades'&&(r.adventure.campaignExtension?.facts||[]).includes('bond_broken')){
    g.fillStyle='#65784c';g.globalAlpha=.48;for(let i=0;i<24;i++){const x=w*(.58+(i%6)*.035),y=h*(.3+Math.floor(i/6)*.065);g.fillRect(Math.round(x),Math.round(y),4,2);g.fillRect(Math.round(x)+2,Math.round(y)-3,2,3);}
   }
   g.restore();return true;
  }
  const changed=(r.adventure?.campaignExtension?.facts||[]).filter(f=>/bond_broken|ending:campaign|repair:|defense:/.test(f)).join('|'),key=[p.id,w,h,changed].join(':');let c=layers.get(key);
  if(!c){c=document.createElement('canvas');c.width=Math.ceil(w/2);c.height=Math.ceil(h/2);const q=c.getContext('2d');q.scale(w/960/2,h/540/2);const t=tones[p.region]||tones[r.region]||tones.woodland;
   // Calm the source material before adding large readable authored ground forms.
   q.fillStyle=t[0];q.globalAlpha=p.region==='aurelian'?.32:p.region==='cinder'?.25:.13;q.fillRect(0,0,960,540);q.globalAlpha=1;
   const slab=(x,y,ww,hh,color=t[2],alpha=.23)=>{q.globalAlpha=alpha;q.fillStyle=color;q.fillRect(x,y,ww,hh);q.globalAlpha=1;};
   const band=(points,width=28,color=t[2],alpha=.2)=>{q.save();q.lineWidth=width;q.strokeStyle=color;q.lineJoin='bevel';q.lineCap='butt';q.globalAlpha=alpha;q.beginPath();points.forEach(([x,y],i)=>q[i?'lineTo':'moveTo'](x,y));q.stroke();q.restore();};
   const oval=(x,y,rx,ry,color=t[1],alpha=.17)=>{q.save();q.fillStyle=color;q.globalAlpha=alpha;q.beginPath();q.ellipse(x,y,rx,ry,0,0,Math.PI*2);q.fill();q.restore();};
   const radial=(cx,cy,rx,ry,n=8)=>{for(let i=0;i<n;i++){const a=i*Math.PI*2/n;band([[cx+Math.cos(a)*42,cy+Math.sin(a)*28],[cx+Math.cos(a)*rx,cy+Math.sin(a)*ry]],7,t[1],.32);}};
   // Authored passable paving. Individual stone joints and worn edges retain the
   // regional material instead of leaving large flat diagram-like polygons.
   const stoneFill=(shape,dark=false)=>{q.save();shape();q.clip();q.globalAlpha=p.region==='cinder'?.9:p.region==='aurelian'?.72:.46;q.fillStyle=t[dark?1:2];q.fillRect(0,0,960,540);
    for(let yy=38,row=0;yy<535;yy+=22,row++)for(let xx=12+(row%2)*17,col=0;xx<955;xx+=34,col++){
     const n=(row*37+col*19)%11,w=25+n%5,hh=15+n%3;q.globalAlpha=dark?.15:.18;q.fillStyle=t[n%3===0?3:0];q.fillRect(xx,yy,w,hh);
     q.globalAlpha=dark?.25:.31;q.fillStyle=t[2];q.fillRect(xx+2,yy,w-4,2);q.globalAlpha=.16;q.fillStyle=t[3];q.fillRect(xx+w-2,yy+3,2,hh-3);
     if(n<3){q.globalAlpha=.22;q.fillStyle=t[1];q.fillRect(xx+7,yy+5,4,2);q.fillRect(xx+9,yy+7,2,4);}
    }q.restore();};
   const paving=pts=>stoneFill(()=>{q.beginPath();pts.forEach(([x,y],i)=>q[i?'lineTo':'moveTo'](x,y));q.closePath();},true);
   switch(p.layout){
    case 'civic':
     stoneFill(()=>{q.beginPath();q.ellipse(480,265,279,188,0,0,Math.PI*2);});
     for(const[rx,ry,n]of[[262,175,40],[197,130,32]])for(let i=0;i<n;i++){
      if(i===7||i===8||i===24)continue;const a=i*Math.PI*2/n,b=(i+.88)*Math.PI*2/n;
      q.globalAlpha=.32;poly(q,[[480+Math.cos(a)*rx,265+Math.sin(a)*ry],[480+Math.cos(b)*rx,265+Math.sin(b)*ry],[480+Math.cos(b)*(rx-9),265+Math.sin(b)*(ry-6)],[480+Math.cos(a)*(rx-9),265+Math.sin(a)*(ry-6)]],i%3?t[1]:t[2]);q.globalAlpha=1;
     }
     for(const[x,y,s]of[[470,226,1],[493,248,-1],[470,270,1],[447,248,-1]])for(let k=0;k<4;k++){q.globalAlpha=.44;poly(q,[[x,y+k*5],[x+s*(17-k*4),y+k*5+10],[x,y+k*5+14],[x-s*3,y+k*5+7]],k%2?t[1]:'#b7a77c');q.globalAlpha=1;}
     band([[110,405],[328,322],[419,293]],18,t[3],.35);band([[690,160],[795,114],[850,118]],14,t[3],.35);break;
    case 'residential':
     paving([[45,225],[370,225],[570,282],[945,282],[945,372],[560,372],[350,310],[45,310]]);
     band([[65,219],[380,219],[575,276],[940,276]],4,t[2],.7);band([[65,316],[350,316],[555,378],[940,378]],4,t[1],.7);
     for(const[x,y,ww]of[[130,95,200],[550,135,275],[220,370,220],[620,390,185]]){slab(x,y,ww,48,t[1],.22);slab(x,y+4,ww,3,t[2],.4);}
     band([[100,285],[390,285],[570,325],[870,325]],55,t[2],.22);
     for(const[x,y]of[[345,170],[700,375],[270,440]]){slab(x,y,16,10,'#77675c',.65);slab(x+3,y+2,9,2,'#c2a181',.6);}break;
    case 'infirmary':
     slab(210,125,570,290,t[1],.2);slab(230,147,530,245,t[2],.25);band([[480,110],[480,438]],43,t[2],.32);
     for(const[x,y]of[[285,180],[590,180],[285,320],[590,320]]){slab(x,y,85,29,'#c2baa1',.32);slab(x+4,y+5,77,3,'#e1d3b2',.25);}
     break;
    case 'military':
     if(p.region==='aurelian'){
      paving([[120,95],[760,95],[865,175],[865,440],[760,465],[120,465]]);
      for(let i=0;i<3;i++){
       const y=140+i*105;slab(145,y,625,3,'#d0bc8e',.75);slab(145,y+58,625,2,'#323d44',.75);
       for(let k=0;k<9;k++){slab(210+k*60,y+9,2,20,'#c7b48d',.55);slab(205+k*60,y+29,12,2,'#c7b48d',.55);}
      }
      for(const[x,y]of[[170,112],[790,425]]){slab(x,y,26,8,'#374857',.8);slab(x+9,y-5,8,18,'#c3a66f',.7);}
      band([[120,415],[350,270],[485,292]],13,'#353b3c',.5);
     }else{for(let i=0;i<3;i++)band([[130,155+i*94],[420,155+i*94],[510,177+i*94],[820,177+i*94]],22,t[2],.5);}
     break;
    case 'overlook':
     for(let i=0;i<4;i++)band([[85,75+i*18],[685,75+i*18],[815,135+i*18]],6,t[2],.38);
     band([[480,500],[480,315],[600,215]],94,t[2],.19);radial(600,215,150,95,6);break;
    case 'broken-road':
     // Fractured cooled basalt with ash-filled seams remains walkable. No fake hazard.
     for(const pts of [[[0,85],[210,57],[360,127],[340,152],[170,108],[0,137]],[[635,410],[780,393],[960,450],[960,514],[780,455],[665,465]]]){poly(q,pts,'#3a3d41');band(pts.slice(0,3),6,'#938273',.6);}
     for(const pts of [[[35,243],[260,208],[300,257],[262,315],[34,333]],[[290,205],[485,185],[520,246],[477,300],[304,314]],[[530,217],[710,235],[735,298],[543,311]],[[754,233],[932,253],[932,327],[749,303]]]){
      q.save();q.translate(0,7);poly(q,pts,'#252b32');q.restore();paving(pts);band(pts.slice(0,3),5,'#a18d78',.8);
      band([pts[pts.length-1],pts[0]],3,'#b5a18a',.65);
      for(let i=0;i<pts.length-1;i++){const[x,y]=pts[i],b=pts[i+1];for(let n=1;n<5;n++){const px=x+(b[0]-x)*n/5,py=y+(b[1]-y)*n/5;slab(px,py,5+n%2*3,3,t[2],.3);}}
     }
     paving([[468,302],[539,306],[526,380],[491,510],[419,510],[453,372]]);
     for(const[x,y]of[[290,267],[518,242],[742,285]]){band([[x-8,y-24],[x+2,y],[x-6,y+25]],7,'#20272f',.9);band([[x-3,y-20],[x+7,y],[x-1,y+22]],2,'#bb9b78',.65);slab(x+10,y+8,9,4,t[2],.65);}break;
    case 'ravine':
     poly(q,[[0,74],[310,60],[600,191],[960,155],[960,180],[600,218],[310,90],[0,103]],t[1]);
     band([[75,405],[320,388],[490,270],[740,295],[890,390]],58,t[2],.21);break;
    case 'slope':
     for(const [x,y]of[[180,70],[500,130],[720,315]]){q.globalAlpha=.25;poly(q,[[x,y],[x+180,y+15],[x+70,y+110],[x-50,y+135]],t[2]);q.globalAlpha=1;}
     band([[70,450],[420,285],[850,220]],31,t[1],.35);break;
    case 'crown':
     oval(480,280,330,205,t[3],.31);radial(480,280,275,170,9);
     band([[240,305],[230,180],[360,237],[480,123],[600,237],[730,180],[720,305]],17,t[2],.3);
     band([[240,329],[440,329]],12,t[2],.3);band([[500,329],[720,329]],12,t[2],.3);break;
    case 'siphon-west':
     for(const path of [[[65,95],[265,145],[480,265]],[[70,445],[285,380],[480,265]],[[850,100],[695,175],[480,265]]]){band(path,24,t[1],.5);band(path,5,changed.includes('bond_broken')?t[2]:'#756591',.35);}break;
    case 'siphon-east':
     for(let i=0;i<4;i++)band([[180+i*32,90+i*80],[640+i*32,120+i*80],[750,170+i*80]],16,t[1],.45);
     band([[760,420],[650,270],[410,270]],7,changed.includes('bond_broken')?t[2]:'#756591',.42);break;
    case 'pools':
     for(const[x,y,rx,ry]of[[300,190,190,100],[660,350,210,108]]){oval(x,y,rx,ry,t[1],.24);oval(x,y,rx-16,ry-9,t[2],.18);oval(x+12,y,rx-49,ry-28,t[0],.4);}break;
    case 'orbit':
     for(const[n,rx,ry]of[[0,245,150],[1,180,110],[2,90,55]]){q.save();q.strokeStyle=t[n%2?1:2];q.globalAlpha=.35;q.lineWidth=5;q.beginPath();q.ellipse(525,270,rx,ry,-.2,-.4,Math.PI*1.65);q.stroke();q.restore();}radial(525,270,210,125,5);break;
    case 'sanctuary':
     band([[480,75],[480,470]],68,t[2],.18);for(let i=0;i<5;i++)slab(407,146+i*48,146,5,t[1],.38);oval(480,280,220,135,t[1],.17);break;
    case 'furrows':
     for(const[x,y,ww,hh]of[[90,95,290,125],[570,118,255,110],[145,370,260,80]])for(let n=0;n<hh;n+=14)band([[x,y+n],[x+ww*.45,y+n+7],[x+ww,y+n]],3,t[1],.24);break;
    case 'procession':
     band([[40,340],[280,310],[560,270],[920,240]],74,t[2],.2);for(const s of[-1,1])band([[40,340+s*22],[280,310+s*22],[560,270+s*22],[920,240+s*22]],5,t[1],.31);break;
    case 'junction':band([[60,270],[480,275],[890,260]],65,t[2],.17);band([[480,55],[480,275],[640,495]],54,t[2],.19);oval(480,275,110,63,t[1],.16);break;
    case 'bend':band([[90,460],[340,350],[570,285],[720,85]],88,t[2],.16);band([[110,450],[350,350],[580,285],[730,95]],6,t[1],.2);break;
    case 'crossing':band([[60,275],[900,275]],92,t[2],.17);band([[60,234],[900,234]],5,t[1],.25);band([[60,317],[900,317]],5,t[1],.25);break;
    case 'split':band([[200,85],[340,220],[330,470]],32,t[2],.2);band([[760,85],[620,220],[630,470]],32,t[2],.2);break;
    case 'mouth':oval(480,130,240,80,t[3],.2);for(let i=-2;i<=2;i++)band([[480+i*26,120],[480+i*92,460]],9,t[1],.18);break;
    case 'ritual':oval(480,280,235,143,t[1],.2);oval(480,280,213,128,t[2],.15);radial(480,280,190,110,8);break;
    case 'court':slab(220,120,530,320,t[1],.16);for(const[x,y,ww,hh]of[[220,120,530,5],[220,435,530,5],[220,120,5,320],[745,120,5,320]])slab(x,y,ww,hh,t[2],.35);break;
    case 'alcove':slab(320,220,240,125,t[2],.1);for(let i=0;i<4;i++)slab(355+i*48,265,15,3,t[2],.4);break;
    case 'den':oval(480,285,235,148,t[1],.24);for(let i=0;i<7;i++)band([[350+i*23,290],[370+i*23,325]],3,t[2],.22);break;
    case 'scar':oval(500,225,200,108,t[3],.25);for(let i=0;i<6;i++)band([[350+i*43,170],[315+i*53,335]],9,t[3],.25);break;
    case 'camp':oval(480,300,170,112,t[1],.21);for(const[x,y]of[[310,220],[600,250],[350,370]])slab(x,y,50,23,t[2],.18);break;
    case 'clearing':oval(420,290,245,155,t[2],.12);band([[170,180],[300,130],[510,140],[660,215]],34,t[1],.2);break;
   }
   layers.set(key,c);while(layers.size>4)layers.delete(layers.keys().next().value);
  }
  g.save();g.imageSmoothingEnabled=false;g.drawImage(c,0,0,w,h);g.restore();return true;
 }
 function placements(id,r,w,h){const p=plans[id];if(!p||!['aurelian','verdant','cinder'].includes(p.region))return null;const restored=(r.adventure.campaignExtension?.facts||[]).includes('bond_broken');return p.placements.map(([key,x,y,width])=>[key.replace('STATE',restored?'restored':['veil_grove','veil_threshold','veil_haven'].includes(id)?'healthy':'drained'),x*w,y*h,width]);}
 const clusters={bend:[[.16,.21],[.26,.22],[.81,.77],[.75,.73],[.18,.76],[.84,.18]],clearing:[[.17,.2],[.25,.17],[.2,.78],[.28,.8],[.82,.25],[.79,.75],[.65,.21]],camp:[[.16,.22],[.2,.75],[.82,.27],[.76,.79]],junction:[[.17,.22],[.81,.21],[.22,.78],[.78,.77]],crossing:[[.18,.17],[.82,.17],[.18,.82],[.82,.82]],procession:[[.18,.19],[.28,.17],[.76,.8],[.84,.77]]};
 function objects(r,w,h){const p=plans[r.adventure?.area];if(!p||r.townInterior||r.phase==='town'||r.adventure.dungeon||['aurelian','verdant','cinder'].includes(p.region)||p.id==='caravan')return null;
  const api=window.GauntletWorldScenery;if(!api)return null;const rows=clusters[p.layout]||clusters.camp,reserved=[...(r.adventure.features||[]),...(r.adventure.exits||[])],dry=p.region==='dunmere',row={woodland:0,ruins:1,cavern:2,frost:3}[r.region]||0;
  const key=[p.id,w,h,api.revision(),JSON.stringify(reserved.map(f=>[f.id,f.x,f.y])),JSON.stringify(r.environment?.barriers||[])].join('|');if(legacyLayouts.has(key))return legacyLayouts.get(key);
  const entries=rows.map(([nx,ny],i)=>({x:Math.round(nx*w),y:Math.round(ny*h),variant:i%3===2?2:0,row,scale:dry?.6:i%2?.85:1.05,dry})).filter(o=>!reserved.some(f=>Math.hypot(f.x-o.x,f.y-o.y)<115)&&!(r.environment?.barriers||[]).some(b=>o.x>b.x-60&&o.x<b.x+b.width+60&&o.y>b.y-30&&o.y<b.y+b.height+70)).map((o,i)=>({key:p.id+':authored-'+i,depth:o.y,occluder:true,bounds:api.bounds(o),draw:g=>api.drawObject(g,o)}));
  legacyLayouts.set(key,entries);while(legacyLayouts.size>4)legacyLayouts.delete(legacyLayouts.keys().next().value);return entries;
 }
 window.GauntletRoomDesigns={ground,placements,objects,plans,landmark,solid,solidBounds,feature,featureBounds,groundFile:region=>['aurelian','verdant','cinder'].includes(region)?'release-ground-'+region+'-v5.png':null,diagnostics:()=>({plans:Object.keys(plans).length,layers:layers.size,layouts:legacyLayouts.size,homesLoaded:Boolean(homes?.naturalWidth),defensesLoaded:Boolean(defenses?.naturalWidth),floorImages:floorImages.size,floorImageBytes:[...floorImages.values()].reduce((n,c)=>n+(c.naturalWidth||0)*(c.naturalHeight||0)*4,0),errors:[...errors],layerBytes:[...layers.values()].reduce((n,c)=>n+c.width*c.height*4,0)})};
})();
