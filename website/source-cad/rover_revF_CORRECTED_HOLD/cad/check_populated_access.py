"""Nominal envelope access checks. No purchased hardware geometry is exported."""
from pathlib import Path
import json,subprocess,concurrent.futures
from design import GeoWriter,box,cyl,hexprism,face
ROOT=Path(__file__).resolve().parent.parent
GM='/Applications/FreeCAD.app/Contents/Resources/bin/gmsh'
paths={r['id']:str(ROOT/r['step']) for r in json.loads((ROOT/'parts_manifest.json').read_text())}
oled=[box(1.5,27.3,27.3,93,-13.65,146.172),box(2.72,26.7,19.26,94.5,-13.35,150.192),box(1.5,27.3,27.3,91.5,-13.65,146.172),box(10,10.16,2.54,83,-5.08,170.552)]
head=oled+[box(15,45,20,86.8,4.5,122),box(15,45,20,86.8,-49.5,122),cyl(14,1.5,73.7,0,132,axis=(1,0,0)),cyl(10,2.5,71.2,0,132,axis=(1,0,0)),box(15,14,14,57,-7,125)]
tray=[box(43,43,27,-49,5,49),box(45,21,18,-100.5,-45.5,56),box(21,18,10,-34.5,-39,56),box(28,55,12,-92,-2.5,56)]
cases=[('populated_visor_forward',['B10','B10R'],head,['B08','B03'],(1,0,0),40,1),('populated_OLED_up_after_visor_removed',['B10R'],oled,['B10'],(0,0,1),30,1),('populated_tray_lift',['B05','B06'],tray,['B01','B02','B03'],(0,0,1),100,2),('M3_nuts_at_carrier_rails',[],[face(hexprism(5.5,2.4),94.9,y,161) for y in [-27,27]],['B10','B10R'],(0,0,0),0,1)]
def run(case):
 name,moving,shapes,fixed,axis,end,step=case;lines=['SetFactory("OpenCASCADE");'];mv=[];fv=[]
 for i,pid in enumerate(moving+fixed):
  var='p'+str(i)+'()';lines.append(var+'=ShapeFromFile("'+paths[pid]+'");');(mv if i<len(moving) else fv).append(var)
 for i,shape in enumerate(shapes):
  w=GeoWriter();w.i=50000+i*100;v=w.emit(shape);lines+=w.lines[2:];mv.append(v)
 for dist in range(0,end+1,step):
  if dist:lines.append('Translate{'+','.join(str(a*step) for a in axis)+'}{Volume{'+','.join(mv)+'};}')
  for a in mv:
   for b in fv:
    q='q'+str(len(lines))+'()';lines.append(q+'=BooleanIntersection{Volume{'+a+'};}{Volume{'+b+'};};');lines.append('If (#'+q+'>0) mass=0; For k In {0:#'+q+'-1} mass+=Mass Volume{'+q.replace('()','(k)')+'}; EndFor Printf("OBSTRUCTION '+name+' '+str(dist)+' %.9g",mass); Recursive Delete{Volume{'+q+'};} EndIf')
 lines.append('Printf("ACCESS_FINISHED");');p=ROOT/'cad/generated'/(name+'.geo');p.write_text('\n'.join(lines).replace(' mass=0; For ', '\nmass=0;\nFor ').replace('} mass+=', '}\nmass+=').replace('; EndFor', ';\nEndFor\n'));proc=subprocess.run([GM,str(p),'-0','-v','3'],capture_output=True,text=True);log=proc.stdout+'\n'+proc.stderr;(ROOT/'cad/build_logs'/(name+'.txt')).write_text(log);bad=[x for x in log.splitlines() if x.startswith(('OBSTRUCTION','Error'))];return dict(name=name,positions=end//step+1,travel_mm=end,interval_mm=step,axis=axis,finished='ACCESS_FINISHED' in log,obstructions=bad,passed=proc.returncode==0 and 'ACCESS_FINISHED' in log and not bad)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:res=list(pool.map(run,cases))
(ROOT/'populated_access_validation.json').write_text(json.dumps({'method':'Discrete intersections using supplied nominal envelopes and labelled connector/component budgets','checks':res,'exclusions':['Actual wiring bends/retainers, connected plug sizes, human/tool reach, motor/wheel coordinates, physical manufacturing tolerances','No continuous motion proof or thermal/strength certification']},indent=2));print(json.dumps(res,indent=2));assert all(x['passed'] for x in res)
