"""Content-only semantic layout pilot; reuses v1 typography and QA helpers."""
from pathlib import Path
import importlib.util,json,math
from PIL import Image,ImageDraw
OUT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('base',OUT.parent/'v1/scripts/render.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
b.BASE=OUT
p=b.Page('02_内容要点图');BLUE=b.BG;INK=b.INK;PALE='#EDF5FC'
cfg=json.loads((OUT/'内容配置.json').read_text())
def text(s,x,y,w,size=32,bold=False,color=INK,center=False):
 return p.text(s,x,y,w,size,'Bold' if bold else 'Regular',fill=color,align='center' if center else 'left',tag='content')
def rect(box,fill=PALE,r=16):p.d.rounded_rectangle(b.xy(box),radius=r*2,fill=fill)
def line(pts,color=BLUE,width=2):p.line(pts,fill=color,width=width)
def arrow(pts):
 line(pts); a,z=pts[-2:];ang=math.atan2(z[1]-a[1],z[0]-a[0])
 for d in [-.5,.5]:line([z,(z[0]-10*math.cos(ang+d),z[1]-10*math.sin(ang+d))])
 p.paths.append(pts)
def icon(kind,cx,cy,size=40):
 # Draw at a common unit scale so all icons have matching weight.
 x=cx-size/2;y=cy-size/2;u=size/40
 def L(points):line([(x+a*u,y+c*u) for a,c in points],width=2)
 def E(box):p.d.ellipse(b.xy(tuple((x+v*u) if i%2==0 else (y+v*u) for i,v in enumerate(box))),outline=BLUE,width=4)
 def R(box):p.d.rectangle(b.xy(tuple((x+v*u) if i%2==0 else (y+v*u) for i,v in enumerate(box))),outline=BLUE,width=4)
 if kind=='belief':
  L([(20,1),(39,13),(1,13),(20,1)]);L([(3,37),(37,37)])
  for xx in [7,19,31]:L([(xx,16),(xx,33)])
 elif kind=='rules':
  R((7,1,33,38));L([(13,10),(27,10)]);L([(13,19),(27,19)]);L([(13,28),(24,28)])
 elif kind=='money':
  E((2,2,38,38));L([(12,10),(20,20),(28,10)]);L([(20,20),(20,32)]);L([(11,22),(29,22)]);L([(11,28),(29,28)])
 elif kind=='plant':
  L([(20,38),(20,1)])
  for yy in [9,22]:L([(20,yy),(4,yy-7),(8,yy+3),(20,yy+6)]);L([(20,yy),(36,yy-7),(32,yy+3),(20,yy+6)])
 elif kind=='person':
  E((13,1,27,15));p.d.arc(b.xy((x+4*u,y+20*u,x+36*u,y+52*u)),180,360,fill=BLUE,width=4);L([(4,36),(36,36)])
 elif kind=='science':
  L([(12,2),(28,2)]);L([(15,2),(15,16),(4,36),(36,36),(25,16),(25,2)]);L([(10,26),(30,26)])
 elif kind=='energy':L([(23,1),(7,23),(19,23),(15,39),(34,15),(22,15),(23,1)])
 elif kind=='eye':
  L([(1,20),(10,9),(20,5),(30,9),(39,20),(30,31),(20,35),(10,31),(1,20)]);E((13,13,27,27))
 else:
  E((2,2,30,30));L([(27,27),(39,39)])
 p.register((x,y,x+size,y+size),'icon '+kind)

b.title(p,cfg['title'])
text(cfg['claim'],48,201,984,40,True,'white',True)
# Main mechanism: concrete examples converge into shared recognition and cooperation.
rect((48,282,1032,642),'white',22)
text('01  认知革命：故事连接陌生人',72,308,936,40,True,BLUE)
for yy,kind,label in [(410,'belief','宗教与信仰'),(474,'rules','国家与法律'),(538,'money','金钱与公司')]:
 icon(kind,105,yy,38);text(label,142,yy-16,224,32,True,BLUE)
 line([(332,yy),(373,yy)])
line([(373,410),(373,538)]);arrow([(373,474),(414,474)])
rect((424,420,656,528),BLUE,20)
text('共同想象',436,439,208,40,True,'white',True)
text('共同认可的秩序',436,491,208,26,False,'white',True)
arrow([(665,474),(713,474)])
# Network is a logical collective, not quantitative data.
coords=[(810,398),(913,416),(934,501),(861,547),(770,509),(851,466)]
for i,j in [(0,5),(1,5),(2,5),(3,5),(4,5),(0,1),(1,2),(2,3),(3,4),(4,0)]:line([coords[i],coords[j]],'#A5C8E6')
for i,(x,y) in enumerate(coords):
 p.d.ellipse(b.xy((x-12,y-12,x+12,y+12)),fill=BLUE)
text('大规模合作',736,572,264,32,True,BLUE,True)
text('陌生人也能协作',424,570,244,26,False,INK,True)
# Agriculture: contrasted consequences rather than a fabricated data curve.
rect((48,662,530,1112),'white',22)
text('02  农业革命',72,689,434,40,True,BLUE)
text('群体扩张，不等于个体幸福',72,751,434,26,False,INK,True)
icon('plant',181,824,50);icon('person',397,824,50)
text('社会规模',78,872,198,32,True,BLUE,True)
text('个体生活',302,872,198,32,True,BLUE,True)
text('≠',267,870,44,32,True,BLUE,True)
text('人口与聚落扩张\n财富积累\n阶层逐渐分化',78,923,198,26,False,INK,True)
text('劳作更加辛苦\n生活更受约束\n未必更加幸福',302,923,198,26,False,INK,True)
# Science: two complementary mechanisms, preserving source-supported arrows.
rect((550,662,1032,1112),'white',22)
text('03  科学革命',574,689,434,40,True,BLUE)
text('承认无知，才能探索未知',574,751,434,26,False,INK,True)
icon('science',656,823,50);icon('energy',926,823,50)
arrow([(714,823),(865,823)])
text('观察与实验',577,871,180,32,True,BLUE,True)
text('知识与技术',822,871,186,32,True,BLUE,True)
rect((574,938,1008,1086),PALE,14)
text('投资 + 劳动 + 科技',590,957,402,26,True,BLUE,True)
arrow([(790,1000),(790,1020)])
text('推动经济增长',590,1038,402,32,True,BLUE,True)
# Reflection: two conceptual statements, separate from author's historical narrative.
rect((48,1132,1032,1392),'white',22)
text('04  读后思考：重新理解进步',72,1156,936,40,True,BLUE)
line([(540,1224),(540,1368)],'#C7DDED')
icon('eye',105,1252,40);text('增长 ≠ 人人受益',142,1236,360,32,True,BLUE)
text('文明更强大，\n不等于每个人都过得更好。',78,1293,426,26)
icon('reflect',600,1252,40);text('秩序并非天然',638,1236,370,32,True,BLUE)
text('我们共同维系制度，\n也被制度反过来塑造。',574,1293,426,26)
p.save()
Image.open(OUT/'02_内容要点图.png').resize((360,480),Image.Resampling.LANCZOS).save(OUT/'手机预览.png')
(OUT/'排版检查.json').write_text(json.dumps(b.REPORT,ensure_ascii=False,indent=2))
print(json.dumps(b.REPORT,ensure_ascii=False,indent=2))
