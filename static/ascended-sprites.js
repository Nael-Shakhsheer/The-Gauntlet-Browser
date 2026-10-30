// Real directional forms; progression, movement, collision and cast clocks stay server-owned.
(() => {
  const root=document.currentScript?.dataset.spriteRoot||'/sprites/';
  const supported=new Set(['Knight','Wizard','Archer','Cleric','Rogue','Druid','Bard','Healer']);
  const packs=new Map(),actors=new Map(),masks=new Map();
  const colors={Knight:'#e8d49c',Wizard:'#a6d8f1',Archer:'#9ae0d6',Cleric:'#efcb88',Rogue:'#aa80dd',Druid:'#8ecb8d',Bard:'#eab6aa',Healer:'#b9e8dd'};
  let scene='',epoch='',cursor=0,lastAt=0;
  const reduced=()=>Boolean(window.GauntletAudio?.visualSettings().reduced);
  const still=()=>Boolean(window.matchMedia?.('(prefers-reduced-motion: reduce)').matches);
  const loaded=img=>Boolean(img?.complete&&img.naturalWidth);
  const direction=p=>(Math.round((Math.PI/2-Math.atan2(p.facingY??1,p.facingX??0))/(Math.PI/4))+8)%8;
  function ensure(hero,actions=false){
    if(!supported.has(hero))return null;let pack=packs.get(hero);
    if(!pack){pack={body:new Image(),actions:null,meta:null};packs.set(hero,pack);pack.body.src=root+'ascended-'+hero.toLowerCase()+'-body-v1.png';
      fetch(root+'ascended-'+hero.toLowerCase()+'-v1.json').then(r=>r.ok?r.json():Promise.reject()).then(m=>pack.meta=m).catch(()=>{});}
    if(actions&&!pack.actions){pack.actions=new Image();pack.actions.src=root+'ascended-'+hero.toLowerCase()+'-actions-v1.png';}
    return pack;
  }
  function observe(room){
    const now=performance.now(),key=[room.code,room.you,room.adventure?.area||'',room.stage,room.townInterior||''].join('|');
    const continuous=scene===key&&lastAt>0&&now-lastAt<1400&&!document.hidden;
    if(!continuous)actors.clear();scene=key;lastAt=now;const live=new Set();
    for(const p of room.players||[]){
      if(!p.ascended||p.connected===false||!ensure(p.class,Boolean(p.abilityAnimation)||room.phase==='combat'))continue;
      live.add(p.id);const old=actors.get(p.id),jump=old&&Math.hypot(p.x-old.x,p.y-old.y)>70;
      const r=old&&old.hero===p.class&&!jump?old:{hero:p.class,x:p.x,y:p.y,trails:[],emitAt:now,hitAt:-Infinity,transformAt:-Infinity};
      if(old&&(p.damageTaken||0)>old.damageTaken)r.hitAt=now;
      if(!p.moving||p.status!=='alive'||jump||!continuous||p.indoors)r.trails=[];
      else if(now-r.emitAt>=75&&Math.hypot(p.x-r.x,p.y-r.y)>2){r.emitAt=now;if(!reduced())r.trails.push({x:r.x,y:r.y,at:now,dir:direction(p),frame:3+Math.floor(now/180)%3});}
      r.trails=r.trails.filter(t=>now-t.at<320&&Math.hypot(t.x-p.x,t.y-p.y)<60).slice(-4);
      Object.assign(r,{x:p.x,y:p.y,damageTaken:p.damageTaken||0});actors.set(p.id,r);
    }
    for(const id of actors.keys())if(!live.has(id))actors.delete(id);
    const f=room.feedback;if(f){const fresh=f.epoch!==epoch;
      for(const e of f.events||[])if(e.kind==='ascension_transform'&&e.age<.8&&continuous&&!fresh&&e.id>cursor){const r=actors.get(e.ownerId);if(r)r.transformAt=now-e.age*1000;}
      epoch=f.epoch;cursor=f.cursor;
    }
  }
  function pose(p){
    const now=performance.now(),r=actors.get(p.id),motion=window.GauntletAbilityAnimations?.motion(p);
    if(p.status!=='alive')return{sheet:'body',frame:7,dir:direction(p)};
    if(now-(r?.transformAt??-Infinity)<800)return{sheet:'actions',frame:now-r.transformAt<350?6:7,dir:direction(p)};
    if(motion){const elapsed=motion.elapsed+(now-motion.at)/1000,release=motion.releaseAt??0;
      const waiting=motion.kind?.startsWith('ascend_')&&motion.released===false;
      const step=motion.cancelled?2:elapsed<release||waiting?0:elapsed<release+.13?1:2;
      const group=motion.kind?.startsWith('ascend_')?2:motion.attackType==='light'?0:motion.attackType==='ultimate'?2:1;
      return{sheet:'actions',frame:group*3+step,dir:direction(motion)};
    }
    if(now-(r?.hitAt??-Infinity)<130)return{sheet:'body',frame:6,dir:direction(p)};
    if(p.basicPreparation>0)return{sheet:'actions',frame:0,dir:direction(p)};
    const walking=p.moving;
    return{sheet:'body',frame:(walking?3:0)+Math.floor(now/(walking?(p.class==='Knight'?220:165):360))%3,dir:direction(p)};
  }
  function featureMask(hero,q,img){
    const key=[hero,q.sheet,q.frame,q.dir].join(':');if(masks.has(key))return masks.get(key);
    const c=document.createElement('canvas');c.width=c.height=96;const g=c.getContext('2d');g.drawImage(img,q.frame*96,q.dir*96,96,96,0,0,96,96);
    const data=g.getImageData(0,0,96,96),v=data.data;
    for(let i=0;i<v.length;i+=4){const r=v[i],gr=v[i+1],b=v[i+2],bright=r+gr+b>490,teal=gr>r*1.15&&b>r*1.08,violet=b>gr*1.25&&r>gr*1.06;
      if(!v[i+3]||!(hero==='Rogue'?violet:['Healer','Archer','Wizard'].includes(hero)?teal||bright:bright))v[i+3]=0;
    }
    g.putImageData(data,0,0);if(masks.size>=96)masks.delete(masks.keys().next().value);masks.set(key,c);return c;
  }
  function hero(ctx,p,x,y){
    if(!p.ascended)return false;const q=pose(p),pack=ensure(p.class,q.sheet==='actions'),img=pack?.[q.sheet];
    if(!pack?.meta||!loaded(img))return false;
    const hover=p.class==='Wizard'&&p.status==='alive'?-6-(still()?0:Math.round(Math.sin(performance.now()/440))):0;
    const reaction=q.sheet==='body'&&q.frame===6?1:0;
    ctx.save();ctx.imageSmoothingEnabled=false;ctx.drawImage(img,q.frame*96,q.dir*96,96,96,x-48+reaction,y-72+hover,96,96);
    if(!reduced()&&p.status==='alive'){ctx.globalAlpha*=.07;ctx.drawImage(featureMask(p.class,q,img),x-48,y-72+hover);}
    if(p.class==='Wizard'&&!reduced()&&!still()&&p.status==='alive'){
      ctx.globalAlpha=.65;ctx.strokeStyle=colors.Wizard;ctx.lineWidth=1;
      if(Math.floor(performance.now()/150)%5<2){ctx.beginPath();ctx.moveTo(x-10,y-29+hover);ctx.lineTo(x-14,y-24+hover);ctx.lineTo(x-9,y-21+hover);ctx.lineTo(x-12,y-15+hover);ctx.stroke();}
    }
    ctx.restore();return true;
  }
  function ground(ctx,room){
    if(document.hidden)return;const now=performance.now();
    for(const p of room.players||[]){const r=actors.get(p.id);if(!p.ascended||!r||p.status!=='alive'||p.connected===false||p.indoors)continue;
      if(!reduced())for(const [i,t]of r.trails.entries()){
        const age=(now-t.at)/320;if(age<0||age>1)continue;ctx.save();ctx.globalAlpha=(1-age)*(p.class==='Rogue'?.1:.3);ctx.fillStyle=colors[p.class];
        if(p.class==='Rogue'&&i%2===0){const pack=ensure(p.class);if(loaded(pack?.body)){const scale=room.phase==='town'?.78:1.65;ctx.imageSmoothingEnabled=false;ctx.drawImage(pack.body,t.frame*96,t.dir*96,96,96,t.x-48*scale,t.y-72*scale,96*scale,96*scale);}}
        else if(p.class==='Druid'){ctx.beginPath();ctx.moveTo(t.x,t.y+15);ctx.lineTo(t.x+4,t.y+11);ctx.lineTo(t.x+7,t.y+15);ctx.lineTo(t.x+2,t.y+17);ctx.fill();}
        else if(p.class==='Archer'){ctx.fillRect(t.x,t.y+12,5,1);ctx.fillRect(t.x+2,t.y+10,1,5);}
        else if(p.class==='Bard'){ctx.fillRect(t.x,t.y+12,8,1);ctx.fillRect(t.x+4,t.y+15,5,1);}
        else if(p.class==='Wizard')ctx.fillRect(t.x,t.y+13,3,2);
        ctx.restore();
      }
      const age=now-r.transformAt;if(age>=0&&age<1000){ctx.save();ctx.globalAlpha=.8*(1-age/1000);ctx.strokeStyle=colors[p.class];ctx.lineWidth=2;
        const t=reduced()||still()?.5:age/1000,stroke=points=>{ctx.beginPath();points.forEach(([x,y],i)=>ctx[i?'lineTo':'moveTo'](p.x+x,p.y+y));ctx.stroke();};
        if(p.class==='Knight')stroke([[-23,-66],[-23,-83],[-11,-75],[0,-91],[11,-75],[23,-83],[23,-66],[-23,-66]]);
        else if(p.class==='Healer')for(const s of[-1,1])stroke([[0,-34],[s*28,-60],[s*49,-62],[s*34,-34],[s*17,-25]]);
        else if(p.class==='Cleric')for(const s of[-1,1])stroke([[s*35,-23],[s*45,-39],[s*35,-55],[s*25,-39],[s*35,-23]]);
        else if(p.class==='Wizard')for(const s of[-1,1])stroke([[s*10,-18],[s*24,-30],[s*17,-37],[s*33,-53]]);
        else if(p.class==='Rogue')for(const s of[-1,1])stroke([[s*12,-50],[s*(30+t*15),-17],[s*22,4]]);
        else if(p.class==='Druid')for(const s of[-1,1])stroke([[0,14],[s*20,4],[s*30,-14],[s*23,-25],[s*34,-34]]);
        else if(p.class==='Bard')for(let i=0;i<3;i++)stroke([[-37-i*5,-23],[-20-i*5,-35],[0,-27],[20+i*5,-35],[37+i*5,-23]]);
        else if(p.class==='Archer')for(const s of[-1,1])stroke([[s*12,-30],[s*30,-55],[s*42,-59],[s*33,-43],[s*12,-30]]);
        ctx.restore();}
    }
  }
  function reset(){actors.clear();masks.clear();scene='';lastAt=0;epoch='';cursor=0;}
  document.addEventListener('visibilitychange',()=>{if(document.hidden)reset();});
  window.GauntletAscendedSprites={observe,hero,ground,reset,pose,supports:hero=>supported.has(hero),diagnostics:()=>({loadedForms:packs.size,actors:actors.size,trails:[...actors.values()].reduce((n,r)=>n+r.trails.length,0),masks:masks.size})};
})();

// Native normal-form reactions share the existing hero scale and floor anchors.
(() => {
  const root=document.currentScript?.dataset.spriteRoot||'/sprites/';
  const offsets={Knight:-72,Wizard:-80,Archer:-78,Cleric:-76,Rogue:-76,Druid:-76,Bard:-77,Healer:-79};
  const packs=new Map(),actors=new Map();let scene='',lastAt=-Infinity;
  const direction=p=>(Math.round((Math.PI/2-Math.atan2(p.facingY??1,p.facingX??0))/(Math.PI/4))+8)%8;
  function ensure(hero){
    if(!(hero in offsets))return null;
    if(!packs.has(hero)){const img=new Image(),pack={img,error:false};packs.set(hero,pack);img.onerror=()=>{pack.error=true;};img.src=root+'normal-hero-'+hero.toLowerCase()+'-reactions-v5.png';}
    return packs.get(hero);
  }
  function reset(){actors.clear();scene='';lastAt=-Infinity;}
  function observe(room){
    const now=performance.now(),key=[room.code,room.you,room.adventure?.area||'',room.stage,room.townInterior||''].join('|');
    const continuous=scene===key&&now-lastAt<1400&&!document.hidden;
    if(!continuous)actors.clear();scene=key;lastAt=now;const live=new Set();
    if(document.hidden)return;
    for(const p of room.players||[]){
      if(p.ascended||p.connected===false||!ensure(p.class)||live.size>=16)continue;
      live.add(p.id);const old=actors.get(p.id),same=old?.hero===p.class;
      const hit=continuous&&same&&p.status==='alive'&&old.status==='alive'&&(p.damageTaken||0)>old.damageTaken;
      actors.set(p.id,{hero:p.class,damageTaken:p.damageTaken||0,status:p.status,hitAt:hit?now:same?old.hitAt:-Infinity});
    }
    for(const id of actors.keys())if(!live.has(id))actors.delete(id);
  }
  function pose(p){
    if(p.ascended||!(p.class in offsets))return null;
    if(p.status&&p.status!=='alive')return{frame:1,dir:direction(p)};
    if(performance.now()-(actors.get(p.id)?.hitAt??-Infinity)<130)return{frame:0,dir:direction(p)};
    return null;
  }
  function hero(ctx,p,x,y){
    const q=pose(p);if(!q)return false;const pack=ensure(p.class),img=pack?.img;
    if(!img?.complete||!img.naturalWidth||pack.error)return false;
    ctx.save();ctx.imageSmoothingEnabled=false;ctx.drawImage(img,q.frame*96,q.dir*96,96,96,x-48,y+offsets[p.class],96,96);ctx.restore();return true;
  }
  document.addEventListener('visibilitychange',()=>{if(document.hidden)reset();});
  window.GauntletHeroReactions={observe,hero,pose,reset,diagnostics:()=>({packs:packs.size,actors:actors.size,errors:[...packs].filter(([,p])=>p.error).map(([hero])=>hero),decodedBytes:[...packs.values()].reduce((n,p)=>n+(p.img.complete&&p.img.naturalWidth?192*768*4:0),0)})};
})();
