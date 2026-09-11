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
            if align=='justify' and i<len(lines)-1 and len(line)>1:
                gap=(width*S-self.d.textlength(line,font=f))/(len(line)-1)
                cursor=xx*S
                baseline=yy*S-f.getbbox(line,anchor='ls')[1]
                for ch in line:
                    self.d.text((round(cursor),round(baseline)),ch,font=f,fill=fill,anchor='ls')
                    cursor+=self.d.textlength(ch,font=f)+gap
                bbox=(round(xx*S),bbox[1],round((xx+width)*S),bbox[3])
            else:
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

def title_size(text,width=984):
    # Ten full-width Chinese characters establish the shared visual anchor.
    size=math.floor(width*S/10)/S
    if len(text)>10:
        size=min(size,size*width/(font(size,'Heavy').getlength(text)/S))
    while font(size,'Heavy').getlength(text)/S>width:
        size-=.1
    return size

def title(p,text):
    size=title_size(text)
    p.text(text,48,54,984,size,'Heavy',align='center',tag='title')
    REPORT['checks'].append({'title':text,'title_size':round(size,2),'centered':True})

def association():
    p=Page('01_书籍联想图');title(p,C['association_title'])
    main_h=round(360*Image.open(BASE/C['book']['cover']).height/Image.open(BASE/C['book']['cover']).width)
    main=p.cover(C['book']['cover'],540,round(720-main_h/2),width=360,tag='主书封面')
    # Four independent text/cover zones, with clear connection corridors.
    placements=[(190,285),(890,285),(190,970),(890,970)]
    rb=[]
    for b,(cx,y) in zip(C['related'],placements):
        r=p.cover(b['cover'],cx,y,height=250,tag=b['title']+'封面');rb.append(r)
        p.text(b['title'],cx-155,y+269,310,26,'Bold',align='center',tag='related title')
        p.text(b.get('reason_display',b['reason']),cx-155,y+312,310,26,align='center',lh=36,tag='reason')
    p.text(C['book']['title'],360,main[3]+22,360,32,'Bold',align='center',tag='main title')
    p.text(C['book']['author'],360,main[3]+70,360,32,align='center',tag='main author')
    p.bezier((420,main[1]),(380,420),(355,410),(rb[0][2],410))
    p.bezier((660,main[1]),(710,420),(725,410),(rb[1][0],410))
    p.bezier((360,880),(320,880),(325,1095),(rb[2][2],1095))
    p.bezier((720,880),(760,880),(755,1095),(rb[3][0],1095))
    p.save()

def arrow(p,a,b):
    p.line([a,b],fill=BG,width=2)
    angle=math.atan2(b[1]-a[1],b[0]-a[0])
    for delta in [-.5,.5]:
        p.line([b,(b[0]-9*math.cos(angle+delta),b[1]-9*math.sin(angle+delta))],fill=BG,width=2)

def icon(p,kind,x,y):
    # Consistent code-drawn line icons; no external font or image dependency.
    d=p.d
    if kind=='story':
        d.rounded_rectangle(xy((x,y,x+36,y+26)),radius=5*S,outline=BG,width=2*S)
        p.line([(x+9,y+26),(x+6,y+34),(x+20,y+26)],fill=BG)
        for yy in [8,16]:p.line([(x+7,y+yy),(x+29,y+yy)],fill=BG)
    elif kind=='plant':
        p.line([(x+18,y+35),(x+18,y+2)],fill=BG)
        for yy in [7,19]:
            p.line([(x+18,y+yy+7),(x+3,y+yy),(x+8,y+yy+10),(x+18,y+yy+12)],fill=BG)
            p.line([(x+18,y+yy),(x+32,y+yy-5),(x+29,y+yy+6),(x+18,y+yy+8)],fill=BG)
    elif kind=='science':
        p.line([(x+12,y),(x+24,y)],fill=BG)
        p.line([(x+14,y),(x+14,y+12),(x+4,y+32),(x+32,y+32),(x+22,y+12),(x+22,y)],fill=BG)
        p.line([(x+9,y+22),(x+27,y+22)],fill=BG)
    else:
        d.ellipse(xy((x+2,y+1,x+27,y+26)),outline=BG,width=2*S)
        p.line([(x+24,y+24),(x+35,y+35)],fill=BG,width=3)

def content():
    p=Page('02_内容要点图');title(p,C['book']['title'])
    p.text(C['core_claim'],48,208,984,40,'Bold',align='center',tag='core claim')
    count=len(C['modules']); assert 2<=count<=4
    module_h=(1060-(count-1)*20)/count
    for i,m in enumerate(C['modules']):
        y=305+i*(module_h+20)
        p.d.rounded_rectangle(xy((48,y,1032,y+module_h)),radius=20*S,fill=WHITE)
        icon(p,m['icon'],74,y+24)
        p.text(f"{i+1:02d}  {m['heading']}",130,y+24,870,40,'Bold',fill=BG,tag='module title')
        cells=m['diagram']['cells'];kind=m['diagram']['type'];count=len(cells)
        widths={2:420,3:280};cw=widths[count]
        starts={2:[72,588],3:[72,400,728]}[count]
        for j,(x,cell) in enumerate(zip(starts,cells)):
            p.d.rounded_rectangle(xy((x,y+88,x+cw,y+214)),radius=12*S,fill='#EEF5FB')
            p.text(cell['title'],x+12,y+101,cw-24,32,'Bold',fill=BG,align='center',tag='concept')
            p.text(cell['detail'],x+12,y+149,cw-24,26,fill=INK,align='center',lh=35,tag='detail')
            if j<count-1:
                left=x+cw;right=starts[j+1]
                if kind=='sequence':arrow(p,(left+8,y+150),(right-8,y+150))
                elif kind=='contrast':p.text('≠',left+10,y+135,right-left-20,32,'Bold',fill=BG,align='center',tag='contrast')
                elif kind=='cycle':
                    arrow(p,(left+8,y+142),(right-8,y+142))
                    arrow(p,(right-8,y+164),(left+8,y+164))
        if m.get('caption'):
            p.text(m['caption'],72,y+222,936,26,fill=INK,align='center',tag='module caption')
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
    used=p.text(C.get('intro_display',C['intro']),124,49,696,32,align='justify',lh=42,tag='intro')
    assert used<=210, f'Intro too long: {used}'
    p.cover(C['book']['cover'],948,56,width=168,tag='main cover')
    cx,cy,r=540,720,344
    layer=Image.new('RGBA',p.im.size);d=ImageDraw.Draw(layer)
    for i in range(1,11):
        rr=r*i/10; d.ellipse(xy((cx-rr,cy-rr,cx+rr,cy+rr)),outline=(255,255,255,46),width=3*S)
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
    p.line(points+[points[0]],width=4)
    labels=[('解决问题层级',444,297,230),('行文与结构',890,590,185),('严谨程度',785,1015,180),('原创视角',269,1036,180),('值得复读',46,590,160)]
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
    REPORT['checks'].append({'average':str(total),'scores':C['scores'],'rings':10,'ring_opacity':.18,'ring_width':3,'polygon_width':4,'intro_lines':used/42})
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
