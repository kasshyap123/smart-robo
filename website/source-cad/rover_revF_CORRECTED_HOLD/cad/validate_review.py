from pathlib import Path
import json,subprocess,re,itertools,math,sys
import numpy as np
import os
ROOT=Path(__file__).resolve().parent.parent;GM=os.environ.get('GMSH_EXECUTABLE','/Applications/FreeCAD.app/Contents/Resources/bin/gmsh')
sys.path.insert(0,str(ROOT/'cad'));from design import GeoWriter,box,cyl
from mesh_utils import read_triangles
for folder in ['cad/generated','cad/build_logs','preview']:(ROOT/folder).mkdir(parents=True,exist_ok=True)
records=json.loads((ROOT/'parts_manifest.json').read_text());parts=[];lines=['SetFactory("OpenCASCADE");','Geometry.OCCBoundsUseStl=1;']
def load_stl(path):
    tris=np.array(read_triangles(path))
    verts,idx=np.unique(np.round(tris.reshape(-1,3),5),axis=0,return_inverse=True)
    faces=idx.reshape(-1,3)
    edges=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]);edges=np.sort(edges,axis=1)
    edge_set,counts=np.unique(edges,axis=0,return_counts=True)
    directed=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]);du,dc=np.unique(directed,axis=0,return_counts=True)
    inconsistent=int(np.sum(dc!=1))
    # Mesh volume is independently calculated from oriented triangles.
    signed=np.sum(np.einsum('ij,ij->i',tris[:,0],np.cross(tris[:,1],tris[:,2])))/6
    return verts,faces,dict(triangles=len(tris),inconsistent_directed_edges=inconsistent,boundary_edges=int(np.sum(counts==1)),nonmanifold_edges=int(np.sum(counts>2)),absolute_mesh_volume_mm3=abs(float(signed)),weld_tolerance_mm=1e-5)
mesh=[];checks=[]
for r in records:
    verts,faces,check=load_stl(ROOT/r['stl']);check['id']=r['id'];check['cad_volume_mm3']=r['volume_mm3'];check['volume_relative_error']=abs(check['absolute_mesh_volume_mm3']-r['volume_mm3'])/r['volume_mm3'];checks.append(check)
    base=verts.copy()
    for index,cp in enumerate(r['copies']):
        v=base.copy();x,y,z,angle=cp
        if angle:
            t=math.radians(angle);co=math.cos(t);si=math.sin(t)
            rot=np.array([[1,0,0],[0,co,-si],[0,si,co]]) if r['id']=='B11' else np.array([[co,-si,0],[si,co,0],[0,0,1]])
            v=v@rot.T
        v+=np.array([x,y,z]);name=r['id']+'_'+str(index+1);var='p'+str(len(parts));lines.append(f'{var}()=ShapeFromFile("{(ROOT/r["step"]).as_posix()}");')
        if angle:lines.append('Rotate{{'+('1,0,0' if r['id']=='B11' else '0,0,1')+'},{0,0,0},'+str(math.radians(angle))+'}{Volume{'+var+'()};}')
        if x or y or z:lines.append(f'Translate{{{x},{y},{z}}}{{Volume{{{var}()}};}}')
        lines.append(f'Physical Volume("{name}")={{{var}()}};')
        parts.append(dict(id=name,var=var,bounds=[*v.min(0),*v.max(0)]))
        mesh.append(dict(id=name,name=r['name'],role='baseline',kind=r['id'],vertices=v.tolist(),local_vertices=base.tolist(),faces=faces.tolist()))
lines.append(f'Save "{(ROOT/"cad/generated/reference_from_masters.step").as_posix()}";')
# Keep validation booleans in a separate script so the assembly contains only the 18 intended instances.
validation=lines[:-1].copy();pairs=[]
for a,b in itertools.combinations(parts,2):
    ab=a['bounds'];bb=b['bounds'];over=[min(ab[i+3],bb[i+3])-max(ab[i],bb[i]) for i in range(3)]
    if min(over)>0.001:
        tag='q'+str(len(pairs));pairs.append((a['id'],b['id']))
        validation.append(f'{tag}()=BooleanIntersection{{Volume{{{a["var"]}()}};}}{{Volume{{{b["var"]}()}};}};')
        validation.append(f'If (#{tag}()>0) mass=0; For i In {{0:#{tag}()-1}} mass+=Mass Volume{{{tag}(i)}}; EndFor Printf("OVERLAP {a["id"]} {b["id"]} %.9g",mass); Recursive Delete{{Volume{{{tag}()}};}} EndIf')
# Real-hardware nominal envelopes: nothing here is a pretend detailed board model.
hw=[('B05_L298N_candidate_43x43x27',box(43,43,27,-49,5,49)),
 ('B05_LM2596_45x21_budget',box(45,21,18,-100.5,-45.5,56)),
 ('B05_PAM8403_21x18_budget',box(21,18,10,-34.5,-39,56)),
 ('B06_ESP32_28x55_budget',box(28,55,12,-92,-2.5,56)),
 ('holder_supplied_approximation',box(77.1,39.8,14.9,-86.55,-19.9,4)),
 ('speaker_left',box(70,6.5,40,25,58.2,27)),('speaker_right',box(70,6.5,40,25,-64.7,27)),
 ('head_sonar_left',box(15,45,20,86.8,4.5,122)),('head_sonar_right',box(15,45,20,86.8,-49.5,122)),
 ('microphone_user_nominal_14mm',cyl(14,1.5,73.7,0,132,axis=(1,0,0))),
 ('microphone_component_budget',cyl(10,2.5,71.2,0,132,axis=(1,0,0))),
 ('microphone_rear_wire_budget',box(15,14,14,57,-7,125)),
 ('OLED_PCB_reference',box(1.5,27.3,27.3,93,-13.65,146.172)),
 ('OLED_glass_reference',box(2.72,26.7,19.26,94.5,-13.35,150.192)),
 ('OLED_rear_components_budget',box(1.5,27.3,27.3,91.5,-13.65,146.172)),
 ('OLED_header_budget',box(10,10.16,2.54,83,-5.08,170.552)),
 ('OLED_active_area_optical_corridor',box(5,21.744,11.204,97,-10.872,156.148)),
 ('buzzer',cyl(30,15,33,0,138,axis=(1,0,0))),
 ('rear_connector_budget',box(24,84,22,-115.2,-42,16)),('usb_service_corridor',box(32,55,18,-94,58,54))]
for hname,shape in hw:
    writer=GeoWriter();writer.i=10000+hw.index((hname,shape))*100
    hvar=writer.emit(shape);validation.extend(writer.lines[2:])
    for part in parts:
        tag='ht'+str(len(validation))
        validation.append(f'{tag}()=BooleanIntersection{{Volume{{{part["var"]}()}};}}{{Volume{{{hvar}}};}};')
        validation.append(f'If (#{tag}()>0) mass=0; For i In {{0:#{tag}()-1}} mass+=Mass Volume{{{tag}(i)}}; EndFor Printf("HARDWARE {hname} {part["id"]} %.9g",mass); Recursive Delete{{Volume{{{tag}()}};}} EndIf')
    validation.append(f'Recursive Delete{{Volume{{{hvar}}};}}')
validation.append('Printf("VALIDATION_FINISHED");')
for name,content in [('assembly','\n'.join(lines)),('collision','\n'.join(validation))]:
    path=ROOT/'cad/generated'/f'{name}.geo';path.write_text(content.replace(' mass=0; For ', '\nmass=0;\nFor ').replace('} mass+=', '}\nmass+=').replace('; EndFor', ';\nEndFor\n'))
    proc=subprocess.run([GM,str(path),'-0','-v','3'],capture_output=True,text=True)
    log=proc.stdout+'\n'+proc.stderr;(ROOT/'cad/build_logs'/f'{name}.txt').write_text(log)
    print(name,proc.returncode,flush=True)
log=(ROOT/'cad/build_logs/collision.txt').read_text()
collisions=[ln for ln in log.splitlines() if ln.startswith(('OVERLAP','HARDWARE','Error'))]
(ROOT/'preview/geometry.json').write_text(json.dumps(mesh,separators=(',',':')))
out=dict(mesh_checks=checks,positive_volume_collisions=collisions,finished='VALIDATION_FINISHED' in log,physical_fit_verified=False,print_release='BLOCKED',chassis_reference_mm=[255,148,3],baseline_printed_pieces=18,distinct_core_designs=14,hardware_envelope_scope=[x[0] for x in hw],exclusions=['Exact chassis hole pattern / outline and wheel/motor locations','Unmeasured boards and connected plugs','Fasteners and insulation','Thermal / strength / print / physical stability tests'])
out['planning_only_envelopes']=['OLED and microphone use latest supplied nominal references. Microphone PCB thickness 1.5, component depth 2.5 and rear wire space 15 × 14 × 14 mm are adjustable installation assumptions. OLED glass forward depth 2.72 and header budget 10 mm are conservative space checks; confirm connected hardware. L298N is a candidate, not purchased/verified.']
(ROOT/'validation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
