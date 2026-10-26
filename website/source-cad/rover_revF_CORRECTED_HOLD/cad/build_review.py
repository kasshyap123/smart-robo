import json,subprocess,re,shutil,hashlib,concurrent.futures
from pathlib import Path
from local_corrections import ImportWriter,corrected
from mesh_utils import orient_stl
ROOT=Path(__file__).resolve().parent.parent;GM='/Applications/FreeCAD.app/Contents/Resources/bin/gmsh'
def build(r):
 pid=r['id'];w=ImportWriter();w.emit(corrected(r));step=ROOT/'part_masters'/(pid+'_master.step');mesh=ROOT/'cad/internal_mesh'/(pid+'.stl');f=ROOT/'cad/generated'/(pid+'.geo')
 w.lines += ['v()=Volume{:};','bb()=BoundingBox Volume{v()};',f'Printf("CHECK {pid} %g %.9g %.9g %.9g %.9g %.9g %.9g",#v(),bb(0),bb(1),bb(2),bb(3),bb(4),bb(5));','mass=0; For i In {0:#v()-1} mass+=Mass Volume{v(i)}; EndFor','Printf("MASS %.9g",mass);']
 if pid in ['B10']:w.lines += [f'Save "{step.as_posix()}";']
 else:shutil.copy2(ROOT/r['step'],step)
 w.lines += ['Mesh.MeshSizeMin=.7; Mesh.MeshSizeMax=3; Mesh.MeshSizeFromCurvature=32; Mesh.Algorithm=6; Mesh.Binary=0;','Mesh 2;',f'Save "{mesh.as_posix()}";','Printf("BUILD_FINISHED");']
 f.write_text('\n'.join(w.lines)+'\n');p=subprocess.run([GM,str(f),'-0','-v','3'],capture_output=True,text=True);log=p.stdout+'\n'+p.stderr;(ROOT/'cad/build_logs'/(pid+'.txt')).write_text(log)
 q={k:v for k,v in r.items() if k not in ['source_path','stl','sha256','mesh_processing']};q.update(step=str(step.relative_to(ROOT)),stl=str(mesh.relative_to(ROOT)),source_sha256=r['sha256'],geometry_changed=pid in ['B10'],errors=[x for x in log.splitlines() if x.startswith('Error')],print_release='HOLD')
 c=re.search(r'CHECK '+pid+r' (\d+) ([-+eE\d. ]+)',log);mass=re.search(r'MASS ([-+eE\d.]+)',log)
 if c:q.update(solid_count=int(c[1]),bounds=list(map(float,c[2].split())))
 if mass:q['volume_mm3']=float(mass[1])
 q['size_mm']=[round(q['bounds'][i+3]-q['bounds'][i],4) for i in range(3)]
 if mesh.exists():q['mesh_processing']=orient_stl(mesh)
 q['export_sha256']=hashlib.sha256(step.read_bytes()).hexdigest() if step.exists() else None
 if not q['geometry_changed']:assert q['export_sha256']==q['source_sha256']
 print(pid,q.get('solid_count'),q['errors'],flush=True);assert p.returncode==0 and q.get('solid_count')==1 and not q['errors'];return q
if __name__=='__main__':
 import sys
 for name in ['part_masters','cad/internal_mesh','cad/generated','cad/build_logs']:(ROOT/name).mkdir(exist_ok=True,parents=True)
 records=json.loads((ROOT/'input_manifest.json').read_text())
 selected=set(sys.argv[1:]); records=[r for r in records if not selected or r['id'] in selected]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:res=list(pool.map(build,records))
 old=json.loads((ROOT/'parts_manifest.json').read_text()) if selected and (ROOT/'parts_manifest.json').exists() else []
 merged={r['id']:r for r in old};merged.update({r['id']:r for r in res})
 (ROOT/'parts_manifest.json').write_text(json.dumps(sorted(merged.values(),key=lambda r:r['id']),indent=2))
