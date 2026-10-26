"""Make STL winding consistent without changing vertex positions or geometry."""
import struct,math
from collections import defaultdict,deque
from pathlib import Path

def read_triangles(path):
 data=Path(path).read_bytes()
 if len(data)>=84 and len(data)==84+50*struct.unpack_from('<I',data,80)[0]:
  return [[list(struct.unpack_from('<3f',data,84+50*i+12+12*j)) for j in range(3)] for i in range(struct.unpack_from('<I',data,80)[0])]
 verts=[[float(x) for x in ln.split()[1:]] for ln in data.decode().splitlines() if ln.lstrip().startswith('vertex')]
 return [verts[i:i+3] for i in range(0,len(verts),3)]

def orient_stl(path):
 raw=read_triangles(path)
 triangles=[t for t in raw if len({tuple(round(x,5) for x in v) for v in t})==3]
 removed=len(raw)-len(triangles)
 edges=defaultdict(list);keys={};faces=[]
 for i,tri in enumerate(triangles):
  f=[]
  for v in tri:
   key=tuple(round(x,5) for x in v)
   if key not in keys:keys[key]=len(keys)
   f.append(keys[key])
  faces.append(f)
  for a,b in zip(f,f[1:]+f[:1]):edges[min(a,b),max(a,b)].append((i,a<b))
 assert all(len(e)==2 for e in edges.values()),'STL is not a closed two-manifold'
 adj=[[] for _ in faces]
 for e in edges.values():
  (i,a),(j,b)=e;adj[i].append((j,a==b));adj[j].append((i,a==b))
 flip={};components=[]
 for start in range(len(faces)):
  if start in flip:continue
  flip[start]=False;queue=deque([start]);component=[]
  while queue:
   i=queue.popleft();component.append(i)
   for j,toggle in adj[i]:
    want=flip[i]^toggle
    if j in flip:assert flip[j]==want,'Non-orientable mesh'
    else:flip[j]=want;queue.append(j)
  components.append(component)
 for i in flip:
  if flip[i]:triangles[i][1],triangles[i][2]=triangles[i][2],triangles[i][1]
 def volume(tri):
  a,b,c=tri
  return (a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
 # These solids contain no fully enclosed voids; each connected surface faces outward.
 for component in components:
  if sum(volume(triangles[i]) for i in component)<0:
   for i in component:triangles[i][1],triangles[i][2]=triangles[i][2],triangles[i][1]
 with Path(path).open('wb') as fh:
  fh.write(b'Rover RevB millimetres - consistent outward triangle winding'.ljust(80,b' '));fh.write(struct.pack('<I',len(triangles)))
  for a,b,c in triangles:
   u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)];n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];length=math.sqrt(sum(x*x for x in n));n=[x/length for x in n] if length else [0,0,0]
   fh.write(struct.pack('<12fH',*n,*a,*b,*c,0))
 return dict(collapsed_triangles_removed=removed,winding_repaired_triangles=sum(flip.values()),surface_components=len(components),triangle_count=len(triangles))
