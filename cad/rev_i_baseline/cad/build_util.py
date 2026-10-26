"""One-batch rover prototype: local fit changes to actual Rev F solids.

Millimetres, rigid transforms only. Purchased hardware is validation geometry,
never a printed part. Physical fit and printer performance cannot be certified
by these numerical tests.
"""
from pathlib import Path
import sys,json,shutil,subprocess,re,math,hashlib,concurrent.futures

ROOT=Path(__file__).resolve().parent.parent
GM='/Applications/FreeCAD.app/Contents/Resources/bin/gmsh'
sys.path.insert(0,str(ROOT/'cad'))
from design import GeoWriter,box,rr,cyl,hexprism,cut,fuse,face,rot,tr
from mesh_utils import orient_stl,read_triangles

class Writer(GeoWriter):
    def emit(self,s):
        if s['op']=='import':
            var=self.new()+'()'
            self.lines.append(f'{var}=ShapeFromFile("{ROOT/s["path"]}");')
            return var
        return super().emit(s)

def imported(pid):return dict(op='import',path=f'input_step/{pid}.step')

def wheel_tools():
    # Envelope being cleared: X=±20..108, |Y|>=40, Z<=25.
    # Rounded openings extend 3 mm beyond that budget in X and Z.
    return [face(rr(94,88,52,3),x,side*40,-16,'left' if side>0 else 'right')
            for x in [-64,64] for side in [-1,1]]

def foot():
    # Fits in the clear central 78 mm width. Ties can reach the observed
    # bumper slots; the optional screw slot does not assume a hole map.
    body=rr(36,16,8,3)
    tools=[cyl(3.4,10,10,0,-1),hexprism(5.8,2.8,x=10,z=0),
           rr(18,8,10,2,x=-6,z=-1)]
    tools += [rr(6,3,10,1.4,x=13,y=y,z=-1) for y in [-6,6]]
    return cut(body,*tools)

def speaker_cage():
    # Rear crossbar is outside the 20 mm speaker budget. The bottom edge
    # clears the 25 mm tyre keepout; two upper posts retain the cage.
    frame=cut(rr(90,48.5,2.5,5,y=-5.75),rr(66,32.5,4,1,y=-1.75,z=-.5))
    return cut(fuse(frame,box(70,10,2.5,-35,-5,0),
                    *[cyl(7,25,x,-26,0) for x in [-40,40]]),
               *[cyl(3.4,27,x,-26,-1) for x in [-40,40]])

def esp_carrier():
    plate=cut(rr(50,64,3,3,x=-78,y=25,z=57),
              rr(30,44,5,2,x=-78,y=25,z=56),
              *[rr(38,3.4,5,1.6,x=-78,y=y,z=56) for y in [0,50]],
              *[rr(3.4,8,5,1.6,x=x,y=y,z=56)
                for x in [-98,-58] for y in [15,35]])
    points=[(x,y) for x in [-90,-60] for y in [0,50]]
    return cut(fuse(plate,*[cyl(9,10.1,x,y,47) for x,y in points]),
               *[cyl(3.4,15,x,y,46) for x,y in points])

def shape(pid):
    old=imported(pid)
    if pid in ['B01','B02']:
        side=1 if pid=='B01' else -1
        # New crossbeam and feet use X=±110,Y=±30, inside the wheel gap.
        beam=box(9.4,79,4,106 if side>0 else -115.4,-39.5,8)
        body=cut(fuse(old,beam),*wheel_tools(),
                 *[cyl(3.4,7,side*110,y,7) for y in [-30,30]])
        ports=[box(7,3.4,10,110 if side>0 else -117,y+d-1.7,7)
               for y in [-30,30] for d in [-6,6]]
        if pid=='B01':
            # More room for actual speaker solder tabs, with no outer-wall
            # cut beyond the wheel opening.
            ports += [box(13,22.2,16,91,43 if s>0 else -65.2,39) for s in [-1,1]]
        else:
            ports.append(box(42,14,28,-99,57,50))
        return cut(body,*ports)
    if pid=='B04':
        # Clear the upper USB service notch without changing lid thickness.
        return cut(old,box(44,8,4,-100,59,74))
    if pid=='B06':return esp_carrier()
    if pid=='B07':
        return cut(old,box(84,44,8,-90,-22,4),
                   box(38,18,10,-119,22,-1),box(38,18,10,-119,-40,-1))
    if pid=='B08':
        # Increase the internal display opening while keeping outer head.
        return cut(old,box(12,66,31,88,-33,145))
    if pid=='B09':
        # A flat strap seat avoids a guessed buzzer diameter or ear pitch.
        body=cut(old,box(3.1,56,42,30,-28,117))
        slots=[face(rr(3.4,18,8,1.6),26,y,138) for y in [-29,29]]
        return cut(body,*slots)
    if pid=='B10':
        cuts=[box(16,14,10,80,y-7,112.5) for y in [-27,27]]
        cuts += [box(10.3,3.2,1.4,88,y,145) for y in [-8.6,5.4]]
        cuts += [face(rr(25.5,15.2,5,.5),97,0,161.75)]
        return cut(old,*cuts)
    if pid=='B11':return speaker_cage()
    if pid=='B12':
        tools=[]
        for y in [0,30]:
            tools += [box(5,19.3,12.3,-122,y-9.65,20.85),
                      box(1.3,23,16,-119.2,y-11.5,19)]
        return cut(old,*tools)
    if pid=='B13':return foot()
    return old

CHANGED={'B01','B02','B04','B06','B07','B08','B09','B10','B11','B12','B13'}

def run(name,lines):
    p=ROOT/'verification'/f'{name}.geo'
    p.write_text('\n'.join(lines)+'\n')
    r=subprocess.run([GM,str(p),'-0','-v','3'],capture_output=True,text=True)
    log=r.stdout+'\n'+r.stderr
    (ROOT/'verification'/f'{name}.log').write_text(log)
    assert r.returncode==0 and 'Error' not in log and 'COMPLETE' in log,log[-4000:]
    return log

def transform_print(pid,p):
    x,y,z=p
    if pid in ['B04','B06']:return (x,-y,-z)
    if pid in ['B08','B09','B10R','B12']:return (y,z,x)
    if pid=='B10':return (y,-z,-x)
    return (x,y,z)

def write_print_mesh(pid,path):
    raw=read_triangles(path)
    transformed=[[transform_print(pid,p) for p in tri] for tri in raw]
    mins=[min(p[i] for t in transformed for p in t) for i in range(3)]
    lines=['solid rover_mm']
    for tri in transformed:
        lines += ['facet normal 0 0 0','outer loop']
        for p in tri:lines.append('vertex '+' '.join(f'{p[i]-mins[i]:.9g}' for i in range(3)))
        lines += ['endloop','endfacet']
    lines.append('endsolid rover_mm');path.write_text('\n'.join(lines)+'\n')
    return orient_stl(path)

def build(r):
    pid=r['id'];w=Writer();v=w.emit(shape(pid))
    step=ROOT/'master_step'/f'{pid}.step'
    mesh=ROOT/'verification'/f'{pid}.stl'
    w.lines += [f'bb()=BoundingBox Volume{{{v}}};',f'Printf("SOLIDS %g",#{v});',
                'Printf("BOUNDS %.9g %.9g %.9g %.9g %.9g %.9g",bb(0),bb(1),bb(2),bb(3),bb(4),bb(5));',
                f'mass=0;','For k In {0:#'+v+'-1}',f'mass+=Mass Volume{{{v.replace("()","(k)")}}};','EndFor',
                'Printf("MASS %.9g",mass);',f'Save "{step}";',
                'Mesh.MeshSizeMin=.65; Mesh.MeshSizeMax=3; Mesh.MeshSizeFromCurvature=24; Mesh.Binary=0;',
                'Mesh 2;',f'Save "{mesh}";','Printf("COMPLETE");']
    log=run('build_'+pid,w.lines)
    assert re.search(r'SOLIDS 1\b',log),pid
    bounds=list(map(float,re.search(r'BOUNDS ([-+eE\d. ]+)',log)[1].split()))
    mass=float(re.search(r'MASS ([-+eE\d.]+)',log)[1])
    topology=orient_stl(mesh)
    assert topology['surface_components']==1,topology
    printable=ROOT/'verification'/f'{pid}_print.stl';shutil.copy2(mesh,printable)
    print_topology=write_print_mesh(pid,printable)
    triangles=read_triangles(printable)
    sizes=[round(max(v[i] for t in triangles for v in t)-min(v[i] for t in triangles for v in t),3) for i in range(3)]
    result=dict(id=pid,name=r['name'],quantity=r['quantity'],step=str(step.relative_to(ROOT)),
                bounds=bounds,volume_mm3=mass,solid_count=1,mesh=topology,
                print_dimensions_mm=sizes,print_mesh=str(printable.relative_to(ROOT)),
                source_sha256=hashlib.sha256((ROOT/'input_step'/f'{pid}.step').read_bytes()).hexdigest(),
                geometry_changed=pid in CHANGED)
    print(pid,'built',sizes,flush=True)
    return result

def placement(pid,index=0):
    if pid=='B11':
        item=imported(pid)
        if index:item=rot(item,[0,0,1],180)
        return tr(rot(item,[1,0,0],90 if index else -90),60,-40.2 if index else 40.2,47)
    if pid=='B13':
        x,y=[(100,30),(100,-30),(-100,30),(-100,-30)][index]
        item=imported(pid)
        if x<0:item=rot(item,[0,0,1],180)
        return tr(item,x,y,0)
    return imported(pid)

def export_instances(records):
    instances=[];lines=['SetFactory("OpenCASCADE");'];serial=0
    for r in records:
        pid=r['id']
        for index in range(r['quantity']):
            name=pid if r['quantity']==1 else pid+'_'+str(index+1)
            serial+=1
            # Temporarily point the import operation at the built master.
            tree=placement(pid,index)
            def replace(s):
                if s['op']=='import':s['path']=r['step']
                for key in ['item']:
                    if key in s:replace(s[key])
                for item in s.get('items',[]):replace(item)
            replace(tree);w=Writer();v=w.emit(tree)
            target=ROOT/'positioned_step'/f'{name}.step'
            w.lines += [f'Save "{target}";','Printf("COMPLETE");'];run('place_'+name,w.lines)
            stl=ROOT/'PRINT_ALL'/f'{serial:02d}_{name}.stl'
            shutil.copy2(ROOT/r['print_mesh'],stl)
            lines += [f'p{serial}()=ShapeFromFile("{target}");',f'Physical Volume("{name}")={{p{serial}()}};']
            instances.append(dict(id=name,master=pid,step=str(target.relative_to(ROOT)),print_file=str(stl.relative_to(ROOT)),quantity_in_file=1))
    lines += [f'Save "{ROOT}/Rover_RevG_Assembly.step";','Printf("COMPLETE");']
    run('assembly_export',lines)
    (ROOT/'instances.json').write_text(json.dumps(instances,indent=2)+'\n')
    return instances
