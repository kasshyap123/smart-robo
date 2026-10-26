"""Export every installed copy explicitly. Final STEP files require no extra transforms."""
from pathlib import Path
import json,subprocess,re,math,hashlib,itertools
ROOT=Path(__file__).resolve().parent.parent;GM='/Applications/FreeCAD.app/Contents/Resources/bin/gmsh';m=json.loads((ROOT/'parts_manifest.json').read_text())
instances=[];lines=['SetFactory("OpenCASCADE");','Geometry.OCCBoundsUseStl=1;']
for p in m:
 for i,cp in enumerate(p['copies']):
  suffix={('B11',1):'_right',('B13',1):'_front_right',('B13',2):'_rear_left',('B13',3):'_rear_right'}.get((p['id'],i),'');name=p['id']+suffix;path=ROOT/'final_step'/(name+'_final.step');x,y,z,ang=cp;v='p'+str(len(instances))+'()';lines.append(v+'=ShapeFromFile("'+str(ROOT/p['step'])+'");')
  if ang:lines.append('Rotate{{'+('1,0,0' if p['id']=='B11' else '0,0,1')+'},{0,0,0},'+str(math.radians(ang))+'}{Volume{'+v+'};}')
  if any([x,y,z]):lines.append('Translate{'+f'{x},{y},{z}'+'}{Volume{'+v+'};}')
  lines+=['bb()=BoundingBox Volume{'+v+'};',f'Printf("PLACED {name} %g %.9g %.9g %.9g %.9g %.9g %.9g",#{v},bb(0),bb(1),bb(2),bb(3),bb(4),bb(5));',f'Save "{path}";','Recursive Delete{Volume{'+v+'};}']
  instances.append(dict(id=name,master=p['id'],step=str(path.relative_to(ROOT)),master_step=p['step'],translation_mm=[x,y,z],rotation_axis='X' if p['id']=='B11' else 'Z',rotation_degrees=ang,geometry_quantity=1))
lines+=['Printf("PLACED_EXPORT_FINISHED");'];geo=ROOT/'cad/generated/placed_export.geo';geo.write_text('\n'.join(lines));p=subprocess.run([GM,str(geo),'-0','-v','3'],capture_output=True,text=True);log=p.stdout+'\n'+p.stderr;(ROOT/'cad/build_logs/placed_export.txt').write_text(log)
for ob in instances:
 q=re.search('PLACED '+ob['id']+r' (\d+) ([-+eE\d. ]+)',log);assert q;ob['solid_count']=int(q[1]);ob['bounds_mm']=list(map(float,q[2].split()));ob['sha256']=hashlib.sha256((ROOT/ob['step']).read_bytes()).hexdigest();assert ob['solid_count']==1
assert p.returncode==0 and 'PLACED_EXPORT_FINISHED' in log and not any(x.startswith('Error') for x in log.splitlines());(ROOT/'assembly_instances.json').write_text(json.dumps(instances,indent=2))
# Audit explicit exported positions, with no hidden or repeated transforms.
lines=['SetFactory("OpenCASCADE");','Geometry.OCCBoundsUseStl=1;'];vars={}
for i,p in enumerate(instances):
 v='p'+str(i)+'()';vars[p['id']]=v;lines.append(v+'=ShapeFromFile("'+str(ROOT/p['step'])+'");');lines.append('s()=Boundary{Volume{'+v+'};}; e()=CombinedBoundary{Surface{s()};};');lines.append(f'Printf("CLOSED {p["id"]} %g %g",#{v},#e());')
lines.append(f'Save "{ROOT}/cad/Rover_RevF_HOLD_Assembly.step";')
for a,b in itertools.combinations(instances,2):
 # Bounding boxes prove separation where no positive intersection is possible.
 ab=a['bounds_mm'];bb=b['bounds_mm'];over=[min(ab[k+3],bb[k+3])-max(ab[k],bb[k]) for k in range(3)]
 if min(over)<-.0001:continue
 q='q'+str(len(lines))+'()';lines.append(q+'=BooleanIntersection{Volume{'+vars[a['id']]+'};}{Volume{'+vars[b['id']]+'};};');lines+=['If (#'+q+'>0)','mass=0;','For k In {0:#'+q+'-1}','mass+=Mass Volume{'+q.replace('()','(k)')+'};','EndFor',f'Printf("INTERFERENCE {a["id"]} {b["id"]} %.9g",mass);','Recursive Delete{Volume{'+q+'};}','EndIf']
lines.append('Printf("EXPLICIT_ASSEMBLY_FINISHED");');geo=ROOT/'cad/generated/explicit_assembly.geo';geo.write_text('\n'.join(lines));p=subprocess.run([GM,str(geo),'-0','-v','3'],capture_output=True,text=True);log=p.stdout+'\n'+p.stderr;(ROOT/'cad/build_logs/explicit_assembly.txt').write_text(log);fail=[l for l in log.splitlines() if l.startswith(('INTERFERENCE','Error'))];closed=[dict(id=n,solid_count=int(c),open_boundary_edges=int(e)) for n,c,e in re.findall(r'CLOSED (\S+) (\d+) (\d+)',log)];out=dict(finished='EXPLICIT_ASSEMBLY_FINISHED' in log,instance_count=len(instances),checks=closed,positive_intersections_or_errors=fail,positioning='Every final_step file has its installed position baked in; no transforms applied during this check',print_release='HOLD');(ROOT/'explicit_assembly_validation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2));assert p.returncode==0 and out['finished'] and len(closed)==18 and all(x['solid_count']==1 and x['open_boundary_edges']==0 for x in closed) and not fail
