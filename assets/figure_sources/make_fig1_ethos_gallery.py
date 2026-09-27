#!/usr/bin/env python3
"""Build the editable EthosGPT hero from the released figure data.

The world outlines and projected country locations are reused from the
previous vector map. That map was generated from Natural Earth 1:110m
public-domain geometry and the versioned 64-country coordinate ledger.
No economic outcome is inferred from the map or the survey comparisons.
"""
from __future__ import annotations

import csv
import html
import json
import math
import re
from collections import Counter
from pathlib import Path
from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = ROOT / "results" / "figures"
ASSETS = HERE / "clip-art-set-v2"
INK = "#18324A"
BLUE = "#3B5CCC"
TEAL = "#078C82"
MAGENTA = "#B33B72"
AMBER = "#D88A24"
SLATE = "#4E5B68"
PALE_BLUE = "#EAF0FF"
PALE_GREEN = "#E5F4F1"
PALE_WARM = "#FFF3E8"
DIVIDER = "#D6DEE7"
LIGHT = "#F0F3F7"
WHITE = "#FFFFFF"

# Four original accent families, with two quiet variants for categorical
# region locations. Teal/magenta are used for lower/higher error only in the
# adjacent result plot, which has its own explicit key.
REGIONS = [
    ("African-Islamic", "#078C82", "circle"),
    ("Catholic Europe", "#D88A24", "diamond"),
    ("Confucian", "#B33B72", "square"),
    ("English-Speaking", "#3B5CCC", "triangle"),
    ("Latin America", "#3AA39B", "circle"),
    ("Orthodox Europe", "#5976AA", "diamond"),
    ("Protestant Europe", "#B47A48", "square"),
    ("West & South Asia", "#8B5971", "triangle"),
]

def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def esc(s: object) -> str:
    return html.escape(str(s), quote=True)

def text(x, y, content, size=16, color=INK, weight="normal", anchor="start", extra=""):
    # At a 394.56 pt display width, 16 SVG px become 7.04 pt.
    size=max(size,16)
    return (f'<text x="{x}" y="{y}" font-family="Nimbus Roman,Times New Roman,serif" '
            f'font-size="{size}" font-weight="{weight}" fill="{color}" '
            f'text-anchor="{anchor}" {extra}>{esc(content)}</text>')

def rect(x,y,w,h,fill=WHITE,stroke=DIVIDER,r=12,sw=1.4,dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>'

def line(x1,y1,x2,y2,color=DIVIDER,width=1.2,dash="",extra=""):
    d=f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{d} {extra}/>'

def mark(x,y,color,shape,size=4.8,hollow=False):
    fill = WHITE if hollow else color
    base=f'fill="{fill}" stroke="{color}" stroke-width="1.6"'
    if shape == "circle":return f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{size}" {base}/>'
    if shape == "square":return f'<rect x="{x-size:.2f}" y="{y-size:.2f}" width="{2*size}" height="{2*size}" rx="1" {base}/>'
    if shape == "diamond":return f'<path d="M{x:.2f} {y-size:.2f} L{x+size:.2f} {y:.2f} L{x:.2f} {y+size:.2f} L{x-size:.2f} {y:.2f}Z" {base}/>'
    return f'<path d="M{x:.2f} {y-size:.2f} L{x+size:.2f} {y+size:.2f} L{x-size:.2f} {y+size:.2f}Z" {base}/>'

def icon_survey():
    return f'''<g fill="none" stroke="{INK}" stroke-width="2.3" stroke-linejoin="round" stroke-linecap="round">
       <path d="M14 7h24v34H14z" fill="{PALE_BLUE}"/><path d="M20 0h24v34h-6M20 10h14M20 17h12M20 24h9"/>
       <circle cx="33" cy="25" r="3" fill="{TEAL}" stroke="none"/></g>'''

def icon_models():
    return f'''<g stroke="{INK}" stroke-width="2" stroke-linejoin="round" fill="none">
       <rect x="2" y="5" width="22" height="28" rx="3" fill="{PALE_BLUE}" stroke="{BLUE}"/>
       <rect x="26" y="10" width="22" height="28" rx="3" fill="{PALE_GREEN}" stroke="{TEAL}"/>
       <path d="M7 20h12M31 25h12"/><circle cx="13" cy="13" r="2" fill="{BLUE}" stroke="none"/>
       <circle cx="37" cy="18" r="2" fill="{TEAL}" stroke="none"/></g>'''

def icon_replacement():
    return f'''<g stroke="{INK}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round">
       <path d="M2 31h18V14H2z" fill="{LIGHT}"/><path d="M5 19h12M5 25h12" fill="none"/>
       <path d="M30 35h20V9H30z" fill="{PALE_GREEN}"/><path d="M34 14h12M34 21h12M34 28h12" fill="none"/>
       <path d="M19 8h15" stroke="{AMBER}" stroke-dasharray="3 3" fill="none"/></g>'''

ICONS={"survey-stack":icon_survey(),"paired-models":icon_models(),"replacement":icon_replacement()}

def save_icons():
    (ASSETS/"assets").mkdir(parents=True,exist_ok=True)
    for name,parts in ICONS.items():
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-4 -4 60 52" width="60" height="52">{parts}</svg>'
        (ASSETS/"assets"/f"{name}.svg").write_text(svg,encoding="utf-8")
    sheet=['<svg xmlns="http://www.w3.org/2000/svg" width="450" height="120" viewBox="0 0 450 120">',rect(1,1,448,118)]
    for i,(name,parts) in enumerate(ICONS.items()):
        x=45+150*i
        sheet += [f'<g transform="translate({x} 24)">{parts}</g>',text(x+25,95,name.replace('-',' '),15,INK,anchor='middle')]
    sheet.append('</svg>')
    (ASSETS/"contact-sheet.svg").write_text(''.join(sheet),encoding='utf-8')
    manifest={"style":"original editable front-view editorial vectors; 2 px navy stroke; no baked text or data",
              "palette":{"ink":INK,"blue":BLUE,"teal":TEAL,"amber":AMBER,"surface":[PALE_BLUE,PALE_GREEN,LIGHT]},
              "assets":[{"id":name,"role":role,"source":"original repository vector geometry",
                         "status":status,"prohibited_implication":"no measured performance or causal effect"}
                        for name,role,status in [("survey-stack","survey questions","verified-object"),
                                                 ("paired-models","paired archived outputs","verified-object"),
                                                 ("replacement","innovation replacing incumbent","conceptual-mechanism")]]}
    (ASSETS/"provenance.json").write_text(json.dumps(manifest,indent=2),encoding='utf-8')

def old_map_geometry():
    tree=etree.parse(str(OUT/"fig1_spatial_story.svg"))
    collection=tree.xpath('//*[@id="PatchCollection_1"]')[0]
    background=[p.get('d') for p in collection]
    all_rows=rows(DATA/"country_level_spatial_changes.csv")
    bound=max(abs(float(r['delta_tvd'])) for r in all_rows)
    threshold=.1*bound
    masks=[lambda v:v < -threshold,lambda v:abs(v)<=threshold,lambda v:v>threshold]
    points={}
    for gname,mask in zip(("PathCollection_8","PathCollection_9","PathCollection_10"),masks):
        subset=[r for r in all_rows if mask(float(r['delta_tvd']))]
        group=tree.xpath(f'//*[@id="{gname}"]')[0]
        assert len(subset)==len(group),(gname,len(subset),len(group))
        for row,path in zip(subset,group):
            nums=list(map(float,re.findall(r'-?\d+(?:\.\d+)?',path.get('d'))))
            xs,ys=nums[0::2],nums[1::2]
            points[row['country']]=((min(xs)+max(xs))/2,(min(ys)+max(ys))/2,row['cultural_region'])
    assert len(points)==64
    # Source marker centroids and row order are checked against geographic anchors.
    assert points['China'][0]>points['Andorra'][0]
    assert points['Australia'][1]>points['Andorra'][1]
    return background,points

def map_panel(paths,points):
    parts=[rect(18,82,495,303,WHITE,TEAL),text(35,112,'A  Where are the sampled countries?',22,INK,'bold'),
           text(35,135,'64 countries across eight descriptive cultural-region labels',16,SLATE)]
    scale=2.08; dx=76-44.67415*scale; dy=152-130.717113*scale
    parts.append(f'<g id="natural-earth-world-outlines" transform="translate({dx:.4f} {dy:.4f}) scale({scale})">')
    for d in paths:
        parts.append(f'<path d="{esc(d)}" fill="{LIGHT}" stroke="#C8D1DB" stroke-width="0.31"/>')
    parts.append('</g>')
    lookup={name:(col,shape) for name,col,shape in REGIONS}
    for name,(x,y,region) in points.items():
        col,shape=lookup[region]
        parts.append(f'<g id="country-{re.sub("[^a-z0-9]+","-",name.lower()).strip("-")}">')
        parts.append(mark(dx+x*scale,dy+y*scale,col,shape,3.5))
        parts.append(f'<title>{esc(name)} · {esc(region)}</title></g>')
    parts += [text(35,371,'Map marks use the region keys in B; locations are samples, not borders.',16,SLATE)]
    return parts

def region_panel():
    est={(r['cultural_region'],r['metric']):r for r in rows(DATA/"eight_region_sensitivity.csv")}
    parts=[rect(528,82,354,303,WHITE,BLUE),text(545,112,'B  What changed in eight regions?',21,INK,'bold'),
           text(706,155,'n',14,SLATE,anchor='middle'),
           text(784,139,'Category',14,SLATE,anchor='middle'),text(784,155,'TVD',14,SLATE,anchor='middle'),
           text(850,139,'Ordered',14,SLATE,anchor='middle'),text(850,155,'W1',14,SLATE,anchor='middle')]
    # Each mini forest has its own symmetric axis, labeled in the caption.
    for cx in (784,850): parts.append(line(cx,164,cx,337,DIVIDER,1))
    for i,(name,color,shape) in enumerate(REGIONS):
        y=180+i*22.0
        n=int(est[(name,'TVD')]['countries'])
        parts += [mark(547,y-4,color,shape,4.3),text(560,y,name,15.1,INK),text(706,y,str(n),15,SLATE,anchor='middle')]
        for metric,cx,domain in [('TVD',784,.022),('W1',850,.012)]:
            r=est[(name,metric)];v=float(r['delta_56_minus_55']); low=r['delta_ci_low_bca'];high=r['delta_ci_high_bca']
            x=cx+v/domain*26
            if low and high:
                x1=cx+float(low)/domain*26;x2=cx+float(high)/domain*26
                parts.append(line(x1,y-4,x2,y-4,SLATE,1.2))
            fill=TEAL if v<0 else MAGENTA
            uncertain=(not low) or (float(low)<=0<=float(high))
            parts.append(mark(x,y-4,fill,'circle',3.0,uncertain))
    parts += [line(547,339,865,339,DIVIDER,1),
              text(545,356,'Δ = 5.6 Sol − 5.5',16,SLATE),
              mark(695,350,TEAL,'circle',3.1),text(704,356,'lower',16,SLATE),
              mark(761,350,MAGENTA,'circle',3.1),text(770,356,'higher',16,SLATE),
              line(550,373,566,373,SLATE,1.2),mark(558,373,TEAL,'circle',3.0,True),
              text(572,378,'bar = 95% CI; open = spans 0 or n < 5',16,SLATE)]
    return parts

def signed_panel():
    data={r['question_id']:r for r in rows(DATA/"signed_global_items.csv")}
    names=[('Q48','Agency'),('Q57','Trust'),('Q106','Income equality*'),('Q108','Personal responsibility'),('Q121','Immigration*'),('Q159','Science opportunity')]
    parts=[rect(18,363,425,283,WHITE,TEAL),text(36,395,'C  Which views differ from the survey?',21,INK,'bold'),
           text(36,415,'Signed model − survey · equal-country mean',16,SLATE)]
    left,right=244,419;zero=left+(0.12/0.24)*(right-left)
    for tick in [-.1,0,.1]:
        x=left+(tick+.12)/.24*(right-left)
        parts.append(line(x,432,x,577,INK if tick==0 else DIVIDER,1 if tick else 1.4))
        parts.append(text(x,592,('0' if tick==0 else f'{tick:+.1f}'),14,SLATE,anchor='middle'))
    for i,(qid,label) in enumerate(names):
        y=448+i*24.2; r=data[qid]; a=float(r['mean_bias_55']);b=float(r['mean_bias_56'])
        xa=left+(a+.12)/.24*(right-left);xb=left+(b+.12)/.24*(right-left)
        parts.append(text(36,y+5,label,15,INK))
        parts.append(line(xa,y-2,xb,y-2,BLUE,1.3))
        parts.append(mark(xa,y-5,BLUE,'circle',3.3,True))
        parts.append(mark(xb,y+2,INK,'circle',3.6))
    parts += [text(36,608,'Zero = survey; left less, right more of named view',16,SLATE),
              mark(43,622,BLUE,'circle',3.3,True),text(55,627,'GPT-5.5',16,SLATE),
              mark(163,622,INK,'circle',3.6),text(175,627,'GPT-5.6 Sol',16,SLATE),
              text(307,627,'* wording',16,SLATE)]
    return parts

def scenario_panel(label='D  '):
    data={r['model']:r for r in rows(DATA/"creative_eight_region_simulation.csv")
          if r['scenario']=='illustrative' and r['cultural_region']=='African-Islamic'}
    assert set(data)=={'GPT-5.5','GPT-5.6 Sol'}
    a,b=data['GPT-5.5'],data['GPT-5.6 Sol']
    assert int(a['countries'])==int(b['countries'])==15
    def pair(field):
        return float(a[field]),float(b[field])
    arrival=pair('mean_delta_arrival_pp')
    quality=pair('mean_delta_20step_log_quality_pp')
    transition=pair('mean_delta_unassisted_transitions_per_100')
    assert abs(arrival[1]+1.2896098)<.0001 and abs(quality[1]+1.0115883)<.0001
    assert abs(transition[1]+.7604408)<.0001
    parts=[rect(458,363,424,283,PALE_WARM,AMBER,dash='7 5'),
           text(477,395,label+'African–Islamic: what shifts?',21,INK,'bold'),
           text(477,415,'15-country mean · model-guided − survey-guided',16,SLATE)]
    parts += [f'<g transform="translate(483 429) scale(.70)">{ICONS["survey-stack"]}</g>',
              f'<g transform="translate(606 429) scale(.70)">{ICONS["paired-models"]}</g>',
              f'<g transform="translate(754 429) scale(.70)">{ICONS["replacement"]}</g>',
              line(533,449,595,449,AMBER,2,'5 4',extra='marker-end="url(#arrow)"'),
              line(655,449,739,449,AMBER,2,'5 4',extra='marker-end="url(#arrow)"'),
              text(480,478,'Compare views',14,SLATE),text(597,478,'Assume choices',14,SLATE),text(735,478,'New replaces old',14,SLATE)]
    blocks=[('Arrival gap',f'{arrival[0]:+.2f} → {arrival[1]:+.2f} pp',504),
            ('20-round quality',f'{quality[0]:+.2f} → {quality[1]:+.2f} pp',539),
            ('Unassisted /100',f'{transition[0]:+.2f} → {transition[1]:+.2f}',574)]
    for label,value,y in blocks:
        parts += [line(478,y+11,856,y+11,'#EBD6BF',1),
                  text(478,y,label,16,INK),text(858,y,value,16,AMBER,anchor='end')]
    parts += [text(478,607,'Values: GPT-5.5 → GPT-5.6 Sol; pp = points',16,SLATE),
              text(478,626,'Dashed amber = assumed, not observed.',16,SLATE)]
    return parts

def weight_sensitivity_panel():
    """A compact ternary view of the archived weighted-error sensitivity.

    The three weights sum to one. This visualizes a descriptive loss
    comparison, not the illustrative G/U mechanism shown in Figure 2.
    """
    surface = rows(DATA / "economic_weight_surface.csv")
    grid = {(round(float(r['weight_distribution_adjustment'])*50),
             round(float(r['weight_coordination_legitimacy'])*50)): r
            for r in surface}
    assert len(grid) == 1326 and all(d+c <= 50 for d,c in grid)
    bound = max(abs(float(r['delta_weighted_loss_56_minus_55'])) for r in surface)
    assert abs(bound - .0213311855) < .000001

    left, right, apex, base_y, apex_y = 558., 793., 675.5, 602., 451.
    def xy(key):
        d,c = key
        return (left + (right-left)*(d+.5*c)/50,
                base_y - (base_y-apex_y)*c/50)
    def rgb(code):
        return tuple(int(code[i:i+2],16) for i in (1,3,5))
    def blend(first, second, t):
        a,b = rgb(first),rgb(second)
        return '#' + ''.join(f'{round(x+(y-x)*t):02X}' for x,y in zip(a,b))
    def fill(value):
        t = min(1.,max(0.,(value+bound)/(2*bound)))
        return blend(TEAL,"#F7F8FA",2*t) if t <= .5 else blend("#F7F8FA",MAGENTA,2*t-1)

    triangles = []
    for d in range(50):
        for c in range(50-d):
            triangles.append(((d,c),(d+1,c),(d,c+1)))
            if d+c < 49:
                triangles.append(((d+1,c),(d+1,c+1),(d,c+1)))
    assert len(triangles) == 2500
    parts = [rect(458,363,424,283,WHITE,BLUE),
             text(477,395,'D  Does emphasis change the audit?',21,INK,'bold'),
             text(477,416,'Weighted error: teal = lower for 5.6 Sol',16,SLATE),
             text(apex,441,'Coordination + legitimacy',16,INK,'bold',anchor='middle'),
             '<g id="weight-sensitivity-surface">']
    for triangle in triangles:
        points = [xy(key) for key in triangle]
        value = sum(float(grid[key]['delta_weighted_loss_56_minus_55'])
                    for key in triangle)/3
        color = fill(value)
        path = ' '.join((('M' if i == 0 else 'L') + f'{x:.3f},{y:.3f}')
                        for i,(x,y) in enumerate(points))+' Z'
        parts.append(f'<path d="{path}" fill="{color}" stroke="{color}" stroke-width=".5"/>')
    parts.append('</g>')

    # Interpolate level-zero crossings on the released 0.02-weight grid.
    # Join adjacent segments before applying the dashed point-loss style.
    def contour_paths(field):
        segments = []
        for triangle in triangles:
            crossing = []
            for a,b in ((0,1),(1,2),(2,0)):
                va = float(grid[triangle[a]][field]); vb = float(grid[triangle[b]][field])
                if va*vb < 0:
                    t = va/(va-vb)
                    xa,ya = xy(triangle[a]); xb,yb = xy(triangle[b])
                    crossing.append((round(xa+t*(xb-xa),3),round(ya+t*(yb-ya),3)))
            if len(crossing) == 2 and crossing[0] != crossing[1]:
                segments.append(tuple(crossing))
        neighbors = {}
        for a,b in segments:
            neighbors.setdefault(a,[]).append(b)
            neighbors.setdefault(b,[]).append(a)
        remaining = {frozenset((a,b)) for a,b in segments}
        paths = []
        while remaining:
            endpoints = [p for p, links in neighbors.items()
                         if sum(frozenset((p,q)) in remaining for q in links) == 1]
            current = endpoints[0] if endpoints else next(iter(next(iter(remaining))))
            run = [current]
            while True:
                nxt = next((q for q in neighbors[current]
                            if frozenset((current,q)) in remaining),None)
                if nxt is None: break
                remaining.remove(frozenset((current,nxt)))
                current = nxt;run.append(current)
            if len(run)>1: paths.append('M'+' L'.join(f'{x:.3f},{y:.3f}' for x,y in run))
        return paths

    for field,color,width,dash in (
        ('ci_high_95',INK,2.1,''),
        ('delta_weighted_loss_56_minus_55',AMBER,2.,'6 4')):
        for path in contour_paths(field):
            style = f' stroke-dasharray="{dash}"' if dash else ''
            parts.append(f'<path d="{path}" fill="none" stroke="{color}" '
                         f'stroke-width="{width}" stroke-linejoin="round"{style}/>')
    parts += [f'<path d="M{left},{base_y} L{right},{base_y} L{apex},{apex_y}Z" '
              f'fill="none" stroke="{INK}" stroke-width="1.5"/>']
    parts += [line(480,501,505,501,INK,2.1),
              text(512,506,'95% CI',16,INK),
              line(480,533,505,533,AMBER,2.,'6 4'),
              text(512,538,'equal loss',16,INK)]
    cx,cy = xy((50/3,50/3))
    star = [(cx+8*math.cos(-math.pi/2+k*math.pi/5)
             *(1 if k%2==0 else .45),
             cy+8*math.sin(-math.pi/2+k*math.pi/5)
             *(1 if k%2==0 else .45)) for k in range(10)]
    parts += [f'<path d="M'+' L'.join(f'{x:.2f},{y:.2f}' for x,y in star)+
              f'Z" fill="{WHITE}" stroke="{INK}" stroke-width="1.4"/>',
              text(cx,cy+25,'equal weights',16,INK,anchor='middle'),
              text(481,617,'Opportunity',16,INK,'bold'),
              text(481,635,'+ participation',16,INK),
              text(861,617,'Distribution',16,INK,'bold',anchor='end'),
              text(861,635,'+ adjustment',16,INK,anchor='end')]
    for k in range(24):
        parts.append(rect(625+k*4.5,610,4.6,8,fill(-bound+2*bound*(k+.5)/24),
                          WHITE,r=0,sw=0))
    parts += [text(625,635,'−',16,SLATE,anchor='middle'),
              text(679,635,'0',16,SLATE,anchor='middle'),
              text(732,635,'+',16,SLATE,anchor='middle')]
    return parts

def build():
    OUT.mkdir(parents=True,exist_ok=True);save_icons()
    paths,points=old_map_geometry()
    region_counts={r['cultural_region']:int(r['countries']) for r in rows(DATA/"eight_region_sensitivity.csv") if r['metric']=='TVD'}
    assert Counter(r for _,_,r in points.values())==Counter(region_counts)
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="700" viewBox="0 0 900 700">',
           '<title>EthosGPT: mapped sample, model update, signed survey gaps, and theory-weight sensitivity</title>',
           f'<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M1 1L9 5 1 9" fill="none" stroke="{AMBER}" stroke-width="1.7"/></marker></defs>',
           rect(0,0,900,700,WHITE,WHITE,r=0,sw=0),
           text(20,34,'EthosGPT | Whose values guide technological change?',27,INK,'bold'),
           text(20,62,'Survey representation → language-model update → possible innovation and adjustment',18,SLATE)]
    parts += map_panel(paths,points)+region_panel()
    parts += ['<g transform="translate(0 40)">']+signed_panel()+weight_sensitivity_panel()+['</g>']
    parts += ['</svg>']
    svg=''.join(parts)
    outfile=OUT/"fig1_ethos_gallery.svg";outfile.write_text(svg,encoding='utf-8')
    case_svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="580" viewBox="0 0 900 580">',
        '<title>A conditional African-Islamic regional case under the declared adviser rule</title>',
        f'<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M1 1L9 5 1 9" fill="none" stroke="{AMBER}" stroke-width="1.7"/></marker></defs>',
        rect(0,0,900,580,WHITE,WHITE,r=0,sw=0),
        '<g transform="translate(-693.6 -549.1) scale(1.7)">',
        *scenario_panel(label=''),
        '</g></svg>',
    ]
    (OUT/"figS10_regional_scenario.svg").write_text(''.join(case_svg),encoding='utf-8')
    provenance={"figure":"fig1_ethos_gallery","evidence_classes":{"A":"country locations from archived descriptive sample",
                 "B":"exploratory paired country-level losses; within-region bootstrap intervals where n>=5",
                 "C":"equal-country signed model-minus-survey scores, recorded prompts",
                 "D":"archived 1,326-weight theory-indexed sensitivity of measured squared-TVD loss; teal favors GPT-5.6 Sol, navy is the exploratory 95% interval boundary, and amber is equal point loss; not G/U, observed welfare, or a policy effect"},
         "inputs":["results/figures/fig1_spatial_story.svg (Natural Earth map paths and archived marker positions)",
                   "assets/figure_sources/data/country_level_spatial_changes.csv",
                   "assets/figure_sources/data/signed_global_items.csv",
                   "assets/figure_sources/data/economic_weight_surface.csv",
                   "assets/figure_sources/data/eight_region_sensitivity.csv (copied from validated experiment result)"],
         "palette":{"ink":INK,"model":BLUE,"lower":TEAL,"higher":MAGENTA,"assumed":AMBER,
                    "surface":[PALE_BLUE,PALE_GREEN,PALE_WARM]},
         "map_caveat":"Markers locate sampled countries; cultural-region labels are published descriptive tags, not geographic polygons or individual identity.",
         "idioms":{"A":"point-symbol locator map", "B":"paired miniature interval/forest plots",
                   "C":"paired lollipop/dumbbell dots", "D":"ternary weight sensitivity with interval and point-loss contours"}}
    (HERE/"fig1_ethos_gallery_provenance.json").write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    case_provenance = {
        "figure":"figS10_regional_scenario",
        "origin":"previous Figure 1 regional case panel, preserved in the appendix",
        "evidence_class":"illustrative deterministic adviser scenario, not observed choices or outcomes",
        "inputs":["assets/figure_sources/data/creative_eight_region_simulation.csv"],
        "comparison":"GPT-5.5 to GPT-5.6 Sol; each is model-guided minus survey-guided for the same 15 countries",
        "units":"arrival and 20-round quality in percentage points; U per 100 abstract activities per round"
    }
    (HERE/"figS10_regional_scenario_provenance.json").write_text(
        json.dumps(case_provenance,indent=2),encoding='utf-8')
    print(outfile)

if __name__=='__main__': build()
