const fs=require('node:fs'),path=require('node:path'),{spawnSync}=require('node:child_process');
const root=path.join(__dirname,'..'),rows=[];
for(const name of fs.readdirSync(path.join(root,'static')).filter(n=>n.endsWith('.js'))){const r=spawnSync(process.execPath,['--check',path.join(root,'static',name)],{encoding:'utf8',cwd:root,windowsHide:true});rows.push({kind:'parse',name,code:r.status,output:(r.stdout+r.stderr).trim()});}
for(const name of fs.readdirSync(path.join(root,'tests')).filter(n=>/^test_.*\.cjs$/.test(n))){const r=spawnSync(process.execPath,[path.join(root,'tests',name)],{encoding:'utf8',cwd:root,windowsHide:true});rows.push({kind:'suite',name,code:r.status,output:(r.stdout+r.stderr).trim()});}
const report={parse:rows.filter(r=>r.kind==='parse').length,suites:rows.filter(r=>r.kind==='suite').length,failures:rows.filter(r=>r.code!==0),results:rows};
fs.writeFileSync(path.join(root,'reports/VISUAL_CLIENT_2026-10-16.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({parse:report.parse,suites:report.suites,failures:report.failures}));if(report.failures.length)process.exitCode=1;
