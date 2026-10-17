const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
let callback=null;const elements=[];
function node(){const n={children:[],dataset:{},classList:{add(){},remove(){}},setAttribute(){},append(...x){this.children.push(...x)},replaceChildren(){this.children=[]}};elements.push(n);return n;}
const scope={window:{addEventListener(){}},document:{createElement:node,body:node(),addEventListener(){}},performance:{now:()=>0},setTimeout:f=>{callback=f;return 1;},clearTimeout:()=>{callback=null;}};
vm.createContext(scope);vm.runInContext(fs.readFileSync('static/feedback.js','utf8'),scope);
const a=scope.window.GauntletAcquisitions,r={code:'QA',you:'me',feedback:{epoch:'1'}};
a.observe(r,[{kind:'acquisition',ownerId:'me',name:'Healing Draught',rarity:'common',quantity:1,destination:'pouch'}]);
assert.equal(a.diagnostics().showing,true);assert.equal(a.diagnostics().queued,0);
const notice=elements.find(n=>n.id==='acquisitionNotice');assert.match(notice.children.at(-1).children[1].textContent,/common · pouch/);
a.observe(r,Array.from({length:100},(_,i)=>({kind:'acquisition',ownerId:'me',name:'Reward '+i,quantity:1,destination:'pending reward · choose in Journal'})));
assert.equal(a.diagnostics().queued,24,'burst queue is bounded');
a.reset();a.observe(r,[{kind:'magic_acquired',ownerId:'me',quantity:2,balance:4}]);assert.match(notice.children.at(-1).children[0].textContent,/Magic Rune acquired ×2/);assert.match(notice.children.at(-1).children[1].textContent,/Personal balance: 4/);
a.observe({...r,feedback:{epoch:'2'}},[]);assert.equal(a.diagnostics().showing,false,'new scene cannot replay stale rewards');
const nav=fs.readFileSync('static/adventure.js','utf8'),chapter=fs.readFileSync('static/chapter.js','utf8');
assert.match(nav,/GauntletMapNavigation.attach\(viewport,svg/);assert.match(nav,/Confirm.*travel/);assert.match(nav,/role:'button',tabindex:0/);
assert.match(chapter,/Active \/ Ready/);assert.match(chapter,/Completed/);assert.match(chapter,/dialog.scrollTop=scroll/);
console.log('Adventure interface: bounded confirmed-acquisition queue, personal rune balance, scene cleanup, map navigation and runner tabs passed.');
