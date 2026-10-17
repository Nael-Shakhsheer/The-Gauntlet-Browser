const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
let observer;
const sandbox={window:{},ResizeObserver:class{constructor(fn){observer=fn;}observe(){}disconnect(){this.disconnected=true;}}};
const source=fs.readFileSync('static/adventure.js','utf8');
vm.runInNewContext(source.slice(0,source.indexOf('/* Adventure uses')),sandbox);
function fixture(state={},viewBox='0 0 600 240'){
  const events=new Map(),image={style:{},getAttribute:key=>key==='viewBox'?viewBox:null},controls={in:{},out:{},fit:{},value:{}};
  const viewport={offsetWidth:480,offsetHeight:220,clientWidth:456,clientHeight:196,clientLeft:2,clientTop:2,scrollLeft:0,scrollTop:0,
    addEventListener(k,fn,options){events.set(k,{fn,options});},removeEventListener(k){events.delete(k);},getBoundingClientRect:()=>({left:10,top:20})};
  const controller=sandbox.window.GauntletMapNavigation.attach(viewport,image,state,controls);controller.resize();
  function wheel(deltaY,extra={}){let prevented=false;events.get('wheel').fn({deltaY,deltaX:0,deltaMode:0,clientX:120,clientY:90,preventDefault(){prevented=true;},...extra});return prevented;}
  return {viewport,image,controls,controller,state,wheel,events};
}
const f=fixture();assert.equal(f.image.style.width,'456px');assert.equal(f.controls.out.disabled,true);
assert.equal(f.events.get('wheel').options.passive,false,'Wheel zoom can suppress document scrolling');
assert.ok(f.wheel(-120));const z=f.state.zoom;
assert.ok(z>1);assert.ok(Math.abs(f.viewport.scrollLeft-(108*z-108))<.001,'Wheel keeps the pointed map location fixed');
assert.ok(Math.abs(f.viewport.scrollTop-(68*z-68))<.001);
assert.equal(f.wheel(-120,{shiftKey:true}),false,'Shift-wheel remains native horizontal pan');
assert.equal(f.wheel(-10,{deltaX:100}),false,'Horizontal trackpad gestures pan instead of zooming');
const before=[f.state.fit,f.viewport.scrollLeft,f.viewport.scrollTop];
for(let i=0;i<50;i++){f.viewport.clientWidth=i%2?442:456;observer();}
assert.deepEqual([f.state.fit,f.viewport.scrollLeft,f.viewport.scrollTop],before,'Scrollbar changes cannot shake the interior map');
f.controls.in.onclick();assert.ok(f.state.zoom>z);
const saved={...f.state},fresh=fixture(saved);assert.equal(fresh.state.zoom,f.state.zoom);assert.equal(fresh.viewport.scrollLeft,f.viewport.scrollLeft,'Rebuilt state panels retain pan and zoom');
fresh.controls.fit.onclick();assert.equal(fresh.state.zoom,1);assert.equal(fresh.viewport.scrollLeft,0);assert.equal(fresh.viewport.scrollTop,0);
assert.equal(fresh.wheel(120),false,'At Fit, wheel scroll can reach the next dungeon card');
assert.ok(fresh.wheel(-1,{deltaMode:1}));assert.ok(fresh.state.zoom>1,'Line-mode mouse wheels also zoom');
fresh.controller.zoom(100);assert.equal(fresh.state.zoom,3);assert.equal(fresh.controls.in.disabled,true);
fresh.controller.dispose();assert.equal(fresh.events.size,0,'Rebuilt panels dispose their old handlers');
const tall=fixture({},'0 0 400 600');assert.equal(tall.image.style.width,'130px');assert.equal(tall.image.style.height,'195px','Fit handles a tall tower map without cropping its viewBox');
console.log('Dungeon wheel zoom, pointer anchor, Fit, touch buttons, native pan, stable sizing, retained state and handler cleanup: OK');
