import {mkdir,cp,rm} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
await rm(path.join(root,'dist'),{recursive:true,force:true});
await mkdir(path.join(root,'dist'),{recursive:true});
for(const item of ['index.html','style.css','app.js','manifest.webmanifest','sw.js','icon.svg','icon-192.png','icon-512.png','assets','vendor','controls'])await cp(path.join(root,item),path.join(root,'dist',item),{recursive:true});
console.log('Built the showroom and preserved controls in dist/. CAD source and project archives stay outside the hosted assets.');
