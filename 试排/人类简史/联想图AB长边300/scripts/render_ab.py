"""A/C trial refinement. All geometry in logical pixels; skill unchanged."""
from pathlib import Path
import importlib.util,json,math
from PIL import Image,ImageDraw
OUT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('base',OUT.parent/'v1/scripts/render.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
SOURCE=b.BASE;b.BASE=OUT
REASONS=['从自然选择出发，\n理解人类演化','从基因视角，\n对照文化的作用','从地理与环境，\n解释文明差异','延伸历史视野，\n追问科技与未来']
LONG_EDGE=300;STROKE=2;RADIUS=24
GEOMETRY={}
def cover(p,book,cx,y,w):return p.cover(str(SOURCE/book['cover']),cx,y,width=w,tag=book['title']+'封面')
def related_cover(p,book,cx,y):
 im=Image.open(SOURCE/book['cover']).convert('RGB')
 ratio=LONG_EDGE/max(im.size);w=round(im.width*ratio);h=round(im.height*ratio)
 x=cx-w/2
 p.im.paste(im.resize((w*b.S,h*b.S),Image.Resampling.LANCZOS),b.xy((x,y)))
 box=(x,y,x+w,y+h);p.register(box,book['title']+'封面')
 assert max(w,h)==300
 return box
def height(book,w):
 im=Image.open(SOURCE/book['cover']);return round(w*im.height/im.width)
def textbook(p,book,box,reason):
 cx=(box[0]+box[2])/2;w=226
 th=p.text(book['title'],cx-w/2,box[3]+20,w,26,'Bold',align='center',lh=36,tag='related title')
 p.text(reason,cx-w/2,box[3]+20+th+12,w,26,align='center',lh=36,tag='reason')
def line(p,pts):
 samples=[]
 for a,z in zip(pts,pts[1:]):
  for i in range(101):samples.append((a[0]+(z[0]-a[0])*i/100,a[1]+(z[1]-a[1])*i/100))
 p.line(samples,width=STROKE);p.paths.append(samples)
def arc(p,c,start,end):
 pts=[(c[0]+RADIUS*math.cos(math.radians(start+(end-start)*i/48)),c[1]+RADIUS*math.sin(math.radians(start+(end-start)*i/48))) for i in range(49)]
 line(p,pts)
def a():
 p=b.Page('A_圆角正交放射');b.title(p,b.C['association_title'])
 center=(540,730);main=cover(p,b.C['book'],540,730-height(b.C['book'],360)/2,360)
 p.text(b.C['book']['title'],360,main[3]+22,360,32,'Bold',align='center',tag='main title')
 p.text(b.C['book']['author'],360,main[3]+70,360,32,align='center',tag='main author')
 centers=[(180,570),(890,400),(900,890),(190,1060)]
 for book,c,reason in zip(b.C['related'],centers,REASONS):
  box=related_cover(p,book,c[0],c[1]-LONG_EDGE/2);textbook(p,book,box,reason)
 reflect=lambda v:(1080-v[0],1460-v[1])
 # Paired paths retain 180-degree symmetry; endpoints stop outside both paired covers.
 line(p,[(360,570),(282,570)])
 line(p,[(720,890),(798,890)])
 line(p,[(660,main[1]),(660,424)])
 arc(p,(684,424),180,270)
 line(p,[(684,400),(777,400)])
 line(p,[(420,main[3]),(420,1036)])
 arc(p,(396,1036),0,90)
 line(p,[(396,1060),(303,1060)])
 for i,j in [(0,2),(1,3)]:assert reflect(centers[i])==centers[j]
 for i,j in [(0,1),(2,5),(3,6),(4,7)]:
  assert all(math.dist(reflect(v),w)<1e-6 for v,w in zip(p.paths[i],p.paths[j]))
 GEOMETRY['A']={'symmetry_center':center,'cover_centers':centers,'corner_radius':RADIUS,'symmetry_checks':'passed','line_paths':p.paths}
 p.save();return p.im

def c():
 p=b.Page('B_无箭头正交分支');b.title(p,b.C['association_title'])
 main=cover(p,b.C['book'],540,250,360)
 p.text(b.C['book']['title'],750,680,282,32,'Bold',tag='main title')
 p.text(b.C['book']['author'],750,730,282,32,tag='main author')
 centers=[171,417,663,909]
 for book,x,reason in zip(b.C['related'],centers,REASONS):
  box=related_cover(p,book,x,900);textbook(p,book,box,reason)
 # One shared stem. Each arc is a true quarter circle of radius 24.
 line(p,[(540,main[3]),(540,816)])
 arc(p,(516,816),0,90);arc(p,(564,816),180,90)
 line(p,[(195,840),(516,840)]);line(p,[(564,840),(885,840)])
 for x in centers:
  if x<540:arc(p,(x+24,864),270,180)
  else:arc(p,(x-24,864),270,360)
  line(p,[(x,864),(x,900)])
 GEOMETRY['B']={'shared_stem':[[540,main[3]],[540,816]],'branch_y':840,'corner_radius':RADIUS,'cover_centers_x':centers,'cover_top':900,'line_end_y':900,'arrows':False,'symmetry_axis_x':540}
 assert all(centers[i]+centers[3-i]==1080 for i in range(4))
 p.save();return p.im
if __name__=='__main__':
 ims=[a(),c()]
 sheet=Image.new('RGB',(1128,784),'#EFF2F5');d=ImageDraw.Draw(sheet)
 for i,(im,label) in enumerate(zip(ims,['A 错位放射 · 封面高300px','B 共用主干 · 封面高300px'])):
  x=16+i*556;d.text((x+8,16),label,font=b.font(14,'Bold'),fill=b.INK)
  sheet.paste(im.resize((540,720),Image.Resampling.LANCZOS),(x,56))
 sheet.save(OUT/'AB长边版对比.png')
 for name,im in zip(['A','B'],ims):im.resize((360,480),Image.Resampling.LANCZOS).save(OUT/(name+'_手机预览.png'))
 (OUT/'布局配置.json').write_text(json.dumps({'canvas':[1080,1440],'related_cover_long_edge':LONG_EDGE,'main_cover_width':360,'line_width':STROKE,'geometry':GEOMETRY,'related_reasons':REASONS},ensure_ascii=False,indent=2))
 (OUT/'排版检查.json').write_text(json.dumps(b.REPORT,ensure_ascii=False,indent=2))
 print(json.dumps(b.REPORT,ensure_ascii=False,indent=2))
