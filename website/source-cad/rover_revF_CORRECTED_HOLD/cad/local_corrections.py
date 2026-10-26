"""Rev F: only the microphone mounting region changes; all lengths millimetres."""
from pathlib import Path
from design import GeoWriter,box,rr,cyl,cut,fuse,face
ROOT=Path(__file__).resolve().parent.parent
class ImportWriter(GeoWriter):
 def emit(self,s):
  if s['op']=='import':
   n=self.new()+'()';self.lines.append(n+'=ShapeFromFile("'+(ROOT/s['path']).as_posix()+'");');return n
  return super().emit(s)
def cone_x(r1,r2,h,x,y,z):return dict(op='cone',radius=r1,radius2=r2,pos=[x,y,z],vector=[h,0,0])
def corrected(r):
 old={'op':'import','path':r['step']}
 if r['id']!='B10':return old
 # Remove the old cup, transition, ears and short supporting-arm sections only.
 retained=cut(old,box(14.6,42,31.2,71.5,-21,116))
 cup=cut(cyl(21.2,6,72,0,132,axis=(1,0,0)),cyl(15.2,3.3,71.9,0,132,axis=(1,0,0)),cyl(7,3.1,75.1,0,132,axis=(1,0,0)))
 pieces=[retained,cup]
 # Existing front duct remains Ø3 to preserve the narrow inter-sonar web.
 pieces.append(cut(cone_x(10.6,4,8.3,77.9,0,132),cone_x(3.5,1.5,8.3,77.9,0,132)))
 for y in [-16,16]:
  ear=face(rr(8.4,14,3,2),72,y,132)
  pieces.append(cut(ear,face(rr(3.4,8,5,1.6),71,y,132)))
 for y in [-14,10]:pieces.append(box(3,4,6,72,y,129))
 for y in [-8.5,5.5]:
  pieces.append(box(4,3,7.65,75.2,y,138))
  pieces.append(box(10.1,3,3,76.2,y,142.65))
 return fuse(*pieces)
