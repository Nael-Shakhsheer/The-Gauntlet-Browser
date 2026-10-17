// Explicit renderer fixtures: all forms and directions, not earned campaign claims.
const fs=require('node:fs'),path=require('node:path'),{chromium}=require('playwright');
const out=path.join(__dirname,'../art/visual-quality-v3/review'),base=process.env.GAUNTLET_QA_URL||'http://127.0.0.1:8016';
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.GAUNTLET_ART_BROWSER_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 const context=await browser.newContext({viewport:{width:960,height:540}}),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.stack));page.on('response',r=>{if(r.status()>=400)errors.push(r.status()+' '+r.url());});
 try{
  await page.goto(base);await page.waitForTimeout(400);
  await page.evaluate(()=>{
   const canvas=document.querySelector('#world');document.body.replaceChildren(canvas);document.body.className='is-playing';Object.assign(canvas.style,{width:'960px',height:'540px',position:'relative',display:'block',top:0,left:0});
   const heroes=['Knight','Wizard','Archer','Cleric','Rogue','Druid','Bard','Healer'];
   window.artRoom={code:'all-form-renderer-fixture',you:'none',phase:'combat',mode:'adventure',stage:1,region:'woodland',areaSize:[960,540],players:heroes.map((hero,i)=>({id:hero,name:hero,class:hero,ascended:true,x:150+i%4*220,y:210+Math.floor(i/4)*230,hp:100,maxHp:100,status:'alive',color:'#e4d29c',facingX:1,facingY:0,connected:true})),summons:[],enemies:[],effects:[],projectiles:[],hazards:[],pings:[],environment:{obstacles:[],zones:[],barriers:[]},adventure:{area:'road',features:[],exits:[]}};
   window.setArt=(state,region,elapsed=.05,direction=2)=>{
    const r=artRoom;r.region=region;r.adventure=region==='cavern'?{area:'cave_entry',dungeon:{type:'underground'},features:[],exits:[]}:{area:'road',features:[],exits:[]};r.effects=[];
    r.players.forEach((p,i)=>{p.x=150+i%4*220;p.moving=state==='move';p.status=state==='downed'?'downed':'alive';const a=Math.PI/2-direction*Math.PI/4;p.facingX=Math.cos(a);p.facingY=Math.sin(a);
     p.abilityAnimation=['basic','cast','signature'].includes(state)?{id:p.id+state+direction,ownerId:p.id,heroClass:p.class,stage:1,abilityId:'fixture-'+state,kind:state==='signature'?'ascend_'+p.class.toLowerCase():'damage',attackType:state==='basic'?'light':'special',elapsed,releaseAt:state==='signature'?.6:0,released:state==='signature'?elapsed>=.6:true,duration:1.25,remaining:1.25-elapsed,facingX:p.facingX,facingY:p.facingY}:null;
    });
    GauntletAbilityAnimations.observe(r);GauntletAscendedSprites.observe(r);GauntletCombatVisuals.observe(r);GauntletCombatEnvironment.observe(r);GauntletProjectiles.observe(r);drawWorld(r);
    const g=canvas.getContext('2d');g.fillStyle='#18271fe8';g.fillRect(0,0,960,35);g.font='bold 14px monospace';g.fillStyle='#eee5c7';g.fillText('ASCENDED FORMS · '+state.toUpperCase()+' · '+region.toUpperCase()+' · renderer fixture',18,24);
   };setArt('idle','woodland');
  });
  await page.waitForTimeout(900);
  for(const region of ['woodland','cavern'])for(const state of ['idle','move','basic','cast','signature','downed']){
   await page.evaluate(({state,region})=>setArt(state,region,state==='signature'?.64:.05),{state,region});await page.waitForTimeout(120);await page.evaluate(({state,region})=>setArt(state,region,state==='signature'?.64:.05),{state,region});
   await page.locator('#world').screenshot({path:path.join(out,'all-eight-'+region+'-'+state+'.png')});
  }
  // A canvas stream captures actual changing runtime frames and all eight facings.
  const clip=await page.evaluate(async()=>{
   const canvas=document.querySelector('#world'),stream=canvas.captureStream(20),recorder=new MediaRecorder(stream,{mimeType:'video/webm;codecs=vp9',videoBitsPerSecond:2000000}),chunks=[];recorder.ondataavailable=e=>chunks.push(e.data);
   const complete=new Promise(resolve=>recorder.onstop=async()=>{const bytes=new Uint8Array(await new Blob(chunks,{type:'video/webm'}).arrayBuffer());let text='';for(let i=0;i<bytes.length;i+=8192)text+=String.fromCharCode(...bytes.subarray(i,i+8192));resolve(btoa(text));});recorder.start();const start=performance.now();let lastState='';
   await new Promise(resolve=>{function frame(now){const t=(now-start)/1000;if(t>=20){recorder.stop();stream.getTracks().forEach(t=>t.stop());resolve();return;}
    const section=Math.floor(t/2),region=section<5?'woodland':'cavern',state=['idle','move','basic','cast','signature'][section%5],within=t%2;
    const direction=Math.floor(within*4)%8,elapsed=state==='signature'?within%1.1:within%.46;
    if(state!==lastState){GauntletAbilityAnimations.observe({...artRoom,players:[]});lastState=state;}
    setArt(state,region,elapsed,direction);
    if(state==='move'){for(const p of artRoom.players)p.x+=Math.sin(within*3)*12;GauntletAscendedSprites.observe(artRoom);drawWorld(artRoom);}
    requestAnimationFrame(frame);
   }requestAnimationFrame(frame);});return await complete;
  });fs.writeFileSync(path.join(out,'ascended-eight-forms.webm'),Buffer.from(clip,'base64'));
  await page.emulateMedia({reducedMotion:'reduce'});await page.evaluate(()=>setArt('move','cavern'));await page.locator('#world').screenshot({path:path.join(out,'all-eight-reduced-motion.png')});
  const diagnostics=await page.evaluate(()=>GauntletAscendedSprites.diagnostics());fs.writeFileSync(path.join(out,'ascended-review.json'),JSON.stringify({scope:'Renderer-only fixtures; models/actions/directions are real client code. 20s canvas stream. Not earned progression or human timing review.',errors,diagnostics},null,2));
  console.log(JSON.stringify({errors,diagnostics}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
