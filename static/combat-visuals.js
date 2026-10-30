// Cosmetic choreography consumes server footprints and release acknowledgements.
// No damage timers, predicted hits or gameplay authority live in this module.
(() => {
 const casts=new Map(),clips=new Map();let room=null,scene='',at=0,budget=0;
 const colors={herald:'#e5cd8c',shield:'#e5d1a1',sweep:'#e7d3ac',fracture:'#bca889',arcane:'#c8a9f1',frost:'#a9e2eb',lightning:'#acdff1',arrow:'#d8e4bb',astral:'#a8e8de',mixture:'#eec485',seal:'#efd59c',heal:'#a9e5c3',cleanse:'#e4ead3',rescue:'#bbe8df',cut:'#c6a7e8',shadow:'#ad88d0',root:'#9fc77f',thorn:'#b0cb82',growth:'#a5cd8b',fire:'#eeb07c',resonance:'#e4b3c5',voice:'#ead3a2',wind:'#bcd7c5',ward:'#b8dedc',phase:'#c3b6e8',rift:'#bea7e8',trap:'#ccb895',mark:'#e6ce95',poison:'#b5cb7f'};
 const simple=()=>Boolean(window.GauntletAudio?.visualSettings().reduced||window.matchMedia?.('(prefers-reduced-motion: reduce)').matches);
 const age=c=>c.elapsed+(performance.now()-c.at)/1000;
 const clamp=t=>Math.max(0,Math.min(1,t));
 function reset(){casts.clear();clips.clear();scene='';at=0;room=null;}
 function observe(r){const now=performance.now(),key=[r.code,r.you,r.stage,r.adventure?.area,r.townInterior].join('|');
  window.GauntletCampaignEffects?.observe(r);
  if(key!==scene||now-at>1400||document.hidden)reset();scene=key;at=now;room=r;
  window.GauntletReleaseVisuals?.observe(r);
  const live=new Set();for(const e of r.effects||[]){if(e.type!=='ability_cast'||!e.visual||e.stage!==r.stage)continue;live.add(e.id);
   const old=casts.get(e.id);if(old){Object.assign(old,{released:e.released,cancelled:e.cancelled,releaseAt:e.releaseAt,recipientIds:e.recipientIds});}
   else if(casts.size<32)casts.set(e.id,{...e,elapsed:e.elapsed??Math.max(0,e.duration-(e.until*1000-Date.now())/1000),at:now});
  }
  for(const[id,c]of casts)if(!live.has(id)||age(c)>=c.duration){casts.delete(id);clips.delete(id);}
 }
 function line(ctx,x,y,points){if(budget--<=0)return;ctx.beginPath();points.forEach(([px,py],i)=>ctx[i?'lineTo':'moveTo'](Math.round(x+px),Math.round(y+py)));ctx.stroke();}
 function cross(ctx,x,y,s=4){line(ctx,x,y,[[-s,0],[s,0]]);line(ctx,x,y,[[0,-s],[0,s]]);}
 function polygon(ctx,x,y,r,sides=6,turn=0){const p=[];for(let i=0;i<=sides;i++){const a=i*Math.PI*2/sides+turn;p.push([Math.cos(a)*r,Math.sin(a)*r]);}line(ctx,x,y,p);}
 function shield(ctx,x,y,r=18){if(window.GauntletReleaseVisuals){window.GauntletReleaseVisuals.shield(ctx,x,y,r);return;}line(ctx,x,y,[[-r,-r],[r,-r],[r*.8,r*.45],[0,r],[-r*.8,r*.45],[-r,-r]]);}
 function accent(ctx,f,x,y,r,t,dir=0){
  const n=simple()?3:6,move=simple()?.45:t;ctx.lineWidth=2;
  if(['ward','shield','herald'].includes(f)){if(window.GauntletReleaseVisuals)window.GauntletReleaseVisuals.shield(ctx,x,y-20,Math.min(18,r),f==='herald');else shield(ctx,x,y-20,Math.min(18,r));}
  else if(['seal','cleanse'].includes(f)){polygon(ctx,x,y,r*.5,4);polygon(ctx,x,y,r*.34,3,Math.PI/2);}
  else if(['heal','rescue'].includes(f)){
   for(let i=0;i<n;i++){const a=i*Math.PI*2/n,d=r*(1-move*.65);cross(ctx,x+Math.cos(a)*d,y+Math.sin(a)*d-move*12,3);}
   if(f==='rescue'){line(ctx,x,y-26,[[0,0],[-12,-13],[-26,-14],[-18,-2],[-9,3]]);line(ctx,x,y-26,[[0,0],[12,-13],[26,-14],[18,-2],[9,3]]);}
  }else if(['sweep','cut','shadow'].includes(f)){
   const count=f==='shadow'?2:1;for(let k=0;k<count;k++){const p=[];for(let i=0;i<9;i++){const a=dir-1.05+i*.26;p.push([Math.cos(a)*r*(.5+move*.4),Math.sin(a)*r*(.5+move*.4)]);}line(ctx,x,y,p);}
  }else if(['resonance','voice','wind'].includes(f)){
   for(let j=0;j<2;j++){const p=[];for(let i=0;i<=16;i++){const a=i*Math.PI/8;p.push([Math.cos(a)*r*(.25+move*.55+j*.1),Math.sin(a)*r*(.25+move*.55+j*.1)+Math.sin(i*2)*3]);}line(ctx,x,y,p);}
  }else if(['fracture','growth','root','thorn','lightning','rift'].includes(f)){
   for(let i=0;i<n;i++){const a=i*Math.PI*2/n,d=r*(.3+move*.65),dx=Math.cos(a),dy=Math.sin(a);line(ctx,x,y,[[dx*8,dy*8],[dx*d*.45-dy*5,dy*d*.45+dx*5],[dx*d*.6+dy*5,dy*d*.6-dx*5],[dx*d,dy*d]]);
    if(['growth','root','thorn'].includes(f))line(ctx,x+dx*d*.6,y+dy*d*.6,[[0,0],[dx*9-dy*7,dy*9+dx*7]]);
   }
  }else if(f==='poison'){
   for(let i=0;i<n;i++){const a=i*2.4,d=r*.6;polygon(ctx,x+Math.cos(a)*d,y+Math.sin(a)*d,3+move*3,5);}
  }else if(['arrow','astral'].includes(f)){cross(ctx,x,y,7);line(ctx,x,y,[[-14,-5],[-20,-10],[-16,-13],[-8,-8]]);}
  else if(f==='trap'){line(ctx,x,y,[[-13,-7],[-8,3],[0,-3],[8,3],[13,-7]]);line(ctx,x,y,[[-13,7],[-8,-3],[0,3],[8,-3],[13,7]]);}
  else if(f==='mixture'){polygon(ctx,x,y-7,9,6);line(ctx,x,y-7,[[-3,-8],[-3,-15],[3,-15],[3,-8]]);}
  else {for(let i=0;i<n;i++){const a=i*2.4,d=r*(.2+move*.7);cross(ctx,x+Math.cos(a)*d,y+Math.sin(a)*d,2);}}
 }
 function boundary(ctx,x,y,r){if(r<=0)return;ctx.save();ctx.globalAlpha*=.24;ctx.lineWidth=1;ctx.setLineDash([4,12]);ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.stroke();ctx.restore();}
 // Cache ray/rectangle/circle intersections on a snapped position and geometry.
 // The exact server boundary is retained; decoration is clipped before walls.
 function visibility(ctx,r,origin,key){
  const geometry=(r.environment?.barriers||[]).filter(b=>b.blocksShots).concat((r.environment?.obstacles||[]).filter(b=>b.hp>0));
  if(!geometry.length)return;const [x,y]=origin,signature=[Math.round(x/8),Math.round(y/8),...geometry.map(b=>[b.id,b.hp].join(':'))].join('|');let value=clips.get(key);
  if(value?.signature!==signature){const points=[];
   for(let i=0;i<96;i++){const a=i*Math.PI/48,dx=Math.cos(a),dy=Math.sin(a);let reach=2400;
    for(const b of geometry){if(b.width){let near=0,far=2400;for(const[o,d,low,high]of[[x,dx,b.x,b.x+b.width],[y,dy,b.y,b.y+b.height]]){
      if(Math.abs(d)<1e-6){if(o<low||o>high){far=-1;break;}}
      else{const t1=(low-o)/d,t2=(high-o)/d;near=Math.max(near,Math.min(t1,t2));far=Math.min(far,Math.max(t1,t2));}
     }if(near<=far)reach=Math.min(reach,Math.max(0,near));
    }else{const ox=x-b.x,oy=y-b.y,dot=ox*dx+oy*dy,q=dot*dot-(ox*ox+oy*oy-b.radius*b.radius);if(q>=0){const t=-dot-Math.sqrt(q);if(t>=0)reach=Math.min(reach,t);}}}
    points.push([x+dx*reach,y+dy*reach]);
   }value={signature,points};if(clips.size>=48)clips.delete(clips.keys().next().value);clips.set(key,value);
  }
  ctx.beginPath();value.points.forEach(([px,py],i)=>ctx[i?'lineTo':'moveTo'](px,py));ctx.closePath();ctx.clip();
 }
 function zones(ctx,r){budget=simple()?80:220;for(const z of(r.skillZones||[]).slice(0,16)){
  if(z.kind==='ascension_commitment')continue;ctx.save();ctx.strokeStyle=colors[z.kind]||colors.growth;ctx.lineWidth=2;
  visibility(ctx,r,[z.x,z.y],'zone:'+z.id);boundary(ctx,z.x,z.y,z.radius);const t=simple()?.5:((z.elapsed||0)%1);
  if(window.GauntletReleaseVisuals?.zone(ctx,z,r)){ctx.restore();continue;}
  const family={banner:'herald',beacon:'rescue',hallowed:'seal',spring:'growth',rift:'rift',trap:'trap'}[z.kind]||'growth';
  accent(ctx,family,z.x,z.y,Math.min(z.kind==='rift'?z.radius*.85:30,70),t);
  if(z.kind==='spring'){ctx.globalAlpha=.65;for(let i=0;i<(simple()?2:4);i++){const a=i*1.57;cross(ctx,z.x+Math.cos(a)*z.radius*.55,z.y+Math.sin(a)*z.radius*.55-t*12,3);}}
  if(z.kind==='rift'){ctx.globalAlpha=.45;polygon(ctx,z.x,z.y,z.radius*.65,6);}
  ctx.restore();
 }}
 function front(ctx,r){if(document.hidden)return;budget=simple()?90:260;let count=0;
  for(const c of casts.values()){
   if(count++>=(simple()?10:24)||c.cancelled)continue;
   const p=(r.players||[]).find(p=>p.id===c.ownerId&&p.class===c.heroClass&&p.status==='alive'&&p.connected!==false&&!p.indoors);if(!p)continue;
   const elapsed=age(c),v=c.visual,release=c.releaseAt||0,waiting=c.released===false,windup=waiting||elapsed<release;
   if(!windup)window.GauntletCampaignEffects?.ultimate(ctx,c,p,elapsed-release);
   const t=clamp((elapsed-release)/Math.max(.05,c.duration-release)),f=v.family,color=colors[f]||'#c8d7b3';
   const [x,y]=v.center||[c.targetX??p.x,c.targetY??p.y],dir=Math.atan2(c.facingY??1,c.facingX??0);
   ctx.save();ctx.strokeStyle=color;ctx.fillStyle=color;ctx.globalAlpha=windup?.6:1-t;ctx.lineWidth=2;
   if(v.los&&['circle','line'].includes(v.shape)){visibility(ctx,r,[p.x,p.y],c.id);if(v.shape==='circle')visibility(ctx,r,[x,y],c.id+':center');}
   if(window.GauntletReleaseVisuals?.cast(ctx,c,v,p,elapsed-release,t,r,windup,elapsed)){ctx.restore();continue;}
   if(windup){
    // A targeting bracket or lane marks commitment; it is never an active heal/damage field.
     ctx.setLineDash([4,7]);if(v.shape==='line'){const d=v.direction||[1,0],w=(v.width||38)/(v.campaign?2:1),o=v.origin;for(const sign of[-1,1])line(ctx,o[0],o[1],[[d[1]*w*sign,-d[0]*w*sign],[d[0]*v.radius+d[1]*w*sign,d[1]*v.radius-d[0]*w*sign]]);}
    else if(v.shape==='circle')boundary(ctx,x,y,v.radius);
    ctx.setLineDash([]);accent(ctx,f,p.x,p.y-24,18,clamp(elapsed/Math.max(.01,release)),dir);
   }else{
    if(v.shape==='line'){
     const d=v.direction||[1,0],o=v.origin,extent=v.radius,head=Math.min(extent,(elapsed-release)*1800+35),half=v.campaign?v.width/2:v.width||38;
     ctx.beginPath();ctx.moveTo(o[0]-d[1]*half,o[1]+d[0]*half);ctx.lineTo(o[0]+d[0]*extent-d[1]*half,o[1]+d[1]*extent+d[0]*half);ctx.lineTo(o[0]+d[0]*extent+d[1]*half,o[1]+d[1]*extent-d[0]*half);ctx.lineTo(o[0]+d[1]*half,o[1]-d[0]*half);ctx.closePath();ctx.clip();
     if(window.GauntletCampaignEffects?.lane(ctx,c,v,elapsed-release,t)){ctx.restore();continue;}
     // Instant server line attack: release flash, then a fast cosmetic arrow. No deferred hit.
     ctx.globalAlpha=(1-t)*.42;line(ctx,o[0],o[1],[[0,0],[d[0]*extent,d[1]*extent]]);ctx.globalAlpha=1-t;
     window.GauntletProjectiles?.variant(ctx,'deadeye_arrow',o[0]+d[0]*head,o[1]+d[1]*head,Math.atan2(d[1],d[0]),elapsed*1000,1.2);
    }else if(window.GauntletCampaignEffects?.cast(ctx,c,v,p,elapsed-release,t,r)){
     // Distinct campaign mixtures, cuts, tethers, pack strikes and finales.
    }else if(v.shape==='circle'){
     ctx.save();ctx.beginPath();ctx.arc(x,y,v.radius,0,Math.PI*2);ctx.clip();boundary(ctx,x,y,v.radius);accent(ctx,f,x,y,v.radius,t,dir);ctx.restore();
    }else if(v.shape==='recipients'||v.shape==='rescue'){
     for(const id of(c.recipientIds||[]).slice(0,8)){const ally=(r.players||[]).find(a=>a.id===id&&!a.indoors&&a.connected!==false);if(ally)accent(ctx,f,ally.x,ally.y-8,28,t);}
     accent(ctx,f,p.x,p.y-26,20,t);
    }else if(v.shape==='movement'){accent(ctx,f,p.x,p.y-8,26,t,dir);}
    else if(v.shape==='summon'){polygon(ctx,p.x,p.y+14,32,6);accent(ctx,f,p.x,p.y+14,28,t);}
    else if(v.shape!=='zone')accent(ctx,f,p.x,p.y-21,24,t,dir);
   }
   ctx.restore();
  }
  window.GauntletReleaseVisuals?.controls(ctx,r);
 }
 document.addEventListener('visibilitychange',()=>{if(document.hidden)reset();});
 window.GauntletCombatVisuals={observe,zones,front,reset,handles:c=>Boolean(c?.visual),accent,visibility,diagnostics:()=>({casts:casts.size,budget})};
})();
