import { settings } from './manager.mjs';
const action=process.argv[2]||'verify';
const args=process.argv[3]?JSON.parse(process.argv[3]):{};
const base=`http://127.0.0.1:${settings.port}`;
try {
  const {token}=await(await fetch(base+'/api/session')).json();
  const response=await fetch(base+'/api/'+action,{method:'POST',headers:{'Content-Type':'application/json','X-Manager-Token':token},body:JSON.stringify(args)});
  const data=await response.json();console.log(JSON.stringify(data,null,2));if(!response.ok)process.exitCode=1;
}catch(e){console.error('Manager nicht erreichbar: '+e.message+'. Zuerst start.ps1 ausführen.');process.exitCode=1;}
