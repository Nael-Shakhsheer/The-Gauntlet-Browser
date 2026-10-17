/* Oct 16 mix authoring. Explicit recipes; retain manual source/editor overrides. */
const fs=require('node:fs'),path=require('node:path');
const file=path.join(__dirname,'sounds.json'),bank=JSON.parse(fs.readFileSync(file));
if(!fs.existsSync(path.join(__dirname,'before-overhaul-metrics.json')))fs.copyFileSync(path.join(__dirname,'metrics.json'),path.join(__dirname,'before-overhaul-metrics.json'));
for(const [name,r] of Object.entries(bank.sounds)){
 if(r.manual)continue;
 if(/-(impact|light(?:-[12])?)$/.test(name)&&!name.startsWith('ice-')){
   const impact=name.endsWith('impact');r.peak=impact?.20:.30;
   r.params={...r.params,lpFilterCutoff:Math.min(r.params.lpFilterCutoff??.55,impact?.36:.48),hpFilterCutoff:Math.max(r.params.hpFilterCutoff??0,.035),attackTime:.008};
   if(impact)r.params.decayTime=.12;
 }
}
let seed=600;
const add=(name,params,peak=.26,notes='Oct 16 authored Bfxr cue')=>{seed++;if(!bank.sounds[name]?.manual)bank.sounds[name]={seed,params,peak,notes};};
const physical={waveType:3,frequency_start:.24,frequency_slide:-.15,lpFilterCutoff:.36,hpFilterCutoff:.045,attackTime:.008,sustainTime:.012,decayTime:.16};
const tone={waveType:2,frequency_start:.3,frequency_slide:.015,lpFilterCutoff:.48,attackTime:.025,sustainTime:.02,decayTime:.24};
const families={arrow:{waveType:4,frequency_start:.34,frequency_slide:-.22,lpFilterCutoff:.44},blade:{...physical,decayTime:.13},
 fire:{...physical,frequency_start:.18,lpFilterCutoff:.28,decayTime:.21},frost:{...tone,frequency_start:.39,frequency_slide:-.12},
 lightning:{...physical,waveType:9,frequency_start:.3,lpFilterCutoff:.4,decayTime:.15},arcane:{...tone,waveType:4,frequency_start:.29,lpFilterCutoff:.4},
 sacred:{...tone,frequency_start:.32,pitch_jump_amount:.1,pitch_jump_onset_percent:.45},nature:{...physical,frequency_start:.2,lpFilterCutoff:.27},
 mixture:{...tone,frequency_start:.25,pitch_jump_amount:-.12,pitch_jump_onset_percent:.3},tonal:{...tone,waveType:4,pitch_jump_amount:.16,pitch_jump_onset_percent:.4},
 shadow:{...physical,frequency_start:.16,lpFilterCutoff:.3},stone:{...physical,frequency_start:.12,decayTime:.18}};
for(const [family,params] of Object.entries(families)){
 add(family+'-launch',{attackTime:.012,sustainTime:.02,decayTime:.18,...params},.28);
 add('enemy-'+family+'-launch',{attackTime:.018,sustainTime:.02,decayTime:.19,...params,frequency_start:(params.frequency_start||.25)*.87},.29,'Recognizable hostile '+family+' release');
 add(family+'-impact',{...params,attackTime:.006,sustainTime:.012,decayTime:family==='fire'?.19:.13},.2);
}
for(const [material,params] of Object.entries({flesh:{...physical,frequency_start:.12,lpFilterCutoff:.22},metal:{...tone,waveType:4,frequency_start:.24,frequency_slide:-.13},wood:{...physical,frequency_start:.15},stone:{...physical,frequency_start:.1},barrier:{...tone,frequency_start:.23,frequency_slide:.08},magic:{...tone,frequency_start:.3,frequency_slide:-.08}})){
 for(let i=0;i<3;i++)add('hit-'+material+(i?'-'+i:''),{...params,frequency_start:params.frequency_start*(1+(i-1)*.018),attackTime:.007,sustainTime:.012,decayTime:.12},.18,'Quiet '+material+' confirmed impact variant');
}
for(const [name,params] of Object.entries({
 'ui-nav':{...tone,frequency_start:.23,decayTime:.09},'ui-confirm':{...tone,frequency_start:.27,decayTime:.15},'ui-reject':{...physical,waveType:4,frequency_start:.15,decayTime:.13},
 'conversation-open':{...tone,frequency_start:.23,decayTime:.15},'conversation-close':{...tone,frequency_start:.21,frequency_slide:-.04,decayTime:.12},
 'inspect':{...physical,frequency_start:.3,lpFilterCutoff:.35,decayTime:.11},'door':{...physical,frequency_start:.13,decayTime:.2},'stairs':{...physical,frequency_start:.2,decayTime:.16},'mechanism':{...physical,waveType:4,frequency_start:.12,decayTime:.23},
 'skill-learn':{...tone,pitch_jump_amount:.14,pitch_jump_onset_percent:.4,decayTime:.32},'rune-gain':{...tone,frequency_start:.34,pitch_jump_amount:.18,pitch_jump_onset_percent:.45,decayTime:.34},
 'rune-spend':{...tone,frequency_start:.24,frequency_slide:-.07,decayTime:.23},'shrine-activate':{...tone,frequency_start:.21,pitch_jump_amount:.18,pitch_jump_onset_percent:.5,sustainTime:.13,decayTime:.47},
 'quest-accept':{...tone,frequency_start:.24,decayTime:.2},'quest-progress':{...tone,frequency_start:.27,decayTime:.14},'quest-report':{...tone,frequency_start:.28,pitch_jump_amount:.12,pitch_jump_onset_percent:.5,sustainTime:.08,decayTime:.39},
 'portal-travel':{...tone,waveType:4,frequency_start:.24,frequency_slide:.08,decayTime:.32},'portal-charge':{...tone,frequency_start:.21,frequency_slide:.03,decayTime:.17},
 'defeat-soft':{...physical,frequency_start:.15,decayTime:.18},'hit-significant':{...physical,waveType:4,frequency_start:.17,decayTime:.19},
 'amb-leaves':{...physical,frequency_start:.19,lpFilterCutoff:.18,attackTime:.12,decayTime:.29},'amb-wildlife':{...tone,frequency_start:.34,frequency_slide:.03,pitch_jump_amount:-.08,pitch_jump_onset_percent:.5,decayTime:.23},
 'amb-tools':{...physical,waveType:4,frequency_start:.18,decayTime:.14},'amb-droplet':{...tone,frequency_start:.31,frequency_slide:-.1,decayTime:.18},'amb-creak':{...physical,waveType:4,frequency_start:.1,attackTime:.12,decayTime:.4},'amb-dry':{...physical,frequency_start:.13,lpFilterCutoff:.17,attackTime:.13,decayTime:.3}
}))add(name,params,name.startsWith('amb-')?.17:name.startsWith('ui-')?.2:.28);
for(const hero of ['knight','rogue','wizard','druid','archer','cleric','bard','healer']){
 const base=bank.sounds[hero+'-special'].params;
 add('ascend-'+hero,{...base,attackTime:.07,sustainTime:.17,decayTime:.58,pitch_jump_amount:.18,pitch_jump_onset_percent:.45},.43,'One-time '+hero+' transformation; no idle loop');
 add('ascended-'+hero,{...base,attackTime:.025,sustainTime:.075,decayTime:.32},.34,'Confirmed '+hero+' signature release');
 add('ascended-'+hero+'-light',{...bank.sounds[hero+'-light'].params,frequency_slide:hero==='wizard'?.09:.02,lpFilterCutoff:.40,sustainTime:.02,decayTime:.18,pitch_jump_amount:hero==='bard'?.12:.04,pitch_jump_onset_percent:.4},.30,'Quiet transformed '+hero+' common attack; no idle loop');
}
bank.version=3;fs.writeFileSync(file,JSON.stringify(bank,null,2)+'\n');console.log('Refined '+Object.keys(bank.sounds).length+' editable Bfxr recipes.');
