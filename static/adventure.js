/* Interior maps: stable fit dimensions, pointer-centered wheel zoom and touch pan. */
(() => {
  function attach(viewport, image, state, controls) {
    const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
    state.zoom=clamp(state.zoom || 1,1,3);
    const bounds=(image.getAttribute('viewBox')||'0 0 600 240').split(/\s+/).map(Number),ratio=bounds[3]/bounds[2];
    function paint(){
      image.style.width=(state.fit*state.zoom)+'px';
      image.style.height=(state.fit*state.zoom*ratio)+'px';
      controls.out.disabled=state.zoom<=1;controls.in.disabled=state.zoom>=3;
      controls.value.textContent=Math.round(state.zoom*100)+'%';
    }
    function remember(){state.x=viewport.scrollLeft;state.y=viewport.scrollTop;}
    function zoom(value,point){
      const old=state.zoom,next=clamp(value,1,3);if(next===old)return;
      const p=point || [viewport.clientWidth/2,viewport.clientHeight/2];
      const oldInset=Math.max(0,(viewport.clientWidth-state.fit*old)/2);
      const world=[viewport.scrollLeft+p[0]-oldInset,viewport.scrollTop+p[1]];
      state.zoom=next;paint();
      const newInset=Math.max(0,(viewport.clientWidth-state.fit*next)/2);
      viewport.scrollLeft=world[0]*next/old+newInset-p[0];viewport.scrollTop=world[1]*next/old-p[1];remember();
    }
    function resize(){
      // Scrollbars must not feed back into fit sizing (or make the map shake).
      const width=viewport.offsetWidth-24,height=viewport.offsetHeight-24;
      if(width<=0 || height<=0)return;
      const fit=Math.floor(Math.min(width,height/ratio));if(fit===state.fit)return;
      const old=state.fit;state.fit=fit;paint();
      viewport.scrollLeft=old?(state.x || 0)*fit/old:0;viewport.scrollTop=old?(state.y || 0)*fit/old:0;remember();
    }
    const wheel=event=>{
      if(event.shiftKey || Math.abs(event.deltaX)>Math.abs(event.deltaY))return; // Native pan.
      const delta=event.deltaY*(event.deltaMode===1?18:event.deltaMode===2?viewport.clientHeight:1);
      const next=clamp(state.zoom*Math.exp(-clamp(delta,-240,240)*.002),1,3);
      if(next===state.zoom)return; // At Fit, scrolling down continues through the map list.
      event.preventDefault();const box=viewport.getBoundingClientRect();
      zoom(next,[event.clientX-box.left-viewport.clientLeft,event.clientY-box.top-viewport.clientTop]);
    };
    viewport.addEventListener('wheel',wheel,{passive:false});viewport.addEventListener('scroll',remember);
    controls.in.onclick=()=>zoom(state.zoom+.25);controls.out.onclick=()=>zoom(state.zoom-.25);
    controls.fit.onclick=()=>{zoom(1);viewport.scrollLeft=viewport.scrollTop=0;remember();};
    if(state.fit){paint();viewport.scrollLeft=state.x || 0;viewport.scrollTop=state.y || 0;}
    const observer=new ResizeObserver(resize);observer.observe(viewport);
    function focus(point){resize();const scale=state.fit*state.zoom/bounds[2],inset=Math.max(0,(viewport.clientWidth-state.fit*state.zoom)/2);viewport.scrollLeft=(point[0]-bounds[0])*scale+inset-viewport.clientWidth/2;viewport.scrollTop=(point[1]-bounds[1])*scale-viewport.clientHeight/2;remember();}
    return {resize,zoom,focus,dispose(){observer.disconnect();viewport.removeEventListener('wheel',wheel);viewport.removeEventListener('scroll',remember);}};
  }
  window.GauntletMapNavigation={attach};
})();

/* Adventure uses the same inputs/combat renderer; only the server changes facts. */
let adventurePanelSignature = '';
let signpostSignature = '';
$('#adventureMapButton').addEventListener('click', () => {
  openInfo('adventureMapDialog');
  showAtlasInteriors(Boolean(atlasState?.dungeon));
  requestAnimationFrame(()=>{
    sizeAtlas();
    if(!atlasViewOpened && matchMedia('(orientation:landscape) and (max-height:500px)').matches)setAtlasZoom(2);
    else if(!atlasViewOpened && ATLAS_SIZE[1]>950)setAtlasZoom(1.75);
    if(!atlasViewOpened)focusAtlasNode(atlasState?.locations.find(n=>n.current)?.id);
    atlasViewOpened=true;
  });
});
$('#adventureJournalButton').addEventListener('click', () => openInfo('adventureJournalDialog'));
let lastPortalMenu=null;
let travelSelection='',travelMethod='crystal',travelController=null,travelBusy=false,travelSignature='',travelMapArea='';
function selectTravelPoint(id){travelSelection=id;renderTravelDetails();const node=latestRoom?.adventure?.portals?.destinations.find(d=>d.id===id);if(node)travelController?.focus(atlasPoint(node));}
function renderSoulCrystal(room){
  const portal=room?.adventure?.portals,crystal=portal?.crystal,dialog=$('#soulCrystalDialog');
  $('#soulCrystalPouch').classList.toggle('hidden',!crystal || room.phase==='lobby');
  if(!crystal){if(dialog.open)dialog.close();return;}
  const crystalArt=crystal.charge<=0?'empty':crystal.charge>=crystal.capacity?'charged':'charging';
  for(const icon of document.querySelectorAll('[data-soul-crystal-sprite]'))if(icon.dataset.state!==crystalArt){icon.dataset.state=crystalArt;icon.style.backgroundImage='url("/sprites/item-soul-crystal-'+crystalArt+'-v1.png")';icon.textContent='';}
  if(!dialog.open)return;
  const capacity=crystal.capacity||10,charged=crystal.charge>=capacity;
  const text=(id,value)=>{const el=$(id);if(el.textContent!==value)el.textContent=value;};
  text('#soulCrystalCharge','Charge '+crystal.charge+' / '+capacity);
  text('#soulCrystalStatus',charged?'Charged':'Recharging');
  const blocked=portal.reason||portal.methods?.crystal;
  const availability=!charged&&blocked?.includes('crystal needs')?'':blocked||'';
  text('#soulCrystalAvailability',availability);$('#soulCrystalAvailability').classList.toggle('hidden',!availability);
  const meter=$('#soulCrystalMeter');if(meter.max!==capacity)meter.max=capacity;if(meter.value!==crystal.charge)meter.value=crystal.charge;
}
$('#inspectSoulCrystal').onclick=()=>{if(!latestRoom?.adventure?.portals?.crystal)return;openInfo('soulCrystalDialog');renderSoulCrystal(latestRoom);};
$('#soulCrystalTravel').onclick=openVillagePortal;
function renderTravelDetails(){
  const p=latestRoom?.adventure?.portals;if(!p)return;
  $('#villageTeleportButton').textContent=p.crystal?'Crystal '+p.crystal.charge+'/'+p.crystal.capacity:'Travel · server update';
  if(!$('#villagePortalDialog').open)return;
  if(travelMapArea!==latestRoom.adventure.area){$('#villagePortalDialog').close();return;}
  const d=p.destinations.find(d=>d.id===travelSelection),box=$('#transportDetails');if(!box)return;
  const channelText=p.channel?(p.channel.remaining===null?'Waiting for '+p.channel.waiting.join(', '):'Stand still · '+Math.ceil(p.channel.remaining)+'s'):'';
  const channelLabel=$('#travelChannelStatus');if(channelLabel&&channelLabel.textContent!==channelText)channelLabel.textContent=channelText;
  const sig=JSON.stringify([travelSelection,travelMethod,travelBusy,p.destinations,p.reason,p.message,p.methods,p.crystal,Boolean(p.channel)]);if(sig===travelSignature)return;travelSignature=sig;
  window.GauntletUI.preserve(box,()=>{box.replaceChildren();
  if(p.message)notice($('#villagePortalNotice'),p.message);
  $('#villagePortalDestinations').querySelectorAll('[data-travel-point]').forEach(g=>g.setAttribute('aria-pressed',String(g.dataset.travelPoint===travelSelection)));
  window.GauntletTravelMap?.select($('#villagePortalDestinations'),travelSelection,p.destinations);
  const add=(tag,text)=>{const el=document.createElement(tag);el.textContent=text;box.append(el);return el;};
  add('h3',d?.name||'Select a known travel point');
  for(const [step,label] of [[-1,'Previous point'],[1,'Next point']]){const b=add('button',label);b.className='secondary small';window.GauntletUI.control(b,'travel-'+step,'navigation');b.onclick=()=>{const list=p.destinations,index=list.findIndex(n=>n.id===travelSelection);selectTravelPoint(list[(index+step+list.length)%list.length]?.id||'');};}
  add('p',d?.current?'Your party is here.':d?.locked?'Unattuned destination':'Activated destination');
  const blocked=p.reason||p.methods?.[travelMethod]||d?.locked;
  const reason=blocked?.includes('crystal needs')?(p.crystal.charge<p.crystal.capacity?'Your crystal is recharging.':'A teammate’s crystal is recharging.'):
    blocked?.includes('gather at an activated shrine for free travel')?'Move closer to an activated shrine.':blocked;
  for(const method of ['shrine','crystal']){const b=add('button',method==='shrine'?'Shrine':'Crystal');b.className='secondary small';window.GauntletUI.control(b,'method-'+method,'navigation');b.setAttribute('aria-pressed',String(method===travelMethod));b.onclick=()=>{travelMethod=method;renderTravelDetails();};}
  if(reason)add('p',reason).className='notice';
  const status=add('p',channelText);status.id='travelChannelStatus';status.setAttribute('role','status');
  const confirm=add('button','Confirm travel');confirm.className='primary';confirm.disabled=travelBusy||!d||Boolean(reason);
  window.GauntletUI.control(confirm,'travel-confirm','primary');confirm.dataset.state=confirm.disabled?'locked':'available';
  confirm.onclick=async()=>{if(travelBusy)return;const owner=session;travelBusy=true;renderTravelDetails();try{await sendAction('villageTeleport',{destination:d.id,method:travelMethod});if(session===owner){notice($('#villagePortalNotice'),'Confirmed. Gather and stand still.','success');refresh();}}catch(e){if(session===owner)notice($('#villagePortalNotice'),e.message,'error');}finally{if(session===owner){travelBusy=false;renderTravelDetails();}}};
  if(p.channel){const cancel=add('button','Cancel transport');cancel.className='secondary small';window.GauntletUI.control(cancel,'travel-cancel','navigation');cancel.disabled=travelBusy;cancel.onclick=async()=>{if(travelBusy)return;const owner=session;travelBusy=true;renderTravelDetails();try{await sendAction('cancelTeleport');if(session===owner)refresh();}catch(e){if(session===owner)notice($('#villagePortalNotice'),e.message,'error');}finally{if(session===owner){travelBusy=false;renderTravelDetails();}}};}
  });
}
function openVillagePortal(){
  const portal=latestRoom?.adventure?.portals;if(!portal)return;
  if(!portal.crystal||!portal.methods){notice($('#combatNotice'),'Updated travel needs the latest Python server. Restart it after backing up saves, then refresh.');return;}
  travelController?.dispose();travelController=null;travelBusy=false;travelSignature='';travelMapArea=latestRoom.adventure.area;
  travelMethod=portal.methods?.shrine?'crystal':'shrine';
  if(!portal.destinations.some(d=>d.id===travelSelection))travelSelection=portal.destinations.find(d=>!d.locked)?.id||portal.destinations[0]?.id||'';
  const box=$('#villagePortalDestinations');box.replaceChildren();box.className='transport-layout';
  const chart=document.createElement('section'),controls=document.createElement('div');controls.className='map-controls';
  const buttons={};for(const [id,label] of [['out','−'],['fit','Fit'],['in','+'],['value','100%']]){const b=document.createElement(id==='value'?'span':'button');b.textContent=label;b.className='secondary small';buttons[id]=b;controls.append(b);}
  const viewport=document.createElement('div');viewport.className='transport-map-viewport';viewport.tabIndex=0;viewport.setAttribute('aria-label','Travel map. Zoom with wheel or buttons; swipe or scroll to pan.');
  let svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
  const current=latestRoom.adventure.locations.find(l=>l.current),nodes=[...portal.destinations];
  if(current&&!nodes.some(n=>n.current))nodes.push({id:current.id,name:current.name,position:current.position,current:true,mapOnly:true,locked:'Party location'});
  const points=nodes.map(n=>atlasPoint(n)),minX=Math.min(...points.map(p=>p[0]))-130,minY=Math.min(...points.map(p=>p[1]))-70;
  svg.setAttribute('viewBox',[minX,minY,Math.max(400,Math.max(...points.map(p=>p[0]))-minX+150),Math.max(260,Math.max(...points.map(p=>p[1]))-minY+70)].join(' '));
  const make=(tag,attrs)=>{const el=document.createElementNS(svg.namespaceURI,tag);for(const [k,v]of Object.entries(attrs))el.setAttribute(k,v);return el;};
  for(const n of nodes){const [x,y]=atlasPoint(n),g=make('g',{'data-travel-point':n.id,role:'button',tabindex:0,'aria-label':n.name+' · '+(n.current?'party location':n.locked||'available'),'aria-pressed':String(n.id===travelSelection)});
    g.append(make('rect',{x:x-110,y:y-32,width:220,height:64,rx:7,fill:n.current?'#3d5d4c':n.locked?'#263a34':'#4a5237',stroke:n.current?'#ffe4a0':'#829878','stroke-width':3}));
    const title=make('text',{x,y:y-3,'text-anchor':'middle',fill:n.current?'#ffe4a0':'#eee5c5','font-size':14});title.textContent=n.name;g.append(title);
    const status=make('text',{x,y:y+18,'text-anchor':'middle',fill:'#bcd0b6','font-size':11});status.textContent=n.current?'PARTY':n.locked?'INACTIVE':'ACTIVATED';g.append(status);
    const select=()=>{travelSelection=n.id;svg.querySelectorAll('[role=button]').forEach(el=>el.setAttribute('aria-pressed',String(el===g)));renderTravelDetails();};g.onclick=select;g.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}};svg.append(g);
  }
  if(window.GauntletTravelMap)svg=window.GauntletTravelMap.create({nodes,point:atlasPoint,selection:travelSelection,onSelect:selectTravelPoint});
  viewport.append(svg);
  const legend=document.createElement('p');legend.className='transport-legend';legend.textContent='◆ Party here · ✧ Attuned · ▣ Unattuned · dotted lines show shrine travel';
  chart.append(controls,viewport,legend);const details=document.createElement('section');details.id='transportDetails';box.append(chart,details);
  openInfo('villagePortalDialog');travelController=window.GauntletMapNavigation.attach(viewport,svg,{zoom:1},buttons);travelController.resize();
  if(matchMedia('(orientation:landscape) and (max-height:500px)').matches)travelController.zoom(1.75);
  const focusButton=document.createElement('button');focusButton.className='secondary small';focusButton.textContent='Selected point';focusButton.dataset.uiAction='navigation';focusButton.onclick=()=>selectTravelPoint(travelSelection);controls.append(focusButton);
  selectTravelPoint(travelSelection);
  renderTravelDetails();notice($('#villagePortalNotice'),portal.reason||'');
}
$('#villagePortalDialog').addEventListener('close',()=>{if($('#villagePortalDialog').open)return;travelController?.dispose();travelController=null;});
$('#villageTeleportButton').onclick=openVillagePortal;
let trackingBusy=false;
let atlasSelection='',atlasZoom=1,atlasState=null,atlasViewOpened=false,atlasRegion='';
const ATLAS_REGION_NAMES={early:'Woodland & Dunmere',aurelian:'Aurelian City',verdant:'The Verdant Veil',cinder:'The Cinder Crown'};
function atlasRegionFor(id){return id?.startsWith('city_')?'aurelian':id?.startsWith('veil_')?'verdant':id?.startsWith('cinder_')?'cinder':'early';}
$('#atlasRegionChoice').addEventListener('change',event=>{atlasRegion=event.target.value;atlasZoom=1;if(atlasState){renderWoodlandAtlas(atlasState);focusAtlasNode(atlasState.locations.find(n=>atlasRegionFor(n.id)===atlasRegion)?.id);}});
function showAtlasInteriors(interior,dungeonId=null){
  $('#adventureMapDialog').classList.toggle('interior-view',interior);
  $('#toggleAdventureMapView').textContent=interior?'Adventure atlas':'Dungeon maps';
  $('#adventureMapTitle').textContent=interior?'Discovered dungeon interiors':ATLAS_REGION_NAMES[atlasRegion]||'Adventure atlas';
  $('#dungeonMapChoice').hidden=!interior;
  if(interior&&dungeonId){selectedDungeon=dungeonId;dungeonPanelSignature='';if(atlasState)renderDungeonPanels(atlasState);}
  if(interior)requestAnimationFrame(()=>dungeonMapControllers.forEach(c=>c.resize()));
}
$('#toggleAdventureMapView').addEventListener('click',()=>showAtlasInteriors(!$('#adventureMapDialog').classList.contains('interior-view')));
let ATLAS_SIZE=[960,700];
let ATLAS_ORIGIN=[0,0];
// Illustrated geography: IDs/links still come exclusively from public state.
const ATLAS_POINTS={home:[205,118],road:[215,276],crossroads:[475,286],clearing:[760,280],camp:[478,449],shrine:[754,455],bridge:[296,497],ruins:[220,624]};
Object.assign(ATLAS_POINTS,{brook:[65,276],mill_trail:[65,145],yard:[478,615],hollow:[990,590],watch:[990,770],network:[640,770],border:[220,865],dunmere:[220,1035],fields:[640,1035],mill:[640,1210],cellar:[910,1210],eastern_threshold:[1050,1035]});
Object.assign(ATLAS_POINTS,{irrigation_channels:[1050,1330],farmstead:[1350,1330],pump_exterior:[1350,1035]});
const ATLAS_NOTES={home:'The woodland village. Trade, learn ordinary Skills and rest upstairs to choose recovery. Mara’s cottage restores HP and mana for 5 shared ordinary Runes.',road:'The southern approach to Oakvale. Follow the trail and keep an eye out for old landmarks.',crossroads:'The woodland trails meet here. Read the signpost to chart the nearby routes.',camp:'An abandoned camp beside the western trail.',clearing:'A sheltered clearing on the eastern trail.',shrine:'An old woodland shrine among the trees.',bridge:'A crossing on the western river trail.',ruins:'The old stone ruins beyond the river.'};
function atlasPoint(node){return ATLAS_POINTS[node.id] || [205+node.position[0]*270,118+node.position[1]*160];}
function atlasRoute(link,nodes){
  const from=nodes.get(link.fromId),to=nodes.get(link.toId);if(!from||!to)return null;
  const [x1,y1]=atlasPoint(from),[x2,y2]=atlasPoint(to);
  const offset=edge=>({north:[0,-86],south:[0,86],west:[-105,0],east:[105,0]})[edge] || [0,0];
  const [dx1,dy1]=offset(link.fromEdge),[dx2,dy2]=offset(link.toEdge);
  const bend=({'home|road':[-18,0],'crossroads|road':[0,30],'clearing|crossroads':[0,-18],'camp|crossroads':[12,0],'crossroads|shrine':[20,-8],'bridge|camp':[6,25],'bridge|road':[18,0],'bridge|ruins':[0,5],'clearing|shrine':[22,0]})[[link.fromId,link.toId].sort().join('|')] || [0,0];
  const mx=(x1+x2)/2+bend[0],my=(y1+y2)/2+bend[1],tx=(x2-x1)*.15,ty=(y2-y1)*.15;
  return `M ${x1} ${y1} C ${x1+dx1} ${y1+dy1}, ${mx-tx} ${my-ty}, ${mx} ${my} C ${mx+tx} ${my+ty}, ${x2+dx2} ${y2+dy2}, ${x2} ${y2}`;
}
function updateAtlasDetails(){
  const a=atlasState;if(!a)return;
  const node=a.locations.find(n=>n.id===atlasSelection) || a.locations.find(n=>n.current) || a.locations[0];if(!node)return;
  atlasSelection=node.id;
  const details=$('#adventureMapDetails');details.replaceChildren();
  const image=document.createElement('img');image.src=window.GauntletAdventureSprites.mapIcon(node.id,a);image.alt='';image.width=image.height=80;
  const state=document.createElement('p');state.className='eyebrow';state.textContent=node.current?'PARTY LOCATION':node.visited?'VISITED':'CHARTED TRAIL';
  const title=document.createElement('h3');title.textContent=node.name.replace(' · Home village','');
  const text=document.createElement('p');text.textContent=node.description || ATLAS_NOTES[node.id] || 'A charted location in '+(ATLAS_REGION_NAMES[atlasRegionFor(node.id)]||'the Adventure world')+'.';
  details.append(image,state,title,text);
  if(node.id==='road' && (a.dungeons||[]).some(d=>d.id==='cave')){
    const hint=document.createElement('p');hint.className='map-next-step';hint.textContent='Rootwater entrance: lower east edge of the Southern road. At the signpost, follow the southeast branch to the cave mouth and use Enter Rootwater passage. Ordinary retreat stays open until you awaken its boss.';details.append(hint);
  }
  if(node.objective){const objective=document.createElement('p');objective.className='map-objective';objective.textContent=node.objective;details.append(objective);}
  if(node.tracked){const goal=document.createElement('p');goal.className='map-tracking';goal.textContent='★ '+a.tracked.title;details.append(goal);}
  if(node.current && a.tracked && !a.tracked.complete){const step=document.createElement('p');step.className='map-next-step';step.textContent=a.tracked.nextStep;details.append(step);}
  const routes=a.connections.filter(l=>l.fromId===node.id || l.toId===node.id);
  if(routes.length){const heading=document.createElement('h4');heading.textContent='Connected trails';details.append(heading);
    routes.forEach(link=>{const other=a.locations.find(n=>n.id===(link.fromId===node.id?link.toId:link.fromId));if(!other)return;
      const button=document.createElement('button');button.type='button';button.className='map-destination';button.dataset.mapSelect=other.id;
      const name=document.createElement('span');name.textContent=other.name.replace(' · Home village','');
      const status=document.createElement('small');status.textContent=link.locked?'Closed':({north:'↑ North',south:'↓ South',west:'← West',east:'→ East'})[link.fromId===node.id?link.fromEdge:link.toEdge];
      button.append(name,status);details.append(button);
    });
  }
  $('#adventureMap').querySelectorAll('[data-map-select]').forEach(g=>g.setAttribute('aria-pressed',String(g.dataset.mapSelect===node.id)));
  const goalButton=$('[data-map-focus=goal]');goalButton.disabled=!a.locations.some(n=>n.tracked)&&!(a.dungeons||[]).some(d=>d.id===a.tracked.id&&!d.complete);
}
function setAtlasZoom(zoom){
  const viewport=$('#adventureMapViewport'),old=atlasZoom;atlasZoom=Math.max(1,Math.min(2.5,zoom));
  if(atlasZoom!==old){
    const center=[viewport.scrollLeft+viewport.clientWidth/2,viewport.scrollTop+viewport.clientHeight/2];
    $('#adventureMap').style.setProperty('--atlas-zoom',String(atlasZoom));
    viewport.scrollLeft=center[0]*atlasZoom/old-viewport.clientWidth/2;
    viewport.scrollTop=center[1]*atlasZoom/old-viewport.clientHeight/2;
  }
  $('[data-map-zoom=out]').disabled=atlasZoom<=1;$('[data-map-zoom=in]').disabled=atlasZoom>=2.5;
}
function sizeAtlas(){
  const viewport=$('#adventureMapViewport');
  // Scrollbars change clientWidth/clientHeight when a zoomed map overflows.
  // Fit against the stable outer box, reserving its borders and scrollbar space
  // on both axes, so ResizeObserver cannot make it alternate between two sizes.
  const width=viewport.offsetWidth-24,height=viewport.offsetHeight-24;
  if(width<=0||height<=0)return;
  const map=$('#adventureMap'),fit=Math.floor(Math.min(width,height*ATLAS_SIZE[0]/ATLAS_SIZE[1]))+'px';
  if(map.style.getPropertyValue('--atlas-fit')!==fit)map.style.setProperty('--atlas-fit',fit);
}
new ResizeObserver(sizeAtlas).observe($('#adventureMapViewport'));
function focusAtlasNode(id){
  const node=atlasState?.locations.find(n=>n.id===id);if(!node)return;
  if(atlasRegionFor(node.id)!==atlasRegion){atlasRegion=atlasRegionFor(node.id);atlasZoom=1;renderWoodlandAtlas(atlasState);}
  atlasSelection=id;updateAtlasDetails();
  const svg=$('#adventureMap svg'),viewport=$('#adventureMapViewport');if(!svg)return;
  const [x,y]=atlasPoint(node),scale=svg.getBoundingClientRect().width/ATLAS_SIZE[0];
  const offset=Math.max(0,(viewport.clientWidth-svg.getBoundingClientRect().width)/2);
  viewport.scrollTo({left:offset+(x-ATLAS_ORIGIN[0])*scale-viewport.clientWidth/2,top:(y-ATLAS_ORIGIN[1])*scale-viewport.clientHeight/2,behavior:'auto'});
}
$('#adventureMapDialog').addEventListener('click',event=>{
  if(event.target.closest('[data-dungeon-map]')){showAtlasInteriors(true,event.target.closest('[data-dungeon-map]').dataset.dungeonMap);return;}
  const select=event.target.closest('[data-map-select]');if(select){focusAtlasNode(select.dataset.mapSelect);return;}
  const focus=event.target.closest('[data-map-focus]');if(focus){
    if(focus.dataset.mapFocus==='party'&&atlasState?.dungeon || focus.dataset.mapFocus==='goal'&&(atlasState?.dungeons||[]).some(d=>d.id===atlasState.tracked.id&&!d.complete))showAtlasInteriors(true);
    else focusAtlasNode(atlasState?.locations.find(n=>focus.dataset.mapFocus==='party'?n.current:n.tracked)?.id);
    return;
  }
  const zoom=event.target.closest('[data-map-zoom]');if(zoom)setAtlasZoom(zoom.dataset.mapZoom==='fit'?1:atlasZoom+(zoom.dataset.mapZoom==='in'?.5:-.5));
});
$('#adventureMap').addEventListener('keydown',event=>{
  if(event.target.closest('[data-dungeon-map]') && (event.key==='Enter'||event.key===' ')){event.preventDefault();showAtlasInteriors(true,event.target.closest('[data-dungeon-map]').dataset.dungeonMap);return;}
  const node=event.target.closest('[data-map-select]');if(node && (event.key==='Enter'||event.key===' ')){event.preventDefault();focusAtlasNode(node.dataset.mapSelect);}
});
function renderWoodlandAtlas(a){
  atlasState=a;
  const regions=[...new Set(a.locations.map(n=>atlasRegionFor(n.id)))];
  if(!regions.includes(atlasRegion))atlasRegion=atlasRegionFor(a.locations.find(n=>n.current)?.id);
  const choice=$('#atlasRegionChoice');choice.replaceChildren();choice.hidden=regions.length<2;
  for(const id of Object.keys(ATLAS_REGION_NAMES).filter(id=>regions.includes(id))){const option=document.createElement('option');option.value=id;option.textContent=ATLAS_REGION_NAMES[id];choice.append(option);}choice.value=atlasRegion;
  const visible=a.locations.filter(n=>atlasRegionFor(n.id)===atlasRegion),coords=visible.map(atlasPoint);
  ATLAS_ORIGIN=atlasRegion==='early'?[0,0]:[Math.min(...coords.map(p=>p[0]))-135,Math.min(...coords.map(p=>p[1]))-110];
  ATLAS_SIZE=[Math.max(960,...coords.map(p=>p[0]-ATLAS_ORIGIN[0]+135)),Math.max(700,...coords.map(p=>p[1]-ATLAS_ORIGIN[1]+110))];
  if(!$('#adventureMapDialog').classList.contains('interior-view'))$('#adventureMapTitle').textContent=ATLAS_REGION_NAMES[atlasRegion];
  const ns='http://www.w3.org/2000/svg';
  const el=(tag,attrs={})=>{const e=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,String(v)));return e;};
  const svg=el('svg',{viewBox:[...ATLAS_ORIGIN,...ATLAS_SIZE].join(' '),role:'group','aria-label':'Charted locations in '+ATLAS_REGION_NAMES[atlasRegion]+'. Party at '+a.name});
  const extent={x:ATLAS_ORIGIN[0],y:ATLAS_ORIGIN[1],width:ATLAS_SIZE[0],height:ATLAS_SIZE[1]};
  const defs=el('defs'),mask=el('mask',{id:'atlas-reveal',maskUnits:'userSpaceOnUse',...extent});
  mask.append(el('rect',{...extent,fill:'white'}));
  const nodes=new Map(visible.map(n=>[n.id,n]));
  // Each charted area reveals its surrounding territory. Together all eight
  // areas reveal the whole illustration, rather than isolated landmark islands.
  const territories=atlasRegion==='early'?Object.entries(ATLAS_POINTS):Object.entries(window.GauntletCampaignArtData?.scenery?.mapPositions||{}).filter(([id])=>atlasRegionFor(id)===atlasRegion).map(([id,p])=>[id,atlasPoint({id,position:p})]),step=32;
  if(!territories.length)territories.push(...visible.map(n=>[n.id,atlasPoint(n)]));
  for(let y=extent.y;y<extent.y+extent.height;y+=step)for(let x=extent.x;x<extent.x+extent.width;x+=step){
    const closest=territories.reduce((best,[id,[px,py]])=>{
      const distance=(x+step/2-px)**2+(y+step/2-py)**2*1.2;
      return distance<best.distance?{id,distance}:best;
    },{id:'',distance:Infinity});
    if(nodes.has(closest.id))mask.append(el('rect',{x,y,width:step+1,height:step+1,fill:'black'}));
  }
  a.connections.forEach(link=>{const d=atlasRoute(link,nodes);if(d)mask.append(el('path',{d,fill:'none',stroke:'black','stroke-width':94}));});
  const ground=el('pattern',{id:'atlas-ground',width:320,height:320,patternUnits:'userSpaceOnUse'});ground.append(el('image',{href:'/sprites/world-ground-woodland-v2.png',width:320,height:320,style:'image-rendering:pixelated'}));defs.append(ground,mask);svg.append(defs);
  svg.append(el('rect',{...extent,fill:'url(#atlas-ground)'}));
  if(atlasRegion!=='early')svg.append(el('rect',{...extent,fill:{aurelian:'#98907a',verdant:'#496e53',cinder:'#654d49'}[atlasRegion],'fill-opacity':.65}));
  const regionalAtlas=window.GauntletCampaignScenery?.atlas(atlasRegion);
  svg.append(el('image',{href:regionalAtlas||'/sprites/ui-woodland-atlas-v1.png',...(regionalAtlas?extent:{width:960,height:700}),preserveAspectRatio:'none',style:'image-rendering:pixelated'}));
  // Trails are painted as dirt with a narrow sunlit center, then landmarks.
  if(a.locations.some(n=>['dunmere','fields','mill'].includes(n.id))){svg.append(el('rect',{x:75,y:935,width:950,height:420,fill:'#746447','fill-opacity':.3}));for(let y=960;y<1320;y+=28)svg.append(el('path',{d:`M 350 ${y} h 580`,stroke:'#536239','stroke-width':9,'stroke-opacity':.25}));}
  a.connections.forEach(link=>{const d=atlasRoute(link,nodes);if(!d)return;
    const route=el('g',{'aria-hidden':'true'});
    route.append(el('path',{d,fill:'none',stroke:'#25352b','stroke-width':18,'stroke-linecap':'round'}));
    route.append(el('path',{d,fill:'none',stroke:link.locked?'#78594b':'#97784c','stroke-width':13,'stroke-linecap':'round'}));
    route.append(el('path',{d,fill:'none',stroke:link.locked?'#d7a089':'#d1b578','stroke-width':6,'stroke-linecap':'round',...(link.locked?{'stroke-dasharray':'4 13'}:{})}));
    if(!link.locked)route.append(el('path',{d,fill:'none',stroke:'#ecd496','stroke-width':2,'stroke-dasharray':'2 14'}));
    svg.append(route);
  });
  svg.append(el('rect',{...extent,fill:'#162b32','fill-opacity':.97,mask:'url(#atlas-reveal)'}));
  visible.forEach(node=>{
    const [x,y]=atlasPoint(node),g=el('g',{'data-map-select':node.id,class:'atlas-landmark',role:'button',tabindex:0,'aria-label':node.name+(node.current?', party location':'')+(node.tracked?', tracked goal':''),'aria-pressed':'false'});
    const hit=el('rect',{x:x-74,y:y-66,width:148,height:132,fill:'transparent',class:'atlas-hit'});g.append(hit);
    g.append(el('ellipse',{cx:x,cy:y+9,rx:32,ry:10,fill:'#182b25','fill-opacity':.5,'aria-hidden':'true'}));
    g.append(el('path',{d:`M ${x-38} ${y-38} h 10 M ${x-38} ${y-38} v 10 M ${x+38} ${y-38} h -10 M ${x+38} ${y-38} v 10 M ${x-38} ${y+26} h 10 M ${x-38} ${y+26} v -10 M ${x+38} ${y+26} h -10 M ${x+38} ${y+26} v -10`,fill:'none',stroke:'#ffe2a1','stroke-width':3,class:'atlas-selection'}));
    g.append(el('image',{x:x-32,y:y-43,width:64,height:64,href:window.GauntletAdventureSprites.mapIcon(node.id,a),style:'image-rendering:pixelated','aria-hidden':'true'}));
    if(node.current){g.append(el('path',{d:`M ${x-5} ${y-61} h 10 v 6 h -3 v 3 h -4 v -3 h -3 Z`,fill:'#ffe3a0',stroke:'#192b28','stroke-width':2,'aria-hidden':'true'}));}
    if(node.visited){g.append(el('rect',{x:x-3,y:y+24,width:6,height:6,fill:node.current?'#ffe3a0':'#b0d88d',stroke:'#162b25','stroke-width':1,'aria-hidden':'true'}));}
    const name=node.name.replace(' · Home village','');
    const label=el('text',{x,y:y+47,'text-anchor':'middle',class:'atlas-label'});label.textContent=name;g.append(label);
    if(node.tracked){const star=el('text',{x:x+36,y:y-28,class:'atlas-goal','aria-hidden':'true'});star.textContent='★';g.append(star);}
    const title=el('title');title.textContent=name+(node.objective?' · '+node.objective:'');g.append(title);svg.append(g);
  });
  (a.dungeons||[]).forEach(d=>{
    if(atlasRegion!=='early')return;
    const anchorId=d.id==='sluice'?'pump_exterior':d.id==='mill_cellar'?'mill':d.id==='cave'?'road':'camp';
    const anchor=ATLAS_POINTS[anchorId];if(!a.locations.some(n=>n.id===anchorId))return;
    const [x,y]=[anchor[0]+74,anchor[1]+(d.id==='cave'?40:-40)];
    const g=el('g',{'aria-label':d.name+' · '+(d.complete?'cleared':'dungeon entrance'),role:'button',tabindex:0,'data-dungeon-map':d.id,class:'atlas-landmark'});
    g.append(el('image',{x:x-29,y:y-43,width:58,height:58,href:'/sprites/dungeon-entrance-'+(['mill_cellar','sluice'].includes(d.id)?'cave':d.id)+'-v1.png',style:'image-rendering:pixelated'}));
    if(d.current){const marker=el('text',{x,y:y-22,'text-anchor':'middle',fill:'#ffe3a0','font-size':16});marker.textContent='●';g.append(marker);}
    if(a.tracked.id===d.id&&!d.complete){const star=el('text',{x:x+17,y:y-10,class:'atlas-goal'});star.textContent='★';g.append(star);}
    const label=el('text',{x,y:y+25,class:'atlas-label','text-anchor':'middle'});label.textContent=d.id==='sluice'?'Sluice works':d.id==='mill_cellar'?'Mill cellar':d.id==='cave'?'Rootwater':'Briarwatch';g.append(label);svg.append(g);
    if(d.routeOpen){const end=ATLAS_POINTS[d.id==='sluice'?'irrigation_channels':d.id==='mill_cellar'?'fields':d.id==='cave'?'clearing':'bridge'];svg.append(el('path',{d:`M ${anchor[0]} ${anchor[1]} Q ${x+100} ${y+75} ${end[0]} ${end[1]}`,stroke:'#b7a9d4','stroke-width':4,'stroke-dasharray':'7 7',fill:'none','aria-label':'Unlocked dungeon passage'}));}
  });
  const compass=el('g',{transform:'translate('+(extent.x+extent.width-74)+' '+(extent.y+74)+')','aria-hidden':'true'});
  compass.append(el('path',{d:'M 0 -29 L 7 -7 L 29 0 L 7 7 L 0 29 L -7 7 L -29 0 L -7 -7 Z',fill:'#1c3139',stroke:'#c7af7e','stroke-width':2}));
  compass.append(el('path',{d:'M 0 -23 L 4 -4 L 0 0 L -4 -4 Z',fill:'#ffe2a1'}));
  const north=el('text',{x:0,y:-39,'text-anchor':'middle',class:'atlas-compass-letter'});north.textContent='N';compass.append(north);svg.append(compass);
  const viewport=$('#adventureMapViewport'),scroll=[viewport.scrollLeft,viewport.scrollTop];
  $('#adventureMap').replaceChildren(svg);viewport.scrollLeft=scroll[0];viewport.scrollTop=scroll[1];
  $('#adventureMapCount').textContent=a.locations.length+' locations charted';
  sizeAtlas();setAtlasZoom(atlasZoom);updateAtlasDetails();
}
const dungeonMapViews=new Map();
let dungeonMapControllers=[],dungeonMapWorld='',selectedDungeon='',dungeonPanelSignature='';
const dungeonChoice=$('#dungeonMapChoice');
dungeonChoice.onchange=()=>{selectedDungeon=dungeonChoice.value;dungeonPanelSignature='';if(atlasState)renderDungeonPanels(atlasState);};
window.resetAdventurePanels=()=>{
  adventurePanelSignature=signpostSignature=null;lastPortalMenu=null;trackingBusy=false;
  atlasSelection='';atlasZoom=1;atlasState=null;atlasViewOpened=false;atlasRegion='';ATLAS_ORIGIN=[0,0];
  dungeonMapControllers.forEach(c=>c.dispose());dungeonMapControllers=[];dungeonMapViews.clear();dungeonMapWorld='';
  selectedDungeon='';dungeonPanelSignature='';travelBusy=false;travelSignature='';travelController?.dispose();travelController=null;
  $('#adventureFeedback').classList.add('hidden');$('#signpostDirections').classList.add('hidden');
};
function renderDungeonPanels(a){
  if(!(a.dungeons||[]).some(d=>d.id===selectedDungeon))selectedDungeon=a.dungeons?.find(d=>d.current)?.id||a.dungeons?.[0]?.id||'';
  const panelSignature=JSON.stringify([a.dungeons?.map(d=>({...d,breakLeft:0})),Boolean(a.locked),a.tracked.id,a.locations.map(n=>[n.id,n.name]),a.nextRegion,selectedDungeon]);
  if(panelSignature===dungeonPanelSignature)return;dungeonPanelSignature=panelSignature;
  dungeonMapControllers.forEach(c=>c.dispose());dungeonMapControllers=[];
  const world=a.saveInfo?.worldId || latestRoom?.code;
  if(world!==dungeonMapWorld){dungeonMapViews.clear();dungeonMapWorld=world;}
  const maps=$('#adventureDungeonMaps'),journal=$('#adventureDungeonJournal');maps.replaceChildren();journal.replaceChildren();
  $('#toggleAdventureMapView').disabled=!(a.dungeons||[]).length;
  if(!(a.dungeons||[]).some(d=>d.id===selectedDungeon))selectedDungeon=a.dungeons?.find(d=>d.current)?.id||a.dungeons?.[0]?.id||'';
  window.GauntletUI.patch(dungeonChoice,JSON.stringify((a.dungeons||[]).map(d=>[d.id,d.name])),()=>{dungeonChoice.replaceChildren();for(const d of a.dungeons||[]){const o=document.createElement('option');o.value=d.id;o.textContent=d.name;dungeonChoice.append(o);}});dungeonChoice.value=selectedDungeon;
  for(const d of [...(a.dungeons||[])].sort((x,y)=>Number(y.current)-Number(x.current))){
    for(const [parent,isMap] of [[maps,true],[journal,false]]){
      if(isMap&&d.id!==selectedDungeon)continue;
      const card=document.createElement('section');card.className='adventure-quest dungeon-card';card.dataset.dungeonId=d.id;
      card.dataset.state=d.complete?'completed':d.current?'current':'discovered';
      const heading=document.createElement('h3');heading.textContent=(d.complete?'✓ ':'')+d.name+' · '+d.type+' · danger '+d.danger;
      card.append(heading);
      if(!isMap){const desc=document.createElement('p');desc.textContent=d.description;card.append(desc);}
      const destination=id=>a.locations.find(n=>n.id===id)?.name||id;
      const progress=document.createElement('p');progress.className='dungeon-progress';progress.textContent=d.complete?'Open route: '+d.entrances.map(destination).join(' ↔ '):d.type==='tower'?'Cleared floors: '+(d.floors.join(', ')||'none')+' / 3':'Visited chambers: '+d.nodes.filter(n=>n.visited).length+' · treasures: '+d.treasure;
      if(!d.complete)progress.textContent+=' · entrance: '+d.entrances.map(destination).join(' / ');
      if(!isMap)card.append(progress);
      if(d.current&&!isMap){const step=document.createElement('p');step.className='map-tracking';step.textContent=d.objective;card.append(step);if(d.roomHint){const hint=document.createElement('p');hint.className='dungeon-room-hint';hint.textContent=d.roomHint;card.append(hint);}}
      if(!isMap&&!d.complete){const track=document.createElement('button');track.className='secondary small';track.dataset.trackObjective=d.id;track.textContent=a.tracked.id===d.id?'Tracking ★':'Track dungeon';track.disabled=a.tracked.id===d.id;card.append(track);}
      if(d.surveyFound&&!isMap){const note=document.createElement('p');note.textContent='Discovery · Surveyor’s notes chart the old road-to-clearing passage.';card.append(note);}
      if(isMap&&d.nodes.length){
        const svg=window.GauntletDungeonSprites.map(d,Boolean(a.locked));
        const toolbar=document.createElement('div');toolbar.className='dungeon-map-controls';
        const controls={};
        for(const [key,label] of [['out','−'],['in','+'],['fit','Fit']]){
          const b=document.createElement('button');b.type='button';b.className='secondary small';b.textContent=label;
          b.setAttribute('aria-label',key==='fit'?'Fit '+d.name+' map':(key==='in'?'Zoom in':'Zoom out')+' '+d.name+' map');controls[key]=b;toolbar.append(b);
        }
        controls.value=document.createElement('span');toolbar.append(controls.value);
        const hint=document.createElement('span');hint.className='subtle';hint.textContent='Wheel to zoom · drag scrollbars or swipe to pan';toolbar.append(hint);
        const viewport=document.createElement('div');viewport.className='dungeon-map-viewport';viewport.tabIndex=0;viewport.setAttribute('aria-label',d.name+' map viewport');viewport.append(svg);
        card.append(toolbar,viewport);
        const legend=document.createElement('p');legend.className='dungeon-map-legend';legend.textContent='Gold · party   /   Green · cleared   /   Lock · sealed   /   Dark · uncharted';card.append(legend);
        if(!dungeonMapViews.has(d.id))dungeonMapViews.set(d.id,{});
        const controller=window.GauntletMapNavigation.attach(viewport,svg,dungeonMapViews.get(d.id),controls);dungeonMapControllers.push(controller);
      }
      if(isMap){const details=document.createElement('details'),summary=document.createElement('summary'),desc=document.createElement('p');details.className='dungeon-map-metadata';summary.textContent='Progress & route rules';desc.textContent=[d.current&&d.objective,d.roomHint,d.description].filter(Boolean).join(' ');details.append(summary,progress,desc);const legend=card.querySelector('.dungeon-map-legend');if(legend)details.append(legend);card.append(details);}
      parent.append(card);
    }
  }
  if(a.nextRegion){const p=document.createElement('p');p.className='adventure-quest';p.textContent='Next lead · '+a.nextRegion.name+': '+a.nextRegion.description;journal.append(p);}
}
$('#adventureJournalDialog').addEventListener('click',async event=>{
  const button=event.target.closest('[data-track-objective]');if(!button||trackingBusy)return;
  trackingBusy=true;button.disabled=true;
  try{await sendAction('adventureTrack',{objective:button.dataset.trackObjective});}
  catch(error){notice($('#combatNotice'),error.message);}
  finally{trackingBusy=false;refresh();}
});
function adventureSaveText(a) {
  if (a.saveError) return a.saveError;
  if (!a.persistence) return 'Disposable session: disk saving is disabled on this test server.';
  return 'World objectives, cleared groups, equipment and shared Runes save automatically. '+
    (a.checkpointBed ? 'Rest checkpoint: upstairs inn bed. ' : 'Recovery point: Oakvale gate; rest upstairs to choose an inn bed. ')+
    'Restart returns to that recovery point with saved progress. A party wipe costs 15% of shared Runes once. Online free-host storage is temporary.';
}
function adventureEncounterInstruction(a) {
  const objective=a.campaignExtension?.objective;
  if(objective?.type==='defense')return 'Protect '+objective.name+' and clear every assault wave to reopen the trails.';
  if(objective?.type==='boss')return 'Defeat '+objective.name+' to reopen the trails.';
  const dungeon=(a.dungeons||[]).find(d=>d.current);
  if(dungeon?.type==='tower')return 'Clear this floor’s waves to reopen the stairs.';
  if(a.area==='shrine'||a.area==='ruins')return 'Defeat the guardian to reopen the trails.';
  return 'Complete this encounter to reopen the passages.';
}
function adventureEncounterState(room) {
  const a=room.adventure,o=a?.campaignExtension?.objective,d=(a?.dungeons||[]).find(d=>d.current);
  const active=Boolean(a&&(a.locked||o)&&!a.campaignExtension?.cinematic);
  if(!active)return {active:false,detail:'',instruction:''};
  let detail=o?.type==='boss'?o.name+' · exits sealed':o?'Wave '+o.wave+'/'+o.waves+(o.breakLeft?' · next assault in '+o.breakLeft+'s':''):d?.type==='tower'?'Floor '+d.floor+'/3 · wave '+d.wave+'/'+d.waves:'Encounter · exits sealed';
  if(o?.ward)detail=o.ward.name+' · '+Math.ceil(o.ward.hp)+'/'+o.ward.maxHp+' HP · '+detail;
  if(d?.breakLeft)detail+=' · next wave in '+Math.ceil(d.breakLeft)+'s';
  return {active,detail,instruction:adventureEncounterInstruction(a)};
}
function adventureAnnouncement(feedback,encounter) {
  const text=feedback.text;
  if(/^Arrived at |^Wave \d+ (\/|secured\.)/.test(text))return null; // The encounter panel owns progress.
  if(/^Encounter seals the exits:/.test(text))return encounter.active&&Date.now()/1000-feedback.at<1.8?{id:feedback.at+':'+text,ttl:1600}:null;
  return {id:feedback.at+':'+text,tone:/interrupted|failed|could not|not saved/i.test(text)?'error':'info'};
}
function renderAdventure(room) {
  const a=room.adventure;
  const encounter=adventureEncounterState(room);document.body.classList.toggle('encounter-active',encounter.active);
  window.GauntletRecap?.render(room);
  window.renderRewardChoices?.(room);
  renderSoulCrystal(room);
  $('#adventureTools').classList.toggle('hidden',!a);
  document.body.classList.toggle('adventure-playing',Boolean(a));
  for(const feedback of a?.notifications||[]){const options=adventureAnnouncement(feedback,encounter);if(options)window.flowEvents?.push(feedback.text,options);}
  const objective=$('#trackedObjective'),objectiveText=!encounter.active&&a?.tracked&&!a.tracked.complete?a.tracked.title+' · '+a.tracked.nextStep:'';
  if(objective.textContent!==objectiveText)objective.textContent=objectiveText;objective.classList.toggle('hidden',!objectiveText);
  const board=a?.signpost;
  $('#signpostDirections').classList.toggle('hidden',!board);
  const boardSignature=JSON.stringify(board || null);
  if (boardSignature!==signpostSignature) {
    signpostSignature=boardSignature;
    const routes=$('#signpostRoutes');routes.replaceChildren();
    if (board) {
      $('#signpostTitle').textContent=board.name;
      board.directions.forEach(d=>{
        const row=document.createElement('div');row.className='signpost-route';
        const arrow=document.createElement('span');arrow.className='signpost-arrow';arrow.setAttribute('aria-hidden','true');
        arrow.textContent=({north:'↑',east:'→',south:'↓',west:'←'})[d.direction];
        const label=document.createElement('div'),direction=document.createElement('span'),name=document.createElement('strong');
        direction.textContent=d.directionLabel || d.direction;name.textContent=d.name;label.append(direction,name);row.append(arrow,label);routes.append(row);
      });
    }
  }
  if (!a) {window.renderSaveBadge?.(null);window.GauntletOpening?.update(room);return;}
  window.rememberAdventure?.(a.saveInfo);
  window.renderSaveBadge?.(a.saveInfo);
  if(a.portalMenu && a.portalMenu!==lastPortalMenu){lastPortalMenu=a.portalMenu;openVillagePortal();}
  const channel=a.portals?.channel;renderTravelDetails();
  $('#stageHeading').textContent=a.name+(room.townInterior ? (room.innFloor===2?' · Guest rooms':' · Interior') : '');
  $('#adventureStatus').textContent=a.locked?(a.campaignExtension?.objective?.type==='defense'?'Defense':'Encounter')+' · trails sealed':a.travel?'Gather · '+a.ready+'/'+a.total+' confirmed':a.campaignExtension?.completed?'Campaign complete · exploration open':a.campaign?.pumpingRestored&&!a.campaignExtension?.region?'Works restored · optional exploration remains':a.danger?'Local danger '+a.danger+' · trails open':'Village hub';
  $('#adventureStatus').dataset.messageKind='context';$('#adventureStatus').classList.toggle('hidden',encounter.active||!a.locked&&!a.travel&&!a.dungeon&&!a.portals?.channel);$('#adventureStatus').title=a.danger?'Local danger '+a.danger:'Village hub';
  const dungeon=(a.dungeons||[]).find(d=>d.current);
  if(dungeon)$('#adventureStatus').textContent=dungeon.type==='tower'?'Floor '+dungeon.floor+'/3 · '+(dungeon.wave?'wave '+dungeon.wave+'/'+dungeon.waves+(dungeon.breakLeft?' · break '+Math.ceil(dungeon.breakLeft)+'s':''):dungeon.floors.includes(dungeon.floor)?'cleared':'ready')+' · '+(a.locked?'stairs sealed':'stairs open'):dungeon.name+' · '+(a.locked?'boss seals exits':'retreat allowed');
  if(channel)$('#adventureStatus').textContent=channel.remaining===null?'Travel · waiting for '+channel.waiting.join(', '):'Portal · stand still '+Math.ceil(channel.remaining)+'s';
  const near=a.nearby;
  if (!room.townInterior) {
    $('#interactButton').classList.toggle('hidden',near?.kind==='dungeon_story' || !near && room.phase!=='puzzle');
    $('#interactButton').disabled=Boolean(room.movementLocked || near?.locked);
    if (near) $('#interactButton').textContent=near.locked ? 'Closed trail' : near.dungeonEntrance ? 'E · '+near.dungeonEntrance.name+(near.dungeonComplete?' · cleared':'') : near.id==='dungeon_begin'&&dungeon?.type==='tower' ? 'E · Begin floor '+dungeon.floor : 'E · '+(a.exits.some(e=>e.id===near.id)?'Travel: ':'')+near.name+(near.id===a.tracked?.nextExit?' ★':'');
    const waiting=(a.travelMembers || []).filter(p=>p.state!=='ready').map(p=>p.name+' ('+p.state+')').join(', ');
    if (room.phase!=='puzzle') combatContext(room.movementLocked ? 'Continue the conversation.' : near?.reason ||
      (waiting ? 'Waiting for '+waiting+'.' : near?.description || (near ? 'Press E or tap to '+(a.exits.some(e=>e.id===near.id)?'confirm travel together.':'interact.') :
       !encounter.active&&a.locked ? adventureEncounterInstruction(a) : '')));
  }
  $('#combatNotice').dataset.redundant=String(/^Press E or tap to /.test($('#combatNotice').textContent));
  const signature=JSON.stringify([a.locations,a.connections,a.journal,a.checkpointBed,a.saveError,a.persistence,a.tracked,a.discoveries,a.rewards,a.pendingRewards,(a.dungeons||[]).map(d=>({...d,breakLeft:0})),a.nextRegion]);
  window.GauntletOpening?.update(room);
  window.GauntletChapter?.render(room);
  if (signature===adventurePanelSignature) return;
  $('#adventureJournalSave').textContent=adventureSaveText(a);
  const journal=$('#adventureJournal');journal.replaceChildren();
  for(const [state,title] of [['active','Active objectives'],['completed','Completed'],['undiscovered','Not yet revealed']]){
    const quests=a.journal.filter(q=>q.visibility===state).sort((x,y)=>(y.status==='ready-to-turn-in')-(x.status==='ready-to-turn-in')||Number(x.optional)-Number(y.optional));if(!quests.length)continue;
    const heading=document.createElement('h3');heading.className='journal-group-title';heading.textContent=title;journal.append(heading);
    quests.forEach(q=>{
    const card=document.createElement('section');card.className='adventure-quest';
    card.dataset.complete=String(q.status==='complete');
    card.dataset.tracked=String(a.tracked.id===q.id && !a.tracked.complete);
    const h=document.createElement('h3');h.textContent=(q.status==='complete'?'✓ ':q.status==='ready-to-turn-in'?'Ready to report · ':q.optional?'Optional · ':'')+q.title;
    const icon=document.createElement('img');icon.src=window.GauntletCampaignScenery?.questIcon(q.id)||window.GauntletAdventureSprites.mapIcon(({opening:'road',hunter:'clearing',bridge:'bridge',shrine:'shrine',region:'ruins'})[q.id],a);icon.alt='';icon.width=icon.height=40;icon.className='adventure-quest-icon';h.prepend(icon);
    const p=document.createElement('p');p.textContent=q.objective;card.append(h,p);
    if(card.dataset.tracked==='true'&&a.tracked.travelPoint){const hint=document.createElement('p');hint.className='subtle';hint.textContent='Known travel point: '+a.tracked.travelPoint.name;card.append(hint);}
    if(state==='active'){
      const button=document.createElement('button');button.type='button';button.className='secondary small';button.dataset.trackObjective=q.id;
      button.textContent=card.dataset.tracked==='true'?'Tracking ★':'Track goal';button.disabled=card.dataset.tracked==='true';card.append(button);
    }
    journal.append(card);
    });
  }
  const discoveries=$('#adventureDiscoveries');discoveries.replaceChildren();
  const discoveryTitle=document.createElement('h3');discoveryTitle.textContent='Woodland discoveries';discoveries.append(discoveryTitle);
  a.discoveries.forEach(d=>{const section=document.createElement('section');section.className='adventure-quest';
    const title=document.createElement('h4'),text=document.createElement('p');title.textContent='✓ '+d.title;text.textContent=d.text;section.append(title,text);discoveries.append(section);});
  const unknown=document.createElement('p');unknown.className='subtle';unknown.textContent=a.undiscoveredCount?a.undiscoveredCount+(a.undiscoveredCount===1?' optional discovery remains.':' optional discoveries remain.')+' Look for side paths and old landmarks.':'All optional discoveries found.';discoveries.append(unknown);
  const rewards=$('#adventureRewards');rewards.replaceChildren();
  a.rewards.slice().reverse().forEach(r=>{const section=document.createElement('section');section.className='adventure-receipt';
    const title=document.createElement('strong');title.textContent=r.title+' · +'+r.runes+' shared Runes';section.append(title);
    r.recipients.forEach(p=>{const line=document.createElement('p');line.textContent=p.name+': '+p.item+(p.convertedRunes?' converted to '+p.convertedRunes+' shared Runes (pouch full).':' added to pouch.');section.append(line);});rewards.append(section);});
  renderWoodlandAtlas(a);
  renderDungeonPanels(a);
  {
    let site=document.querySelector('#campaignSitePlan');const chart=window.GauntletCampaignScenery?.sitePlan(room);
    if(chart){if(!site){site=document.createElement('details');site.id='campaignSitePlan';site.className='adventure-quest';$('#adventureMapViewport').closest('.atlas-layout').after(site);}const heading=document.createElement('summary');heading.textContent='Current site · '+a.name;site.replaceChildren(heading,chart);site.hidden=false;}
    else if(site)site.hidden=true;
  }
  adventurePanelSignature=signature;
}
function drawAdventure(ctx,room,depthEntries=null) {
  const a=room.adventure;if(!a)return;
  const art=window.GauntletAdventureSprites;
  ctx.save();ctx.imageSmoothingEnabled=false;
  window.GauntletOpening?.backdrop(ctx,room);
  // During the puzzle, its own rune geometry occupies the landmark layer.
  if(room.phase!=='puzzle') {
    art?.scenery(ctx,room);
    a.features.forEach(f=>{
      const drawFeature=()=>{
      const near=a.nearby?.id===f.id || a.signpost?.id===f.id;
      if(f.kind==='portal')return; // Drawn once by the village scenery layer.
      if(f.kind==='hunter'||f.kind==='talk'||f.kind==='witness')drawCharacterShadow(ctx,f.x,f.y+14,f.id==='hunter'?21:16);
      if(!art?.feature(ctx,f,a,near)) {
        // Keep landmarks recognizable while an optional Adventure art pack loads.
        if(f.kind==='hunter'||f.kind==='talk')window.GauntletTownSprites?.character(ctx,f.kind==='talk'?'Villager02':'Villager04',f.x,f.y,{direction:'south',mode:near?'gesture':'idle',scale:1.05});
        else if(f.kind==='chest')drawTreasureChest(ctx,{x:f.x,y:f.y,opened:false});
        else if(f.kind==='shrine') {
          ctx.fillStyle=a.shrineRestored?'#79c992':'#676a5f';ctx.fillRect(f.x-43,f.y-8,86,22);ctx.fillRect(f.x-32,f.y-35,64,28);
          ctx.fillStyle=a.shrineRestored?'#c9ffc4':'#bf967a';ctx.beginPath();ctx.arc(f.x,f.y-22,12,0,Math.PI*2);ctx.fill();
        } else {
          ctx.fillStyle='#856845';ctx.fillRect(f.x-6,f.y-28,12,37);ctx.fillStyle='#c7b389';ctx.fillRect(f.x-28,f.y-34,56,19);
        }
      }
      };
      const drawFeatureLabel=()=>{const near=a.nearby?.id===f.id;
      if(near||f.kind==='hunter'||f.kind==='talk'||f.kind==='travel_shrine'){ctx.fillStyle=near?'#ffe395':'#e2d3b3';ctx.font='bold 11px monospace';ctx.textAlign='center';
        ctx.fillText((near && f.kind!=='signpost'?'E · ':'')+f.name,f.x,f.y+40);}
      };
      if(depthEntries)depthEntries.push({key:a.area+':'+f.id,visibleBounds:()=>art?.featureBounds(f,a),actor:['hunter','talk','witness'].includes(f.kind),depth:f.y+14,occluder:true,bounds:{x:f.x-32,y:f.y-66,width:64,height:100},draw:drawFeature,after:drawFeatureLabel});else{drawFeature();drawFeatureLabel();}
    });
  }
  if(a.area==='home'&&a.complete){ctx.fillStyle='#f0cd70';ctx.font='bold 14px monospace';ctx.textAlign='center';ctx.fillText('OAKVALE CELEBRATES · WOODLAND SECURED',480,48);}
  a.exits.forEach(e=>{
    const drawExit=()=>{
    ctx.save();
    const near=a.nearby?.id===e.id;
    if(!art?.trail(ctx,e,near||a.travel===e.id,room)){ctx.fillStyle=e.locked?'#bf8778':'#c8dcc0';ctx.font='bold 21px monospace';ctx.textAlign='center';ctx.fillText(({north:'↑',south:'↓',west:'←',east:'→'})[e.edge],e.x,e.y+6);}
    if(window.GauntletReleaseVisuals?.exitLabel(ctx,e,near,room)){ctx.restore();return;}
    const tx=Math.max(118,Math.min((room.areaSize?.[0] || 960)-118,e.x)),ty=e.edge==='south'?e.y-26:e.edge==='north'?e.y+31:e.y-31;
    if(near){ctx.fillStyle='#17291fed';ctx.fillRect(tx-128,ty-16,256,27);}
    ctx.fillStyle=e.locked?'#e4a496':e.tracked?'#ffe395':'#eadcb4';ctx.font=near?'bold 13px monospace':'11px monospace';ctx.textAlign='center';
    ctx.shadowColor='#12241f';ctx.shadowBlur=3;
    if(near||e.name!=='Unexplored trail')ctx.fillText((e.locked?'CLOSED · ':near?'E · ':'')+(e.dungeonEntrance?.name||e.name)+(e.dungeonComplete?' ✓':'')+(e.tracked?' ★':''),tx,ty);
    ctx.shadowBlur=0;
    ctx.restore();
    };
    if(depthEntries&&a.area==='home')depthEntries.push({depth:Infinity,draw:drawExit});else drawExit();
  });
  ctx.restore();
}
