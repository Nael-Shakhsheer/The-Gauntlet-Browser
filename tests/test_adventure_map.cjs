const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');

// Model the browser's layout at the narrow-landscape scrollbar threshold.
// The real map code and ResizeObserver callback run against these DOM boxes.
const properties=new Map(),writes=[];
const style={getPropertyValue:key=>properties.get(key)||'',setProperty(key,value){properties.set(key,value);writes.push(key);}};
const viewport={offsetWidth:428,offsetHeight:165,scrollLeft:0,scrollTop:0};
function layout(){
  const width=viewport.offsetWidth-6,height=viewport.offsetHeight-6;
  const mapWidth=parseFloat(properties.get('--atlas-fit')||width)*Number(properties.get('--atlas-zoom')||1);
  const mapHeight=mapWidth*700/960;
  let horizontal=false,vertical=false;
  for(let i=0;i<4;i++){
    horizontal=mapWidth>width-(vertical?14:0);
    vertical=mapHeight>height-(horizontal?14:0);
  }
  return {width:width-(vertical?14:0),height:height-(horizontal?14:0),mapWidth,mapHeight};
}
Object.defineProperties(viewport,{
  clientWidth:{get:()=>layout().width},clientHeight:{get:()=>layout().height},
});
const elements=new Map([['#adventureMapViewport',viewport],['#adventureMap',{style}]]);
function $(id){
  if(!elements.has(id))elements.set(id,{});
  const element=elements.get(id);element.addEventListener=()=>{};return element;
}
let observer;
const sandbox={$,ResizeObserver:class{constructor(callback){observer=callback;}observe(){}},window:{}};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync('static/adventure.js','utf8'),sandbox);
const run=code=>vm.runInContext(code,sandbox);

run('sizeAtlas();setAtlasZoom(2)');
const fit=properties.get('--atlas-fit'),initialWrites=writes.length;
const shapes=new Set();
for(let i=0;i<64;i++){
  observer();shapes.add(JSON.stringify(layout()));
}
assert.equal(shapes.size,1,'Scrollbar changes must not make the map alternate between sizes');
assert.equal(properties.get('--atlas-fit'),fit);
assert.equal(writes.length,initialWrites,'Settled ResizeObserver callbacks do not rewrite layout');

viewport.scrollTop=40;
const before=layout(),centerY=viewport.scrollTop+before.height/2;
run('setAtlasZoom(2.5)');
assert.equal(viewport.scrollTop+layout().height/2,centerY*1.25,'Zoom keeps the viewed point centered when a scrollbar appears');
const pan=[viewport.scrollLeft,viewport.scrollTop],zoomWrites=writes.length;
run('setAtlasZoom(2.5)');
assert.deepEqual([viewport.scrollLeft,viewport.scrollTop],pan,'Unchanged zoom retains the current pan');
assert.equal(writes.length,zoomWrites,'An ordinary state refresh does not write the zoom again');
assert.equal($('[data-map-zoom=in]').disabled,true);
run('setAtlasZoom(1)');
assert.equal($('[data-map-zoom=out]').disabled,true);
assert.ok(layout().mapWidth<=layout().width && layout().mapHeight<=layout().height,'Fit shows the entire map');

viewport.offsetWidth=0;viewport.offsetHeight=0;observer();
assert.equal(properties.get('--atlas-fit'),fit,'Closing the dialog does not erase the fit size');
viewport.offsetWidth=780;viewport.offsetHeight=464;observer();
assert.notEqual(properties.get('--atlas-fit'),fit,'A real window resize still refits the map');
assert.ok(layout().mapWidth<=layout().width && layout().mapHeight<=layout().height);
console.log('Adventure map: stable scrollbar threshold, unchanged observer/zoom, centered zoom, Fit, hidden dialog and real resize: OK');
