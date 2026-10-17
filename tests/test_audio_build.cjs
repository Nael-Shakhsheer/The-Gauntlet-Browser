const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),cp=require('node:child_process'),crypto=require('node:crypto');
const source=path.resolve(__dirname,'../art/audio'),root=fs.mkdtempSync(path.join(path.resolve(__dirname,'..'),'audio-build-qa-')),art=path.join(root,'art/audio'),output=path.join(root,'static/audio');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
try{
 fs.mkdirSync(art,{recursive:true});fs.mkdirSync(output,{recursive:true});fs.cpSync(path.join(source,'vendor'),path.join(art,'vendor'),{recursive:true});fs.copyFileSync(path.join(source,'build-sounds.cjs'),path.join(art,'build-sounds.cjs'));
 const original=JSON.parse(fs.readFileSync(path.join(source,'sounds.json')));const bank={...original,sounds:{'knight-light':original.sounds['knight-light']}};
 fs.writeFileSync(path.join(art,'sounds.json'),JSON.stringify(bank));const build=(args=[])=>cp.spawnSync(process.execPath,[path.join(art,'build-sounds.cjs'),...args],{encoding:'utf8'});
 assert.equal(build().status,0);const file=path.join(output,'knight-light.wav'),first=fs.readFileSync(file);assert.equal(build().status,0);assert.equal(sha(fs.readFileSync(file)),sha(first),'identical rebuild');
 const changed=Buffer.from(first);changed.writeInt16LE(1000,100);fs.writeFileSync(file,changed);assert.notEqual(build().status,0);assert.equal(sha(fs.readFileSync(file)),sha(changed),'modified export stays intact');
 assert.equal(build(['--replace-modified']).status,0);assert.equal(fs.readdirSync(path.join(art,'manual-backups')).length,1);
 fs.writeFileSync(path.join(art,'manual.wav'),first);fs.writeFileSync(path.join(art,'manual.json'),'{}');bank.sounds['knight-light'].manual={source:'manual.wav',editorData:'manual.json'};fs.writeFileSync(path.join(art,'sounds.json'),JSON.stringify(bank));assert.equal(build().status,0);assert.equal(sha(fs.readFileSync(file)),sha(first),'manual source preserved');
 const pins=JSON.parse(fs.readFileSync(path.join(source,'vendor-hashes.json')));for(const [name,digest] of Object.entries(pins))assert.equal(sha(fs.readFileSync(path.join(source,'vendor',name))).toUpperCase(),digest);
 console.log('Bfxr: byte-identical rebuild, modified-export refusal, backup replacement, retained manual source/editor data and unchanged vendor/licenses passed.');
}finally{fs.rmSync(root,{recursive:true,force:true});}
