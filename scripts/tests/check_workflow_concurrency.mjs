// Default fail-closed contract: every GitHub Actions workflow must define
// top-level PR/branch-aware concurrency. Runs of superseded PR commits must
// never occupy extra Chrome/iOS/backend runners indefinitely.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const dir=path.join(root,'.github','workflows');
const workflows=fs.readdirSync(dir).filter(name=>/\.ya?ml$/.test(name)).sort();
if(workflows.length===0)throw Error('No workflows were found');
let errors=0;
for(const filename of workflows){
  const source=fs.readFileSync(path.join(dir,filename),'utf8');
  const start=source.match(/^concurrency:[ \t]*$/gm)||[];
  if(start.length!==1){
    console.error(filename+': expected exactly one TOP-LEVEL concurrency policy');
    errors++;continue;
  }
  const block=source.split(/^concurrency:[ \t]*$/m)[1].split(/^[A-Za-z][\w-]*:/m)[0];
  const group=block.match(/^  group:[ \t]*(.+)$/m);
  const cancel=block.match(/^  cancel-in-progress:[ \t]*(.+)$/m);
  if(!group||!group[1].trim()||!cancel||!cancel[1].trim()){
    console.error(filename+': missing concurrency.group or cancel-in-progress');
    errors++;
  }
}
if(errors)process.exitCode=1;
else console.log('Workflow concurrency policy PASS: '+workflows.length+' workflows');
