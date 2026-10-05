"""Preserve empirical panels A--D; add computed valuation and feedback views.

The lower-row surfaces and paths come exclusively from frozen R3 CSV files.
"""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('restore',ROOT/'assets/figure_sources/compose_structural_hero.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
DATA=ROOT/'experiments/ah_growth/country_revision_results'
SEQ=LinearSegmentedColormap.from_list('ethos_hero',['#EFF7F7','#77BFC0',m.TEAL])

def valuation():
 f=plt.figure(figsize=(495/72,280/72));ax=f.add_axes([.025,.21,.84,.67],projection='3d')
 d=pd.read_csv(DATA/'systems/market-valuation-sheet.csv')
 x,y=np.sort(d.u_A.unique()),np.sort(d.u_B.unique())
 z=d.pivot(index='u_A',columns='u_B',values='patent_value').loc[x,y].to_numpy()
 X,Y=np.meshgrid(100*x,100*y,indexing='ij')
 ax.plot_surface(X,Y,z,cmap=SEQ,edgecolor='#CFD9E3',linewidth=.5,rasterized=False)
 ax.set(xticks=[],yticks=[],zticks=[],zlim=(.3138,.3169))
 ax.view_init(elev=24,azim=-55)
 for axis in (ax.xaxis,ax.yaxis,ax.zaxis):axis.pane.set_visible(False)
 ax.grid(False)
 f.text(.11,.155,'X: needs A',fontsize=16)
 f.text(.54,.155,'Y: needs B',fontsize=16)
 f.text(.855,.48,'Z: patent value vM',fontsize=17,rotation=90,ha='center')
 f.text(.035,.947,'E  Need states shape patent prices',fontsize=20,weight='bold')
 f.text(.075,.090,'Needs A and B span 0–85%; 121 solved starts.',fontsize=15)
 f.text(.075,.025,'vM: .31415–.31670 | truncated Z | 0.81% range',fontsize=15)
 return m.plot_svg(f,'R3-market-surface')

def feedback():
 f=plt.figure(figsize=(354/72,280/72));ax=f.add_axes([.17,.37,.58,.45])
 d=pd.read_csv(DATA/'systems/planner-phase-field.csv')
 x,y=np.sort(d.u_A.unique()),np.sort(d.u_B.unique())
 def mat(col):return d.pivot(index='u_B',columns='u_A',values=col).loc[y,x].to_numpy()
 im=ax.pcolormesh(100*x,100*y,100*mat('n'),cmap=SEQ,shading='nearest',rasterized=False)
 ax.streamplot(100*x,100*y,100*mat('du_A'),100*mat('du_B'),color=m.INK,density=.52,linewidth=.7,arrowsize=.65)
 p=pd.read_csv(DATA/'country-paths.csv');p=p[p.country.eq('Germany')&p.policy.eq('planner held optimal control')]
 for ini,g in p.groupby(['initial_u_A','initial_u_B']):
  if max(ini)>.4:continue
  g=g.sort_values('t');ax.plot(100*g.u_A,100*g.u_B,c=m.ROSE,lw=1.8)
  ax.scatter(100*g.u_A.iloc[0],100*g.u_B.iloc[0],s=30,facecolors='white',edgecolors=m.INK,zorder=5)
 ax.scatter(100*g.u_A.iloc[-1],100*g.u_B.iloc[-1],s=95,marker='*',c=m.ROSE,zorder=6)
 ax.set(xlabel='Needs A (%)',ylabel='Needs B (%)',xticks=[0,20,40],yticks=[0,20,40],xlim=(-1,40),ylim=(-1,40))
 ax.tick_params(labelsize=16,pad=3);ax.xaxis.labelpad=6;ax.yaxis.labelpad=5;ax.grid(False)
 cax=f.add_axes([.83,.37,.035,.45]);cb=f.colorbar(im,cax=cax);cb.solids.set_rasterized(False)
 cb.ax.tick_params(labelsize=16,pad=3);cb.set_ticks([5.5,6.5,7.5])
 f.text(.78,.866,'n (%)',fontsize=17)
 f.text(.035,.947,'F  Planner feedback and state flow',fontsize=20,weight='bold')
 f.legend(handles=[Line2D([],[],c=m.ROSE,lw=1.6,label='Path'),
  Line2D([],[],marker='o',c=m.INK,markerfacecolor='white',lw=0,label='Start'),
  Line2D([],[],marker='*',c=m.ROSE,lw=0,ms=8,label='End')],
  ncol=3,loc='upper center',bbox_to_anchor=(.53,.21),frameon=False,fontsize=16,
  handlelength=1,columnspacing=.9,handletextpad=.4)
 f.text(.065,.025,'Needs settle; growth g* = .01665 > 0',fontsize=16)
 return m.plot_svg(f,'R3-feedback-field')

if __name__=='__main__':
 m.boundary_panel=valuation;m.outcomes_panel=feedback
 old_text=m.simple_text
 def heading(root,x,y,content,*args,**kwargs):
  return old_text(root,x,y,'Conditional Germany model: market valuation and state-dependent innovation support',*args,**kwargs)
 m.simple_text=heading
 saved_export=m.export;m.export=lambda root,name:root
 root=m.hero();root.set('height','1030');root.set('viewBox','0 0 900 1030')
 for group_id in ['illustrative-transition-panel','illustrative-outcomes-panel']:
  group=next(g for g in root.iter() if g.get('id')==group_id)
  child=list(group)[0];child.set('height','280')
 print(saved_export(root,'fig1_extended_hero'))
