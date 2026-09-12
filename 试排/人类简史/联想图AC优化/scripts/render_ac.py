"""A/C trial refinement. All geometry in logical pixels; skill unchanged."""
from pathlib import Path
import importlib.util,json,math
from PIL import Image,ImageDraw
OUT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('base',OUT.parent/'v1/scripts/render.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
SOURCE=b.BASE;b.BASE=OUT
REASONS=['从自然选择出发，\n理解人类演化','从基因视角，\n对照文化的作用','从地理与环境，\n解释文明差异','延伸历史视野，\n追问科技与未来']
WIDTH=216;STROKE=2;RADIUS=24
GEOMETRY={}
def cover(p,book,cx,y,w):return p.cover(str(SOURCE/book['cover']),cx,y,width=w,tag=book['title']+'封面')
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
 p=b.Page('A_中心对称放射');b.title(p,b.C['association_title'])
 center=(540,730);main=cover(p,b.C['book'],540,730-height(b.C['book'],360)/2,360)
 p.text(b.C['book']['title'],360,main[3]+22,360,32,'Bold',align='center',tag='main title')
 p.text(b.C['book']['author'],360,main[3]+70,360,32,align='center',tag='main author')
 centers=[(180,570),(890,400),(900,890),(190,1060)]
 for book,c,reason in zip(b.C['related'],centers,REASONS):
  box=cover(p,book,c[0],c[1]-height(book,WIDTH)/2,WIDTH);textbook(p,book,box,reason)
 reflect=lambda v:(1080-v[0],1460-v[1])
 lines=[[(360,650),(288,605)],[(685,main[1]),(776,410)]]
 for pts in list(lines):lines.append([reflect(v) for v in pts])
 for pts in lines:line(p,pts)
 for i,j in [(0,2),(1,3)]:
  assert reflect(centers[i])==centers[j]
  assert [reflect(v) for v in lines[i]]==lines[j]
 GEOMETRY['A']={'symmetry_center':center,'cover_centers':centers,'line_paths':lines,'symmetry_checks':'passed'}
 p.save();return p.im

def c():
 p=b.Page('C_圆角正交分支');b.title(p,b.C['association_title'])
 main=cover(p,b.C['book'],540,250,360)
 p.text(b.C['book']['title'],750,680,282,32,'Bold',tag='main title')
 p.text(b.C['book']['author'],750,730,282,32,tag='main author')
 centers=[171,417,663,909]
 for book,x,reason in zip(b.C['related'],centers,REASONS):
  box=cover(p,book,x,900,WIDTH);textbook(p,book,box,reason)
 # One shared stem. Each arc is a true quarter circle of radius 24.
 line(p,[(540,main[3]),(540,816)])
 arc(p,(516,816),0,90);arc(p,(564,816),180,90)
 line(p,[(195,840),(516,840)]);line(p,[(564,840),(885,840)])
 for x in centers:
  if x<540:arc(p,(x+24,864),270,180)
  else:arc(p,(x-24,864),270,360)
  line(p,[(x,864),(x,884)])
  # Arrowheads are the sole intentional diagonal marks.
  line(p,[(x-7,875),(x,884),(x+7,875)])
 GEOMETRY['C']={'shared_stem':[[540,main[3]],[540,816]],'branch_y':840,'corner_radius':RADIUS,'cover_centers_x':centers,'cover_top':900,'arrow_tip_y':884,'symmetry_axis_x':540}
 assert all(centers[i]+centers[3-i]==1080 for i in range(4))
 p.save();return p.im
if __name__=='__main__':
 ims=[a(),c()]
 sheet=Image.new('RGB',(1128,784),'#EFF2F5');d=ImageDraw.Draw(sheet)
 for i,(im,label) in enumerate(zip(ims,['A 中心对称 · 直线','C 共用主干 · 圆角正交'])):
  x=16+i*556;d.text((x+8,16),label,font=b.font(14,'Bold'),fill=b.INK)
  sheet.paste(im.resize((540,720),Image.Resampling.LANCZOS),(x,56))
 sheet.save(OUT/'AC优化对比.png')
 for name,im in zip(['A','C'],ims):im.resize((360,480),Image.Resampling.LANCZOS).save(OUT/(name+'_手机预览.png'))
 (OUT/'布局配置.json').write_text(json.dumps({'canvas':[1080,1440],'related_cover_width':WIDTH,'main_cover_width':360,'line_width':STROKE,'geometry':GEOMETRY,'related_reasons':REASONS},ensure_ascii=False,indent=2))
 (OUT/'排版检查.json').write_text(json.dumps(b.REPORT,ensure_ascii=False,indent=2))
 print(json.dumps(b.REPORT,ensure_ascii=False,indent=2))
