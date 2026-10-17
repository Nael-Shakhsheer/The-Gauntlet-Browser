const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('static/app.js','utf8');
const classes=new Set(['is-playing']),notice={classList:{toggle(_k,value){this.hidden=value;}}},main={inert:false};
let sent=0,stops=0,clears=0;
const s={window:{innerWidth:390,innerHeight:844,matchMedia:()=>({matches:true}),GauntletCamera:{landscapeRequired:(p,t,w,h)=>Boolean(p&&t&&h>w)}},
  navigator:{maxTouchPoints:1},document:{documentElement:{dataset:{}},body:{classList:{contains:k=>classes.has(k),toggle(k,v){if(v)classes.add(k);else classes.delete(k);}}}},
  $:selector=>selector==='main'?main:notice,coarseScreen:{matches:false},landscapeBlocked:false,
  keys:new Set(['d','attack']),moveState:{x:1,y:0,attack:true},areaCamera:{clear(){clears++;}},
  endHeldAttack(){s.moveState.attack=false;},sendAction(a){if(a==='stopRevive')stops++;return Promise.resolve();},sendMovement(){sent++;}};
vm.createContext(s);vm.runInContext(source.slice(source.indexOf('function updateLandscape()'),source.indexOf("window.addEventListener('resize',updateLandscape)")),s);
s.updateLandscape();assert.equal(s.landscapeBlocked,true);assert.equal(main.inert,true);assert.equal(notice.classList.hidden,false);
assert.equal(s.keys.size,0);assert.equal(s.moveState.x,0);assert.equal(s.moveState.attack,false);assert.equal(stops,1);assert.equal(sent,1);assert.equal(clears,1);
s.updateLandscape();assert.equal(sent,1,'State polling does not spam stop requests');
s.window.innerWidth=844;s.window.innerHeight=390;s.updateLandscape();assert.equal(s.landscapeBlocked,false);assert.equal(main.inert,false);
assert.equal(s.keys.size,0,'Rotating back must not resume previously held inputs');
classes.delete('is-playing');s.window.innerWidth=390;s.window.innerHeight=844;s.updateLandscape();assert.equal(s.landscapeBlocked,false);
classes.add('is-playing');s.window.matchMedia=()=>({matches:false});s.updateLandscape();assert.equal(s.landscapeBlocked,false,'A touch-capable desktop with a mouse is not treated as a phone');
console.log('Portrait rotation gate releases movement, attack and revive, blocks gameplay UI and restores landscape without stuck inputs: OK');
