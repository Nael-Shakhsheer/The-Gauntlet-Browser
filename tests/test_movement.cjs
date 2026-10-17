const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const sandbox={window:{}};vm.createContext(sandbox);
vm.runInContext(fs.readFileSync('static/movement.js','utf8'),sandbox);
const {create,move,walkable}=sandbox.window.GauntletMovement;
const room={code:'A',stage:1,phase:'combat',you:'p',players:[{id:'p',status:'alive'}],movement:{x:100,y:200,speed:145,age:0,slideVx:0,slideVy:0}};
const motion=create();motion.remember({x:0,y:0},1000);motion.update(room,1000);
motion.remember({x:1,y:0},1000);
assert.ok(motion.position(room,1016).x>102,'Respond on the next frame before any server snapshot arrives');
motion.remember({x:0,y:0},1016);
assert.equal(motion.position(room,1048).x,motion.position(room,1016).x,'Key release stops local movement immediately');
motion.remember({x:1,y:1},1048);
const a=motion.position(room,1048),b=motion.position(room,1098);
assert.ok(Math.abs(Math.hypot(b.x-a.x,b.y-a.y)-145*.05)<.001,'Diagonal speed is normalized');
assert.ok(motion.position(room,1180).x>motion.position(room,1150).x,'Ordinary polling gaps keep walking responsive');
assert.deepEqual(motion.position(room,2000),motion.position(room,1200),'Lost connection stops prediction within 200ms at local latency');
room.movement={...room.movement,x:800,y:300};motion.update(room,1710);
assert.ok(motion.position(room,1710).x>=800,'Dash or teleport snaps large corrections');
room.players[0].status='downed';motion.update(room,1720);
assert.equal(motion.position(room,1740).x,800,'Downed heroes cannot predict movement');
const p={x:100,y:200,slideVx:0,slideVy:0};
room.environment={obstacles:[{hp:24,x:200,y:200,radius:24}],zones:[]};
move(room,p,1,0,300,.5);assert.ok(p.x<=164 && p.x>=156,'Swept movement stops before the cover collision boundary');
const blocked=p.x;room.environment.obstacles[0].hp=0;move(room,p,1,0,300,.5);assert.ok(Math.abs(p.x-blocked-150)<.001,'Destroyed cover opens the path');
room.environment.zones=[{kind:'ice',x:p.x,y:200,radius:90}];
move(room,p,1,0,145,.05);const ice=p.x;move(room,p,0,0,145,.05);assert.ok(p.x>ice,'Ice retains intentional momentum');
const town={phase:'town',townHouses:[{x:480,y:250}]};
assert.equal(walkable(town,480,240),false);assert.equal(walkable(town,550,240),true);
town.townInterior='inn';town.innFloor=2;town.innRooms=[{x:320,locked:false},{x:640,locked:true}];
assert.equal(walkable(town,320,200),true);assert.equal(walkable(town,640,200),false);assert.equal(walkable(town,480,380),true);
assert.equal(walkable({phase:'routes'},480,440),true);assert.equal(walkable({phase:'routes'},400,440),false);
console.log('Immediate movement, release, normalized diagonals, stale prediction, teleports, downing, cover, ice, town and fork collisions: OK');
const large={phase:'combat',areaSize:[1800,900]},walker={x:1200,y:650,slideVx:0,slideVy:0};
move(large,walker,1,0,140,.1);assert.ok(walker.x>1200 && walker.y>540,'Large-field prediction agrees with server bounds');
move(large,walker,1,1,1000,2);assert.equal(walker.x,1772);assert.equal(walker.y,870);
console.log('Large Adventure movement prediction and outer bounds: OK');
const rooted=create(),rootRoom={...room,environment:{},players:[{id:'p',status:'alive'}],movement:{...room.movement,x:300,y:200,rooted:true}};
rooted.remember({x:1,y:0},2000);rooted.update(rootRoom,2000);assert.equal(rooted.position(rootRoom,2100).x,300,'Rooted movement stays server-authoritative without rubber-banding');
const sNotice=sandbox.window.GauntletMovement.createSaveNotice();const info={worldId:'one',revision:1};
sNotice.update(info,0);assert.equal(sNotice.visible(2000),true);sNotice.update(info,2000);assert.equal(sNotice.visible(2600),false,'Polling cannot extend a saved notification forever');
sNotice.update({...info,error:'Disk full'},3000);assert.equal(sNotice.visible(20000),true,'Failures remain discoverable');sNotice.update({...info,revision:2},21000);assert.equal(sNotice.visible(24000),false);

// A normal-speed walk under jitter and alternating tick ages. The old 70ms
// exponential correction could turn a ~12px polling error into a backwards frame.
const walking=create(),walkRoom={code:'jitter',stage:1,phase:'combat',you:'p',players:[{id:'p',status:'alive'}],movement:{x:150,y:200,speed:145,age:0,slideVx:0,slideVy:0}};
walking.remember({x:1,y:0},0);walking.update(walkRoom,0);
let previousX=walking.position(walkRoom,0).x,sampleAt=64,minStep=Infinity,maxStep=0;
for(let t=16;t<=2400;t+=16){
  if(t>=sampleAt){
    const delay=[24,80,48,120,32][Math.floor(t/64)%5];
    const age=[0,.04,.02][Math.floor(t/64)%3];
    walkRoom.movement={...walkRoom.movement,x:150+145*Math.max(0,t-delay/2-age*1000)/1000,age};
    walking.update(walkRoom,t,delay);sampleAt=t+48+(Math.floor(t/64)%3)*16;
  }
  const x=walking.position(walkRoom,t).x,step=x-previousX;
  minStep=Math.min(minStep,step);maxStep=Math.max(maxStep,step);previousX=x;
}
assert.ok(minStep>=145*.016*.91,'Ordinary walking stays within 9% of nominal speed: '+minStep);
assert.ok(maxStep<=145*.016*1.09,'Corrections cannot cause a burst of walking speed: '+maxStep);
assert.ok(Math.abs(previousX-(150+145*2.4))<18,'Continuous walk remains close to the authoritative position');
walking.remember({x:0,y:0},2400);const stopped=walking.position(walkRoom,2400).x;
assert.ok(Math.abs(walking.position(walkRoom,2416).x-stopped)<=145*.25*.016+.001,'Release never carries on walking while reconciliation settles');
console.log('Normal-speed jittered snapshots: forward frames, bounded correction speed, continuous distance and responsive release: OK');
