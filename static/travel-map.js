// Illustrated travel chart. The public destination list alone owns discovery/locks.
(() => {
 const ns='http://www.w3.org/2000/svg';let serial=0;
 const make=(tag,attrs={})=>{const n=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);return n;};
 function create({nodes,point,selection,onSelect}){
  const svg=make('svg',{class:'shrine-travel-chart',role:'group','aria-label':'Discovered waystones and party location'}),coords=nodes.map(point);
  const left=Math.min(...coords.map(p=>p[0]))-165,top=Math.min(...coords.map(p=>p[1]))-155;
  const width=Math.max(430,Math.max(...coords.map(p=>p[0]))-left+165),height=Math.max(360,Math.max(...coords.map(p=>p[1]))-top+150);
  svg.setAttribute('viewBox',[left,top,width,height].join(' '));
  svg.append(make('rect',{x:left,y:top,width,height,fill:'#d2c39a'}),make('image',{href:'/sprites/shrine-travel-map-v1.png',x:0,y:0,width:1120,height:1340,preserveAspectRatio:'none',style:'image-rendering:pixelated'}));
  for(const region of['aurelian','verdant','cinder']){
   const chart=window.GauntletCampaignScenery?.atlas(region),known=nodes.filter(n=>window.GauntletCampaignScenery?.mapRegion(n.id)===region);if(!chart||!known.length)continue;
   const p=known.map(point),x=Math.min(...p.map(c=>c[0]))-165,y=Math.min(...p.map(c=>c[1]))-155,w=Math.max(330,Math.max(...p.map(c=>c[0]))-x+165),h=Math.max(310,Math.max(...p.map(c=>c[1]))-y+155);
   svg.append(make('image',{href:chart,x,y,width:w,height:h,preserveAspectRatio:'none',style:'image-rendering:pixelated','aria-hidden':'true'}));
  }
  // Geographic decoration carries no undiscovered destinations or route facts.
  const fog='travel-unknown-'+(++serial),defs=make('defs'),mask=make('mask',{id:fog,maskUnits:'userSpaceOnUse',x:left,y:top,width,height});
  const gradient=make('radialGradient',{id:fog+'-edge'});gradient.append(make('stop',{offset:'65%','stop-color':'black'}),make('stop',{offset:'100%','stop-color':'white'}));defs.append(gradient);
  mask.append(make('rect',{x:left,y:top,width,height,fill:'white'}));for(const[x,y]of coords)mask.append(make('ellipse',{cx:x,cy:y,rx:240,ry:215,fill:'url(#'+fog+'-edge)'}));defs.append(mask);svg.append(defs,make('rect',{x:left,y:top,width,height,fill:'#c4bf98',opacity:.5,mask:'url(#'+fog+')',class:'travel-uncharted'}));
  const origin=nodes.find(n=>n.current),originPoint=origin&&point(origin),links=make('g',{'aria-hidden':'true',class:'travel-links'});
  if(originPoint)for(const n of nodes){if(n.current||!n.active)continue;const[x,y]=point(n),[ox,oy]=originPoint,bend=(x-ox)*.18;
   links.append(make('path',{d:`M ${ox} ${oy} C ${ox+bend} ${(oy+y)/2} ${x-bend} ${(oy+y)/2} ${x} ${y}`,'data-travel-link':n.id,fill:'none',stroke:'#4f7160','stroke-width':5,'stroke-dasharray':'8 13',opacity:.6}));
  }svg.append(links);
  for(const n of nodes){const[x,y]=point(n),mapOnly=Boolean(n.mapOnly),g=make('g',{class:'travel-point'+(n.current?' is-current':'')+(n.locked&&!n.current?' is-inactive':''),'data-travel-point':n.id,role:mapOnly?'img':'button',...(mapOnly?{}:{tabindex:0,'aria-pressed':String(n.id===selection)}),'aria-label':n.name+' · '+(n.current?'party location':n.locked||'activated')});
   g.append(make('ellipse',{class:'travel-halo',cx:x,cy:y,rx:64,ry:42,fill:n.current?'#e7cb83aa':'#e7d5aaa0',stroke:n.current?'#674e2b':'#64775a','stroke-width':4}));
   const campaign=window.GauntletCampaignScenery?.mapIcon(n.id,{},Boolean(n.active));
   if(campaign)g.append(make('image',{href:campaign,x:x-67,y:y-106,width:134,height:112,'aria-hidden':'true',style:'image-rendering:pixelated'}));
   else if(['brook','hollow','watch'].includes(n.id)){
    const row={brook:0,hollow:1,watch:2}[n.id],col=n.active?1:0,icon=make('svg',{x:x-80,y:y-138,width:160,height:160,viewBox:[col*160,row*160,160,160].join(' '),overflow:'hidden','aria-hidden':'true'});
    icon.append(make('image',{href:'/sprites/travel-shrines-v2.png',width:320,height:480}));g.append(icon);
   }else if(['home','dunmere'].includes(n.id))g.append(make('image',{href:'/sprites/adventure-map-home-v1.png',x:x-67,y:y-106,width:134,height:112,'aria-hidden':'true'}));
   else g.append(make('path',{d:`M ${x} ${y-42} l 17 22 l -17 22 l -17 -22 Z`,fill:'#e7ce89',stroke:'#4c5535','stroke-width':4}));
   g.append(make('rect',{class:'travel-caption',x:x-135,y:y+28,width:270,height:78,rx:3,fill:'#e4d4ac',stroke:'#7b8058','stroke-width':2}));
   const title=make('text',{x,y:y+57,'text-anchor':'middle',class:'travel-label'});title.textContent=n.name.replace(' travel shrine','').replace(' village','');g.append(title);
   const status=make('text',{x,y:y+88,'text-anchor':'middle',class:'travel-state'});status.textContent=n.current?'PARTY HERE':n.locked?'UNATTUNED':'ATTUNED';g.append(status);
   if(n.locked&&!n.current)g.append(make('path',{d:`M ${x+42} ${y-21} v -12 a 11 11 0 0 1 22 0 v 12 M ${x+38} ${y-21} h 30 v 24 h -30 Z`,fill:'#d7c9a4',stroke:'#4e5a40','stroke-width':4}));
   if(!mapOnly){g.onclick=()=>onSelect(n.id);g.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onSelect(n.id);}};}
   svg.append(g);
  }
  select(svg,selection,nodes);return svg;
 }
 function select(svg,id,nodes=[]){svg.querySelectorAll('[data-travel-point][role=button]').forEach(g=>{const n=nodes.find(n=>n.id===g.dataset.travelPoint);g.setAttribute('aria-pressed',String(g.dataset.travelPoint===id));g.setAttribute('data-selected',String(g.dataset.travelPoint===id));g.setAttribute('data-ui-action','navigation');if(n){g.setAttribute('data-current',String(Boolean(n.current)));g.setAttribute('data-state',n.current?'current':n.locked?'inactive':'available');}});svg.querySelectorAll('[data-travel-link]').forEach(p=>{p.setAttribute('stroke',p.dataset.travelLink===id?'#985c38':'#4f7160');p.setAttribute('stroke-width',p.dataset.travelLink===id?'8':'5');p.setAttribute('opacity',p.dataset.travelLink===id?'1':'.6');});}
 window.GauntletTravelMap={create,select};
})();
