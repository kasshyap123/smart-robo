"""Independent STEP round-trip, exact unit declarations and M3 assembly-axis checks.
No purchased component geometry is exported. Tests are limited to the current RevC dimensions.
"""
from pathlib import Path
import json,re,subprocess,math,os
from design import GeoWriter,cyl
ROOT=Path(__file__).resolve().parent.parent
GM=os.environ.get('GMSH_EXECUTABLE','/Applications/FreeCAD.app/Contents/Resources/bin/gmsh')
records=json.loads((ROOT/'parts_manifest.json').read_text());lines=['SetFactory("OpenCASCADE");','Geometry.OCCBoundsUseStl=1;'];items={};units=[]
for r in records:
 path=ROOT/r['step'];unit_ok='SI_UNIT(.MILLI.,.METRE.)' in path.read_text();units.append(dict(id=r['id'],step_length_unit='millimetres' if unit_ok else 'UNKNOWN',unit_ok=unit_ok))
 var=r['id'];lines.append(f'{var}()=ShapeFromFile("{path.as_posix()}");');lines.append(f'bb()=BoundingBox Volume{{{var}()}}; Printf("ROUNDTRIP {var} %g %.9g %.9g %.9g %.9g %.9g %.9g",#{var}(),bb(0),bb(1),bb(2),bb(3),bb(4),bb(5));')
 if r['id'] in ['B11','B13']:
  for i,cp in enumerate(r['copies']):
   name=var+'_'+str(i+1);x,y,z,ang=cp;lines.append(f'{name}()=Duplicata{{Volume{{{var}()}};}};')
   axis='1,0,0' if var=='B11' else '0,0,1'
   lines.append(f'Rotate{{{{{axis}}},{{0,0,0}},{math.radians(ang)}}}{{Volume{{{name}()}};}}')
   lines.append(f'Translate{{{x},{y},{z}}}{{Volume{{{name}()}};}}');items[name]=name+'()'
 else:items[var]=var+'()'
tests=[]
def probe(label,names,x,y,z,h,axis=(0,0,1)):
 tests.append(dict(label=label,parts=names,axis_start_mm=[x,y,z],axis_vector=list(axis),length_mm=h,probe_diameter_mm=3.2))
 writer=GeoWriter();writer.i=20000+len(tests)*20;a=writer.emit(cyl(3.2,h,x,y,z,axis));lines.extend(writer.lines[2:])
 for name in names:
  q='q'+str(len(lines));lines.append(f'{q}()=BooleanIntersection{{Volume{{{items[name]}}};}}{{Volume{{{a}}};}};')
  lines.append(f'If (#{q}()>0) mass=0; For i In {{0:#{q}()-1}} mass+=Mass Volume{{{q}(i)}}; EndFor Printf("AXIS_BLOCKED {label} {name} %.9g",mass); Recursive Delete{{Volume{{{q}()}};}} EndIf')
 lines.append(f'Recursive Delete{{Volume{{{a}}};}}')
for x in [-108,-12]:
 for y in [-62,62]:probe('rear_lid_'+str((x,y)),['B02','B04'],x,y,67,15)
for x in [9,111]:
 for y in [-62,62]:probe('front_deck_'+str((x,y)),['B01','B03'],x,y,67,15)
for x in [-94,-26]:
 for y in [-60,60]:probe('tray_'+str((x,y)),['B02','B05'],x,y,37,11)
for x in [-90,-60]:
 for y in [0,50]:probe('esp_carrier_'+str((x,y)),['B05','B06'],x,y,43,11)
for x in [41,87]:
 for y in [-23,23]:probe('neck_'+str((x,y)),['B03','B08'],x,y,104,9)
for y in [-48,48]:
 for z in [117,171]:probe('head_cover_'+str((y,z)),['B08','B09'],26,y,z,15,(1,0,0))
for y in [-48,48]:
 for z in [113,175]:probe('visor_'+str((y,z)),['B08','B10'],89,y,z,13,(1,0,0))
for y in [-46,46]:
 for z in [12,42]:probe('rear_panel_'+str((y,z)),['B02','B12'],-122,y,z,8,(1,0,0))
for z in [43,55]:probe('shell_seam_'+str(z),['B01','B02'],7,-70,z,140,(0,1,0))
for x in [20,100]:
 for z in [21,73]:probe('speaker_'+str((x,z)),['B01','B11_1','B11_2'],x,-70,z,140,(0,1,0))
for i,(x,y) in enumerate([(100,58),(100,-58),(-100,58),(-100,-58)]):probe('body_foot_'+str(i+1),['B01' if x>0 else 'B02','B13_'+str(i+1)],x,y,-1,14)

for y in [-27,27]:probe('OLED_carrier_'+str(y),['B10','B10R'],87,y,161,10.5,(1,0,0))
lines.append('Printf("INTERFACES_FINISHED");');outdir=ROOT/'cad/generated';outdir.mkdir(exist_ok=True);(ROOT/'cad/build_logs').mkdir(exist_ok=True);path=outdir/'interfaces.geo';path.write_text('\n'.join(lines));proc=subprocess.run([GM,str(path),'-0','-v','3'],capture_output=True,text=True);log=proc.stdout+'\n'+proc.stderr;(ROOT/'cad/build_logs/interfaces.txt').write_text(log)
roundtrip=[]
for line in log.splitlines():
 if line.startswith('ROUNDTRIP'):
  sp=line.split();r=next(r for r in records if r['id']==sp[1]);bb=list(map(float,sp[3:]));err=max(abs(a-b) for a,b in zip(bb,r['bounds']));roundtrip.append(dict(id=r['id'],imported_solid_count=int(sp[2]),bounds_mm=bb,max_bound_difference_mm=err,passed=int(sp[2])==1 and err<.005))
failures=[ln for ln in log.splitlines() if ln.startswith(('AXIS_BLOCKED','Error'))]
res=dict(print_release='BLOCKED',finished='INTERFACES_FINISHED' in log,units=units,scale_factor_applied=1.0,step_roundtrip=roundtrip,mount_axis_checks=tests,axis_failures=failures,exceptions=['Chassis hole alignment, motor and wheel positions not verified','PCB retainers, connector plugs and switch latch/terminal geometry not verified','M3 probe checks do not verify purchased fastener lengths or nut access'])
(ROOT/'interface_validation.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2));assert proc.returncode==0 and res['finished'] and len(roundtrip)==14 and all(x['passed'] for x in roundtrip) and all(x['unit_ok'] for x in units) and not failures
