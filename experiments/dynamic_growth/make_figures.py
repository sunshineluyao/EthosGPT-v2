"""Editable, serif publication figures from the released result tables.

Figures have a final width of 6.9 inches and minimum 8.5 pt ordinary text.
Measured representation and simulated mechanisms are separated explicitly.
"""
from pathlib import Path
import json,hashlib
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle,Polygon,FancyArrowPatch
from matplotlib.colors import ListedColormap
from scipy.special import expit
from scipy.optimize import brentq
from scipy.integrate import solve_ivp
from dynamics import P,fold,equilibrium,equilibria,jacobian

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'results'
FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
SAMPLES=ROOT/'sample_results'
INK='#17293F';TEAL='#007F86';PINK='#B93678';GOLD='#A97512';GREY='#728091';PALE='#F4F7FA'
COLORS={'Reference advice':TEAL,'Overoptimistic advice':PINK,'More adjustment':GOLD,'Best admissible menu point':INK}
SHAPES={'Reference advice':'o','Overoptimistic advice':'X','More adjustment':'^','Best admissible menu point':'D'}
plt.rcParams.update({'font.family':'STIXGeneral','mathtext.fontset':'stix','font.size':9,'axes.titlesize':10,'axes.labelsize':9,'axes.titleweight':'normal','axes.edgecolor':'#8994A2','axes.labelcolor':INK,'text.color':INK,'xtick.color':INK,'ytick.color':INK,'xtick.labelsize':8.5,'ytick.labelsize':8.5,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.65,'lines.linewidth':1.6,'svg.fonttype':'none','pdf.fonttype':42,'figure.facecolor':'white','axes.facecolor':'white','legend.fontsize':8.5,'savefig.facecolor':'white'})
MANIFEST=[]


def read(name):return pd.read_csv(DATA/name)
def decorate(ax,title,xlabel,ylabel):
    ax.set_title(title,loc='left',pad=11)
    ax.set_xlabel(xlabel,labelpad=7);ax.set_ylabel(ylabel,labelpad=7)
    ax.grid(alpha=.14,linewidth=.5);ax.set_axisbelow(True)
    ax.tick_params(length=3,width=.6,pad=5)


def save(fig,name,inputs,scope='Computed mechanism study'):
    for ax in fig.axes:
        ax.tick_params(pad=5)
    for extension in ['pdf','svg','png']:
        fig.savefig(FIG/(name+'.'+extension),dpi=210,metadata={'Creator':'Matplotlib'} if extension=='pdf' else None)
    # Chart labels are intentionally free rather than text inside diagram nodes.
    svg=FIG/(name+'.svg');tree=ET.parse(svg)
    for index,node in enumerate(tree.getroot().iter('{http://www.w3.org/2000/svg}text')):
        node.set('data-containment','free')
        if 'id' not in node.attrib:node.set('id',f'{name}-label-{index}')
    root=tree.getroot()
    title=ET.Element('{http://www.w3.org/2000/svg}title');title.text=name.replace('_',' ')
    root.insert(0,title)
    temporary=svg.with_suffix('.svg.tmp');tree.write(temporary,encoding='utf-8',xml_declaration=True)
    temporary.replace(svg)
    MANIFEST.append({'figure':name,'width_inches':float(fig.get_figwidth()),'height_inches':float(fig.get_figheight()),'evidence_status':scope,'input_files':inputs,'input_sha256':{s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in inputs},'exports':{e:hashlib.sha256((FIG/(name+'.'+e)).read_bytes()).hexdigest() for e in ['pdf','svg','png']},'editable_master':name+'.svg','raster_layers':False,'font_family':'STIXGeneral','ordinary_font_floor_pt':8.5})
    plt.close(fig)


def envelope(frame):
    ordered=frame.sort_values(['worst_burden','growth'],ascending=[True,False])
    best=-np.inf;keep=[]
    for r in ordered.itertuples(index=False):
        if r.growth>best+1e-12:keep.append(r);best=r.growth
    return pd.DataFrame(keep)


def policy_points(ax,compact=False,menu=True):
    if menu:
        grid=read('policy_menu.csv')
        ax.scatter(grid.worst_burden*100,grid.growth*100,s=2,c=GREY,alpha=.18,linewidths=0)
        e=envelope(grid);ax.plot(e.worst_burden*100,e.growth*100,color=INK,linewidth=.8)
    for r in read('selected_policies.csv').itertuples(index=False):
        if compact and r.policy=='Best admissible menu point':continue
        ax.scatter(r.worst_burden*100,r.growth*100,s=36,marker=SHAPES[r.policy],c=COLORS[r.policy],edgecolors='white',linewidths=.5,zorder=6,label=r.policy)


def small_book(ax,x,y):
    ax.add_patch(Rectangle((x,y),.033,.17,fill=False,edgecolor=INK,linewidth=.9,gid='hero-literature-book'))
    for i in range(3):ax.plot([x+.005,x+.027],[y+.125-i*.025]*2,color=INK,linewidth=.6)
    ax.plot([x+.034,x+.061,x+.061],[y+.025,y+.003,y+.146],color=INK,linewidth=.9)


def hero():
    fig=plt.figure(figsize=(6.9,4.4))
    top=fig.add_axes([.018,.73,.964,.26]);top.set_axis_off();top.set_xlim(0,1);top.set_ylim(0,1)
    top.text(.0,.95,'Whose values guide technological change?',fontsize=12.5,va='top')
    top.text(.0,.70,'2025 economics Nobel: useful knowledge, innovation, and creative destruction',fontsize=9.5,va='top')
    small_book(top,.0,.32)
    top.text(.08,.42,'Mokyr',fontsize=10,va='center',gid='hero-mokyr-label');top.text(.08,.22,'Knowledge and institutions',fontsize=9,va='center')
    for i in range(4):top.plot([.37+i*.032,.40+i*.032],[.22+i*.046]*2,color=TEAL,linewidth=1.4)
    top.add_patch(FancyArrowPatch((.365,.205),(.506,.422),arrowstyle='-|>',mutation_scale=7,color=TEAL,linewidth=.7,gid='hero-quality-ladder'))
    top.text(.53,.42,'Aghion and Howitt',fontsize=10,va='center',gid='hero-quality-label');top.text(.53,.22,'Higher quality through replacement',fontsize=9,va='center')
    top.plot([0,1],[.10,.10],color='#CED5DD',linewidth=.6)
    # Protected panel titles and evidence classes.
    fig.text(.02,.695,'A  Measured representation',fontsize=10,gid='representation-label')
    fig.text(.355,.695,'B  Simulated transition boundary',fontsize=10)
    fig.text(.69,.695,'C  Simulated outcomes',fontsize=10)
    ax=fig.add_axes([.112,.31,.202,.30]);ax.set_gid('measured-agreement')
    estimates=pd.read_csv(ROOT/'inputs/metric_estimates.csv')
    tvd=estimates[estimates.metric=='TVD']
    for y,(model,color) in enumerate([('GPT-5.5',INK),('GPT-5.6 Sol',TEAL)]):
        r=tvd[tvd.model==model].iloc[0]
        ax.errorbar(r.estimate,y,xerr=[[r.estimate-r.ci_low_bca],[r.ci_high_bca-r.estimate]],fmt='o',color=color,markersize=4,capsize=2,linewidth=1)
    ax.set_yticks([0,1],['GPT-5.5','GPT-5.6 Sol']);ax.set_xlim(.275,.34);ax.set_xticks([.28,.31,.34]);ax.set_ylim(-.6,1.6)
    ax.set_xlabel('Category-share error',fontsize=9);ax.grid(axis='x',alpha=.14)
    fig.text(.026,.13,'64 countries; six questions\nMost improvement: Q106/Q108',fontsize=8.5,va='center')
    ax=fig.add_axes([.412,.31,.213,.30]);ax.set_gid('perceived-transition-boundary')
    b=read('boundary.csv');a=b.aid
    ax.plot(a,b.actual_fold,c=TEAL,label='Actual');ax.plot(a,b.perceived_fold,c=PINK,ls='--',label='Perceived')
    ax.plot(a,b.budget_capacity,c=INK,ls=':',lw=1)
    ax.fill_between(a,b.actual_fold,np.minimum(b.perceived_fold,b.budget_capacity),where=b.budget_capacity>b.actual_fold,color=PINK,alpha=.13)
    ax.set_xlim(0,.72);ax.set_ylim(.6,2.5);ax.set_xticks([0,.35,.7]);ax.set_yticks([1,2]);ax.set_xlabel('Aid allocation');ax.set_ylabel('Launch intensity',labelpad=7)
    ax.grid(alpha=.13)
    fig.text(.357,.13,'Perceived limits change;\nactual paths follow policy choices.',fontsize=8.5,va='center')
    ax=fig.add_axes([.766,.31,.209,.30]);ax.set_gid('quality-and-adjustment-outcomes')
    policy_points(ax,compact=True)
    ax.set_xlim(0,80);ax.set_ylim(0,15);ax.set_xticks([0,40,80]);ax.set_yticks([0,7,14]);ax.set_xlabel('Worst-group exposure (%)');ax.set_ylabel('Quality growth (log points)',labelpad=7)
    ax.grid(alpha=.13)
    fig.text(.693,.13,'Same system and spending\nLow exposure can reflect\nstalled adoption.',fontsize=8.5,va='center',gid='policy-consequences-label')
    handles=[Line2D([],[],color=TEAL,marker='o',lw=1,label='Reference'),Line2D([],[],color=PINK,marker='X',ls='--',lw=1,label='Overoptimistic advice'),Line2D([],[],color=GOLD,marker='^',lw=1,label='More adjustment')]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.57,.005),ncol=3,frameon=False,columnspacing=1.3,handlelength=1.6)
    save(fig,'fig_dynamic_hero',['inputs/metric_estimates.csv','results/boundary.csv','results/policy_menu.csv','results/selected_policies.csv'],'Measured survey comparison and separately labeled illustrative mechanisms')


def gallery():
    fig,axs=plt.subplots(2,2,figsize=(6.9,5.2))
    fig.subplots_adjust(left=.10,right=.985,top=.92,bottom=.20,wspace=.43,hspace=.8)
    ax=axs[0,0]
    d=read('continuation.csv')
    for c,col in [(0,TEAL),(.18,PINK)]:
        g=d[np.isclose(d.culture,c)&d.nu.between(.35,1.7)]
        for stable,style in [(True,'-'),(False,'--')]:
            ax.plot(g.nu,np.where(g.stable==stable,g.z,np.nan),c=col,ls=style,lw=1.5)
        z,n=fold(.3,c);ax.scatter(n,z,c=col,marker='D',s=23,zorder=5)
    ax.set_xlim(.35,1.7);ax.set_ylim(-1.5,1.45)
    decorate(ax,'A  Reinforcing feedback creates a threshold','Launch intensity','Coordination')
    ax=axs[0,1]
    d=read('error_sensitivity_controls.csv')
    for label,col,style in [('Fold example',TEAL,'-'),('No-fold control',GREY,'--')]:
        g=d[d.system==label];ax.plot(g.assumed_error,100*g.growth,c=col,ls=style,label=label)
    fig.legend(handles=ax.get_legend_handles_labels()[0],labels=['Fold','No fold'],loc='center',bbox_to_anchor=(.75,.54),ncol=2,frameon=False,handlelength=1.4,handletextpad=.8,columnspacing=1.2)
    decorate(ax,'B  A threshold is not inevitable','Assumed adviser-channel error','Quality growth (log points)')
    ax=axs[1,0]
    d=read('audit_linked_policy_results.csv')
    s=pd.read_csv(ROOT/'inputs/country_question_scores.csv').groupby(['model','country']).tvd.mean()
    baseline=read('selected_policies.csv').iloc[0].growth
    for model,col,mark in [('GPT-5.5',INK,'o'),('GPT-5.6 Sol',TEAL,'^')]:
        g=d[(d.model==model)&(d['shape']=='linear')&(d.strength==1)&(d['items']=='all six')]
        x=[s.loc[(model,c)] for c in g.country]
        ax.scatter(x,100*(g.growth-baseline),c=col,marker=mark,s=12,alpha=.6,linewidths=0,label=model)
    ax.axhline(0,c=GREY,lw=.7,ls=':')
    fig.legend(handles=ax.get_legend_handles_labels()[0],labels=ax.get_legend_handles_labels()[1],loc='center',bbox_to_anchor=(.29,.055),ncol=2,frameon=False,handletextpad=.8,columnspacing=1.)
    decorate(ax,'C  Measured errors, conditional outcomes','Mean category-share error','Quality-growth change (log points)')
    ax=axs[1,1]
    d=read('rollout_rate_grid.csv')
    for delta,col,style in [(0,INK,'-'),(.025,GOLD,'-'),(.05,GOLD,'--')]:
        g=d[np.isclose(d.adjustment_allocation,delta)]
        ax.plot(g.rollout_rate,100*g.growth,c=col,ls=style,lw=1.5,label=f'Extra aid {100*delta:g}%')
        for r in g.itertuples(index=False):
            ax.scatter(r.rollout_rate,100*r.growth,s=22,facecolor=col if r.admissible else 'white',edgecolor=col,lw=.8,zorder=4)
    ax.axhline(10,c=GREY,lw=.7,ls=':');ax.set_xscale('log',base=2);ax.set_xticks([.05,.2,.8,3.2],['.05','.2','.8','3.2']);ax.set_ylim(6,11.3)
    handles,labels=ax.get_legend_handles_labels()
    fig.legend(handles,[s.replace('Extra aid ','') for s in labels],loc='center',bbox_to_anchor=(.755,.055),ncol=3,frameon=False,handlelength=1.2,columnspacing=.8,handletextpad=.7)
    decorate(ax,'D  Adjustment widens tested viable rates','Technology-rollout rate','Quality growth (log points)')
    save(fig,'fig_dynamic_results_gallery',['results/continuation.csv','results/error_sensitivity_controls.csv','results/audit_linked_policy_results.csv','inputs/country_question_scores.csv','results/selected_policies.csv','results/rollout_rate_grid.csv'])


def policy_tradeoff():
    fig,axs=plt.subplots(1,2,figsize=(6.9,4.2));fig.subplots_adjust(left=.10,right=.89,top=.88,bottom=.30,wspace=.50)
    ax=axs[0];policy_points(ax)
    ax.axhline(10,c=GREY,lw=.7,ls=':');ax.axvline(50,c=GREY,lw=.7,ls=':')
    ax.set_xlim(0,85);ax.set_ylim(0,15)
    decorate(ax,'A  The shared attainable set','Worst-group exposure (%)','Quality growth (log points)')
    predicted=read('predicted_policy_point.csv').iloc[0];actual=read('selected_policies.csv').iloc[1]
    ax.scatter(100*predicted.worst_burden,100*predicted.growth,s=34,marker='X',facecolors='white',edgecolors=PINK,zorder=5)
    ax.annotate('',xy=(100*actual.worst_burden,100*actual.growth),xytext=(100*predicted.worst_burden,100*predicted.growth),arrowprops={'arrowstyle':'->','lw':.9,'color':PINK})
    ax=axs[1];d=read('exact_spending_menu.csv')
    ax.plot(d.aid,100*d.growth,c=TEAL,label='Quality growth')
    ax2=ax.twinx();ax2.plot(d.aid,100*d.worst_burden,c=GOLD,ls='--',label='Worst exposure')
    ax2.set_ylabel('Worst-group exposure (%)',labelpad=8,color=GOLD);ax2.tick_params(labelsize=8.5,colors=GOLD)
    ax.set_xlim(0,.9);ax.set_ylim(0,15);ax2.set_ylim(0,90)
    decorate(ax,'B  Allocating the same spending','Aid allocation','Quality growth (log points)')
    handles=[Line2D([],[],marker=SHAPES[n],c=COLORS[n],lw=0,label=n) for n in COLORS]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.03),ncol=2,frameon=False,columnspacing=2)
    save(fig,'fig_dynamic_policy_tradeoff',['results/policy_menu.csv','results/exact_spending_menu.csv','results/selected_policies.csv','results/predicted_policy_point.csv'])


def policy_paths():
    fig,axs=plt.subplots(1,2,figsize=(6.9,4.0));fig.subplots_adjust(left=.095,right=.99,top=.87,bottom=.35,wspace=.39)
    d=read('selected_policy_paths.csv')
    for name,g in d.groupby('policy',sort=False):
        axs[0].plot(g.time,100*g.adoption,c=COLORS[name],label=name)
        axs[1].plot(g.time,100*g.group_A_exposure,c=COLORS[name]);axs[1].plot(g.time,100*g.group_B_exposure,c=COLORS[name],ls='--',lw=1)
    decorate(axs[0],'A  Adoption over time','Normalized time','Adoption (%)')
    decorate(axs[1],'B  Two groups face different burdens','Normalized time','Transition exposure (%)')
    for ax in axs:ax.set_xlim(0,60);ax.set_ylim(0,100 if ax is axs[0] else 65)
    fig.legend(handles=[Line2D([],[],c=COLORS[n],label=n) for n in COLORS],loc='lower center',bbox_to_anchor=(.5,.048),ncol=2,frameon=False)
    fig.text(.102,.015,'Solid exposure paths: group A. Dashed: group B. Every policy spends the same resource budget.',fontsize=8.5)
    save(fig,'fig_dynamic_policy_paths',['results/selected_policy_paths.csv'])


def culture_families():
    fig,axs=plt.subplots(2,3,figsize=(6.9,5.2));fig.subplots_adjust(left=.09,right=.99,top=.89,bottom=.28,wspace=.39,hspace=.65)
    d=read('cultural_families.csv');families=['C0','C1','C2','C3','C4']
    for col,shape in enumerate(['linear','saturating','spline']):
        for name in ['Reference advice','Overoptimistic advice','More adjustment']:
            g=d[(d['shape']==shape)&(d.policy==name)].set_index('family').reindex(families)
            axs[0,col].plot(range(5),100*g.growth,c=COLORS[name],marker=SHAPES[name],markersize=3)
            axs[1,col].plot(range(5),100*g.worst_burden,c=COLORS[name],marker=SHAPES[name],markersize=3)
        axs[0,col].axhline(10,c=GREY,ls=':',lw=.7);axs[1,col].axhline(50,c=GREY,ls=':',lw=.7)
        for row in [0,1]:axs[row,col].set_xticks(range(5),families);axs[row,col].grid(alpha=.14)
        axs[0,col].set_title(shape.capitalize()+' response',loc='left',pad=11)
        axs[1,col].set_xlabel('Cultural-change family')
        axs[0,col].set_ylim(1.5,12.5);axs[1,col].set_ylim(10,60)
    axs[0,0].set_ylabel('Quality growth (log points)');axs[1,0].set_ylabel('Worst-group exposure (%)')
    fig.legend(handles=[Line2D([],[],c=COLORS[n],marker=SHAPES[n],label=n) for n in ['Reference advice','Overoptimistic advice','More adjustment']],loc='lower center',bbox_to_anchor=(.5,.061),ncol=3,frameon=False)
    fig.text(.09,.018,'C0 unchanged; C1 drift; C2 outcome feedback; C3 group interaction; C4 memory and a temporary shock.',fontsize=8.5)
    save(fig,'fig_dynamic_culture_families',['results/cultural_families.csv'])


def lag_and_rates():
    fig,axs=plt.subplots(1,2,figsize=(6.9,3.8));fig.subplots_adjust(left=.095,right=.99,top=.87,bottom=.40,wspace=.40)
    d=read('lag_rate_grid.csv').pivot(index='adviser_lag',columns='forcing_rate',values='adoption_final')
    ax=axs[0];mesh=ax.pcolormesh(np.arange(8)-.5,np.arange(6)-.5,d.to_numpy()*100,cmap='Blues',vmin=0,vmax=100,rasterized=False)
    ax.set_xticks(range(7),['.05','.1','.2','.4','.8','1.6','3.2']);ax.set_yticks(range(5),d.index.astype(int))
    decorate(ax,'A  Delay and changing culture','Cultural-path rate','Adviser update lag')
    # Color key in its own protected band.
    cax=fig.add_axes([.11,.105,.34,.022]);cb=fig.colorbar(mesh,cax=cax,orientation='horizontal');cb.set_ticks([0,50,100]);cb.set_label('Final adoption (%)',fontsize=8.5,labelpad=1);cb.ax.tick_params(labelsize=8.5,length=2,pad=1)
    ax=axs[1];paths=read('lag_rate_paths.csv')
    cases=[(.1,6,TEAL,'-', 'Slow change, lag 6'),(1.6,6,PINK,'--','Fast change, lag 6'),(1.6,0,INK,':','Fast change, no lag')]
    for rate,lag,col,style,label in cases:
        g=paths[np.isclose(paths.forcing_rate,rate)&(paths.adviser_lag==lag)]
        ax.plot(g.time,100*g.adoption,c=col,ls=style,label=label)
    ax.set_ylim(0,100);ax.set_xlim(0,60)
    fig.legend(handles=ax.get_legend_handles_labels()[0],labels=ax.get_legend_handles_labels()[1],loc='lower center',bbox_to_anchor=(.76,.055),frameon=False,labelspacing=.8,handletextpad=1.0)
    decorate(ax,'B  The same cultural endpoints','Normalized time','Adoption (%)')
    save(fig,'fig_dynamic_lag_and_rates',['results/lag_rate_grid.csv','results/lag_rate_paths.csv'])


def rollout():
    fig,axs=plt.subplots(1,2,figsize=(6.9,3.8));fig.subplots_adjust(left=.10,right=.99,top=.87,bottom=.35,wspace=.40)
    d=read('rollout_rate_grid.csv')
    for delta,col,style in [(0,INK,'-'),(.025,GOLD,'-'),(.05,GOLD,'--')]:
        g=d[np.isclose(d.adjustment_allocation,delta)]
        for ax,field in [(axs[0],'growth'),(axs[1],'adoption_final')]:ax.plot(g.rollout_rate,100*g[field],c=col,ls=style,label=f'Extra aid {100*delta:g}%')
        for r in g.itertuples(index=False):axs[0].scatter(r.rollout_rate,100*r.growth,s=26,facecolor=col if r.admissible else 'white',edgecolor=col,lw=.9,zorder=4)
    axs[0].axhline(10,c=GREY,ls=':',lw=.7);axs[1].axhline(50,c=GREY,ls=':',lw=.7)
    for ax in axs:ax.set_xscale('log',base=2);ax.set_xticks([.05,.2,.8,3.2],['.05','.2','.8','3.2']);ax.grid(alpha=.15)
    decorate(axs[0],'A  Balance, rather than maximum aid','Technology-rollout rate','Quality growth (log points)')
    decorate(axs[1],'B  Final adoption tests persistence','Technology-rollout rate','Final adoption (%)')
    fig.legend(handles=axs[0].get_legend_handles_labels()[0],labels=axs[0].get_legend_handles_labels()[1],loc='lower center',bbox_to_anchor=(.5,.067),ncol=3,frameon=False)
    fig.text(.10,.015,'Filled points meet all three criteria. Opportunity endpoints and actual spending match across rates.',fontsize=8.5)
    save(fig,'fig_dynamic_rollout_rates',['results/rollout_rate_grid.csv'])


def directions_and_audit():
    fig,axs=plt.subplots(1,2,figsize=(6.9,3.4));fig.subplots_adjust(left=.205,right=.985,top=.87,bottom=.23,wspace=.85)
    d=read('equal_distance_directions.csv');d=d[d['shape']=='linear']
    base=read('selected_policies.csv').iloc[0].growth
    labels=['Positive direction','Negative direction','Zero projection']
    for y,(label,col) in enumerate(zip(labels,[PINK,TEAL,GREY])):
        r=d[d.direction==label].iloc[0]
        axs[0].plot([0,r.projection*100],[y,y],c=col,lw=1.5);axs[0].scatter(r.projection*100,y,c=col,s=26)
        axs[1].plot([0,(r.growth-base)*100],[y,y],c=col,lw=1.5);axs[1].scatter((r.growth-base)*100,y,c=col,s=26)
    for ax in axs:ax.set_yticks(range(3),labels);ax.set_ylim(-.6,2.6);ax.axvline(0,c=GREY,ls=':',lw=.7);ax.grid(axis='x',alpha=.14)
    decorate(axs[0],'A  Identical category-share error',r'Adviser-channel shift ($\times100$)','')
    decorate(axs[1],'B  Different quality consequences','Quality-growth change (log points)','')
    fig.text(.205,.05,'All three have mean item-TVD = 0.00417. The balanced redistribution has zero projection.',fontsize=8.5)
    save(fig,'fig_dynamic_error_directions',['results/equal_distance_directions.csv','results/selected_policies.csv'])
    fig,axs=plt.subplots(1,2,figsize=(6.9,3.3));fig.subplots_adjust(left=.10,right=.99,top=.86,bottom=.25,wspace=.36)
    d=read('audit_linked_summary.csv')
    for ax,items in zip(axs,['all six','Q48/Q57/Q159']):
        for model,col,mark in [('GPT-5.5',INK,'o'),('GPT-5.6 Sol',TEAL,'^')]:
            for shape,style in [('linear','-'),('saturating','--'),('spline',':')]:
                g=d[(d['items']==items)&(d.model==model)&(d['shape']==shape)].sort_values('strength')
                ax.plot(g.strength,g.low_adoption_profiles,c=col,ls=style,marker=mark,markersize=3)
        decorate(ax,'All six items' if items=='all six' else 'Q48/Q57/Q159 only','Assumed response strength','Low-adoption profiles / 64')
        ax.set_xticks([0,.25,.5,1]);ax.set_ylim(-.5,16.5)
    fig.legend(handles=[Line2D([],[],c=INK,marker='o',label='GPT-5.5'),Line2D([],[],c=TEAL,marker='^',label='GPT-5.6 Sol'),Line2D([],[],c=GREY,ls='-',label='Linear'),Line2D([],[],c=GREY,ls='--',label='Saturating'),Line2D([],[],c=GREY,ls=':',label='Spline')],loc='lower center',bbox_to_anchor=(.5,.025),ncol=5,frameon=False,columnspacing=1.1,handlelength=1.5)
    save(fig,'fig_dynamic_audit_sensitivity',['results/audit_linked_summary.csv'],'Observed error inputs propagated through specified, uncalibrated mechanisms')


def boundary():
    fig,axs=plt.subplots(1,2,figsize=(6.9,3.9));fig.subplots_adjust(left=.10,right=.99,top=.87,bottom=.33,wspace=.40)
    b=read('boundary.csv');a=b.aid
    axs[0].plot(a,b.actual_fold,c=TEAL,label='Actual culture')
    axs[0].plot(a,b.perceived_fold,c=PINK,ls='--',label='Assumed +0.18 bias')
    axs[0].plot(a,b.budget_capacity,c=INK,ls=':',label='Budget capacity')
    axs[0].fill_between(a,b.actual_fold,np.minimum(b.perceived_fold,b.budget_capacity),where=b.budget_capacity>b.actual_fold,color=PINK,alpha=.15)
    axs[0].set_ylim(0,2.5);axs[0].set_xlim(0,.72)
    decorate(axs[0],'A  A misplaced branch-existence limit','Aid allocation','Launch intensity')
    d=read('continuation.csv')
    for c,col in [(0,TEAL),(.18,PINK)]:
        g=d[np.isclose(d.culture,c)]
        for stable,style in [(True,'-'),(False,'--')]:axs[1].plot(g.nu,np.where(g.stable==stable,g.z,np.nan),c=col,ls=style)
        z,n=fold(.3,c);axs[1].scatter(n,z,c=col,marker='D',s=27)
    axs[1].set_xlim(.35,1.7);axs[1].set_ylim(-1.5,1.5)
    decorate(axs[1],'B  Following stable and unstable states','Launch intensity','Coordination')
    fig.legend(handles=axs[0].get_legend_handles_labels()[0],labels=axs[0].get_legend_handles_labels()[1],loc='lower center',bbox_to_anchor=(.5,.07),ncol=3,frameon=False)
    fig.text(.10,.016,'Solid branches attract nearby states; dashed branches have an unstable direction. Diamonds mark folds.',fontsize=8.5)
    save(fig,'fig_dynamic_boundaries',['results/boundary.csv','results/continuation.csv'])


def benchmark():
    fig,axs=plt.subplots(1,2,figsize=(6.9,3.1));fig.subplots_adjust(left=.10,right=.99,top=.87,bottom=.29,wspace=.38)
    d=read('growth_benchmark.csv')
    axs[0].plot(d.aid,d.capital_ratio_equilibrium,c=TEAL,marker='o');axs[1].plot(d.worst_burden*100,d.growth*100,c=TEAL,marker='o')
    decorate(axs[0],'A  A unique balanced-growth capital ratio','Aid allocation','Capital / technology')
    decorate(axs[1],'B  An ordinary growth–adjustment trade-off','Worst-group exposure (%)','Quality growth (log points)')
    fig.text(.10,.035,'Closed resource account. Every capital equilibrium is locally attracting; no coordination fold is imposed.',fontsize=8.5)
    save(fig,'fig_dynamic_growth_benchmark',['results/growth_benchmark.csv'])


def teaching():
    # The aggregate phase plane, rate model, and cusp are distinct mathematical examples.
    phase=pd.read_csv(SAMPLES/'phase_basins.csv')
    fig,ax=plt.subplots(figsize=(6.9,4.0));fig.subplots_adjust(left=.11,right=.99,top=.87,bottom=.26)
    zcol,ucol,basincol=phase.columns[0],phase.columns[1],phase.columns[-1]
    zs=np.sort(phase[zcol].unique());us=np.sort(phase[ucol].unique())
    values=phase.pivot(index=ucol,columns=zcol,values=basincol).reindex(index=us,columns=zs).to_numpy()
    if len(np.unique(values))>2:values=(values>0).astype(int)
    ax.contourf(zs,us,values,levels=[-.5,.5,1.5],colors=['#F5E6EE','#E4F1F2'])
    Z,U=np.meshgrid(zs,us);nu=1.10;aid=.3
    DZ=Z-Z**3+.7+.45*aid-.9*nu-.35*U
    DU=.565*nu*expit(2*Z)*(1-U)-(.22+1.1*aid)*U
    ax.streamplot(zs,us,DZ,DU,color=GREY,density=.65,linewidth=.45,arrowsize=.55)
    ax.contour(Z,U,DZ,[0],colors=INK,linewidths=1.)
    ax.contour(Z,U,DU,[0],colors=GOLD,linewidths=1.,linestyles='--')
    decorate(ax,'Aggregate illustration: initial conditions select different outcomes','Initial coordination','Initial transition exposure')
    fig.text(.11,.055,'Teal: high-adoption basin. Rose: low-adoption basin. Curves mark zero change in each state.',fontsize=8.5)
    save(fig,'fig_dynamic_phase_space',['sample_results/phase_basins.csv'],'Separate aggregate two-state teaching model; finite-horizon basin classification')
    rates=pd.read_csv(SAMPLES/'rate_tipping.csv')
    fig,axs=plt.subplots(1,2,figsize=(6.9,3.4));fig.subplots_adjust(left=.10,right=.99,top=.87,bottom=.30,wspace=.4)
    for label,col,style in [('Slow forcing',TEAL,'-'),('Fast forcing',PINK,'--')]:
        g=rates[rates.scenario==label]
        axs[0].plot(g.time,g['shift'],c=col,ls=style,label=label)
        axs[1].plot(g.time,g.state_y,c=col,ls=style)
        axs[1].plot(g.time,g.instant_high_equilibrium,c=col,ls=':',lw=.6)
    for ax in axs:ax.set_xlim(-20,30)
    decorate(axs[0],'A  Identical start and end points','Normalized time','Moving environment')
    decorate(axs[1],'B  The high state persists but tracking fails','Normalized time','Adjustment state')
    fig.legend(handles=axs[0].get_legend_handles_labels()[0],labels=axs[0].get_legend_handles_labels()[1],loc='lower center',bbox_to_anchor=(.5,.04),ncol=2,frameon=False)
    save(fig,'fig_dynamic_rate_teaching',['sample_results/rate_tipping.csv'],'Independent mathematical rate-tipping example; no disappearing stable branch')
    cusp=pd.read_csv(SAMPLES/'cusp_surface.csv')
    aa=np.sort(cusp.alpha.unique());yy=np.sort(cusp.equilibrium_y.unique())
    A,Y=np.meshgrid(aa,yy);B=Y**3-A*Y;stable=A-3*Y**2<=0
    fig=plt.figure(figsize=(6.9,4.0))
    ax=fig.add_axes([.10,.25,.36,.59])
    y=np.linspace(-1.6,1.6,1000);beta=y**3-y
    keep=np.abs(beta)<=1.2;y=y[keep];beta=beta[keep]
    for stable,style,col in [(True,'-',TEAL),(False,'--',PINK)]:
        mask=(1-3*y*y<0)==stable
        ax.plot(beta,np.where(mask,y,np.nan),c=col,ls=style)
    for sign in [-1,1]:
        yf=sign/np.sqrt(3);ax.scatter(yf**3-yf,yf,c=GOLD,marker='D',s=22,zorder=5)
    ax.set_xlim(-1.2,1.2);ax.set_ylim(-1.6,1.6)
    decorate(ax,'A  Equilibrium section: feedback = 1','Tilt','Equilibrium')
    af=np.linspace(0,1.7,200)
    ax=fig.add_axes([.675,.24,.305,.60])
    for sign in [-1,1]:
        y=sign*np.sqrt(af/3);ax.plot(af,y**3-af*y,c=GOLD)
    ax.scatter([0],[0],c=INK,s=25);ax.set_xlim(-.5,1.7);ax.set_ylim(-1,1);ax.set_xticks([0,.5,1,1.5])
    decorate(ax,'B  Two folds meet at a cusp','Feedback','Tilt')
    fig.legend(handles=[Line2D([],[],c=TEAL,lw=3,label='Stable sheet'),Line2D([],[],c=PINK,lw=3,label='Unstable sheet'),Line2D([],[],c=GOLD,label='Fold curves')],loc='lower center',bbox_to_anchor=(.5,.052),ncol=3,frameon=False)
    fig.text(.09,.016,'A teaching normal form. An economic cusp would require a separate model and nondegeneracy tests.',fontsize=8.5)
    save(fig,'fig_dynamic_cusp_teaching',['sample_results/cusp_surface.csv'],'Mathematical normal form; no economic cusp identified')


def main():
    hero();gallery();policy_tradeoff();policy_paths();culture_families();lag_and_rates();rollout();directions_and_audit();boundary();benchmark();teaching()
    manifest={'iconography_mode':'minimal-scientific','palette':{'ink':INK,'surface':PALE,'primary':TEAL,'secondary':PINK,'status_accent':GOLD,'divider':'#CED5DD'},'hero_graphic':{'concept':'Knowledge, quality replacement, and shared resource choices','shape_ids':['measured-agreement','perceived-transition-boundary','quality-and-adjustment-outcomes']},'semantic_graphics':[{'concept':'Useful knowledge','visual_encoding':'Original outlined annotated book','shape_ids':['hero-literature-book','hero-mokyr-label'],'origin':'original','evidence_implication':'Literature grounding, not empirical measurement'},{'concept':'Creative destruction','visual_encoding':'Ascending quality ladder with replacement direction','shape_ids':['hero-quality-ladder','hero-quality-label'],'origin':'original','evidence_implication':'Conceptual quality-replacement mechanism'},{'concept':'Representation','visual_encoding':'Model estimates and country-bootstrap intervals','shape_ids':['measured-agreement','representation-label'],'origin':'verified aggregate inputs','evidence_implication':'Agreement with the unweighted derivative'},{'concept':'Policy consequences','visual_encoding':'Separate actual/perceived boundaries and an actual attainable-set plot','shape_ids':['perceived-transition-boundary','quality-and-adjustment-outcomes'],'origin':'computed mechanisms','evidence_implication':'Conditional results, not economic estimates'}],'composition_mechanism':'Protected title, plot, legend and reading-note bands; statistical plots with explicit evidence classes','grayscale_encoding':'Line patterns, marker shapes and open/filled admission marks complement color; heatmap intensity is ordinal','figures':MANIFEST,'config_sha256':hashlib.sha256((ROOT/'parameters.json').read_bytes()).hexdigest()}
    (FIG/'figure_manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Generated',len(MANIFEST),'editable publication figures')


if __name__=='__main__':main()
