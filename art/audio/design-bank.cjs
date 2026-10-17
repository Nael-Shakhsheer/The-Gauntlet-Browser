/* Authoring pass: writes explicit recipes, never randomizes at build time. */
const fs=require('node:fs'),path=require('node:path');
const file=path.join(__dirname,'sounds.json'),bank=JSON.parse(fs.readFileSync(file));
const families={
 knight:{waveType:0,squareDuty:.36,frequency_start:.19,frequency_slide:-.09,lpFilterCutoff:.48,sustainTime:.025,decayTime:.22},
 rogue:{waveType:3,frequency_start:.4,frequency_slide:-.2,hpFilterCutoff:.12,lpFilterCutoff:.52,sustainTime:.014,decayTime:.15},
 archer:{waveType:4,frequency_start:.34,frequency_slide:-.21,lpFilterCutoff:.55,sustainTime:.02,decayTime:.18},
 wizard:{waveType:4,frequency_start:.31,frequency_slide:-.08,lpFilterCutoff:.62,vibratoDepth:.055,vibratoSpeed:.25,sustainTime:.06,decayTime:.24},
 druid:{waveType:3,frequency_start:.25,frequency_slide:.06,lpFilterCutoff:.33,sustainTime:.025,decayTime:.21},
 cleric:{waveType:2,frequency_start:.32,pitch_jump_amount:.16,pitch_jump_onset_percent:.38,sustainTime:.025,decayTime:.2},
 bard:{waveType:4,frequency_start:.33,pitch_jump_amount:.16,pitch_jump_onset_percent:.35,sustainTime:.04,decayTime:.26,lpFilterCutoff:.68},
 healer:{waveType:2,frequency_start:.34,frequency_slide:.055,attackTime:.022,sustainTime:.04,decayTime:.27}
};
let seed=200;
const add=(name,params,notes,peak=.5)=>{++seed;if(!bank.sounds[name]?.manual)bank.sounds[name]={seed,params,peak,notes};};
for(const [hero,base] of Object.entries(families)) {
  for(const category of ['light','special','ultimate']) {
    const big=category==='ultimate',special=category==='special';
    const params={...base,...(special||big?{attackTime:.025,sustainTime:big?.13:.075,decayTime:big?.43:.32,pitch_jump_amount:big?.19:.1,pitch_jump_onset_percent:.45}: {})};
    const name=hero+'-'+category;
    add(name,params,hero+' '+category+' family',big?.48:.42);
    if(category==='light') {
      for(let i=1;i<=2;i++)add(name+'-'+i,{...params,frequency_start:params.frequency_start*(i===1?.975:1.025)},'Subtle repeated '+hero+' Light variant',.42);
    }
  }
  add(hero+'-impact',{...base,attackTime:0,sustainTime:.012,decayTime:.13,frequency_slide:-.16},hero+' confirmed impact',.4);
}
for(const [name,params] of Object.entries({
 'ice-cast':{waveType:4,frequency_start:.38,frequency_slide:-.08,decayTime:.22,sustainTime:.025,lpFilterCutoff:.6},
 'summon-fire':{waveType:3,frequency_start:.21,frequency_slide:.08,decayTime:.31,sustainTime:.06,lpFilterCutoff:.35},
 'summon-ice':{waveType:2,frequency_start:.3,frequency_slide:.06,decayTime:.34,sustainTime:.06},
 'summon-storm':{waveType:9,frequency_start:.25,frequency_slide:.05,decayTime:.29,sustainTime:.04,lpFilterCutoff:.46},
 'summon-nature':{waveType:3,frequency_start:.15,decayTime:.32,sustainTime:.03,lpFilterCutoff:.3},
 'ward':{waveType:2,frequency_start:.24,frequency_slide:.07,sustainTime:.04,decayTime:.3,pitch_jump_amount:.15,pitch_jump_onset_percent:.5},
 'metal-impact':{waveType:0,squareDuty:.36,frequency_start:.19,frequency_slide:-.13,sustainTime:.015,decayTime:.17,lpFilterCutoff:.42},
 'wood-impact':{waveType:3,frequency_start:.16,sustainTime:.014,decayTime:.17,lpFilterCutoff:.3},
 'stone-impact':{waveType:3,frequency_start:.11,sustainTime:.02,decayTime:.23,lpFilterCutoff:.34},
 'enemy-windup':{waveType:4,frequency_start:.14,frequency_slide:.03,attackTime:.03,sustainTime:.02,decayTime:.15,lpFilterCutoff:.5},
 'enemy-release':{waveType:3,frequency_start:.2,frequency_slide:-.1,sustainTime:.025,decayTime:.17,lpFilterCutoff:.38},
 'boss-warning':{waveType:4,frequency_start:.2,pitch_jump_amount:-.18,pitch_jump_onset_percent:.5,sustainTime:.08,decayTime:.32,lpFilterCutoff:.55},
 'boss-complete':{waveType:4,frequency_start:.28,pitch_jump_amount:.18,pitch_jump_onset_percent:.3,pitch_jump_2_amount:.21,pitch_jump_onset2_percent:.65,sustainTime:.16,decayTime:.47,lpFilterCutoff:.58},
 'repair':{waveType:0,squareDuty:.36,frequency_start:.16,pitch_jump_amount:.17,pitch_jump_onset_percent:.45,sustainTime:.04,decayTime:.28,lpFilterCutoff:.4},
 'restore':{waveType:2,frequency_start:.27,frequency_slide:.08,pitch_jump_amount:.2,pitch_jump_onset_percent:.5,attackTime:.04,sustainTime:.1,decayTime:.4},
 'discovery':{waveType:4,frequency_start:.35,pitch_jump_amount:.14,pitch_jump_onset_percent:.5,sustainTime:.04,decayTime:.3,lpFilterCutoff:.62},
 'equip':{waveType:0,squareDuty:.36,frequency_start:.24,sustainTime:.01,decayTime:.11,lpFilterCutoff:.4},
 'purchase':{waveType:2,frequency_start:.4,pitch_jump_amount:.12,pitch_jump_onset_percent:.45,sustainTime:.018,decayTime:.19},
 'amb-village':{waveType:2,frequency_start:.25,attackTime:.08,sustainTime:.025,decayTime:.26},
 'amb-woodland':{waveType:3,frequency_start:.2,lpFilterCutoff:.26,attackTime:.07,sustainTime:.035,decayTime:.26},
 'amb-chamber':{waveType:2,frequency_start:.18,attackTime:.05,sustainTime:.03,decayTime:.34},
 'amb-tower':{waveType:4,frequency_start:.16,lpFilterCutoff:.28,attackTime:.07,sustainTime:.03,decayTime:.3},
 'amb-boss':{waveType:3,frequency_start:.12,lpFilterCutoff:.25,attackTime:.1,sustainTime:.03,decayTime:.35},
 'amb-fire':{waveType:3,frequency_start:.14,lpFilterCutoff:.28,sustainTime:.012,decayTime:.09},
 'amb-water':{waveType:3,frequency_start:.29,lpFilterCutoff:.33,attackTime:.05,sustainTime:.015,decayTime:.2},
 'amb-landmark':{waveType:2,frequency_start:.28,attackTime:.07,sustainTime:.02,decayTime:.28}
}))add(name,params,name+' authored Bfxr accent',name.startsWith('amb-')?.28:.45);
add('ice-impact',{waveType:4,frequency_start:.42,frequency_slide:-.2,lpFilterCutoff:.48,sustainTime:.01,decayTime:.13},'Short confirmed frost / ice-summon impact',.4);
bank.version=2;bank.generator='Retained Bfxr 1.0.4 DSP; explicit recipes, seeded noise, recipe filters and edge fades';
fs.writeFileSync(file,JSON.stringify(bank,null,2)+'\n');
console.log(Object.keys(bank.sounds).length+' recipes');

