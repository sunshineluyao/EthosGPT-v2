"""Restyle frozen R3 numerical results; all numerical coordinates are preserved.

No new model calls, simulations or estimates. SVG text remains editable.
"""
from pathlib import Path
import argparse, hashlib, json
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FuncFormatter

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'country_revision_results'
INK,BLUE,TEAL,ROSE,GRAY='#18324A','#4057D6','#007F86','#B93678','#728091'
SURFACE,DIVIDER='#F4F7FA','#CFD9E3'
COUNTRIES=['China','Germany','Egypt']
RULES=[('implemented Section 6 market','Human survey','Human rule',INK,'-'),
 ('implemented Section 6 market','GPT-5.5','GPT-5.5',BLUE,'--'),
 ('implemented Section 6 market','GPT-5.6 Sol','GPT-5.6 Sol',TEAL,'-.')]
ALL=[('unsubsidized market','Human survey','Unsubsidized',GRAY,':')]+RULES+[
 ('planner held optimal control','physical-economy benchmark','Planner',ROSE,'-')]
SEQ=LinearSegmentedColormap.from_list('ethos_teal',['#EFF7F7','#77BFC0',TEAL])
AID=LinearSegmentedColormap.from_list('ethos_violet',['#F1F1FD','#A5ACEA',BLUE])
plt.rcParams.update({'font.family':'STIXGeneral','mathtext.fontset':'stix','font.size':9,
 'axes.labelsize':9,'axes.titlesize':10,'xtick.labelsize':8,'ytick.labelsize':8,
 'text.color':INK,'axes.labelcolor':INK,'axes.edgecolor':GRAY,'xtick.color':INK,'ytick.color':INK,
 'svg.fonttype':'none','svg.hashsalt':'EthosGPT-R3-publication','pdf.fonttype':42,
 'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.65,
 'axes.grid':True,'grid.color':DIVIDER,'grid.alpha':.55,'grid.linewidth':.45,
 'figure.facecolor':'white','savefig.facecolor':'white','xtick.major.pad':7,'ytick.major.pad':7,
 'axes.labelpad':10,'axes.titlepad':12})

def selected(paths,country,policy,source):
 d=paths[paths.country.eq(country)&paths.policy.eq(policy)&paths.source.eq(source)&
         np.isclose(paths.initial_u_A,.08)&np.isclose(paths.initial_u_B,.08)].sort_values('t')
 assert len(d)>0
 return d

def legend(fig,rules,y=.975):
 fig.legend(handles=[Line2D([],[],c=c,ls=ls,label=lab,lw=1.5) for _,_,lab,c,ls in rules],
  loc='upper center',bbox_to_anchor=(.5,y),ncol=len(rules),frameon=False,
  handlelength=2,columnspacing=1.4,fontsize=9)

def grid(height=3.6,bottom=.20,top=.84):
 f,aa=plt.subplots(2,3,figsize=(7,height),squeeze=False)
 f.subplots_adjust(left=.12,right=.97,bottom=bottom,top=top,wspace=.42,hspace=.72)
 return f,aa

def footer(fig,text,y=.015):
 fig.text(.5,y,text,ha='center',va='bottom',fontsize=8.5,color=INK)

def finish(fig,name,out,registry,message,sources):
 for j,ax in enumerate(fig.axes):ax.set_gid(f'{name}-axes-{j}')
 for j,t in enumerate(fig.findobj(matplotlib.text.Text)):
  if t.get_text():t.set_gid(f'{name}-text-{j}')
 for ext in ['svg','pdf','png']:
  meta={'Date':None} if ext=='svg' else {'CreationDate':None,'ModDate':None} if ext=='pdf' else None
  fig.savefig(out/(name+'.'+ext),metadata=meta,dpi=150)
 ns='http://www.w3.org/2000/svg';ET.register_namespace('',ns)
 tree=ET.parse(out/(name+'.svg'));r=tree.getroot()
 ET.SubElement(r,'{'+ns+'}title').text=name.replace('fig_r3_','').replace('_',' ')
 ET.SubElement(r,'{'+ns+'}desc').text=message
 tree.write(out/(name+'.svg'),encoding='utf-8',xml_declaration=True)
 registry.append({'name':name,'width_inches':7,'evidence':'conditional synthetic model result',
  'reader_task':'evidence','caption_evidence_class':'descriptive','message':message,'data_sources':sources,
  'svg_sha256':hashlib.sha256((out/(name+'.svg')).read_bytes()).hexdigest(),
  'semantic_graphics':[{'concept':message,'visual_encoding':'computed data marks with axes, units and redundant keys',
   'shape_ids':[f'{name}-axes-0',next(t.get_gid() for t in fig.findobj(matplotlib.text.Text) if t.get_text() and t.get_gid())],'origin':'original','evidence_implication':'conditional computation, not measured national outcomes'}]})
 plt.close(fig)

def arrows(ax,x,y,color=TEAL,index=6):
 k=min(index,len(x)-3)
 ax.annotate('',xy=(x[k+2],y[k+2]),xytext=(x[k],y[k]),
  arrowprops={'arrowstyle':'-|>','color':color,'lw':1.1,'mutation_scale':8})

def endpoint_labels(ax,items):
 lo,hi=ax.get_ylim();pos=np.array([(v-lo)/(hi-lo) for _,v,_ in items]);order=np.argsort(pos)
 for k in range(1,len(order)):pos[order[k]]=max(pos[order[k]],pos[order[k-1]]+.38)
 if max(pos)>.90:pos-=max(pos)-.90
 if min(pos)<.1:pos+=.1-min(pos)
 for i,(lab,v,col) in enumerate(items):
  ax.text(1.12,pos[i],f'{lab} {v:+.3f}',transform=ax.transAxes,
   color=col,fontsize=8,va='center',clip_on=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('--outdir',type=Path,default=ROOT/'figures')
 out=p.parse_args().outdir;out.mkdir(parents=True,exist_ok=True);reg=[]
 paths=pd.read_csv(DATA/'country-paths.csv');sweep=pd.read_csv(DATA/'matched-sensitivity.csv')
 ref=pd.read_csv(DATA/'country-refinement.csv');up=pd.read_csv(DATA/'three-country-upgrade-comparison.csv')
 field=pd.read_csv(DATA/'systems/planner-phase-field.csv')
 f,aa=grid(3.5,.40,.82);f.subplots_adjust(left=.12,right=.97,wspace=.55,hspace=.88)
 legend(f,[('','', 'Human rule = zero',GRAY,':')]+RULES[1:],.99)
 for j,c in enumerate(COUNTRIES):
  h=selected(paths,c,RULES[0][0],RULES[0][1]);aa[0,j].set_title(c,pad=7);ends=[[],[]]
  for pol,src,lab,col,ls in RULES[1:]:
   d=selected(paths,c,pol,src);assert np.allclose(d.t,h.t)
   ys=[d.log_quality.to_numpy()-h.log_quality.to_numpy(),
    100*(np.maximum(d.u_A,d.u_B).to_numpy()-np.maximum(h.u_A,h.u_B).to_numpy())]
   for i,v in enumerate(ys):
    aa[i,j].plot(d.t,v,c=col,ls=ls,lw=1.7)
    aa[i,j].scatter(100,v[-1],s=15,marker='o' if src=='GPT-5.5' else 'D',c=col,zorder=5)
    ends[i].append(('5.5' if src=='GPT-5.5' else '5.6',v[-1],col))
  for i,a in enumerate(aa[:,j]):
   a.axhline(0,c=GRAY,lw=.7,ls=':');a.set(xlim=(0,100),xticks=[0,50,100]);a.margins(y=.28)
  if j==0:
   aa[0,j].set_ylabel('Delta G(t)');aa[1,j].set_ylabel('Needs change (pp)')
  aa[1,j].set_xlabel('Model time')
  xx=.23+.304*j
  f.text(xx,.20,'At t = 100: 5.5 / 5.6',ha='center',fontsize=8)
  f.text(xx,.14,'Delta G  '+' / '.join(f'{v:+.4f}' for _,v,_ in ends[0]),ha='center',fontsize=8)
  f.text(xx,.08,'Needs pp  '+' / '.join(f'{v:+.3f}' for _,v,_ in ends[1]),ha='center',fontsize=8)
 footer(f,'Signed keys give endpoint differences; pp = percentage points. Same economy and initial needs (8%, 8%).',.015)
 finish(f,'fig_r3_advice_paths',out,reg,'Growth falls in all three cases; needs directions relative to human advice differ.',['country-paths.csv'])

 f,aa=grid(4.8,.40,.82);legend(f,RULES,.995)
 for j,c in enumerate(COUNTRIES):
  aa[0,j].set_title(c);end=[]
  for pol,src,lab,col,ls in RULES:
   d=selected(paths,c,pol,src);end.append(d.iloc[-1])
   aa[0,j].plot(d.t,d.log_quality,c=col,ls=ls,lw=1.5)
   aa[1,j].plot(d.t,100*np.maximum(d.u_A,d.u_B),c=col,ls=ls,lw=1.5)
  for a in aa[:,j]:a.set(xlim=(0,100),xticks=[0,50,100])
  if j==0:aa[0,j].set_ylabel('Cumulative gain G(t)');aa[1,j].set_ylabel('Current needs (%)')
  aa[1,j].set_xlabel('Model time');xx=.23+.304*j
  f.text(xx,.215,'At t = 100: Human / 5.5 / 5.6',ha='center',fontsize=8.5)
  f.text(xx,.163,'G  '+' / '.join(f'{r.log_quality:.4f}' for r in end),ha='center',fontsize=8.5)
  f.text(xx,.111,'Needs (%)  '+' / '.join(f'{100*max(r.u_A,r.u_B):.3f}' for r in end),ha='center',fontsize=8.5)
 footer(f,'All original absolute trajectories are retained. Signed adviser differences appear in main Figure 3.',.061)
 footer(f,'Same physical economy and initial needs (8%, 8%); current worst-group needs differ from time-average needs.')
 finish(f,'fig_r3_advice_paths_absolute',out,reg,'Near-overlapping levels have small, explicitly reported adviser differences.',['country-paths.csv'])

 f,aa=grid(4.8,.28,.78);f.subplots_adjust(hspace=1.2)
 for j,c in enumerate(COUNTRIES):
  for i,(pol,src) in enumerate([(RULES[0][0],RULES[0][1]),(ALL[-1][0],ALL[-1][1])]):
   a=aa[i,j];dd=paths[paths.country.eq(c)&paths.policy.eq(pol)&paths.source.eq(src)]
   for ini,g in dd.groupby(['initial_u_A','initial_u_B']):
    g=g.sort_values('t');x,y=100*g.u_A.to_numpy(),100*g.u_B.to_numpy()
    a.plot(x,y,c=TEAL,lw=1.1);a.scatter(x[0],y[0],facecolors='white',edgecolors=INK,s=21,zorder=4);arrows(a,x,y)
   a.scatter(x[-1],y[-1],marker='*',c=ROSE,s=65,zorder=6)
   a.set_title(c+' | '+('Human-rule market' if i==0 else 'Planner')+f'\nEndpoint ({x[-1]:.2f}, {y[-1]:.2f})%',fontsize=9,linespacing=2.1)
   a.set(xlim=(-3,85),ylim=(-3,85),xlabel='Needs A (%)',ylabel='Needs B (%)',xticks=[0,40,80],yticks=[0,40,80])
   if i==0:a.set_xlabel('');a.tick_params(axis='x',labelbottom=False)
   if j>0:a.set_ylabel('')
 f.legend(handles=[Line2D([],[],c=TEAL,label='Path; arrows show time direction'),
  Line2D([],[],marker='o',markerfacecolor='white',c=INK,lw=0,label='Tested start'),
  Line2D([],[],marker='*',c=ROSE,lw=0,ms=8,label='Tested endpoint')],ncol=3,loc='upper center',bbox_to_anchor=(.5,.99),frameon=False,fontsize=9)
 footer(f,'Six starts: (0,0), (8,8), (30,5), (5,30), (45,35), (80,80)%. Tested convergence is not global uniqueness.')
 finish(f,'fig_r3_initial_states',out,reg,'Six starts approach the same tested endpoint within each country and policy.',['country-paths.csv'])

 f,aa=grid(4.8,.40,.82);legend(f,ALL,.995)
 for j,c in enumerate(COUNTRIES):
  aa[0,j].set_title(c)
  for pol,src,lab,col,ls in ALL:
   d=selected(paths,c,pol,src);aa[0,j].plot(d.t,100*d.n,c=col,ls=ls,lw=1.5)
   if lab!='Unsubsidized':aa[1,j].plot(d.t,d.a,c=col,ls=ls,lw=1.5)
  for a in aa[:,j]:a.set(xlim=(0,100),xticks=[0,50,100])
  if j==0:aa[0,j].set_ylabel('Research labor (%)');aa[1,j].set_ylabel('Assistance intensity')
  aa[1,j].set_xlabel('Model time')
  end=[selected(paths,c,pol,src).iloc[-1] for pol,src,_,_,_ in RULES]
  xx=.23+.304*j
  f.text(xx,.215,'At t = 100: Human / 5.5 / 5.6',ha='center',fontsize=8.5)
  f.text(xx,.163,'n (%)  '+' / '.join(f'{100*r.n:.3f}' for r in end),ha='center',fontsize=8.5)
  f.text(xx,.111,'a  '+' / '.join(f'{r.a:.4f}' for r in end),ha='center',fontsize=8.5)
 footer(f,'Unsubsidized and human-rule assistance coincide exactly. Numeric keys resolve overlapping advice controls.',.061)
 footer(f,'Line style and color identify rules. The planner changes the objective; a common cap does not equalize spending.')
 finish(f,'fig_r3_controls',out,reg,'The planner changes controls with need states; fixed-advice markets have distinct targets.',['country-paths.csv','country-policy-comparisons.csv'])

 for var,name in [('omega','fig_r3_welfare_weights'),('q','fig_r3_innovation_sizes')]:
  f,aa=grid(4.8,.40,.80)
  for j,c in enumerate(COUNTRIES):
   d=sweep[sweep.country.eq(c)&sweep.variable.eq(var)].sort_values('value');x=d.value.to_numpy() if var=='omega' else 100*d.value.to_numpy()
   aa[0,j].set_title(c)
   for i,(y,col,mark,label) in enumerate([(d.G.to_numpy(),TEAL,'o','Cumulative gain G'),(100*d.Umax.to_numpy(),ROSE,'s','Mean needs (%)')]):
    a=aa[i,j];a.plot(x,y,marker=mark,c=col,ms=4,lw=1.3)
    a.margins(x=.14,y=.35);a.set(xticks=x if var=='q' else [0,.3,.6,.9]);a.axvline(.3 if var=='omega' else 8,c=GRAY,ls=':',lw=.7)
    if j==0:a.set_ylabel(label)
    if i==1:a.set_xlabel('Needs penalty weight $\\omega$' if var=='omega' else 'Economic quality jump 100q (%)')
   mid=int(np.flatnonzero(np.isclose(d.value.to_numpy(),.3 if var=='omega' else .08))[0]);rr=d.iloc[[0,mid,-1]]
   xx=.23+.304*j
   f.text(xx,.215,'First / reference / last parameter',ha='center',fontsize=8.5)
   f.text(xx,.163,'G  '+' / '.join(f'{r.G:.3f}' for r in rr.itertuples()),ha='center',fontsize=8.5)
   f.text(xx,.111,'Needs (%)  '+' / '.join(f'{100*r.Umax:.2f}' for r in rr.itertuples()),ha='center',fontsize=8.5)
  f.legend(handles=[Line2D([],[],c=TEAL,marker='o',label='Cumulative innovation gain'),Line2D([],[],c=ROSE,marker='s',label='Mean worst-group needs'),Line2D([],[],c=GRAY,ls=':',label='Reference parameter')],ncol=3,loc='upper center',bbox_to_anchor=(.5,.99),frameon=False,fontsize=9)
  footer(f,'Every point reoptimizes the same problem. Numeric keys give first, reference, and last outcomes.',.061)
  footer(f,'Higher needs penalties reduce growth and needs; Egypt changes sharply near the reference weight.' if var=='omega' else 'Larger economic quality jumps increase growth and needs. This is separate from a GPT version update.')
  finish(f,name,out,reg,'Matched scans expose how innovation gains and needs depend on assumed parameters.',['matched-sensitivity.csv'])

 f,aa=grid(4.2,.34,.82);settings=['1','2','3','4']
 for j,c in enumerate(COUNTRIES):
  d=ref[ref.country.eq(c)].sort_values('grid');x=np.arange(len(d));aa[0,j].set_title(c)
  aa[0,j].semilogy(x,d.rollout_value_error_percent,'o-',c=TEAL,ms=4)
  aa[0,j].yaxis.set_major_formatter(FuncFormatter(lambda v,_:f'{v:g}'));aa[0,j].yaxis.set_minor_formatter(plt.NullFormatter())
  aa[1,j].plot(x,d.G_relative_to_finest_percent,'s-',c=ROSE,ms=4);aa[1,j].axhline(0,c=GRAY,ls=':',lw=.7)
  for i,vs in enumerate([d.rollout_value_error_percent,d.G_relative_to_finest_percent]):
   aa[i,j].margins(x=.15,y=.4);aa[i,j].set(xticks=x,xticklabels=[] if i==0 else settings)
   if i==1:aa[i,j].set_xlabel('Refinement setting')
  if j==0:aa[0,j].set_ylabel('Value error (%)');aa[1,j].set_ylabel('G vs finest (%)')
 footer(f,'Settings (state/action/interval): 1 = 41/31/.5; 2 = 61/41/.25; 3 = 81/61/.25; 4 = 101/61/.125.',.086)
 footer(f,'Small value discrepancies can coexist with sizeable relative differences in Egypt\'s small growth gain.')
 finish(f,'fig_r3_refinement',out,reg,'Value-function agreement does not certify every path statistic.',['country-refinement.csv'])

 gx,gy=np.sort(field.u_A.unique()),np.sort(field.u_B.unique())
 def mat(col):return field.pivot(index='u_B',columns='u_A',values=col).loc[gy,gx].to_numpy()
 N,A,du,dv=mat('n'),mat('a'),mat('du_A'),mat('du_B');dp=selected(paths,'Germany',ALL[-1][0],ALL[-1][1])
 def marks(ax):
  ax.plot(100*dp.u_A,100*dp.u_B,c=ROSE,lw=1.8)
  ax.scatter(8,8,s=25,facecolors='white',edgecolors=INK,zorder=5)
  ax.scatter(100*dp.u_A.iloc[-1],100*dp.u_B.iloc[-1],s=65,marker='*',c=ROSE,zorder=6)
 f,aa=plt.subplots(1,2,figsize=(7,3.6));f.subplots_adjust(left=.09,right=.85,bottom=.34,top=.83,wspace=.67)
 for ax,z,cmap,title,unit in zip(aa,[100*N,A],[SEQ,AID],['A  State-dependent research','B  State-dependent assistance'],['Research labor (%)','Assistance intensity']):
  im=ax.pcolormesh(100*gx,100*gy,z,cmap=cmap,shading='nearest',rasterized=False)
  cb=f.colorbar(im,ax=ax,pad=.04,fraction=.055);cb.set_label(unit,fontsize=9,labelpad=12);cb.solids.set_rasterized(False)
  marks(ax);ax.set(title=title,xlabel='Needs A (%)',ylabel='Needs B (%)',xticks=[0,20,40],yticks=[0,20,40]);ax.grid(False)
 f.legend(handles=[Line2D([],[],c=ROSE,label='Reoptimized path'),Line2D([],[],marker='o',markerfacecolor='white',c=INK,lw=0,label='Start (8%, 8%)'),Line2D([],[],marker='*',c=ROSE,lw=0,ms=8,label='Tested endpoint')],ncol=3,loc='upper center',bbox_to_anchor=(.5,1),frameon=False,fontsize=9)
 footer(f,f'Endpoint: needs = ({100*dp.u_A.iloc[-1]:.2f}, {100*dp.u_B.iloc[-1]:.2f})%; research = {100*dp.n.iloc[-1]:.2f}%; assistance = {dp.a.iloc[-1]:.3f}.',.085)
 footer(f,'Germany conditional planner. Colors show sampled actions; paths reoptimize using value, not interpolated controls.')
 finish(f,'fig_r3_action_fields',out,reg,'Research and assistance depend on current need states.',['systems/planner-phase-field.csv','country-paths.csv'])

 f,aa=plt.subplots(1,2,figsize=(7,3.2));f.subplots_adjust(left=.09,right=.97,bottom=.32,top=.80,wspace=.58)
 im=aa[0].pcolormesh(100*gx,100*gy,100*N,cmap=SEQ,shading='nearest',rasterized=False)
 cb=f.colorbar(im,ax=aa[0],fraction=.045,pad=.03);cb.set_label('Research labor (%)',fontsize=8.5,labelpad=12);cb.solids.set_rasterized(False)
 aa[0].streamplot(100*gx,100*gy,100*du,100*dv,color=INK,density=.48,linewidth=.55,arrowsize=.65)
 marks(aa[0]);aa[0].set(title='A  Feedback depends on needs',xlabel='Needs A (%)',ylabel='Needs B (%)',xticks=[0,20,40],yticks=[0,20,40]);aa[0].grid(False)
 for pol,src,lab,col,ls in ALL:
  d=selected(paths,'Germany',pol,src);aa[1].plot(d.t,d.log_quality,c=col,ls=ls,lw=1.5)
 aa[1].set(title='B  A steady rate adds quality',xlabel='Model time',ylabel='Cumulative gain G(t)',xlim=(0,100),xticks=[0,50,100]);legend(f,ALL,.995)
 footer(f,'A: arrows = local change; open circle = start; star = tested endpoint. B: planner endpoint G = 1.665.',.070)
 footer(f,'Germany: needs settle at (6.75%, 3.26%); the log-quality growth rate approaches 0.01665 per model-time unit.')
 finish(f,'fig_r3_system_summary',out,reg,'Stationary needs coexist with continuing cumulative quality growth.',['systems/planner-phase-field.csv','country-paths.csv'])

 f,aa=plt.subplots(1,2,figsize=(7,4.0));f.subplots_adjust(left=.11,right=.96,bottom=.40,top=.82,wspace=.58)
 for row,mark,off in zip(up.itertuples(),['o','s','D'],[(-36,23),(5,16),(-12,-22)]):
  xx,yy=100*row.upgrade_change_G,100*row.upgrade_change_Umax
  aa[0].scatter(xx,yy,s=40,c=TEAL,marker=mark)
  aa[0].annotate(row.country,(xx,yy),xytext=off,textcoords='offset points',fontsize=8.5)
 aa[0].set(xlim=(-.48,.01),ylim=(-.045,.005),xlabel='Quality-gain change (100 Delta G)',ylabel='Mean-needs change (pp)',title='A  Less growth and fewer needs')
 aa[0].grid(False);aa[1].grid(False)
 yy=np.arange(3);vs=100*up.upgrade_absolute_bias_change_Umax.to_numpy()
 aa[1].barh(yy,vs,color=[TEAL if v<0 else ROSE for v in vs],height=.5);aa[1].axvline(0,c=INK,lw=.8)
 aa[1].set(yticks=yy,yticklabels=up.country,xlim=(-.065,.065),xlabel='Absolute needs-gap change (pp)',title='B  Reference fidelity can worsen');aa[1].invert_yaxis()
 for y,v in zip(yy,vs):aa[1].text(v+(.006 if v>=0 else -.006),y,f'{v:+.4f}',ha='left' if v>=0 else 'right',va='center',fontsize=8.5)
 footer(f,'Coordinates (100 Delta G, needs pp): China (-.270, -.0313); Germany (-.195, -.0288); Egypt (-.401, -.0323).',.155)
 footer(f,'GPT-5.6 Sol minus GPT-5.5. Gap change: negative = closer to the human rule; positive = farther.',.085)
 footer(f,'Outcome direction and reference fidelity differ; human advice is not a proven welfare optimum.')
 finish(f,'fig_r3_upgrade_comparisons',out,reg,'Lower needs do not always mean closer human-reference needs.',['three-country-upgrade-comparison.csv'])

 val=pd.read_csv(DATA/'systems/market-valuation-sheet.csv');x,y=np.sort(val.u_A.unique()),np.sort(val.u_B.unique())
 z=val.pivot(index='u_A',columns='u_B',values='patent_value').loc[x,y].to_numpy();X,Y=np.meshgrid(100*x,100*y,indexing='ij')
 f=plt.figure(figsize=(7,3.6));ax=f.add_axes([.03,.25,.47,.64],projection='3d')
 ax.plot_surface(X,Y,z,cmap=SEQ,edgecolor=DIVIDER,linewidth=.3,antialiased=True,rasterized=False)
 ax.set(xticks=[],yticks=[],zticks=[],zlim=(.3138,.3169))
 ax.tick_params(pad=8,labelsize=8);ax.view_init(elev=25,azim=-55);ax.grid(False)
 for axis in (ax.xaxis,ax.yaxis,ax.zaxis):axis.pane.set_visible(False)
 f.text(.075,.21,'X: needs A (0–85%)',fontsize=9)
 f.text(.285,.21,'Y: needs B (0–85%)',fontsize=9)
 f.text(.485,.53,'Z: patent value vM',fontsize=9,rotation=90,ha='center')
 ax2=f.add_axes([.63,.30,.26,.53]);im=ax2.pcolormesh(100*x,100*y,z.T,cmap=SEQ,shading='nearest',rasterized=False)
 cb=f.colorbar(im,ax=ax2,fraction=.08,pad=.05);cb.solids.set_rasterized(False);cb.set_label('Normalized patent value',fontsize=9,labelpad=12)
 ax2.set(xlabel='Needs A (%)',ylabel='Needs B (%)',xticks=[0,40,80],yticks=[0,40,80]);ax2.grid(False)
 f.text(.20,.93,'A  Forward-selected pricing sheet',ha='center',fontsize=10)
 f.text(.73,.93,'B  Same values, overhead view',ha='center',fontsize=10)
 footer(f,f'Value range {z.min():.6f} to {z.max():.6f}; variation is {100*(z.max()/z.min()-1):.2f}%. The vertical axis is truncated.',.082)
 footer(f,'Germany human-rule market; 121 solved initial states. Patent value is neither physical energy nor social welfare.')
 finish(f,'fig_r3_market_valuation',out,reg,'Initial needs alter normalized patent value modestly; the plotted range is disclosed.',['systems/market-valuation-sheet.csv'])

 f=plt.figure(figsize=(7,3.8));ax=f.add_axes([.10,.34,.29,.49]);ax3=f.add_axes([.50,.29,.41,.59],projection='3d')
 ax.streamplot(100*gx,100*gy,100*du,100*dv,color=GRAY,density=.65,linewidth=.6)
 dd=paths[paths.country.eq('Germany')&paths.policy.eq(ALL[-1][0])]
 for (ini,g),mark in zip(dd.groupby(['initial_u_A','initial_u_B']),['o','s','^','D','v','P']):
  g=g.sort_values('t')
  if max(ini)<=.4:
   ax.plot(100*g.u_A,100*g.u_B,c=TEAL,lw=1.3)
   ax.scatter(100*g.u_A.iloc[0],100*g.u_B.iloc[0],marker=mark,facecolors='white',edgecolors=INK,s=25,zorder=4)
   arrows(ax,100*g.u_A.to_numpy(),100*g.u_B.to_numpy())
  ax3.plot(g.log_quality,100*g.u_A,100*g.u_B,c=TEAL,lw=1.1)
  ax3.scatter(0,100*g.u_A.iloc[0],100*g.u_B.iloc[0],marker=mark,c=INK,s=16)
 ax.scatter(100*dp.u_A.iloc[-1],100*dp.u_B.iloc[-1],c=ROSE,marker='*',s=75,zorder=6)
 ax.set(xlabel='Needs A (%)',ylabel='Needs B (%)',xlim=(-1,40),ylim=(-1,40),xticks=[0,20,40],yticks=[0,20,40])
 ax3.set(xticks=[],yticks=[],zticks=[]);ax3.view_init(elev=23,azim=-65);ax3.grid(False)
 for axis in (ax3.xaxis,ax3.yaxis,ax3.zaxis):axis.pane.set_visible(False)
 f.text(.53,.22,'X: quality gain G',fontsize=9)
 f.text(.75,.22,'Y: needs A (%)',fontsize=9)
 f.text(.94,.59,'Z: needs B (%)',fontsize=9,rotation=90,ha='center')
 f.text(.25,.94,'A  Needs approach a steady state',ha='center',fontsize=10)
 f.text(.72,.94,'B  Quality follows growth rays',ha='center',fontsize=10)
 footer(f,'Arrows = local change; markers = starts; star = endpoint. Four paths fit in A; all six appear in B.',.082)
 footer(f,'Germany conditional planner: growing quality and steady needs coexist. No global stability theorem is claimed.')
 finish(f,'fig_r3_phase_growth',out,reg,'Needs settle while quality continues along the tested balanced-growth rays.',['systems/planner-phase-field.csv','country-paths.csv'])
 (out/'publication-figure-manifest.json').write_text(json.dumps({'iconography_mode':'minimal-scientific',
  'palette':{'ink':INK,'primary':TEAL,'secondary':BLUE,'status_accent':ROSE,'surface':SURFACE,'divider':DIVIDER},
  'style_reference':'Retained empirical figures: serif type, navy ink, teal and rose, quiet panels.',
  'semantic_graphics':[item for f in reg for item in f['semantic_graphics']],
  'composition_mechanism':'Shared country columns, aligned outcome rows, protected numerical keys and explicit unit/color scales.',
  'grayscale_encoding':'Dashed/dash-dot advisers, open starts and star endpoints, distinct scan markers, and signed numeric keys accompany color.',
  'minimum_design_font_points':8,'width_inches':7,'figures':reg},indent=2)+'\n')
 print(json.dumps({'publication_figures':len(reg),'outdir':str(out)}))

if __name__=='__main__':main()
