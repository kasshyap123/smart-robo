"""CSG primitives for local corrections to imported STEP geometry; millimetres.
The audited original solids are retained in input_step/.
"""
import math

def box(l,w,h,x=0,y=0,z=0):return dict(op='box',size=[l,w,h],pos=[x,y,z])
def cb(l,w,h,z=0):return box(l,w,h,-l/2,-w/2,z)
def rr(l,w,h,r=3,x=0,y=0,z=0):return dict(op='roundbox',size=[l,w,h],radius=r,pos=[x-l/2,y-w/2,z])
def cyl(d,h,x=0,y=0,z=0,axis=(0,0,1)):
 return dict(op='cylinder',radius=d/2,pos=[x,y,z],vector=[a*h for a in axis])
def hexprism(af,h,x=0,y=0,z=0):return dict(op='hexprism',af=af,height=h,pos=[x,y,z])
def cone(d1,d2,h,x=0,y=0,z=0):return dict(op='cone',radius=d1/2,radius2=d2/2,pos=[x,y,z],vector=[0,0,h])
def fuse(*s):return s[0] if len(s)==1 else dict(op='fuse',items=list(s))
def cut(s,*tools):return s if not tools else dict(op='cut',items=[s]+list(tools))
def intersect(a,b):return dict(op='intersect',items=[a,b])
def tr(s,x=0,y=0,z=0):return dict(op='translate',item=s,vector=[x,y,z])
def rot(s,axis,angle):return dict(op='rotate',item=s,axis=axis,angle=angle)
def face(s,x,y,z,side='front'):
 if side=='front':s=rot(s,[1,1,1],120)
 elif side=='rear':s=rot(rot(s,[1,1,1],120),[0,0,1],180)
 elif side=='left':s=rot(s,[1,0,0],-90)
 elif side=='right':s=rot(s,[1,0,0],90)
 return tr(s,x,y,z)
def ring(l,w,h,il,iw,r=2,z=0):return cut(rr(l,w,h,r,z=z),rr(il,iw,h+2,min(r,1),z=z-1))
def holes(points,d,h,z=-1):return [cyl(d,h,x,y,z) for x,y in points]
def sl(length,width,h,x=0,y=0,z=-1):return rr(length,width,h,width/2-.001,x,y,z)
def web_ring(a,b,depth,clear=.4):
 return ring(a+2*clear+5.6,b+2*clear+5.6,depth,a+2*clear,b+2*clear,2,z=-depth+.1)

class GeoWriter:
 def __init__(self):self.lines=['SetFactory("OpenCASCADE");','Geometry.OCCBoundsUseStl = 1;'];self.i=0
 def new(self):self.i+=1;return 's'+str(self.i)
 def emit(self,s):
  op=s['op'];n=self.new();arr=n+'()'
  if op in ['box','cylinder','cone']:
   self.lines.append(n+'=newv;')
   if op=='box':self.lines.append(f'Box({n}) = {{{",".join(map(str,s["pos"]+s["size"]))}}};')
   else:
    args=s['pos']+s['vector']+[s['radius']]+([s['radius2']] if op=='cone' else [])
    self.lines.append(f'{"Cone" if op=="cone" else "Cylinder"}({n}) = {{{",".join(map(str,args))}}};')
   self.lines.append(arr+'={'+n+'};')
  elif op=='hexprism':
   x,y,z=s['pos'];radius=s['af']/math.sqrt(3);pts=[];edges=[]
   for i in range(6):
    pt=n+'p'+str(i);pts.append(pt);ang=i*math.pi/3
    self.lines.append(f'{pt}=newp; Point({pt})={{{x+radius*math.cos(ang)},{y+radius*math.sin(ang)},{z}}};')
   for i in range(6):
    e=n+'l'+str(i);edges.append(e);self.lines.append(f'{e}=newl; Line({e})={{{pts[i]},{pts[(i+1)%6]}}};')
   self.lines.append(n+'cl=newll; Curve Loop('+n+'cl)={'+','.join(edges)+'};')
   self.lines.append(n+'=news; Plane Surface('+n+')={'+n+'cl};')
   self.lines.append(n+'e()=Extrude {0,0,'+str(s['height'])+'} {Surface{'+n+'};};')
   self.lines.append(arr+'={'+n+'e(1)};')
  elif op=='roundbox':
   l,w,h=s['size'];assert min(l,w,h)>0
   self.lines.append(n+'=news;')
   self.lines.append(f'Rectangle({n}) = {{{",".join(map(str,s["pos"]+[l,w,s["radius"]]))}}};')
   self.lines.append(n+'e()=Extrude {0,0,'+str(h)+'} {Surface{'+n+'};};')
   self.lines.append(arr+'={'+n+'e(1)};')
  elif op in ['fuse','cut','intersect']:
   args=[self.emit(x) for x in s['items']];a=args[0];b=','.join(args[1:]);name={'fuse':'BooleanUnion','cut':'BooleanDifference','intersect':'BooleanIntersection'}[op]
   self.lines.append(arr+'='+name+'{Volume{'+a+'}; Delete;}{Volume{'+b+'}; Delete;};')
  elif op in ['translate','rotate']:
   a=self.emit(s['item']);self.lines.append(arr+'={'+a+'};')
   if op=='translate':self.lines.append('Translate{'+','.join(map(str,s['vector']))+'}{Volume{'+arr+'};}')
   else:self.lines.append('Rotate{{'+','.join(map(str,s['axis']))+'},{0,0,0},'+str(s['angle']*math.pi/180)+'}{Volume{'+arr+'};}')
  return arr
