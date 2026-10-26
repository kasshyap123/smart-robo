"""Measure representative wall/panel sections on actual STEP solids by intersection volume / probe area."""
from pathlib import Path
import json,subprocess,re
from design import GeoWriter,box
R=Path(__file__).resolve().parent.parent;records=json.loads((R/'parts_manifest.json').read_text());paths={r['id']:(R/r['step']).as_posix() for r in records};lines=['SetFactory("OpenCASCADE");'];cases=[
('B01','front wall',box(10,2,2,112,-1,42),4,2.8),('B02','rear wall',box(10,2,2,-122,-1,54),4,2.8),
('B03','flat deck',box(2,2,8,20,20,76),4,3),('B04','rear lid',box(2,2,8,-50,20,76),4,3),
('B05','tray floor',box(2,2,6,-55,2,43),4,3),('B06','carrier plate',box(2,2,6,-102,24,49),4,3),
('B07','cradle floor',box(2,2,8,-49,-1,-1),4,4),('B08','head side wall',box(2,10,2,60,-60,150),4,2.8),
('B09','rear cover',box(8,2,2,25,35,135),4,3),('B10','visor panel',box(6,2,2,97,19,160),4,2.8),
('B11','retainer plate',box(2,2,6,38,0,-1),4,2.5),('B12','switch panel',box(8,2,2,-123,-35,25),4,2.8),
('B13','foot support',box(2,2,12,0,6,-1),4,8),('B10R','OLED rear carrier',box(6,2,2,87,19,160),4,3)]
for i,(pid,label,shape,area,expected) in enumerate(cases):
 lines.append(f'p{i}()=ShapeFromFile("{paths[pid]}");');w=GeoWriter();w.i=50000+i*100;probe=w.emit(shape);lines.extend(w.lines[2:]);q=f'q{i}';lines.append(f'{q}()=BooleanIntersection{{Volume{{p{i}()}};Delete;}}{{Volume{{{probe}}};Delete;}}; mass=0; If (#{q}()>0) For k In {{0:#{q}()-1}} mass+=Mass Volume{{{q}(k)}}; EndFor EndIf Printf("SECTION {i} %.9g",mass);')
lines.append('Printf("SECTIONS_FINISHED");');p=R/'cad/generated/sections.geo';p.write_text('\n'.join(lines)+'\n');run=subprocess.run(['/Applications/FreeCAD.app/Contents/Resources/bin/gmsh',str(p),'-0','-v','3'],capture_output=True,text=True);log=run.stdout+'\n'+run.stderr;(R/'cad/build_logs/sections.txt').write_text(log);values={int(i):float(v) for i,v in re.findall(r'SECTION (\d+) ([-+eE\d.]+)',log)};out=[]
for i,(pid,label,shape,area,expected) in enumerate(cases):
 value=values.get(i,0)/area;out.append(dict(part=pid,section=label,measured_mm=value,expected_mm=expected,passed=abs(value-expected)<.005))
(R/'section_validation.json').write_text(json.dumps(dict(method='Selected planar section probes; not a global minimum-wall or strength analysis',checks=out),indent=2));print(json.dumps(out,indent=2));assert run.returncode==0 and all(x['passed'] for x in out)
