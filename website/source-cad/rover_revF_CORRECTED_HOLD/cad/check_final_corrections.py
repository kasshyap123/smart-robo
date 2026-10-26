"""Independent direct STEP probes: original clashes, local edit preservation and service budgets."""
from pathlib import Path
import json,subprocess,re,hashlib
from local_corrections import ImportWriter
from design import box,cut
R=Path(__file__).resolve().parent.parent
def imp(path):return dict(op='import',path=path)
def master(p):return imp('part_masters/'+p+'_master.step')
def placed(p):return imp('final_step/'+p+'_final.step')
cases=[]
for p in ['B11','B13']:
 cases.append(('raw_B07_'+p,imp('input_step/B07_final.step'),imp('input_step/'+p+'_final.step'),'positive_control'))
for p in ['B11','B11_right','B13','B13_front_right','B13_rear_left','B13_rear_right']:
 cases.append(('installed_B07_'+p,placed('B07'),placed(p),'zero'))
# Symmetric difference outside the explicitly bounded microphone edit region.
roi=box(14.81,42,31.2,71.5,-21,116)
old=cut(imp('input_step/B10_final.step'),roi);new=cut(master('B10'),roi)
cases += [('B10_old_only_outside_edit',cut(old,new),None,'zero'),('B10_new_only_outside_edit',cut(new,old),None,'zero')]
# The holder is lifted after the tray and retaining strap are removed.
for d in range(31):cases.append(('holder_lift_'+str(d),box(77.1,39.8,14.9,-86.55,-19.9,4+d),master('B07'),'zero'))
# This is an available route ABOVE the cradle wall, not an invented lead exit location.
cases.append(('holder_two_lead_route_budget',box(12,8,6,-98,-4,11),master('B07'),'zero'))
# Board-level service budgets are deliberately model-independent. Lid is removed.
for p in ['B01','B02','B03','B05','B06']:
 cases.append(('LM_adjustment_top_access_'+p,box(45,21,35,-100.5,-45.5,74),master(p),'zero'))
 cases.append(('LM_rear_terminal_budget_'+p,box(8,21,12,-108.5,-45.5,56),master(p),'zero'))
 cases.append(('PAM_wire_budget_'+p,box(8,18,10,-13.5,-39,56),master(p),'zero'))
 cases.append(('driver_front_terminal_budget_'+p,box(5,43,12,-6,5,52),master(p),'zero'))
lines=['SetFactory("OpenCASCADE");'];values=[]
for i,(name,a,b,expect) in enumerate(cases):
 w=ImportWriter();w.i=100000+i*200;aa=w.emit(a);bb=w.emit(b) if b is not None else None;lines+=w.lines[2:]
 if bb:
  q='q'+str(i)+'()';lines.append(q+'=BooleanIntersection{Volume{'+aa+'};Delete;}{Volume{'+bb+'};Delete;};')
 else:q=aa
 lines+=['mass=0;','If (#'+q+'>0)','For k In {0:#'+q+'-1}','mass+=Mass Volume{'+q.replace('()','(k)')+'};','EndFor','EndIf',f'Printf("RESULT {i} %.12g",mass);','Recursive Delete{Volume{'+q+'};}']
lines.append('Printf("LOCAL_CHECKS_FINISHED");');f=R/'cad/generated/final_corrections.geo';f.write_text('\n'.join(lines));p=subprocess.run(['/Applications/FreeCAD.app/Contents/Resources/bin/gmsh',str(f),'-0','-v','3'],capture_output=True,text=True);log=p.stdout+'\n'+p.stderr;(R/'cad/build_logs/final_corrections.txt').write_text(log)
vals={int(i):float(v) for i,v in re.findall(r'RESULT (\d+) ([-+\deE.]+)',log)}
for i,(name,a,b,expect) in enumerate(cases):
 v=vals.get(i);values.append(dict(name=name,intersection_or_difference_mm3=v,criterion=expect,passed=v is not None and (v>1 if expect=='positive_control' else abs(v)<.0001)))
unchanged=[]
for f in sorted((R/'part_masters').glob('*.step')):
 pid=f.stem.replace('_master','');s=R/'input_step'/(pid+'_final.step');eq=hashlib.sha256(f.read_bytes()).hexdigest()==hashlib.sha256(s.read_bytes()).hexdigest();unchanged.append(dict(part=pid,byte_identical_to_RevE=eq));assert eq==(pid!='B10')
out=dict(finished='LOCAL_CHECKS_FINISHED' in log,checks=values,preservation=unchanged,errors=[l for l in log.splitlines() if l.startswith('Error')],limitations=['Service corridors are CAD space budgets, not measured connector shapes.','Holder lift assumes tray and retaining strap removed; loose wires disconnected or given slack.','Microphone outside-edit comparison covers the entire original solid outside the defined local box.'])
(R/'correction_validation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2));assert p.returncode==0 and out['finished'] and not out['errors'] and all(x['passed'] for x in values)
