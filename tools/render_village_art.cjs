// Artwork authoring through the real renderer, using local fixtures in a fresh
// browser context. Does not create rooms, call actions or write player saves.
const fs=require('node:fs'),path=require('node:path'),{chromium}=require('playwright');
const out=path.join(__dirname,'../art/village-redesign');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.GAUNTLET_ART_BROWSER_PATH?{executablePath:process.env.GAUNTLET_ART_BROWSER_PATH}:{channel:process.env.GAUNTLET_ART_BROWSER||'msedge'})});
 const page=await browser.newPage({viewport:{width:960,height:540}}),messages=[],views=[];
 page.on('pageerror',e=>messages.push(e.message));
 page.on('console',e=>{if(e.type()==='error')messages.push(e.text());});
 try{
  await page.goto('http://127.0.0.1:8000/');await page.waitForTimeout(1600);await page.evaluate(()=>document.fonts.ready);
  const layouts=JSON.parse(fs.readFileSync(path.join(out,'layout-fixtures.json'),'utf8'));
  await page.evaluate(layouts=>{
   const c=document.querySelector('#world');document.body.replaceChildren(c);document.body.classList.add('is-playing');
   Object.assign(c.style,{width:'960px',height:'540px',position:'relative',inset:'auto',display:'block'});
   Object.assign(document.body.style,{margin:'0',padding:'0',width:'960px',height:'540px',overflow:'hidden'});
   window.villageArtLayouts=layouts;
   const names=['Rowan','Mira','Kai','Lark'],roles=['Archer','Wizard','Knight','Bard'];
   const players=names.map((name,i)=>({id:'art-'+i,name,class:roles[i],x:417+i*42,y:460,facingX:0,facingY:1,hp:100,maxHp:100,status:'alive',connected:true,color:'#b0c5b5'}));
   window.villageArtRoom={code:'village-art-fixture',you:players[0].id,phase:'town',stage:3,region:'woodland',classes:{},areaSize:[960,540],players,enemies:[],summons:[],
    environment:{obstacles:[],zones:[]},projectiles:[],effects:[],hazards:[],pings:[],townNpcs:{gate:{x:480,y:500}},townExitVotes:0,townExitTotal:4,townInstance:1,innFloor:1};
   window.GauntletCombatEnvironment.observe(villageArtRoom);window.GauntletProjectiles.observe(villageArtRoom);
  },layouts);
  for(const region of ['woodland','ruins','cavern','frost']){
   for(const kind of Object.keys(layouts)){
    await page.evaluate(({region,kind})=>{Object.assign(villageArtRoom,villageArtLayouts[kind],{region,townInterior:null,townNpcs:{gate:{x:480,y:500}}});drawWorld(villageArtRoom);},{region,kind});
    const filename='village-'+region+'-'+kind+'.png';await page.locator('#world').screenshot({path:path.join(out,filename)});views.push(filename);
   }
   for(const id of ['inn','store','lab','guild','cottage','lodge']){
    await page.evaluate(({region,id})=>{
     villageArtRoom.region=region;villageArtRoom.townInterior=id;villageArtRoom.innFloor=1;
     const service={inn:'innkeeper',store:'merchant',lab:'alchemist',guild:'guildmaster'}[id];
     villageArtRoom.townNpcs=service?{[service]:{x:480,y:220}}:{};
     villageArtRoom.players[0].x=480;villageArtRoom.players[0].y=410;drawWorld(villageArtRoom);
    },{region,id});
    const filename='interior-'+region+'-'+id+'.png';await page.locator('#world').screenshot({path:path.join(out,filename)});views.push(filename);
   }
   await page.evaluate(region=>{
    villageArtRoom.region=region;villageArtRoom.townInterior='inn';villageArtRoom.innFloor=2;
    villageArtRoom.townNpcs={stairs_down:{x:710,y:430},bed_guest_1:{x:260,y:190},bed_guest_3:{x:700,y:190}};
    villageArtRoom.innRooms=[{id:'guest_1',name:'Room 1',x:260,y:190,locked:false},{id:'guest_2',name:'Room 2',x:480,y:190,locked:true},{id:'guest_3',name:'Room 3',x:700,y:190,locked:false}];
    villageArtRoom.players[0].x=480;villageArtRoom.players[0].y=420;drawWorld(villageArtRoom);
   },region);
   const filename='upstairs-'+region+'.png';await page.locator('#world').screenshot({path:path.join(out,filename)});views.push(filename);
   await page.evaluate(()=>{villageArtRoom.players.forEach((p,i)=>{p.x=417+i*42;p.y=460;});});
  }
  await page.evaluate(()=>{
   Object.assign(villageArtRoom,villageArtLayouts.market_ring,{region:'woodland',townInterior:null,townNpcs:{gate:{x:480,y:500}}});
   const tree=window.GauntletTownSprites.layout(villageArtRoom).find(o=>o.kind==='tree');
   if(tree){villageArtRoom.players[0].x=tree.x;villageArtRoom.players[0].y=tree.y-20;}drawWorld(villageArtRoom);
  });
  await page.locator('#world').screenshot({path:path.join(out,'woodland-canopy-behind.png')});
  await page.evaluate(()=>{villageArtRoom.players[0].y+=40;drawWorld(villageArtRoom);});
  await page.locator('#world').screenshot({path:path.join(out,'woodland-canopy-front.png')});
  await page.evaluate(()=>{
   villageArtRoom.players[0].x=420;villageArtRoom.players[0].y=460;
   villageArtRoom.adventure={area:'home',complete:false,features:[{id:'runner',name:'Village Runner',kind:'talk',x:360,y:390},{id:'hunter_recovered',name:'Recovered Hunter',kind:'hunter',x:675,y:390}],
    exits:[{id:'road',name:'Southern road',edge:'south',x:480,y:490}],nearby:{id:'road'}};
   drawWorld(villageArtRoom);
  });
  await page.locator('#world').screenshot({path:path.join(out,'adventure-oakvale.png')});views.push('adventure-oakvale.png');
  await page.evaluate(()=>{villageArtRoom.adventure.complete=true;drawWorld(villageArtRoom);});
  await page.locator('#world').screenshot({path:path.join(out,'adventure-oakvale-celebration.png')});views.push('adventure-oakvale-celebration.png');
  fs.writeFileSync(path.join(out,'render-notes.json'),JSON.stringify({purpose:'Actual client artwork fixtures; no gameplay suite or personal rooms/saves',regions:4,seededLayouts:7,views,messages},null,2)+'\n');
  console.log('Rendered '+views.length+' village/interior/upstairs artwork views. Browser diagnostics: '+messages.length);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
