"""Independent Boolean probes of the exported OLED opening, microphone seat and M2 bores."""
from pathlib import Path
import json,subprocess,re,math
from design import GeoWriter,box,cyl,rr,face
R=Path(__file__).resolve().parent.parent
cases=[]
# A rectangular probe retains only the four rounded corners of the opening.
cases.append(('B10','OLED_24.7x14.2_R0.5_corner_volume',box(2.8,24.7,14.2,98,-12.35,154.65),2.8*(4-math.pi)*.25))
for y in [-12.4,12.35]:cases.append(('B10','OLED_vertical_edge_'+str(y),box(2.8,.05,10,98,y,156.75),1.4))
for z in [154.60,168.85]:cases.append(('B10','OLED_horizontal_edge_'+str(z),box(2.8,20,.05,98,-10,z),2.8))
cases.append(('B10','mic_15.2mm_pocket_clear',cyl(15.19,3,72.1,0,132,axis=(1,0,0)),0))
cases.append(('B10','mic_7mm_sound_collector_clear',cyl(6.99,1.1,75.1,0,132,axis=(1,0,0)),0))
for y in [-10.35,10.35]:
 for z in [171.422,148.222]:cases.append(('B10R','OLED_M2_axis_'+str((y,z)),cyl(2.4,3.2,87.9,y,z,axis=(1,0,0)),0))
cases += [('B10','mic_outer21.2_seat15.2_section',cyl(21.2,.5,73.5,0,132,axis=(1,0,0)),math.pi*(10.6**2-7.6**2)*.5),('B10','mic_retaining_shoulder',cyl(15.2,.5,75.3,0,132,axis=(1,0,0)),math.pi*(7.6**2-3.5**2)*.5),('B10','old29mm_lower_cup_removed',box(1,4,3,73,-2,118),0)]
lines=['SetFactory("OpenCASCADE");'];results=[]
for i,(pid,name,shape,expected) in enumerate(cases):
 lines.append(f'p{i}()=ShapeFromFile("{R}/part_masters/{pid}_master.step");');w=GeoWriter();w.i=10000+i*100;q=w.emit(shape);lines+=w.lines[2:];v='c'+str(i)+'()';lines.append(v+'=BooleanIntersection{Volume{p'+str(i)+'()};Delete;}{Volume{'+q+'};Delete;};');lines.append('mass=0; If (#'+v+'>0) For k In {0:#'+v+'-1} mass+=Mass Volume{'+v.replace('()','(k)')+'}; EndFor EndIf Printf("FEATURE '+str(i)+' %.9g",mass);')
lines.append('Printf("FEATURES_FINISHED");');p=R/'cad/generated/features.geo';p.write_text('\n'.join(lines).replace(') For ', ')\nFor ').replace('} mass+=', '}\nmass+=').replace('; EndFor', ';\nEndFor\n').replace(' EndIf Printf', '\nEndIf\nPrintf'));run=subprocess.run(['/Applications/FreeCAD.app/Contents/Resources/bin/gmsh',str(p),'-0','-v','3'],capture_output=True,text=True);log=run.stdout+'\n'+run.stderr;(R/'cad/build_logs/features.txt').write_text(log);vals={int(i):float(v) for i,v in re.findall(r'FEATURE (\d+) ([-+\deE.]+)',log)}
for i,(pid,name,shape,expected) in enumerate(cases):results.append(dict(part=pid,name=name,expected_probe_volume_mm3=expected,actual_probe_volume_mm3=vals.get(i),passed=i in vals and abs(vals[i]-expected)<.002))
(R/'feature_validation.json').write_text(json.dumps({'checks':results,'finished':'FEATURES_FINISHED' in log,'scale_factor':1,'errors':[l for l in log.splitlines() if l.startswith('Error')]},indent=2));print(json.dumps(results,indent=2));assert run.returncode==0 and all(x['passed'] for x in results)
