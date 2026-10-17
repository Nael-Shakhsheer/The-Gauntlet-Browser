/* Rebuild the shipped Bfxr bank with Node's standard library only. */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '../..');
const manifest = JSON.parse(fs.readFileSync(path.join(__dirname, 'sounds.json')));
const output = path.join(root, 'static/audio');
fs.mkdirSync(output, { recursive: true });
const sandbox = vm.createContext({ console });
vm.runInContext(`const SAMPLE_RATE=44100, CONVERSION_FACTOR=2*Math.PI/44100;
const TEMPLATES_JSON={}; const AUDIO_CONTEXT={createBuffer(c,n,r){
  const data=new Float32Array(n); return {getChannelData(){return data;},copyToChannel(src){data.set(src);}};
}}; function ULBS(){};`, sandbox);
for (const file of ['globals.js','Bfxr_DSP.js','RealizedSound.js','SynthBase.js','Bfxr.js']) {
  vm.runInContext(fs.readFileSync(path.join(__dirname, 'vendor', file), 'utf8'), sandbox, { filename: file });
}
const metrics = {};
const hash=buffer=>crypto.createHash('sha256').update(buffer).digest('hex');
const indexPath=path.join(__dirname,'exports.json');
const hashes=fs.existsSync(indexPath)?JSON.parse(fs.readFileSync(indexPath)):{};
const pending=[], replacement=process.argv.includes('--replace-modified');
// Preflight the entire bank before writing: protect manual edits and exports.
for(const [name,recipe] of Object.entries(manifest.sounds)) {
  const target=path.join(output,name+'.wav');
  if(fs.existsSync(target) && (!hashes[name+'.wav'] || hash(fs.readFileSync(target))!==hashes[name+'.wav'])) {
    if(!replacement) throw Error(name+': modified/unregistered WAV protected. Declare manual source/editorData, or use --replace-modified (backs it up).');
    const backup=path.join(__dirname,'manual-backups',Date.now()+'-'+name+'.wav');
    fs.mkdirSync(path.dirname(backup),{recursive:true});fs.copyFileSync(target,backup);
  }
}
for (const [name, recipe] of Object.entries(manifest.sounds)) {
  if(!/^[a-z0-9-]+$/.test(name))throw Error('Invalid filename');
  if(recipe.manual) {
    const source=path.resolve(__dirname,recipe.manual.source),editor=path.resolve(__dirname,recipe.manual.editorData);
    if(!source.startsWith(__dirname+path.sep)||!editor.startsWith(__dirname+path.sep)||!fs.existsSync(editor))throw Error(name+': retain local manual WAV and editor data');
    const wav=fs.readFileSync(source);
    if(wav.toString('ascii',0,4)!=='RIFF'||wav.toString('ascii',36,40)!=='data'||wav.readUInt16LE(22)!==1||wav.readUInt16LE(34)!==16||wav.readUInt32LE(24)!==44100)throw Error(name+': expected canonical mono 44.1kHz PCM16 WAV');
    pending.push([name,wav]);continue;
  }
  sandbox.recipe = recipe;
  const samples = vm.runInContext(`(() => {
    let seed=recipe.seed;
    Math.random=()=>{seed|=0; seed=seed+0x6D2B79F5|0;
      let t=Math.imul(seed^seed>>>15,1|seed); t=t+Math.imul(t^t>>>7,61|t)^t;
      return ((t^t>>>14)>>>0)/4294967296;};
    const synth=new Bfxr(); synth.apply_params(recipe.params); synth.generate_sound();
    return synth.sound.getBuffer();
  })()`, sandbox);
  // Bound level, trim long silence, and ramp edges to avoid playback clicks.
  let end = samples.length;
  while (end > 441 && Math.abs(samples[end - 1]) < .0001) end--;
  let peak = 0;
  for (let i=0;i<end;i++) {
    if (!Number.isFinite(samples[i])) throw Error(name + ': invalid sample');
    peak = Math.max(peak, Math.abs(samples[i]));
  }
  if (!peak || end > 44100 * 2) throw Error(name + ': invalid length or silent sound');
  const gain = (recipe.peak ?? .48) / peak;
  const wav = Buffer.alloc(44 + end * 2);
  wav.write('RIFF'); wav.writeUInt32LE(wav.length-8,4); wav.write('WAVEfmt ',8);
  wav.writeUInt32LE(16,16); wav.writeUInt16LE(1,20); wav.writeUInt16LE(1,22);
  wav.writeUInt32LE(44100,24); wav.writeUInt32LE(88200,28);
  wav.writeUInt16LE(2,32); wav.writeUInt16LE(16,34); wav.write('data',36);
  wav.writeUInt32LE(end*2,40);
  let sum=0, exportedPeak=0;
  for(let i=0;i<end;i++) {
    const value=samples[i]*gain*Math.min(1,i/88,(end-1-i)/176);
    sum+=value*value; wav.writeInt16LE(Math.round(value*32767),44+i*2);
    exportedPeak=Math.max(exportedPeak,Math.abs(value));
  }
  pending.push([name,wav]);
}
for(const [name,wav] of pending) {
  let peak=0,sum=0,clipped=0,maxStep=0,previous=0,leading=0,trailing=0;
  for(let i=44;i<wav.length;i+=2){const v=wav.readInt16LE(i)/32768;peak=Math.max(peak,Math.abs(v));sum+=v*v;if(Math.abs(v)>=.999)clipped++;
    maxStep=Math.max(maxStep,Math.abs(v-previous));previous=v;}
  while(44+leading*2<wav.length&&wav.readInt16LE(44+leading*2)===0)leading++;
  while(wav.length-2-trailing*2>=44&&wav.readInt16LE(wav.length-2-trailing*2)===0)trailing++;
  const count=(wav.length-44)/2,rms=Math.sqrt(sum/count);
  if(!peak||clipped||count>88200||Math.abs(wav.readInt16LE(44))>100||Math.abs(wav.readInt16LE(wav.length-2))>100)throw Error(name+': export QA failed (silence/length/clipping/edges)');
  metrics[name]={seconds:+(count/44100).toFixed(4),peak:+peak.toFixed(5),rms:+rms.toFixed(5),rmsDBFS:+(20*Math.log10(rms)).toFixed(2),bytes:wav.length,clippedSamples:clipped,edgeSamples:[wav.readInt16LE(44),wav.readInt16LE(wav.length-2)],leadingSilenceMs:+(leading/44.1).toFixed(3),trailingSilenceMs:+(trailing/44.1).toFixed(3),maximumSampleStep:+maxStep.toFixed(5),sha256:hash(wav),manual:Boolean(manifest.sounds[name].manual)};
}
for(const [name,wav] of pending){fs.writeFileSync(path.join(output,name+'.wav'),wav);hashes[name+'.wav']=hash(wav);}
fs.writeFileSync(indexPath,JSON.stringify(hashes,null,2)+'\n');
fs.writeFileSync(path.join(__dirname,'metrics.json'), JSON.stringify(metrics,null,2)+'\n');
console.log('Built '+Object.keys(metrics).length+' Bfxr sounds.');
