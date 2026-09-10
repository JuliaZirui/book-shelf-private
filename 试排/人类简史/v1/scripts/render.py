"""Deterministic pilot renderer. Run: python3 scripts/render.py [config.json]."""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import json, math, sys
from PIL import Image, ImageDraw, ImageFont, ImageChops

ROOT = Path(__file__).resolve().parents[1]
CONFIG = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'内容配置.json'
C = json.loads(CONFIG.read_text())
BASE = CONFIG.parent
S = 2
W,H = C['canvas']
WHITE = '#FFFFFF'
INK = '#102B42'
BG = C['background']
FONTS = (BASE/C['font_dir']).resolve()
REPORT = {'canvas': [W,H], 'fonts': str(FONTS), 'pages': {}, 'checks': []}

def font(size,weight='Regular'):
    return ImageFont.truetype(str(FONTS/f'SourceHanSansCN-{weight}.ttf'),round(size*S))

def xy(box): return tuple(round(v*S) for v in box)

class Page:
    def __init__(self,name):
        self.name=name
        self.im=Image.new('RGB',(W*S,H*S),BG)
        self.d=ImageDraw.Draw(self.im)
        self.boxes=[]
        self.paths=[]
    def register(self,box,tag):
        assert box[0]>=0 and box[1]>=0 and box[2]<=W and box[3]<=H, (tag,box)
        self.boxes.append((box,tag))
    def text(self,text,x,y,width,size=32,weight='Regular',fill=WHITE,align='left',lh=None,tag='text'):
        role={80:'title',40:'module',32:'body',26:'aux'}.get(size)
        if role: size=C['type_sizes'][role]
        if tag=='average': size=C['type_sizes']['score']
        f=font(size,weight); lh=lh or round(size*1.4)
        lines=[]
        for para in text.split('\n'):
            line=''
            for ch in para:
                if self.d.textlength(line+ch,font=f)>width*S and line:
                    # Keep closing punctuation on the preceding line.
                    if ch in '，。？！、；：）》”':
                        carry=line[-1]; lines.append(line[:-1]); line=carry+ch
                    else: lines.append(line); line=ch
                else: line+=ch
            lines.append(line)
        for i,line in enumerate(lines):
            tw=self.d.textlength(line,font=f)/S
            xx=x+(width-tw)/2 if align=='center' else x
            yy=y+i*lh
            bbox=self.d.textbbox(xy((xx,yy)),line,font=f,anchor='lt')
            if tag in ('axis score','average','douban'):
                bg=tuple(round(v*(1-22/255)+22) for v in bytes.fromhex(BG[1:]))
                self.d.rectangle((bbox[0]-4*S,bbox[1]-4*S,bbox[2]+4*S,bbox[3]+4*S),fill=bg)
            self.d.text(xy((xx,yy)),line,font=f,fill=fill,anchor='lt')
            if line: self.register(tuple(v/S for v in bbox),f'{tag}: {line}')
        return len(lines)*lh
    def cover(self,path,cx,y,width=None,height=None,tag='cover'):
        im=Image.open(BASE/path).convert('RGB')
        if width: h=round(width*im.height/im.width); w=width
        else: h=height; w=round(h*im.width/im.height)
        x=round(cx-w/2)
        self.im.paste(im.resize((w*S,h*S),Image.Resampling.LANCZOS),xy((x,y)))
        box=(x,y,x+w,y+h); self.register(box,tag)
        return box
    def line(self,pts,fill=WHITE,width=2):
        self.d.line([xy(p) for p in pts],fill=fill,width=width*S,joint='curve')
    def bezier(self,a,b,c,d):
        pts=[]
        for i in range(101):
            t=i/100;u=1-t
            pts.append((u**3*a[0]+3*u*u*t*b[0]+3*u*t*t*c[0]+t**3*d[0],u**3*a[1]+3*u*u*t*b[1]+3*u*t*t*c[1]+t**3*d[1]))
        self.line(pts,width=2);self.paths.append(pts)
    def save(self):
        conflicts=[]
        for i,(a,ta) in enumerate(self.boxes):
            for b,tb in self.boxes[i+1:]:
                if min(a[2],b[2])-max(a[0],b[0])>1 and min(a[3],b[3])-max(a[1],b[1])>1:
                    conflicts.append([ta,tb])
        line_conflicts=[]
        for pts in self.paths:
            for box,tag in self.boxes:
                if any(box[0]+2<x<box[2]-2 and box[1]+2<y<box[3]-2 for x,y in pts):line_conflicts.append(tag)
        REPORT['pages'][self.name]={'elements':len(self.boxes),'overlaps':conflicts,'line_collisions':line_conflicts}
        assert not conflicts, (self.name,conflicts)
        assert not line_conflicts,(self.name,line_conflicts)
        self.im.resize((W,H),Image.Resampling.LANCZOS).save(BASE/f'{self.name}.png')

def title(p,text):
    used=p.text(text,48,54,984,80,'Heavy',tag='title')
    assert used<=200, 'Title requires editorial shortening'

def association():
    p=Page('01_书籍联想图');title(p,C['association_title'])
    main=p.cover(C['book']['cover'],540,590,width=360,tag='主书封面')
    # Four independent text/cover zones, with clear connection corridors.
    placements=[(190,285),(890,285),(190,970),(890,970)]
    rb=[]
    for b,(cx,y) in zip(C['related'],placements):
        r=p.cover(b['cover'],cx,y,height=250,tag=b['title']+'封面');rb.append(r)
        p.text(b['title'],cx-155,y+269,310,26,align='center',tag='related title')
        p.text(b.get('reason_display',b['reason']),cx-155,y+312,310,26,align='center',lh=36,tag='reason')
    p.text('人类简史',48,785,280,32,tag='main title')
    p.text('尤瓦尔·赫拉利',48,836,280,32,tag='main author')
    p.bezier((420,590),(380,530),(355,413),(rb[0][2],410))
    p.bezier((660,590),(710,530),(725,413),(rb[1][0],410))
    p.bezier((360,1025),(320,1025),(325,1120),(rb[2][2],1120))
    p.bezier((720,1025),(760,1025),(755,1120),(rb[3][0],1120))
    p.save()

def content():
    p=Page('02_内容要点图');title(p,C['book']['title'])
    p.text(C['subtitle'],48,209,984,40,'Bold',tag='subtitle')
    for i,m in enumerate(C['modules']):
        y=305+i*270
        p.d.rounded_rectangle(xy((48,y,1032,y+250)),radius=20*S,fill=WHITE)
        p.text(f'{i+1:02d}',72,y+24,65,40,'Bold',fill=BG,tag='module number')
        p.text(m['title'],151,y+24,850,40,'Bold',fill=BG,tag='module title')
        p.line([(72,y+87),(1008,y+87)],fill='#CDDEEC',width=1)
        for j,point in enumerate(m['points']):
            yy=y+105+j*44
            p.d.ellipse(xy((78,yy+12,86,yy+20)),fill=BG)
            p.text(point,106,yy,900,32,fill=INK,tag='point')
    p.save()

def logo():
    src=Image.open(C['logo_source']).convert('RGB')
    # The original is a blue mark on white. Derive alpha from its blue ink,
    # retaining anti-aliased edges and all internal white cut-outs.
    alpha=src.getchannel('R').point(lambda r: round((255-r)/255*255))
    mask=alpha.point(lambda a: 255 if a>30 else 0)
    box=mask.getbbox(); assert box
    out=Image.new('RGBA',src.size,'white');out.putalpha(alpha)
    out=out.crop(box);out.save(BASE/'logo-white.png')
    return out

def score():
    p=Page('03_打分图')
    l=logo(); lw=64;lh=round(lw*l.height/l.width)
    l=l.resize((lw*S,lh*S),Image.Resampling.LANCZOS)
    p.im.paste(l,xy((24,53)),l);p.register((24,53,24+lw,53+lh),'logo')
    used=p.text(C.get('intro_display',C['intro']),124,49,696,32,lh=42,tag='intro')
    assert used<=210, f'Intro too long: {used}'
    p.cover(C['book']['cover'],948,56,width=168,tag='main cover')
    cx,cy,r=540,720,344
    layer=Image.new('RGBA',p.im.size);d=ImageDraw.Draw(layer)
    for i in range(1,11):
        rr=r*i/10; d.ellipse(xy((cx-rr,cy-rr,cx+rr,cy+rr)),outline=(255,255,255,26),width=2*S)
    p.im=Image.alpha_composite(p.im.convert('RGBA'),layer).convert('RGB');p.d=ImageDraw.Draw(p.im)
    angles=[math.radians(-90+72*i) for i in range(5)]
    end=[(cx+r*math.cos(a),cy+r*math.sin(a)) for a in angles]
    points=[(cx+r*v/10*math.cos(a),cy+r*v/10*math.sin(a)) for a,v in zip(angles,C['scores'])]
    layer=Image.new('RGBA',p.im.size);d=ImageDraw.Draw(layer)
    d.polygon([xy(pt) for pt in points],fill=(255,255,255,22))
    p.im=Image.alpha_composite(p.im.convert('RGBA'),layer).convert('RGB');p.d=ImageDraw.Draw(p.im)
    for ex,ey in end:
        p.line([(cx,cy),(ex,ey)],width=2)
        p.d.ellipse(xy((ex-10,ey-10,ex+10,ey+10)),fill=WHITE)
    p.line(points+[points[0]],width=3)
    labels=[('解决问题\n层级',452,267,180),('行文与结构',890,590,185),('严谨程度',785,1015,180),('原创视角',269,1036,180),('值得复读',46,590,160)]
    for t,x,y,w in labels:p.text(t,x,y,w,32,tag='axis label')
    for (x,y),v in zip([(518,477),(694,672),(608,824),(396,864),(342,665)],C['scores']):
        p.text(str(v),x,y,44,32,align='center',tag='axis score')
    total=(sum(Decimal(str(v)) for v in C['scores'])/Decimal(5)).quantize(Decimal('.1'),rounding=ROUND_HALF_UP)
    if C.get('douban_score') is not None:p.text(f"豆瓣评分 {C['douban_score']}",370,626,340,32,align='center',tag='douban')
    p.text(f'{total}分',360,682,360,80,'Bold',align='center',tag='average')
    # Fixed stair shapes and labels follow the supplied score references.
    rgba=tuple(bytes.fromhex(BG[1:]));muted=tuple(round(v*.65+255*.35) for v in rgba)
    for i,(a,b) in enumerate([('道','世界观'),('法','方法论'),('术','技巧'),('器','工具')]):
        y=983+i*92;x=106;right=214+i*23
        selected=a in C['classification']
        p.d.polygon([xy(pt) for pt in [(x,y),(right,y),(right+21,y+81),(x,y+81)]],fill=WHITE if selected else muted)
        p.text(a,x+18,y+7,100,26,fill='#607180',tag='class')
        p.text(b,x+18,y+42,140,26,fill=INK,tag='class text')
    for i,(a,b) in enumerate([('炼气','入门'),('筑基','初级'),('结丹','进阶'),('元婴','高阶')]):
        x=630+i*92;top=1235-i*30
        p.d.polygon([xy(pt) for pt in [(x,top),(x+81,top-25),(x+81,1342),(x,1342)]],fill=WHITE if b in C['audience'] else muted)
        p.text(a,x+9,1270,70,26,fill='#607180',tag='audience alias')
        p.text(b,x+9,1305,70,26,fill=INK,tag='audience')
    REPORT['checks'].append({'average':str(total),'scores':C['scores'],'rings':10,'ring_opacity':.1})
    p.save()

if __name__=='__main__':
    assert len(C['scores'])==5 and all(0<=v<=10 for v in C['scores'])
    assert len(C['related'])==4
    association();content();score()
    thumbs=[]
    for name in REPORT['pages']:
        im=Image.open(BASE/f'{name}.png');thumbs.append(im.resize((360,480),Image.Resampling.LANCZOS))
    preview=Image.new('RGB',(1112,496),'#E6EBEF')
    for i,im in enumerate(thumbs):preview.paste(im,(8+i*368,8))
    preview.save(BASE/'三图总览.png')
    (BASE/'排版检查.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2))
    print(json.dumps(REPORT,ensure_ascii=False,indent=2))
