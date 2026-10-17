const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const app = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');
const requests = [];
class Image {
  constructor() { this.complete = false; this.naturalWidth = 0; }
  set src(value) {
    assert.ok(fs.existsSync(path.join(__dirname, '../static', value)), value);
    requests.push(value); this.url = value;
  }
}
const context = vm.createContext({Image, document: {createElement: () => ({})}});
vm.runInContext(app.slice(app.indexOf('const villageArt = {}'), app.indexOf('function drawVillageProp')), context);
assert.equal(requests.length, 0, 'Village art must not download on the main menu');
for (const region of ['woodland', 'ruins', 'cavern', 'frost']) {
  for (const kind of ['ground', 'buildings', 'props', 'beds', 'interiors', 'upstairs']) {
    context.room = {region}; context.kind = kind;
    assert.equal(vm.runInContext('villageImage(room, kind)', context), null);
    const count = requests.length;
    assert.equal(vm.runInContext('villageImage(room, kind)', context), null);
    assert.equal(requests.length, count, 'Pending requests must be reused');
    vm.runInContext('villageTerrainKey="cached"; villageArt[room.region][kind].complete=true; villageArt[room.region][kind].naturalWidth=64; villageArt[room.region][kind].onload()', context);
    assert.ok(vm.runInContext('villageImage(room, kind)', context));
    assert.equal(vm.runInContext('villageTerrainKey', context), '', 'Arrival must invalidate the cached terrain');
    assert.equal(requests.length, count, 'Loaded requests must be reused');
  }
}
assert.equal(vm.runInContext('villageImage({region:"unknown"}, "interiors") === villageArt.woodland.interiors', context), true);
assert.equal(requests.length, 24);
console.log('Village sprites: no eager downloads, all regions and interiors load once, cache invalidation and fallback pass.');
