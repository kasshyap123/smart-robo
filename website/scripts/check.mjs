import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
const data=JSON.parse(fs.readFileSync('assets/geometry.json'));
const bin=fs.readFileSync('assets/robot.bin');
assert.equal(data.instances.length,18);
assert.equal(new Set(data.instances.map(x=>x.group)).size,13);
assert.equal(data.masters.length,14);
for(const r of data.instances){
 const file=fs.readFileSync(path.join('source-cad/rover_revF_CORRECTED_HOLD',r.file));
 assert.equal(crypto.createHash('sha256').update(file).digest('hex'),r.sha256,r.id+' source hash');
 assert.equal(r.byteLength,r.vertices*3*4);
 assert.ok(r.offset+r.byteLength<=bin.length);
 for(let i=r.offset;i<r.offset+r.byteLength;i+=4)assert.ok(Number.isFinite(bin.readFloatLE(i)),r.id+' finite coordinate');
}
for(const file of ['index.html','controls/index.html']){
 const html=fs.readFileSync(path.join('dist',file),'utf8');
 for(const [,ref] of html.matchAll(/(?:src|href)="([^"]+)"/g)){
  if(ref.startsWith('http')||ref.startsWith('#'))continue;
  assert.ok(fs.existsSync(path.resolve('dist',path.dirname(file),ref)),file+' asset '+ref);
 }
}
for(const file of ['app.js','sw.js','controls/app.js'])execFileSync(process.execPath,['--check',file]);
console.log('PASS: 18 original STEP hashes, 14 masters / 13 card groups, complete finite mesh buffers, showroom/control assets, JavaScript syntax.');
