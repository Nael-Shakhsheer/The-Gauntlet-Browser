// Release presentation: all geometry, recipients and release clocks are server-owned.
(() => {
 const clamp=x=>Math.max(0,Math.min(1,x)),TAU=Math.PI*2;
 const images=new Map(),loadErrors=new Set(),controlMarks=new Map();let controlScene='';
 function image(file){if(!images.has(file)){const img=new Image();img.onerror=()=>loadErrors.add(file);img.src='/sprites/'+file;images.set(file,img);}return images.get(file);}
 const reduced=()=>Boolean(window.GauntletAudio?.visualSettings().reduced||window.matchMedia?.('(prefers-reduced-motion: reduce)').matches);
 function poly(g,points,fill,stroke){g.beginPath();points.forEach(([x,y],i)=>g[i?'lineTo':'moveTo'](Math.round(x),Math.round(y)));g.closePath();if(fill){g.fillStyle=fill;g.fill();}if(stroke){g.strokeStyle=stroke;g.lineWidth=1;g.stroke();}}
 function shield(g,x,y,size=18,crowned=false){
  g.save();g.translate(Math.round(x),Math.round(y));const s=Math.min(21,size)/18;g.scale(s,s);
  poly(g,[[-17,-19],[17,-19],[15,5],[10,13],[0,20],[-10,13],[-15,5]],'#172833','#d5c490');
  poly(g,[[-13,-15],[12,-15],[10,4],[6,10],[0,15],[-8,9],[-12,3]],'#647782');
  poly(g,[[0,-14],[12,-14],[10,4],[6,10],[0,14]],'#394b59');
  g.fillStyle='#b3c5ca';g.fillRect(-11,-13,3,15);g.fillRect(-8,-13,18,2);
  g.fillStyle='#d2b774';g.fillRect(-2,-10,4,19);g.fillRect(-8,-4,16,4);
  g.fillStyle='#f2dfa8';g.fillRect(-2,-4,4,4);
  for(const [a,b]of[[-12,-12],[10,-12],[-10,2],[8,2]]){g.fillStyle='#e6d5a5';g.fillRect(a,b,2,2);}
  if(crowned){poly(g,[[-10,-21],[-12,-30],[-5,-26],[0,-33],[5,-26],[12,-30],[10,-21]],'#b89c58','#f1d99a');g.fillStyle='#374d5b';g.fillRect(-7,-24,3,2);g.fillRect(4,-24,3,2);}
  g.restore();
 }
 function protection(p){
  if(!p||p.status!=='alive')return{label:'',description:'',ward:false};
  const parts=[],detail=[];
  if(p.barrier>0){const seconds=Number.isFinite(p.barrierRemaining)&&p.barrierRemaining>0?' · '+Math.ceil(p.barrierRemaining)+'s':'';parts.push('Barrier '+p.barrier+seconds);detail.push('Absorbs '+p.barrier+' damage'+(seconds?' for up to '+Math.ceil(p.barrierRemaining)+' seconds':'')+'.');}
  const ward=Number.isFinite(p.protectionRemaining)&&p.protectionRemaining>0&&Number.isFinite(p.protectionFactor)&&p.protectionFactor<1;
  if(ward){const percent=Math.round((1-p.protectionFactor)*100),seconds=p.protectionRemaining>=.95?' · '+Math.ceil(p.protectionRemaining)+'s':'';parts.push('Guarded '+percent+'%'+seconds);detail.push('Timed ward: '+percent+'% damage reduction'+(seconds?' for '+Math.ceil(p.protectionRemaining)+' seconds':' while active')+'.');}
  return{label:parts.join('\n'),description:detail.join(' '),ward};
 }
 function protectionMark(g,p){if(!protection(p).ward)return;const x=Math.round(p.x+25),y=Math.round(p.y-10);g.save();poly(g,[[x-4,y-5],[x+4,y-5],[x+3,y+1],[x,y+5],[x-3,y+1]],'#4b6970','#c9d3ba');g.fillStyle='#d7c38d';g.fillRect(x-1,y-3,2,5);g.restore();}
 function crack(g,x,y,r,t){
  const n=reduced()?4:7;for(let i=0;i<n;i++){const a=i*TAU/n+.17,dx=Math.cos(a),dy=Math.sin(a),reach=r*(.25+.7*t);g.save();g.translate(x,y);g.rotate(a);
   poly(g,[[10,-2],[reach*.45,-3],[reach*.55,-8],[reach*.63,-4],[reach,-2],[reach*.68,1],[reach*.55,-3],[reach*.4,2],[10,2]],'#332f31');
   g.fillStyle='#bcb9a2';g.fillRect(reach*.5,-2,5,2);g.restore();
  }
 }
 function astral(g,c,v,p,age,windup,elapsed){
  const[x,y]=v.center,r=v.radius,progress=clamp(elapsed/Math.max(.01,c.releaseAt||.6));
  const meta=window.GauntletReleaseSceneData?.impact,img=meta&&image(meta.file);
  const stamp=frame=>{if(!img?.complete||!img.naturalWidth)return;const scale=Math.min(1.25,r/120);g.save();g.imageSmoothingEnabled=false;g.drawImage(img,frame*128,0,128,128,x-meta.anchor[0]*scale,y-meta.anchor[1]*scale,128*scale,128*scale);g.restore();};
  g.save();g.globalAlpha=1;g.lineWidth=2;
  g.beginPath();g.arc(x,y,r,0,TAU);g.clip();
  if(windup){
   g.strokeStyle='#8d9cab';g.globalAlpha=.65;g.setLineDash([5,11]);g.beginPath();g.arc(x,y,r-1,0,TAU);g.stroke();g.setLineDash([]);
   // Six fixed astral stones mark the committed footprint. Nothing tracks the target.
   for(let i=0;i<6;i++){const a=i*TAU/6-Math.PI/2,px=x+Math.cos(a)*(r-9),py=y+Math.sin(a)*(r-9);
    poly(g,[[px,py-5],[px+4,py],[px,py+5],[px-4,py]],'#3e5570','#b6d9e5');
    const d=(r-18)*(1-progress*.55);g.fillStyle='#c7e4e9';g.fillRect(Math.round(x+Math.cos(a)*d)-1,Math.round(y+Math.sin(a)*d)-1,3,3);
   }
   if(progress>.7&&!reduced()){g.globalAlpha=.65;stamp(progress>.88?1:0);}else{g.globalAlpha=.2+progress*.25;poly(g,[[x,y-7],[x+5,y],[x,y+7],[x-5,y]],'#c1e2f0');}
  }else{
   g.globalAlpha=clamp(1-age/.55);if(age<.55)stamp(reduced()?3:age<.09?2:age<.21?3:age<.37?4:5);
  }
  g.restore();
  // The living root/control state is read independently of the damage flash.
 }
 function knight(g,c,v,p,age,t,r,windup){
  const id=c.abilityId,[x,y]=v.center||[p.x,p.y],a=Math.atan2(c.facingY??1,c.facingX??0),dx=Math.cos(a),dy=Math.sin(a);
  if(windup){shield(g,p.x+dx*16,p.y-27+dy*10,13,false);return true;}
  if(['guardian_cry','oath_link','iron_wall','riposte'].includes(id)){
   if(age>.42)return true;
   g.globalAlpha*=clamp(1-age/.42);
   const ids=id==='iron_wall'||id==='riposte'?[p.id]:c.recipientIds||[];
   for(const ident of ids.slice(0,8)){const ally=(r.players||[]).find(q=>q.id===ident&&q.connected!==false&&!q.indoors);if(ally)shield(g,ally.x,ally.y-35,15,id==='guardian_cry');}
  }else if(id==='shield_bash'||id==='shield_rush'){
   shield(g,p.x+dx*(22+12*t),p.y-20+dy*18,18,false);
   g.save();g.translate(p.x+dx*32,p.y-12+dy*22);g.rotate(a);poly(g,[[2,-13],[11,-6],[4,0],[11,6],[2,13],[18,0]],'#d9cfac');g.restore();
  }else if(id==='challenge'){
   for(let i=0;i<3;i++){g.save();g.translate(p.x+dx*(25+i*15),p.y-35+dy*(25+i*15));g.rotate(a);poly(g,[[-4,-8],[3,-8],[9,0],[3,8],[-4,8],[2,0]],'#c3a66d');g.restore();}
  }else if(id==='citadel_oath'||id==='earthshaker'){
   crack(g,x,y,v.radius,clamp(age/.28));if(age<.28)shield(g,p.x,p.y-32,16,id==='citadel_oath');
   if(id==='citadel_oath'&&age<.4)for(const ident of(c.recipientIds||[])){const q=r.players.find(q=>q.id===ident);if(q&&q.id!==p.id)shield(g,q.x,q.y-28,11);}
  }else if(id==='cleaving_arc'){
   g.save();g.translate(p.x,p.y-12);g.rotate(a);poly(g,[[10,-8],[25,-38],[49,-48],[70,-32],[82,-7],[69,12],[62,-10],[48,-28],[28,-27]],'#607681','#d8e0d0');g.restore();
  }else return false;
  return true;
 }
 function cast(g,c,v,p,age,t,r,windup,elapsed){
  if(c.abilityId==='astral_convergence'||c.kind==='ascend_wizard'){astral(g,c,v,p,age,windup,elapsed);return true;}
  if(v.campaign)return false; // The authored campaign renderer owns its24 skill identities.
  if(c.heroClass==='Knight')return knight(g,c,v,p,age,t,r,windup);
  if(windup)return false;
  const id=c.abilityId,hero=c.heroClass,[x,y]=v.center||[p.x,p.y],a=Math.atan2(c.facingY??1,c.facingX??0),fade=clamp(1-age/.55);
  const note=(xx,yy,scale=1)=>{g.save();g.translate(Math.round(xx),Math.round(yy));g.scale(scale,scale);poly(g,[[-4,1],[1,-1],[4,1],[3,4],[-2,5],[-5,3]],'#e1bd8b');g.fillStyle='#f0d3a0';g.fillRect(2,-12,2,15);poly(g,[[2,-12],[10,-9],[10,-5],[2,-8]],'#be8c9c');g.restore();};
  const blade=(xx,yy,angle,length=28)=>{g.save();g.translate(xx,yy);g.rotate(angle);poly(g,[[-7,-3],[0,-3],[length,0],[0,3],[-7,3]],'#bac4cc','#485362');g.fillStyle='#856894';g.fillRect(-5,-5,3,10);g.restore();};
  const leaf=(xx,yy,angle,size=9)=>{g.save();g.translate(xx,yy);g.rotate(angle);poly(g,[[0,0],[size*.6,-size*.5],[size*1.6,0],[size*.6,size*.5]],'#88a268','#3d654d');g.restore();};
  const recipients=()=>{const ids=c.recipientIds||[];return ids.map(id=>r.players?.find(q=>q.id===id&&q.connected!==false&&!q.indoors)).filter(Boolean);};
  if(v.shape==='recipients'||v.shape==='rescue'){
   if(age>.65)return true;
   for(const q of recipients()){
    g.save();g.globalAlpha=fade;
    if(hero==='Cleric'){
     // Warm mineral drops and a stopper-shaped seal distinguish mixtures from light.
     poly(g,[[q.x-5,q.y-28],[q.x+5,q.y-28],[q.x+9,q.y-18],[q.x+7,q.y-11],[q.x-7,q.y-11],[q.x-9,q.y-18]],'#d0b76f','#625d53');g.fillStyle='#ece0a7';g.fillRect(q.x-4,q.y-33,8,5);
     for(let i=0;i<(id==='sanctuary_rain'?5:3);i++){const xx=q.x+(i-1)*9,yy=q.y-20+age*38;poly(g,[[xx,yy-4],[xx+2,yy],[xx,yy+2],[xx-2,yy]],'#d4c99c');}
    }else if(hero==='Bard'){
     const count=id==='rallying_chord'?3:id==='grand_crescendo'?4:2;for(let i=0;i<count;i++)note(q.x-14+i*11,q.y-20-age*20-i%2*7,.75);
     if(id==='fleet_rhythm')for(const s of[-1,1])poly(g,[[q.x+s*12,q.y+9],[q.x+s*27,q.y+5],[q.x+s*20,q.y+12]],'#b8d6cc');
    }else{
     const lift=age*28,n=id==='major_mend'||id==='miracle'?3:1;
     for(let i=0;i<n;i++){const xx=q.x+(i-(n-1)/2)*11;poly(g,[[xx-4,q.y-5-lift],[xx-6,q.y-20-lift],[xx,q.y-32-lift],[xx+5,q.y-18-lift],[xx+2,q.y-6-lift]],'#bcded5');g.fillStyle='#e8efcc';g.fillRect(xx-1,q.y-20-lift,2,10);}
     if(['quick_revival','mass_revival','second_dawn','cleansing_splash'].includes(id))for(const s of[-1,1])poly(g,[[q.x+s*4,q.y-18],[q.x+s*16,q.y-39],[q.x+s*33,q.y-43],[q.x+s*20,q.y-27]],'#dce4cd');
     if(id==='life_barrier')poly(g,[[q.x-14,q.y+4],[q.x-19,q.y-12],[q.x-15,q.y-30],[q.x-11,q.y-13],[q.x+11,q.y-13],[q.x+15,q.y-30],[q.x+19,q.y-12],[q.x+14,q.y+4]],'#92bdb7');
    }
    g.restore();
   }
   return true;
  }
  if(v.shape==='circle'){
   g.save();g.beginPath();g.arc(x,y,v.radius,0,TAU);g.clip();g.globalAlpha=fade;
   if(hero==='Wizard'){
    if(id==='glacial_prison')for(let i=0;i<6;i++){const b=i*TAU/6,xx=x+Math.cos(b)*v.radius*.68,yy=y+Math.sin(b)*v.radius*.68,h=18+Math.sin(Math.min(1,age/.2)*Math.PI/2)*15;poly(g,[[xx-8,yy],[xx-5,yy-h],[xx+2,yy-h-8],[xx+7,yy],[xx,yy+4]],'#9cb9cb','#4f6a84');}
    else for(let i=0;i<6;i++){const b=i*TAU/6,rr=v.radius*(.75-.55*clamp(age/.4)),xx=x+Math.cos(b)*rr,yy=y+Math.sin(b)*rr;poly(g,[[xx,yy-12],[xx+7,yy],[xx,yy+12],[xx-7,yy]],'#a99aca','#4d5477');}
   }else if(hero==='Rogue'){
    const n=id==='crosscut'?2:id==='death_bloom'?8:5;
    for(let i=0;i<n;i++){const b=id==='crosscut'?a+(i?-.7:.7):i*TAU/n+a,reach=Math.min(v.radius-24,22+age*200);blade(x+Math.cos(b)*reach,y+Math.sin(b)*reach,b,id==='death_bloom'?32:22);}
   }else if(hero==='Druid'){
    for(let i=0;i<(reduced()?4:7);i++){const b=i*TAU/7,rr=v.radius*clamp(age/.3)*.85;g.save();g.translate(x,y);g.rotate(b);poly(g,[[10,-3],[rr*.4,-8],[rr*.65,-4],[rr,0],[rr*.64,2],[rr*.4,-2]],'#576d4c');g.restore();leaf(x+Math.cos(b)*rr*.7,y+Math.sin(b)*rr*.7,b,8);}
   }else if(hero==='Cleric'){
    for(let i=0;i<7;i++){const b=i*2.4,rr=v.radius*(.25+clamp(age/.35)*.55),xx=x+Math.cos(b)*rr,yy=y+Math.sin(b)*rr;poly(g,[[xx,yy-5],[xx+4,yy],[xx,yy+5],[xx-4,yy]],i%2?'#d6c18c':'#b6bc8d');}
    poly(g,[[x-6,y-15],[x+5,y-15],[x+12,y],[x+8,y+9],[x-8,y+9],[x-12,y]],'#d8ba79','#685e51');
   }else if(hero==='Bard'){
    for(let i=0;i<5;i++){const b=a+(i-2)*.75,rr=Math.min(v.radius-12,24+age*230);note(x+Math.cos(b)*rr,y+Math.sin(b)*rr,.9);g.save();g.translate(x,y);g.rotate(b);poly(g,[[rr-9,-16],[rr+1,-12],[rr+4,0],[rr+1,12],[rr-9,16],[rr-3,0]],'#b78fa9');g.restore();}
   }else if(hero==='Healer'){
    for(let i=0;i<6;i++){const b=i*TAU/6,rr=v.radius*.8*clamp(age/.3);g.save();g.translate(x+Math.cos(b)*rr,y+Math.sin(b)*rr);g.rotate(b);poly(g,[[0,-7],[14,-3],[23,0],[14,3],[0,7],[5,0]],'#b1d9cc');g.restore();}
   }else {g.restore();return false;}
   g.restore();return true;
  }
  if(v.shape==='summon'){
   const tone=id==='fire_wolf'?'#bd8862':id==='ice_bear'?'#8bb8c6':id==='lightning_bird'?'#7d9dca':'#83a36b';g.save();g.globalAlpha=fade;
   for(let i=0;i<4;i++){const b=i*TAU/4;leaf(p.x+Math.cos(b)*26,p.y+12+Math.sin(b)*16,b,7);}
   g.fillStyle=tone;g.fillRect(p.x-2,p.y+8,4,8);g.fillRect(p.x-6,p.y+12,12,3);g.restore();return true;
  }
  if(v.shape==='movement'||['vanish','venom_edge','eagle_eye','quickstep','spell_surge','echo_verse','call_wild'].includes(id)){
   if(age>.3)return true;g.save();g.globalAlpha=fade;
   if(hero==='Rogue'){for(let i=0;i<3;i++){g.save();g.translate(p.x-dxFor(a)*(10+i*12),p.y-10-Math.sin(a)*(10+i*12));g.rotate(a);poly(g,[[-10,-4],[6,-1],[-10,2]],'#826795');g.restore();}}
   else if(hero==='Archer'){for(const s of[-1,1]){g.save();g.translate(p.x+s*15,p.y-24);g.rotate(a);poly(g,[[-5,-9],[6,0],[-5,9],[-1,0]],'#c5c6a0');g.restore();}}
   else if(hero==='Wizard')for(const s of[-1,1])poly(g,[[p.x+s*12,p.y-27],[p.x+s*21,p.y-40],[p.x+s*19,p.y-18]],'#a4a4d0');
   else if(hero==='Druid')for(const s of(r.summons||[]).filter(s=>s.ownerId===p.id).slice(0,4))leaf(s.x,s.y-24,-Math.PI/2,10);
   else if(hero==='Bard')for(let i=0;i<3;i++)note(p.x-15+i*12,p.y-30,.7);
   g.restore();return true;
  }
  // Projectiles and confirmed contact atlases own attacks in flight. Do not add
  // a second unrelated emblem over the shooter's body for every point packet.
  if(['damage','pierce','stun','bleed','mercy_lance','echo'].includes(c.kind))return true;
  return false;
 }
 function dxFor(a){return Math.cos(a);}
 function controls(g,r){
  for(const e of (r.enemies||[]).slice(0,40))if(e.rooted){
   const astral=controlMarks.has(e.id);
   if(!astral)continue;g.save();g.globalAlpha=.7;
   // An ankle clasp communicates restraint; no false damage or extra duration.
   poly(g,[[e.x-14,e.y+7],[e.x-10,e.y-1],[e.x-6,e.y+7],[e.x+6,e.y+7],[e.x+10,e.y-1],[e.x+14,e.y+7],[e.x+9,e.y+12],[e.x-9,e.y+12]],'#526b86','#c1d9e4');g.restore();
  }
 }
 function observe(r){const key=[r.code,r.you,r.stage,r.adventure?.area,r.townInterior].join('|'),now=performance.now();if(key!==controlScene)controlMarks.clear();controlScene=key;
  const enemies=(r.enemies||[]).filter(e=>e.rooted).slice(0,40);
  for(const c of(r.effects||[]))if(c.type==='ability_cast'&&c.abilityId==='astral_convergence'&&c.released&&!c.cancelled&&c.visual?.center){for(const e of enemies)if(Math.hypot(e.x-c.visual.center[0],e.y-c.visual.center[1])<=c.visual.radius&&controlMarks.get(e.id)?.castId!==c.id)controlMarks.set(e.id,{castId:c.id,until:now+1650});}
  for(const[id,m]of controlMarks)if(m.until<now||!enemies.some(e=>e.id===id))controlMarks.delete(id);
 }
 function zone(g,z){const x=z.x,y=z.y;
  if(z.kind==='banner'){
   g.fillStyle='#26333c';g.fillRect(x-7,y+9,16,5);g.fillStyle='#a5adb0';g.fillRect(x-2,y-42,3,53);g.fillStyle='#d2bb7b';g.fillRect(x-4,y-45,7,4);
   poly(g,[[x+1,y-40],[x+27,y-40],[x+24,y-14],[x+14,y-8],[x+1,y-13]],'#384d60','#ab9564');g.fillStyle='#cfb77e';g.fillRect(x+11,y-35,3,18);g.fillRect(x+6,y-30,13,3);return true;
  }
  if(z.kind==='trap'){
   poly(g,[[x-17,y+4],[x-12,y-5],[x-8,y],[x-3,y-5],[x+2,y],[x+8,y-5],[x+13,y-1],[x+17,y+5]],'#a4a696','#4c524b');
   poly(g,[[x-17,y+12],[x-12,y+20],[x-8,y+15],[x-3,y+20],[x+2,y+15],[x+8,y+20],[x+13,y+16],[x+17,y+11]],'#737a71','#3f4e48');return true;
  }
  if(z.kind==='rift'){
   poly(g,[[x-4,y-31],[x+8,y-18],[x+5,y-8],[x+11,y+3],[x+3,y+15],[x-8,y+5],[x-5,y-6],[x-10,y-17]],'#242e45','#8c83b1');g.fillStyle='#d4cee3';g.fillRect(x+5,y-20,2,8);g.fillRect(x-5,y+1,2,8);return true;
  }
  if(z.kind==='spring'){
   for(let i=0;i<5;i++){const a=i*TAU/5;g.save();g.translate(x,y+9);g.rotate(a);poly(g,[[2,0],[14,-8],[22,-3],[13,4]],'#729965','#3d664f');g.restore();}
   poly(g,[[x,y-13],[x+5,y-3],[x,y+2],[x-5,y-3]],'#a2cfbb','#4e8273');return true;
  }
  if(z.kind==='hallowed'){
   poly(g,[[x,y-15],[x+22,y-2],[x+22,y+15],[x,y+28],[x-22,y+15],[x-22,y-2]],null,'#a69a79');
   for(const s of[-1,1]){g.fillStyle='#d0ba83';g.fillRect(x+s*13-3,y+1,6,11);g.fillStyle='#ebe0b3';g.fillRect(x+s*13-2,y-3,4,4);}
   g.fillStyle='#e0ca91';g.fillRect(x-2,y-4,4,22);g.fillRect(x-8,y+4,16,3);return true;
  }
  if(z.kind==='beacon'){
   poly(g,[[x,y-29],[x+7,y-16],[x,y-3],[x-7,y-16]],'#d2e4d4','#618f89');
   for(const s of[-1,1])poly(g,[[x+s*5,y-3],[x+s*20,y-13],[x+s*17,y],[x+s*8,y+7]],'#9cbeb0');return true;
  }
  return false;
 }
 const farms=new Set(['border','dunmere','fields','mill','eastern_threshold','cellar','irrigation_channels','farmstead','pump_exterior','sluice_entry','sluice_gallery','sluice_alcove','pump_chamber']);
 function region(r){const id=r?.adventure?.area||'';return id.startsWith('cinder_')?'cinder':id.startsWith('veil_')?'verdant':id.startsWith('city_')?'aurelian':farms.has(id)?'dunmere':'woodland';}
 const materials={woodland:['#26392a','#6d603d','#b2a16e','#73865a'],dunmere:['#393a32','#8c8063','#c2b48c','#ddd0a3'],aurelian:['#273b42','#7e8c8b','#c1c3ac','#d5b26c'],verdant:['#223f3c','#526f5c','#a8bd8b','#a2d6cc'],cinder:['#242b32','#4b505b','#8b8b88','#d1a16c']};
 const markers=new Map();
 function markerBase(key){if(markers.has(key))return markers.get(key);const c=document.createElement('canvas');c.width=c.height=48;const g=c.getContext('2d'),p=materials[key];g.translate(24,24);
  poly(g,[[-14,15],[-12,-3],[-6,-3],[-6,-10],[-11,-10],[0,-23],[11,-10],[6,-10],[6,-3],[12,-3],[14,15],[7,19],[-7,19]],p[1],p[0]);
  poly(g,[[-9,12],[-8,-1],[-3,-1],[-3,-12],[-6,-12],[0,-19],[6,-12],[3,-12],[3,-1],[8,-1],[9,12],[0,15]],p[2]);
  g.fillStyle=p[0];g.fillRect(-5,3,10,2);g.fillRect(-3,5,6,2);
  if(key==='woodland'||key==='verdant'){
   g.fillStyle=p[0];g.fillRect(-13,7,3,10);g.fillRect(11,3,2,12);g.fillStyle=p[3];g.fillRect(-15,11,4,2);g.fillRect(12,7,3,2);
   if(key==='verdant')poly(g,[[0,-6],[3,-2],[0,2],[-3,-2]],p[3],p[0]);
  }else if(key==='dunmere'){g.fillStyle=p[0];g.fillRect(-11,8,22,2);g.fillRect(-10,14,20,2);g.fillStyle=p[3];g.fillRect(-9,6,3,2);}
  else if(key==='aurelian'){g.fillStyle=p[0];g.fillRect(-10,9,20,2);g.fillStyle=p[3];g.fillRect(-9,7,2,2);g.fillRect(7,7,2,2);poly(g,[[-4,-1],[4,-1],[3,5],[0,8],[-3,5]],p[3],p[0]);}
  else{poly(g,[[-11,3],[-6,7],[-7,13],[-3,16]],p[0]);g.fillStyle=p[3];g.fillRect(-12,10,2,3);g.fillRect(9,2,2,2);g.fillStyle='#8f5745';g.fillRect(-10,14,2,2);}
  markers.set(key,c);return c;
 }
 function trail(g,e,near,r){if(!r?.adventure||r.adventure.dungeon)return false;const key=region(r);g.save();g.translate(Math.round(e.x),Math.round(e.y));g.rotate(({north:0,east:Math.PI/2,south:Math.PI,west:-Math.PI/2})[e.edge]||0);g.imageSmoothingEnabled=false;g.drawImage(markerBase(key),-24,-24);g.restore();
  const x=Math.round(e.x),y=Math.round(e.y);g.save();
  if(e.locked){g.fillStyle='#1e2930';g.fillRect(x-9,y-1,18,12);g.strokeStyle='#d1c3a1';g.lineWidth=2;g.strokeRect(x-5,y-7,10,9);g.fillStyle='#d1c3a1';g.fillRect(x-6,y+2,12,7);g.fillStyle='#39414a';g.fillRect(x-1,y+4,2,4);}
  if(near){g.strokeStyle='#f0e4bc';g.lineWidth=2;for(const s of[-1,1]){g.beginPath();g.moveTo(x+s*19,y+15);g.lineTo(x+s*24,y+15);g.lineTo(x+s*24,y+8);g.stroke();}}
  if(e.tracked)poly(g,[[x+20,y-20],[x+23,y-14],[x+29,y-11],[x+23,y-8],[x+20,y-2],[x+17,y-8],[x+11,y-11],[x+17,y-14]],'#e9ce8b','#29383d');
  if(e.dungeonComplete){g.fillStyle='#273d3c';g.fillRect(x+15,y+6,14,13);poly(g,[[x+17,y+12],[x+21,y+16],[x+28,y+8],[x+25,y+8],[x+21,y+12],[x+19,y+10]],'#d2dfbd');}
  g.restore();return true;
 }
 function exitLabel(g,e,near,r){if(!near&&e.name==='Unexplored trail')return true;const w=r.areaSize?.[0]||960,h=r.areaSize?.[1]||540,max=Math.min(280,w-24),text=(e.locked?'Closed · ':near?'E · ':'')+(e.dungeonEntrance?.name||e.name)+(e.dungeonComplete?' · Cleared':'')+(e.tracked?' ★':'');
  g.save();g.font=near?'bold 12px monospace':'11px monospace';const lines=[];let current='';for(const word of text.split(' ')){const next=current?current+' '+word:word;if(current&&g.measureText(next).width>max-16){lines.push(current);current=word;}else current=next;}if(current)lines.push(current);
  const shown=lines.slice(0,3),width=Math.min(max,Math.max(...shown.map(s=>g.measureText(s).width))+16),height=shown.length*14+8,x=Math.max(width/2+5,Math.min(w-width/2-5,e.x));let y=e.edge==='south'?e.y-height-10:e.edge==='north'?e.y+25:e.y-height-8;y=Math.max(5,Math.min(h-height-5,y));
  g.fillStyle=near?'#17292df2':'#1c2b2ddc';g.fillRect(Math.round(x-width/2),Math.round(y),Math.ceil(width),height);g.fillStyle=e.locked?'#e4b3a0':e.tracked?'#f0db9c':'#eee2c0';g.textAlign='center';shown.forEach((s,i)=>g.fillText(s,Math.round(x),Math.round(y+15+i*14)));g.restore();return true;
 }
 document.addEventListener('visibilitychange',()=>{if(document.hidden)controlMarks.clear();});
 window.GauntletReleaseVisuals={cast,controls,zone,observe,shield,protection,protectionMark,trail,exitLabel,region,handlesControl:e=>Boolean(e.rooted&&controlMarks.has(e.id)),reset(){controlMarks.clear();controlScene='';},diagnostics:()=>({markerCanvases:markers.size,markerBytes:markers.size*48*48*4,images:images.size,controlMarks:controlMarks.size,errors:[...loadErrors]})};
})();
