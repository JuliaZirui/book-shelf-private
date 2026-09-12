"""Four sketch-derived association layout trials; does not modify the skill."""
from pathlib import Path
import importlib.util,json,math
from PIL import Image,ImageDraw
OUT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('base',OUT.parent/'v1/scripts/render.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
SOURCE=b.BASE;b.BASE=OUT
reasons=['从自然选择出发，\n理解人类演化','从基因视角，\n对照文化的作用','从地理与环境，\n解释文明差异','延伸历史视野，\n追问科技与未来']
labels=['A 错位放射 · 斜线','B 错位放射 · 折线','C 上主下分 · 箭头','D 左右对称 · 折线']

def cover(p,book,cx,y,width=None,height=None):
 return p.cover(str(SOURCE/book['cover']),cx,y,width=width,height=height,tag=book['title']+'封面')
def path(p,pts,arrow=False):
 # Sample every segment for text/cover collision checks.
 samples=[]
 for a,z in zip(pts,pts[1:]):
  for i in range(101):samples.append((a[0]+(z[0]-a[0])*i/100,a[1]+(z[1]-a[1])*i/100))
 p.line(samples,width=2);p.paths.append(samples)
 if arrow:
  a,z=pts[-2:];ang=math.atan2(z[1]-a[1],z[0]-a[0])
  for d in [-.55,.55]:p.line([z,(z[0]-12*math.cos(ang+d),z[1]-12*math.sin(ang+d))],width=2)
def render(kind):
 p=b.Page('ABCD'[kind]+'_书籍联想图');b.title(p,b.C['association_title'])
 my=250 if kind==2 else 470
 main=cover(p,b.C['book'],540,my,width=360)
 p.text(b.C['book']['title'],360,main[3]+22,360,32,'Bold',align='center',tag='main title')
 p.text(b.C['book']['author'],360,main[3]+70,360,32,align='center',tag='main author')
 positions=([(185,420),(865,240),(895,900),(210,1030)] if kind<2 else
             [(171,970),(417,970),(663,970),(909,970)] if kind==2 else
             [(185,290),(895,290),(185,970),(895,970)])
 boxes=[]
 for i,(book,(cx,y)) in enumerate(zip(b.C['related'],positions)):
  box=cover(p,book,cx,y,height=240 if kind==2 else 220);boxes.append(box)
  width=226 if kind==2 else 300
  th=p.text(book['title'],cx-width/2,box[3]+20,width,26,'Bold',align='center',lh=36,tag='related title')
  p.text(reasons[i],cx-width/2,box[3]+20+th+12,width,26,align='center',lh=36,tag='reason')
 if kind==0:
  path(p,[(360,650),(boxes[0][2],530)])
  path(p,[(650,470),(boxes[1][0],350)])
  path(p,[(720,850),(boxes[2][0],1010)])
  path(p,[(390,991),(boxes[3][2],1080)])
 elif kind==1:
  path(p,[(360,650),(310,650),(310,530),(boxes[0][2],530)])
  path(p,[(650,470),(650,350),(boxes[1][0],350)])
  path(p,[(720,850),(790,850),(790,1010),(boxes[2][0],1010)])
  path(p,[(390,991),(390,1140),(boxes[3][2],1140)])
 elif kind==2:
  for pts in [[(380,771),(340,880),(171,920),(171,954)],[(420,771),(420,900),(417,920),(417,954)],[(660,771),(660,900),(663,920),(663,954)],[(700,771),(740,880),(909,920),(909,954)]]:path(p,pts,True)
 else:
  path(p,[(360,620),(320,620),(320,400),(boxes[0][2],400)])
  path(p,[(720,620),(760,620),(760,400),(boxes[1][0],400)])
  path(p,[(360,850),(300,850),(300,1080),(boxes[2][2],1080)])
  path(p,[(720,850),(780,850),(780,1080),(boxes[3][0],1080)])
 p.save()
 return p.im.resize((540,720),Image.Resampling.LANCZOS)
if __name__=='__main__':
 ims=[render(i) for i in range(4)]
 sheet=Image.new('RGB',(1128,1560),'#EFF2F5');d=ImageDraw.Draw(sheet)
 for i,im in enumerate(ims):
  x=16+(i%2)*556;y=16+(i//2)*780
  d.text((x+8,y+5),labels[i],font=b.font(14,'Bold'),fill=b.INK)
  sheet.paste(im,(x,y+44))
 sheet.save(OUT/'四方案对比.png')
 (OUT/'排版检查.json').write_text(json.dumps(b.REPORT,ensure_ascii=False,indent=2))
 (OUT/'布局配置.json').write_text(json.dumps({'canvas':[1080,1440],'main_cover_width':360,'related_reasons':reasons,'variants':dict(zip('ABCD',labels)),'sketches':['IMG_4380.HEIC','IMG_4381.heic','IMG_4382.heic','IMG_4384.heic']},ensure_ascii=False,indent=2))
 print(json.dumps(b.REPORT,ensure_ascii=False,indent=2))
