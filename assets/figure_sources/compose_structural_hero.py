"""Compose preserved empirical panels and computed structural panels as editable SVG.

The empirical master is a retained vector. No new model observations are created.
"""
from pathlib import Path
import copy,hashlib,io,re
import xml.etree.ElementTree as ET
import cairosvg
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/figures'
BASE=ROOT/'assets/figure_sources/retained/fig1_ethos_gallery.svg'
NS='http://www.w3.org/2000/svg'
ET.register_namespace('',NS)
INK,TEAL,ROSE,GOLD,GREY='#18324A','#007F86','#B93678','#A97512','#728091'
plt.rcParams.update({'font.family':'STIXGeneral','mathtext.fontset':'stix','font.size':17,
 'axes.labelsize':17,'axes.titlesize':19,'axes.labelcolor':INK,'text.color':INK,
 'axes.edgecolor':'#8994A2','xtick.color':INK,'ytick.color':INK,'xtick.labelsize':17,
 'ytick.labelsize':17,'axes.spines.top':False,'axes.spines.right':False,
 'axes.linewidth':.9,'svg.fonttype':'none','svg.hashsalt':'EthosGPT-corrected-main-figures',
 'pdf.fonttype':42,'figure.facecolor':'white','axes.facecolor':'white'})

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def plot_svg(fig, prefix):
    stream = io.BytesIO()
    fig.savefig(stream, format='svg', metadata={'Date': None})
    plt.close(fig)
    root = ET.fromstring(stream.getvalue())
    # Use explicit SVG font attributes: CairoSVG does not reliably parse the
    # CSS font shorthand used by Matplotlib. Match the retained serif panels.
    for node in root.iter('{'+NS+'}text'):
        style = node.get('style','')
        size = re.search(r'(?:font-size:\s*|\b)([0-9.]+)px',style)
        if size:
            node.set('font-size',size.group(1))
        if 'bold' in style or re.search(r'font-weight:\s*[67]00',style):
            node.set('font-weight','bold')
        style = ';'.join(part for part in style.split(';')
                         if not part.strip().startswith('font'))
        node.set('style',style)
        node.set('font-family','Nimbus Roman,Times New Roman,serif')
    # Imported Matplotlib groups need distinct ids and clip references.
    replacements = {n.attrib['id']: prefix+'-'+n.attrib['id']
                    for n in root.iter() if 'id' in n.attrib}
    for node in root.iter():
        for key, value in list(node.attrib.items()):
            if key == 'id':
                node.set(key, replacements[value])
            else:
                for old, new in replacements.items():
                    value = value.replace('url(#'+old+')', 'url(#'+new+')')
                    if value == '#'+old:
                        value = '#'+new
                node.set(key, value)
    return root


def insert_svg(root, child, x, y, width, height, group_id):
    group = ET.SubElement(root, '{'+NS+'}g', {'id': group_id})
    child.set('x', str(x)); child.set('y', str(y))
    child.set('width', str(width)); child.set('height', str(height))
    group.append(child)


def simple_text(root, x, y, content, size=18, weight='normal', color=INK):
    node = ET.SubElement(root, '{'+NS+'}text', {
        'x': str(x), 'y': str(y), 'font-family': 'Nimbus Roman,Times New Roman,serif',
        'font-size': str(size), 'font-weight': weight, 'fill': color,
        'data-containment': 'free',
    })
    node.text = content


def export(root, name):
    for i, node in enumerate(root.iter('{'+NS+'}text')):
        node.set('data-containment', 'free')
        if 'id' not in node.attrib:
            node.set('id', name+'-label-'+str(i))
    svg = OUT / (name+'.svg')
    ET.ElementTree(root).write(svg, encoding='utf-8', xml_declaration=True)
    cairosvg.svg2pdf(url=str(svg), write_to=str(OUT/(name+'.pdf')))
    cairosvg.svg2png(url=str(svg),write_to=str(OUT/(name+'.png')),scale=2)
    return {ext: digest(OUT/(name+'.'+ext)) for ext in ['svg','pdf','png']}


def hero():
    root = ET.parse(BASE).getroot()
    root.set('height','985');root.set('viewBox','0 0 900 985')
    # Retain every original A--D mark and scientific label. Improve three
    # inherited clearances in D without changing its plotted weight surface.
    panel=next(n for n in root.iter() if n.get('id')=='measurement-weight-panel')
    for node in list(panel):
        if node.tag != '{'+NS+'}text':
            continue
        content=''.join(node.itertext())
        if content=='CI upper = 0':
            node.text='Upper CI';node.set('y','504')
            extra=copy.deepcopy(node);extra.text='= 0';extra.set('y','526')
            panel.append(extra)
        elif content=='Opportunity':
            node.set('x','552');node.set('text-anchor','end')
        elif content=='Distribution':
            node.set('x','878')
        elif content=='equal loss':
            node.set('y','548')
        elif content in ['agency · science','equality · responsibility']:
            node.set('y','637')
    for node in panel.iter('{'+NS+'}line'):
        if node.get('y1')=='533' and node.get('y2')=='533':
            node.set('y1','543');node.set('y2','543')
    simple_text(root,20,718,
                'Illustrative dynamics: innovation and adjustment — 2025 economics Nobel foundations',18)
    insert_svg(root,boundary_panel(),18,730,495,245,'illustrative-transition-panel')
    insert_svg(root,outcomes_panel(),528,730,354,245,'illustrative-outcomes-panel')
    return export(root,'fig1_extended_hero')

