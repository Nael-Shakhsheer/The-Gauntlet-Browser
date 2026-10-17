const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const sandbox={window:{},AbortController};vm.runInNewContext(fs.readFileSync('static/input-transport.js','utf8'),sandbox);
let clock=0;const calls=[],metrics=[];
const transport=sandbox.window.GauntletInput.create({now:()=>clock,metric:(...v)=>metrics.push(v),request:(data,signal)=>new Promise((resolve,reject)=>{calls.push({data,signal,resolve,reject});signal.addEventListener('abort',()=>reject(Error('Aborted')));})});
(async()=>{
 const a={room:'A',player:'a',recovery:'private-a'},b={room:'B',player:'b',recovery:'private-b'};
 transport.session(a);transport.send({x:1,y:0,attack:false},'A:road');assert.equal(calls.length,1);
 clock=20;transport.send({x:0,y:0,attack:false},'A:road');assert.equal(calls.length,2,'A release immediately overtakes a stalled move, without waiting for any timeout');
 assert.ok(calls[0].signal.aborted);assert.equal(calls[1].data.x,0);assert.ok(calls[1].data.sequence>calls[0].data.sequence);
 clock=28;calls[1].resolve({ok:true});await new Promise(setImmediate);assert.equal(metrics.find(v=>v[0]==='releaseAckMs')[1],8);
 clock=30;transport.send({x:-1,y:1},'A:road');transport.session(b);transport.send({x:0,y:1},'B:home');
 assert.ok(calls[2].signal.aborted);assert.equal(calls[3].data.room,'B');assert.equal(calls[3].data.recovery,'private-b');
 calls[2].resolve({ok:true});await new Promise(setImmediate);transport.send({x:0,y:1},'B:home');assert.equal(calls.length,4,'Old response cannot release the new session queue');
 transport.cancel();assert.ok(calls[3].signal.aborted);transport.session(null);transport.send({x:1,y:0},'old');assert.equal(calls.length,4);
 console.log('Lost response release: immediate dispatch, ordered sequences, 8ms controlled acknowledgement; stale session/scene work is cancelled: OK');
})().catch(e=>{console.error(e);process.exitCode=1;});
