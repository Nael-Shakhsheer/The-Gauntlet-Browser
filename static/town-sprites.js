// Town character and hovering chest sprite renderer. No gameplay state changes.
(() => {
  const images = new Map();
  const directions = ["south", "south-east", "east", "north-east", "north", "north-west", "west", "south-west"];
  const characters = ["Merchant", "Guildmaster", "Alchemist", "Innkeeper", ...Array.from({ length: 8 }, (_, i) => "Villager" + String(i + 1).padStart(2, "0"))];
  function load(key) {
    if(images.has(key))return images.get(key);
    if(![...characters,'TreasureChest'].includes(key))return null;
    const image = new Image();
    const path = key === "TreasureChest" ? "/sprites/treasure-chest" : "/sprites/" + key.toLowerCase() + "-idle";
    const entry = { image, metadata: null };
    images.set(key, entry);
    image.src = path + ".png";
    fetch(path + ".json").then((response) => {
      if (!response.ok) throw new Error("Town sprite metadata unavailable");
      return response.json();
    }).then((metadata) => { entry.metadata = metadata; }).catch(() => { entry.metadata = null; });
    return entry;
  }
  function ready(key) {
    const entry = load(key);
    return entry?.metadata && entry.image.complete && entry.image.naturalWidth ? entry : null;
  }
  function character(ctx, key, x, y, options = {}) {
    const entry = ready(key);
    if (!entry) return false;
    const sheet = entry.metadata.spritesheet;
    const direction = directions.includes(options.direction) ? options.direction : "south";
    const row = sheet.rows.find((candidate) => candidate.type === "animation" && candidate.direction === direction);
    const frames = entry.metadata.animations[options.mode || "idle"] || entry.metadata.animations.idle;
    if (!row || !frames?.length) return false;
    const column = frames[Math.floor((Date.now() + (options.phase || 0)) / 180) % frames.length];
    const cell = sheet.cell_size;
    const scale = options.scale || 1;
    ctx.save();
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(entry.image, column * cell.width, row.row * cell.height, cell.width, cell.height,
      x - 32 * scale, y - 42 * scale, 64 * scale, 64 * scale);
    ctx.restore();
    return true;
  }
  function chest(ctx, entity) {
    const entry = ready("TreasureChest");
    if (!entry) return false;
    const sheet = entry.metadata.spritesheet;
    const mode = entity.opened ? "open_float" : "float";
    const animation = entry.metadata.animations[mode];
    if (!animation?.frames?.length) return false;
    const column = animation.frames[Math.floor(Date.now() / animation.frame_duration_ms) % animation.frames.length];
    const cell = sheet.cell_size;
    ctx.save();
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(entry.image, column * cell.width, animation.row * cell.height, cell.width, cell.height,
      entity.x - 38, entity.y - 34, 76, 76);
    ctx.restore();
    return true;
  }
  const regions=['woodland','ruins','cavern','frost'],props=new Image(),dressing=new Map();
  props.src='/sprites/village-details-v2.png';
  const palettes={
    woodland:['#99835b','#b8a078','#6e7751','#ddcba0'],
    ruins:['#92816a','#b5a28b','#6d7565','#d7cbb5'],
    cavern:['#4a5e6e','#6b8290','#394c5b','#96a6af'],
    frost:['#90a9b6','#b0c5ca','#708a9d','#e0eaf0']
  };
  function hash(text){let n=2166136261;for(const c of text)n=Math.imul(n^c.charCodeAt(0),16777619);return n>>>0;}
  function rng(seed){let n=seed;return()=>{n=(n+0x6D2B79F5)|0;let t=Math.imul(n^n>>>15,1|n);t^=t+Math.imul(t^t>>>7,61|t);return((t^t>>>14)>>>0)/4294967296;};}
  function regionOf(room){return regions.includes(room.region)?room.region:'woodland';}
  function nearPaths(x,y,paths,radius){
    for(const points of paths)for(let i=1;i<points.length;i++){
      const [ax,ay]=points[i-1],[bx,by]=points[i],dx=bx-ax,dy=by-ay;
      const t=Math.max(0,Math.min(1,((x-ax)*dx+(y-ay)*dy)/Math.max(1,dx*dx+dy*dy)));
      if(Math.hypot(x-ax-dx*t,y-ay-dy*t)<radius)return true;
    }return false;
  }
  function trace(g,points){
    if(!points.length)return;g.beginPath();g.moveTo(points[0][0]/2,points[0][1]/2);
    // Rounding stays within four world pixels of the server's existing route.
    for(let i=1;i<points.length-1;i++){
      const [x,y]=points[i],[ax,ay]=points[i-1],[bx,by]=points[i+1];
      const before=Math.hypot(x-ax,y-ay),after=Math.hypot(bx-x,by-y),r=Math.min(8,before/2,after/2);
      g.lineTo((x+(ax-x)*r/Math.max(1,before))/2,(y+(ay-y)*r/Math.max(1,before))/2);
      g.quadraticCurveTo(x/2,y/2,(x+(bx-x)*r/Math.max(1,after))/2,(y+(by-y)*r/Math.max(1,after))/2);
    }
    const last=points.at(-1);g.lineTo(last[0]/2,last[1]/2);
  }
  function paintPaths(g,room){
    const colors=palettes[regionOf(room)],paths=room.townPaths || [],random=rng(hash(String(room.townSeed || room.code)));
    g.save();g.lineCap=g.lineJoin='round';
    // Low contrast edge bands blend into the same ground material as the world.
    for(const [width,alpha,color]of [[62,.08,colors[0]],[54,.12,colors[0]],[46,.25,colors[0]],[38,.68,colors[1]]]){
      g.globalAlpha=alpha;g.strokeStyle=g.fillStyle=color;g.lineWidth=width/2;
      for(const [x,y]of room.townDecor?.plazas || []){g.beginPath();g.ellipse(x/2,y/2,width*.72,width*.47,0,0,Math.PI*2);g.fill();}
      for(const points of paths){trace(g,points);g.stroke();}
    }
    g.globalAlpha=.22;
    for(const points of paths)for(let i=1;i<points.length;i++){
      const [ax,ay]=points[i-1],[bx,by]=points[i],length=Math.hypot(bx-ax,by-ay);
      for(let d=8+random()*12;d<length;d+=16+random()*17){
        const offset=(random()-.5)*20,x=(ax+(bx-ax)*d/length-(by-ay)*offset/Math.max(1,length))/2,y=(ay+(by-ay)*d/length+(bx-ax)*offset/Math.max(1,length))/2;
        g.fillStyle=random()<.6?colors[0]:colors[3];g.fillRect(Math.round(x),Math.round(y),random()<.5?2:3,1);
      }
    }g.restore();
  }
  function detail(ctx,room,variant,x,y,scale=1){
    if(!props.complete||!props.naturalWidth)return false;
    ctx.save();ctx.imageSmoothingEnabled=false;const cell=96,row=regions.indexOf(regionOf(room));
    ctx.drawImage(props,variant*cell,row*cell,cell,cell,Math.round(x-48*scale),Math.round(y-82*scale),cell*scale,cell*scale);ctx.restore();return true;
  }
  function layout(room){
    const houses=room.townHouses || [],paths=room.townPaths || [],region=regionOf(room);
    const story=(room.adventure?.features || []).filter(f=>f.kind==='talk'||f.kind==='hunter');
    const key=JSON.stringify([room.code,room.townInstance,room.townSeed,region,houses,paths,room.townDecor,story.map(f=>[f.id,f.x,f.y])]);
    if(dressing.has(key))return dressing.get(key);
    const random=rng(hash(key)),items=[],row=regions.indexOf(region);
    function clear(x,y,margin=16){
      return x>25&&x<935&&y>70&&y<488&&!houses.some(h=>Math.abs(x-h.x)<80+margin&&y>h.y-85-margin&&y<h.y+44+margin)
        &&(!room.townPortal || Math.hypot(x-room.townPortal.x,y-room.townPortal.y)>100)
        &&Math.hypot(x-480,y-480)>93&&!story.some(f=>Math.hypot(x-f.x,y-f.y)<74);
    }
    function add(kind,variant,x,y,scale=1){
      if(items.some(o=>Math.hypot(x-o.x,y-o.y)<(kind==='tree'?50:32)))return;
      items.push({kind,variant,row,x:Math.round(x),y:Math.round(y),scale,depth:y});
    }
    // Use the actual seeded village tree positions, then fill their understory.
    for(const [i,[x,y]]of (room.townDecor?.trees || []).entries()){
      if(!clear(x,y,9)||nearPaths(x,y,paths,42))continue;
      add('tree',i%2,x,y,.64+random()*.1);
      if(clear(x+34,y+15,5)&&!nearPaths(x+34,y+15,paths,30))add('scenery',2,x+34,y+15,.48);
    }
    for(const [i,house]of houses.entries()){
      for(const side of [i%2?1:-1,i%2?-1:1]){
        const x=house.x+side*99,y=house.y+43;
        if(clear(x,y,2)&&!nearPaths(x,y,paths,22)){add('detail',3,x,y,.87);break;}
      }
      // Lamps sit beside door approaches, outside the center of the route.
      const lx=house.x+(i%2?1:-1)*47,ly=house.y+72;
      if(clear(lx,ly,0)&&!nearPaths(lx,ly,paths,16))add('detail',2,lx,ly,.9);
    }
    for(const [px,py]of room.townDecor?.plazas || []){
      for(const [dx,dy]of [[-62,8],[62,8],[0,-57],[0,57]]){
        const x=px+dx,y=py+dy;
        if(clear(x,y,14)&&!nearPaths(x,y,paths,39)){add('detail',1,x,y,1.0);break;}
      }
    }
    // Low planting islands enrich empty courtyards without covering thresholds.
    for(let y=100;y<480;y+=69)for(let x=46;x<935;x+=83){
      const px=x+(random()-.5)*32,py=y+(random()-.5)*24;
      if(random()<.55&&clear(px,py,12)&&!nearPaths(px,py,paths,34))add('scenery',random()<.78?2:3,px,py,.43+random()*.12);
    }
    if(dressing.size>20)dressing.clear();dressing.set(key,items);return items;
  }
  function environment(room){
    return layout(room).map(o=>({depth:o.depth,occluder:true,bounds:o.kind==='detail'?{x:o.x-48*o.scale,y:o.y-82*o.scale,width:96*o.scale,height:96*o.scale}:window.GauntletWorldScenery?.bounds(o),draw:ctx=>{
      if(o.kind==='detail')detail(ctx,room,o.variant,o.x,o.y,o.scale);
      else window.GauntletWorldScenery?.drawObject(ctx,o);
    }}));
  }
  function portal(ctx,room,{markerOnly=false,structureOnly=false}={}){
    const p=room.townPortal;if(!p)return;
    const x=p.x,y=p.y,near=room.adventure?.nearby?.id==='village_portal';
    // Stable shrine silhouette; the portal renderer overlays channel/travel effects.
    ctx.save();if(!markerOnly){ctx.fillStyle='#465d56';ctx.beginPath();ctx.ellipse(x,y+6,62,34,0,0,Math.PI*2);ctx.fill();
    ctx.strokeStyle='#9aab88';ctx.lineWidth=3;ctx.stroke();
    const drawn=window.GauntletDungeonSprites?.stamp(ctx,'portal_shrine',x,y+18,{scale:1}) || window.GauntletAdventureSprites?.stamp(ctx,'shrine_restored',x,y+18,{scale:.65});
    if(!drawn){ctx.fillStyle='#91a592';ctx.fillRect(x-22,y-17,44,23);ctx.fillStyle='#b9e8d0';ctx.beginPath();ctx.arc(x,y-24,9,0,Math.PI*2);ctx.fill();}
    }if(near&&!structureOnly){ctx.fillStyle='#fff0c8';ctx.font='bold 12px monospace';ctx.textAlign='center';ctx.fillText('E · VILLAGE PORTAL',x,y+53);}
    ctx.restore();
  }
  function portalBounds(room){
    const p=room.townPortal;if(!p)return null;
    const b=window.GauntletDungeonSprites?.bounds('portal_shrine',p.x,p.y+18);
    if(!b)return null;
    const x=Math.min(b.x,p.x-64),y=Math.min(b.y,p.y-30);
    return {x,y,width:Math.max(b.x+b.width,p.x+64)-x,height:Math.max(b.y+b.height,p.y+42)-y};
  }
  window.GauntletTownSprites = { character, chest,paintPaths,detail,environment,layout,portal,portalBounds };
})();
