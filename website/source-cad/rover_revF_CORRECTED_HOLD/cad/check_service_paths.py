"""Sampled rigid extraction checks using exported STEP. No claim of cable/hand or continuous-sweep validation."""
from pathlib import Path
import json,subprocess,concurrent.futures,os
ROOT=Path(__file__).resolve().parent.parent;GM=os.environ.get('GMSH_EXECUTABLE','/Applications/FreeCAD.app/Contents/Resources/bin/gmsh');records=json.loads((ROOT/'parts_manifest.json').read_text());paths={r['id']:(ROOT/r['step']).as_posix() for r in records}
# Covers/fasteners/harnesses must first be removed as stated. Co-moving purchased hardware remains a fit check.
cases=[('rear_lid_lift',['B04'],['B01','B02','B03'],(0,0,1),15,1),('tray_straight_lift',['B05','B06'],['B01','B02','B03'],(0,0,1),100,2),('visor_forward_removal',['B10','B10R'],['B08','B03'],(1,0,0),40,1),('head_cover_rearward',['B09'],['B08'],(-1,0,0),30,2),('battery_cradle_lift',['B07'],['B01','B02','B03'],(0,0,1),100,2),('OLED_carrier_upward_after_visor_removal',['B10R'],['B10'],(0,0,1),30,1),('ESP_carrier_lift',['B06'],['B02','B05'],(0,0,1),70,2)]
def run(case):
 name,moving,fixed,axis,end,step=case;lines=['SetFactory("OpenCASCADE");'];ids={}
 for pid in moving+fixed:
  ids[pid]=pid+'()';lines.append(f'{pid}()=ShapeFromFile("{paths[pid]}");')
 for distance in range(0,end+1,step):
  if distance:
   delta=','.join(str(k*step) for k in axis);lines.append('Translate{'+delta+'}{Volume{'+','.join(ids[p] for p in moving)+'};}')
  for a in moving:
   for b in fixed:
    q='q'+str(len(lines));lines.append(f'{q}()=BooleanIntersection{{Volume{{{ids[a]}}};}}{{Volume{{{ids[b]}}};}};')
    lines.append(f'If (#{q}()>0) mass=0; For k In {{0:#{q}()-1}} mass+=Mass Volume{{{q}(k)}}; EndFor Printf("OBSTRUCTION {name} {distance}mm {a} {b} %.9g",mass); Recursive Delete{{Volume{{{q}()}};}} EndIf')
 lines.append('Printf("PATH_FINISHED");');f=ROOT/'cad/generated'/(name+'.geo');f.write_text('\n'.join(lines).replace(' mass=0; For ', '\nmass=0;\nFor ').replace('} mass+=', '}\nmass+=').replace('; EndFor', ';\nEndFor\n')+'\n');p=subprocess.run([GM,str(f),'-0','-v','3'],capture_output=True,text=True);log=p.stdout+'\n'+p.stderr;(ROOT/'cad/build_logs'/(name+'.txt')).write_text(log);errors=[ln for ln in log.splitlines() if ln.startswith(('OBSTRUCTION','Error'))];return dict(path=name,moving=moving,fixed=fixed,axis=axis,sampled_interval_mm=step,travel_mm=end,positions=end//step+1,finished='PATH_FINISHED' in log,obstructions=errors,exit_code=p.returncode)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,cases))
report=dict(print_release='HOLD',method='Discrete CAD intersection samples, not continuous motion proof',checks=results,exclusions=['Attached wires, connectors, real boards, straps, fasteners, hands and tools','Motor/wheel envelopes and actual chassis holes','Elastic deflection and manufacturing error'])
(ROOT/'service_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));assert all(x['finished'] and not x['obstructions'] and x['exit_code']==0 for x in results)
