// Authoring screenshots through the actual game renderer; no rooms/actions/saves.
const path=require('node:path');const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:process.env.GAUNTLET_ART_BROWSER||'msedge'});
 const page=await browser.newPage({viewport:{width:1280,height:800}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 try {
  await page.goto('http://127.0.0.1:8000/');await page.waitForTimeout(2200);
  await page.evaluate(()=>{
   document.querySelector('#entry').classList.add('hidden');document.querySelector('#lobby').classList.remove('hidden');
   document.querySelector('#arenaPanel').classList.remove('hidden');document.body.classList.add('is-playing');
   const c=document.querySelector('#world');Object.assign(c.style,{width:'960px',height:'540px',position:'relative',inset:'auto',display:'block'});
   const player={id:'preview-hero',name:'Art preview',class:'Wizard',x:980,y:650,facingX:0,facingY:1,hp:100,maxHp:100,status:'alive',connected:true,color:'#b58bff'};
   const a={area:'crossroads',bridge:false,shrineRestored:false,complete:false,locked:false,features:[{id:'sign',name:'Woodland signpost',kind:'signpost',x:980,y:550}],
    exits:[{id:'road',name:'Southern road',edge:'west',x:48,y:540},{id:'camp',name:'Abandoned camp',edge:'south',x:614,y:1032},{id:'clearing',name:'Hunter clearing',edge:'east',x:1872,y:540},{id:'shrine',name:'Overgrown shrine',edge:'south',x:1382,y:1032}]};
   const enemy={id:'preview-wolf',name:'Wolf',kind:'wolf',class:'Knight',affinity:'Nature',x:1150,y:695,facingX:-1,facingY:0,hp:60,maxHp:80,color:'#64c78d',baseColor:'#85977a'};
   window.artRoom={code:'art-only-client',you:player.id,phase:'combat',stage:2,region:'woodland',classes:{Knight:{color:'#eee0b3'}},adventure:a,areaSize:[1920,1080],players:[player],enemies:[enemy],summons:[],environment:{obstacles:[],zones:[]},projectiles:[],effects:[],hazards:[],pings:[]};
   window.GauntletCombatEnvironment.observe(artRoom);window.GauntletProjectiles.observe(artRoom);
   window.artTimer=setInterval(()=>drawWorld(artRoom),16);
  });
  await page.waitForTimeout(350);
  await page.locator('#world').screenshot({path:path.join(__dirname,'../art/adventure-sprites/client-large-area.png')});
  await page.evaluate(()=>{
   artRoom.areaSize=[960,540];artRoom.region='woodland';artRoom.stage=4;artRoom.adventure={...artRoom.adventure,area:'shrine',features:[{id:'altar',name:'Shrine altar',kind:'shrine',x:480,y:265}],exits:[{id:'cross',name:'Crossroads',edge:'north',x:288,y:48},{id:'clearing',name:'Clearing',edge:'north',x:701,y:48}]};
   artRoom.players[0].x=365;artRoom.players[0].y=365;
   artRoom.enemies=[{id:'shrine-guardian',name:'Shrine Stone Guardian',kind:'troll',class:'Knight',affinity:'Nature',x:570,y:330,hp:260,maxHp:320,boss:true,bossPhase:1,color:'#64c78d',baseColor:'#85977a',facingX:-1,facingY:1,
    bossAttack:{kind:'slam',x:365,y:365,progress:.6,remaining:1,startedAt:1}}];
   window.GauntletCombatEnvironment.observe(artRoom);
  });
  await page.waitForTimeout(220);
  await page.locator('#world').screenshot({path:path.join(__dirname,'../art/adventure-sprites/client-guardian.png')});
  await page.evaluate(()=>clearInterval(artTimer));
  if(errors.length)throw Error('Art renderer: '+errors.join('; '));
  console.log('Game-renderer artwork screenshots saved using client-only fixtures; no API room/action requests.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
