import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../docs/release-v1.0.0');
const mime={'.html':'text/html; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.gif':'image/gif','.css':'text/css; charset=utf-8'};
export function helpAsset(url){
 if(!url.startsWith('/release-help/'))return null;
 const relative=url.slice('/release-help/'.length);
 if(relative.includes('..')||/[\\%:]/.test(relative))return null;
 const target=path.resolve(root,relative==='catalog.json'?'help_catalog.json':relative);
 if(!target.startsWith(root+path.sep)||!fs.existsSync(target)||!fs.statSync(target).isFile())return null;
 if(!fs.realpathSync(target).startsWith(fs.realpathSync(root)+path.sep))return null;
 const type=relative==='catalog.json'?'application/json; charset=utf-8':mime[path.extname(target)];
 return type?{target,type}:null;
}
