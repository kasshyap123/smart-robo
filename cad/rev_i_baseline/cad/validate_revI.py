from pathlib import Path
import sys,json,subprocess,re,itertools,concurrent.futures,hashlib
import numpy as np
R=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(R/'cad'))
from design import GeoWriter,box,cyl,face,hexprism
from mesh_utils import read_triangles
GM='/Applications/FreeCAD.app/Contents/Resources/bin/gmsh'
instances=json.loads((R/'instances.json').read_text())
parts=json.loads((R/'parts.json').read_text())
paths={p['id']:R/p['step'] for p in instances}

def load(names):
 return ['SetFactory("OpenCASCADE");']+[f'{n}()=ShapeFromFile("{paths[n]}");' for n in names]
def emit(lines,shape):
 w=GeoWriter();w.i=50000+len(lines)*100;q=w.emit(shape);lines.extend(w.lines[2:]);return q
def intersect(lines,a,b,label):
 q='q'+str(len(lines))+'()'
 lines.extend([q+'=BooleanIntersection{Volume{'+a+'};}{Volume{'+b+'};};',
 'mass=0;','If (#'+q+'>0)','For k In {0:#'+q+'-1}',
 'mass+=Mass Volume{'+q.replace('()','(k)')+'};','EndFor',
 'If (mass>0.0001)',f'Printf("FAIL {label} %.12g",mass);','EndIf',
 'Recursive Delete{Volume{'+q+'};}','EndIf'])
def run(name,lines):
 lines.append('Printf("COMPLETE");')
 p=R/'verification'/f'{name}.geo';p.write_text('\n'.join(lines)+'\n')
 r=subprocess.run([GM,str(p),'-0','-v','3'],capture_output=True,text=True)
 log=r.stdout+'\n'+r.stderr;(R/'verification'/f'{name}.log').write_text(log)
 failures=[x for x in log.splitlines() if x.startswith(('FAIL','Error'))]
 return dict(check=name,passed=r.returncode==0 and 'COMPLETE' in log and not failures,failures=failures)

oled=[box(1.5,29,29,93,-14.5,145.322),box(2.72,26.7,19.26,94.5,-13.35,150.192),
 box(1.5,29,29,91.5,-14.5,145.322),box(10,10.16,2.54,83,-5.08,170.552)]
head=oled+[box(15,45,20,86.8,4.5,122),box(15,45,20,86.8,-49.5,122),
 cyl(14,1.5,73.7,0,132,axis=(1,0,0)),cyl(10,2.5,71.2,0,132,axis=(1,0,0)),box(15,14,14,57,-7,125)]
tray=[box(44,44,28,-49.5,4.5,49),box(45,21,18,-100.5,-45.5,56),box(21,18,10,-34.5,-39,56),
 box(28,55,12,-92,-2.5,63)]
battery=box(83,43,28,-89.5,-21.5,4)
hw=[('L298N_44x44x28',tray[0]),('LM2596_45x21x18',tray[1]),('PAM8403_21x18x10',tray[2]),
 ('ESP32_28x55x12_above_board',tray[3]),('ESP32_underpins_12mm',box(27,38,12,-91.5,6,51)),
 ('loaded_holder_83x43x28',battery),('speaker_left_70x40x20',box(70,20,40,25,45.2,27)),
 ('speaker_right_70x40x20',box(70,20,40,25,-65.2,27)),
 ('speaker_tabs_left',box(8,18,12,95,45.2,41)),('speaker_tabs_right',box(8,18,12,95,-63.2,41)),
 ('head_sonar_left',head[4]),('head_sonar_right',head[5]),('mic_pcb_14x1.5',head[6]),
 ('mic_rear_components',head[7]),('mic_wire_header_space',head[8])]
hw += [('OLED_'+str(i),x) for i,x in enumerate(oled)]
hw += [('OLED_active_optical_corridor',box(5,21.744,11.204,97,-10.872,156.148)),
 ('buzzer_body_D40x24',cyl(40,24,32,0,138,axis=(1,0,0))),
 ('buzzer_ears_52x46',box(2,52,46,32,-26,115)),
 ('rear_switch_connector_space',box(24,84,22,-115.2,-42,16)),
 ('USB_plug_access',box(32,55,20,-94,58,56))]
budgets=json.loads((R/'POWER_BAY_BUDGETS.json').read_text())['boards']
hw += [(b['id'],box(*b['size_mm'],*b['origin_mm'])) for b in budgets]
hw += [('power_bay_wire_turn',box(20,12,18,77,-9,39)),
       ('driver_upper_clearance',box(42,42,8,-48.5,5.5,77)),
       ('driver_terminal_lane_front',box(5,44,14,-5.5,4.5,51)),
       ('driver_terminal_lane_rear',box(3,40,12,-52.5,6.5,51))]
hw += [(f'ESP_female_row_{x}',box(4,38,20,x-2,6,43)) for x in [-91,-65]]
hw += [(f'ESP_lower_wire_turn_{x}',box(5,36,6,x-2.5,7,37)) for x in [-91,-65]]
hw += [(f'HC_header_{y}',box(10,14,9,78,y-7,113)) for y in [-27,27]]
hw += [(f'wheel_{x}_{side}',box(88,50,95,20 if x>0 else -108,40 if side>0 else -90,-70))
 for x in [-1,1] for side in [-1,1]]

harness=[cyl(8,42,87,-3,27),dict(op='cylinder',radius=4,pos=[87,-3,69],vector=[-23,3,0]),cyl(8,50,64,0,69),cyl(8,15,64,0,119,axis=(0,1,0)),cyl(8,35,64,15,119)]
hw += [('head_harness_segment_'+str(i),x) for i,x in enumerate(harness)]

def collisions():
 names=list(paths);lines=load(names)
 for a,b in itertools.combinations(names,2):intersect(lines,a+'()',b+'()',a+'_'+b)
 for label,shape in hw:
  q=emit(lines,shape)
  for n in names:intersect(lines,n+'()',q,label+'_'+n)
  lines.append('Recursive Delete{Volume{'+q+'};}')
 result=run('assembled_collisions',lines);result.update(printed_pairs=171,hardware_envelopes=[x[0] for x in hw],hardware_part_checks=len(hw)*19)
 return result

def interfaces():
 names=list(paths);lines=load(names);count=0
 def probe(label,ns,x,y,z,h,axis=(0,0,1),d=3.2):
  nonlocal count
  count+=1;q=emit(lines,cyl(d,h,x,y,z,axis))
  for n in ns:intersect(lines,n+'()',q,label+'_'+n)
 for x in [-108,-12]:
  for y in [-62,62]:probe('lid', ['B02','B04'],x,y,67,15)
 for x in [9,111]:
  for y in [-62,62]:probe('deck',['B01','B03'],x,y,67,15)
 for x in [-94,-26]:
  for y in [-60,60]:probe('tray',['B02','B05'],x,y,37,11)
 for x in [-90,-60]:
  for y in [0,50]:probe('ESP',['B05','B06'],x,y,43,18)
 for x in [41,87]:
  for y in [-23,23]:probe('neck',['B03','B08'],x,y,104,9)
 for y in [-48,48]:
  for z in [117,171]:probe('rear_head',['B08','B09'],26,y,z,15,(1,0,0))
  for z in [113,175]:probe('visor',['B08','B10'],89,y,z,13,(1,0,0))
 for y in [-46,46]:
  for z in [12,42]:probe('switch_panel',['B02','B12'],-122,y,z,8,(1,0,0))
 for z in [43,55]:probe('shell_seam',['B01','B02'],7,-70,z,140,(0,1,0))
 for x in [20,100]:probe('speaker_upper',['B01','B11_1','B11_2'],x,-70,73,140,(0,1,0))
 for i,(x,y) in enumerate([(110,30),(110,-30),(-110,30),(-110,-30)]):
  probe('foot',['B01' if x>0 else 'B02',f'B13_{i+1}'],x,y,-1,14)
 for y in [-27,27]:probe('OLED_rail',['B10','B10R'],87,y,161,10.5,(1,0,0))
 for hp in [23,24,25]:
  for vp in [23,24,25]:
   for y in [-hp/2,hp/2]:
    for z in [159.822-vp/2,159.822+vp/2]:probe('OLED_slotted_M2',['B10R'],87,y,z,5,(1,0,0),2.5)
 for x in [8,110]:
  for y in [-33,33]:probe('power_tray',['B01' if x>50 else 'B05','B14'],x,y,28,12)
 result=run('fastener_axes',lines);result['axis_count']=count;return result

cases=[('lid_lift',['B04'],[],['B01','B02','B03'],(0,0,1),15,1),
 
 ('populated_visor_forward',['B10','B10R'],head,['B08','B03'],(1,0,0),40,2),
 ('populated_OLED_up',['B10R'],oled,['B10'],(0,0,1),30,2),
 ('head_cover_back',['B09'],[hw[20][1],hw[21][1]],['B08'],(-1,0,0),30,2),
 ('battery_lift',['B07'],[battery],['B01','B02','B03'],(0,0,1),100,5),
 ('ESP_carrier_lift',['B06'],[tray[3]],['B02','B05'],(0,0,1),70,5),
 ('speaker_cage_inward',['B11_1'],[hw[6][1]],['B01'],(0,-1,0),25,1)]
cases.append(('power_tray_lift',['B14'],[box(*b['size_mm'],*b['origin_mm']) for b in budgets],['B01','B02','B05','B06','B11_1','B11_2'],(0,0,1),70,5))
def motion(case):
 name,moving,shapes,fixed,axis,end,step=case;lines=load(moving+fixed);mv=[n+'()' for n in moving]
 mv += [emit(lines,s) for s in shapes]
 for distance in range(0,end+1,step):
  if distance:lines.append('Translate{'+','.join(str(v*step) for v in axis)+'}{Volume{'+','.join(mv)+'};}')
  for a in mv:
   for b in fixed:intersect(lines,a,b+'()',name+'_'+str(distance)+'_'+b)
 result=run(name,lines);result.update(positions=end//step+1,interval_mm=step,travel_mm=end,moving=moving,fixed=fixed)
 return result

def populated_tray_service():
 # Remove B04/B14 and all fasteners/harnesses first. Lift 35 mm, slide
 # 14 mm rearward, then lift out. The rearward step retracts the arms
 # from beneath B03 after the main plate clears the rear shell rim.
 names=['B05','B06'];fixed=['B01','B02','B03'];lines=load(names+fixed)
 mv=[n+'()' for n in names]+[emit(lines,x) for x in tray]
 count=0
 steps=[(0,0,0)]+[(0,0,5)]*7+[(-2,0,0)]*7+[(0,0,5)]*13
 for vector in steps:
  if any(vector):lines.append('Translate{'+','.join(map(str,vector))+'}{Volume{'+','.join(mv)+'};}')
  for a in mv:
   for b in fixed:intersect(lines,a,b+'()','rear_tray_service_'+str(count)+'_'+b)
  count+=1
 result=run('populated_tray_service',lines)
 result.update(positions=count,procedure='Remove rear lid, B14, bolts and harnesses. Lift rear electronics tray 35 mm; translate 14 mm rearward; lift another 65 mm. Discrete samples at 5/2 mm intervals.')
 return result

def meshcheck():
 out=[]
 for p in parts:
  mesh=R/p['print_mesh']
  if not mesh.exists():mesh=R/next(i['print_file'] for i in instances if i['master']==p['id'])
  t=np.array(read_triangles(mesh));verts,idx=np.unique(np.round(t.reshape(-1,3),5),axis=0,return_inverse=True)
  f=idx.reshape(-1,3);edges=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);_,counts=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True)
  _,dc=np.unique(edges,axis=0,return_counts=True)
  vol=float(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6)
  err=abs(vol-p['volume_mm3'])/p['volume_mm3']
  ok=np.all(counts==2) and np.all(dc==1) and vol>0 and err<.005 and np.min(t)>=-1e-5
  out.append(dict(id=p['id'],passed=bool(ok),boundary_edges=int(sum(counts==1)),nonmanifold_edges=int(sum(counts>2)),volume_relative_error=err,signed_volume_mm3=vol))
 return out

def main():
 before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths.values()}
 jobs=[collisions,interfaces,populated_tray_service]+[lambda c=c:motion(c) for c in cases]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  results=[]
  for r in pool.map(lambda f:f(),jobs):results.append(r);print(json.dumps(r),flush=True)
 meshes=meshcheck()
 lines=['SetFactory("OpenCASCADE");',f'a()=ShapeFromFile("{R}/Rover_RevI_Assembly.step");','Printf("ASSEMBLY_SOLIDS %g",#a());']
 assembly=run('assembly_roundtrip',lines)
 log=(R/'verification/assembly_roundtrip.log').read_text();assembly['solid_count']=int(re.search(r'ASSEMBLY_SOLIDS (\d+)',log)[1]);assembly['passed'] &= assembly['solid_count']==19
 same=before=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths.values()}
 out=dict(status='REV_I_GEOMETRY_REVIEW',physical_fit_verified=False,geometry_checks=results,mesh_checks=meshes,assembly=assembly,validation_did_not_change_STEP=same,
  limitations=['New power-board volumes are allocated design budgets, not measurements or electrically selected components. No onboard charger is allocated.', 'Wheel positions and 25 mm rise are conservative design budgets inferred from supplied photos, not a measured survey.','User reports the chassis paper check fits. New internal foot strap passages must still be threaded and checked during installation; no exact acrylic hole map was supplied.','Purchased component envelopes include assumptions. Foam, straps, wiring, fasteners, thermal performance, strength and actual print accuracy are not certified.','Motion checks are discrete CAD samples with the listed covers/fasteners/harnesses first removed; not a continuous sweep proof.'])
 out['all_passed']=all(x['passed'] for x in results+meshes+[assembly]) and same
 (R/'verification/results.json').write_text(json.dumps(out,indent=2)+'\n');print('ALL PASSED',out['all_passed'],flush=True)

if __name__=='__main__':main()
