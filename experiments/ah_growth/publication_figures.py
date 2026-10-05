"""Publication-width figures from the frozen R3 numerical tables.

No model calls or empirical estimates. All text stays live in SVG; each PDF
is generated at its intended seven-inch insertion width. Run with --outdir.
"""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'country_revision_results'
INK='#18324A'; BLUE='#315EFB'; TEAL='#128C80'; ORANGE='#D97745'; GRAY='#798795'
COUNTRIES=['China','Germany','Egypt']
RULES=[('implemented Section 6 market','Human survey','Human',INK,'-'),
 ('implemented Section 6 market','GPT-5.5','GPT-5.5',BLUE,'--'),
 ('implemented Section 6 market','GPT-5.6 Sol','GPT-5.6',TEAL,'-')]
ALL=[('unsubsidized market','Human survey','Unsubsidized',GRAY,':')]+RULES+[
 ('planner held optimal control','physical-economy benchmark','Planner',ORANGE,'-.')]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8,
 'axes.titlesize':9,'xtick.labelsize':7.5,'ytick.labelsize':7.5,
 'text.color':INK,'axes.labelcolor':INK,'svg.fonttype':'none','pdf.fonttype':42,
 'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.14,
 'figure.facecolor':'white','savefig.facecolor':'white'})

def selected(paths,country,policy,source):
    d=paths[paths.country.eq(country)&paths.policy.eq(policy)&paths.source.eq(source)&
        np.isclose(paths.initial_u_A,.08)&np.isclose(paths.initial_u_B,.08)].sort_values('t')
    assert len(d)>0
    return d

def legend(fig,rules,y=1.015):
    fig.legend(handles=[Line2D([],[],c=c,ls=ls,label=lab,lw=1.6) for _,_,lab,c,ls in rules],
        loc='upper center',bbox_to_anchor=(.5,y),ncol=len(rules),frameon=False,
        handlelength=2.2,columnspacing=1.7,fontsize=8)

def grid(rows=2,height=3.7):
    f,aa=plt.subplots(rows,3,figsize=(7,height),squeeze=False)
    f.subplots_adjust(left=.085,right=.985,bottom=.14,top=.86,wspace=.46,hspace=.56)
    for a in aa[-1]:a.set_xlabel('Model time')
    return f,aa

def finish(fig,name,out,registry):
    for j,t in enumerate(fig.findobj(matplotlib.text.Text)):
        if t.get_text():t.set_gid(f'{name}-text-{j}')
    fig.savefig(out/(name+'.svg'),metadata={'Date':None})
    fig.savefig(out/(name+'.pdf'),metadata={'CreationDate':None,'ModDate':None})
    fig.savefig(out/(name+'.png'),dpi=120)
    registry.append({'name':name,'width_inches':7,'evidence':'conditional synthetic model result',
      'svg_sha256':hashlib.sha256((out/(name+'.svg')).read_bytes()).hexdigest()})
    plt.close(fig)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--outdir',type=Path,default=ROOT/'figures')
    args=parser.parse_args();out=args.outdir;out.mkdir(parents=True,exist_ok=True);registry=[]
    paths=pd.read_csv(DATA/'country-paths.csv');sweep=pd.read_csv(DATA/'matched-sensitivity.csv')
    ref=pd.read_csv(DATA/'country-refinement.csv');up=pd.read_csv(DATA/'three-country-upgrade-comparison.csv')
    field=pd.read_csv(DATA/'systems/planner-phase-field.csv')
    f,aa=grid(height=3.3);legend(f,RULES)
    for j,c in enumerate(COUNTRIES):
        aa[0,j].set_title(c)
        for pol,src,lab,color,ls in RULES:
            d=selected(paths,c,pol,src)
            aa[0,j].plot(d.t,d.log_quality,c=color,ls=ls,lw=1.7)
            aa[1,j].plot(d.t,100*np.maximum(d.u_A,d.u_B),c=color,ls=ls,lw=1.7)
        aa[0,j].set_ylabel('Log-quality gain G(t)');aa[1,j].set_ylabel('Current worst needs (%)')
    finish(f,'fig_r3_advice_paths',out,registry)
    f,aa=grid(height=4.2)
    for j,c in enumerate(COUNTRIES):
        for i,(pol,src) in enumerate([('implemented Section 6 market','Human survey'),('planner held optimal control','physical-economy benchmark')]):
            d=paths[paths.country.eq(c)&paths.policy.eq(pol)&paths.source.eq(src)]
            for _,g in d.groupby(['initial_u_A','initial_u_B']):
                g=g.sort_values('t');a=aa[i,j]
                a.plot(100*g.u_A,100*g.u_B,c=BLUE,lw=1.1)
                a.scatter(100*g.u_A.iloc[0],100*g.u_B.iloc[0],facecolors='white',edgecolors=INK,s=18,zorder=4)
                a.scatter(100*g.u_A.iloc[-1],100*g.u_B.iloc[-1],marker='*',c=ORANGE,s=45,zorder=5)
            a.set_title(c+' | '+('Human market' if i==0 else 'Planner'))
            a.set(xlim=(-2,85),ylim=(-2,85),xlabel='Needs A (%)',ylabel='Needs B (%)',xticks=[0,40,80],yticks=[0,40,80])
    finish(f,'fig_r3_initial_states',out,registry)
    f,aa=grid(height=3.8);legend(f,ALL)
    for j,c in enumerate(COUNTRIES):
        aa[0,j].set_title(c)
        for pol,src,lab,color,ls in ALL:
            d=selected(paths,c,pol,src)
            aa[0,j].plot(d.t,100*d.n,c=color,ls=ls,lw=1.5)
            aa[1,j].plot(d.t,d.a,c=color,ls=ls,lw=1.5)
        aa[0,j].set_ylabel('Research labor (%)');aa[1,j].set_ylabel('Assistance intensity a')
    finish(f,'fig_r3_controls',out,registry)
    for var,name in [('omega','fig_r3_welfare_weights'),('q','fig_r3_innovation_sizes')]:
        f,aa=grid(height=3.8)
        for j,c in enumerate(COUNTRIES):
            d=sweep[sweep.country.eq(c)&sweep.variable.eq(var)].sort_values('value')
            x=d.value if var=='omega' else 100*d.value
            aa[0,j].set_title(c);aa[0,j].plot(x,d.G,'o-',c=BLUE,ms=3,lw=1.3)
            aa[1,j].plot(x,100*d.Umax,'s-',c=ORANGE,ms=3,lw=1.3)
            aa[0,j].set_ylabel('Log-quality gain G');aa[1,j].set_ylabel('Mean worst-group needs (%)')
            for a in aa[:,j]:a.set_xticks(x);a.set_xlabel('Penalty weight omega' if var=='omega' else 'Quality jump 100q (%)')
        finish(f,name,out,registry)
    f,aa=grid(height=3.8)
    f.subplots_adjust(left=.125,wspace=.50)
    for j,c in enumerate(COUNTRIES):
        d=ref[ref.country.eq(c)].sort_values('grid')
        aa[0,j].set_title(c);aa[0,j].semilogy(d.grid,d.rollout_value_error_percent,'o-',c=BLUE,ms=3)
        aa[0,j].yaxis.set_major_formatter(FuncFormatter(lambda value,_:f'{value:g}'))
        aa[0,j].yaxis.set_minor_formatter(plt.NullFormatter())
        aa[1,j].plot(d.grid,d.G_relative_to_finest_percent,'s-',c=ORANGE,ms=3)
        aa[1,j].axhline(0,c=GRAY,ls=':',lw=.7)
        aa[0,j].set_ylabel('Value discrepancy (%)');aa[1,j].set_ylabel('G vs finest run (%)')
        for a in aa[:,j]:a.set_xticks([41,61,81,101]);a.set_xlabel('State grid points')
    finish(f,'fig_r3_refinement',out,registry)
    # Full sampled action fields; nearest shading conveys computed nodes only.
    gx=np.sort(field.u_A.unique());gy=np.sort(field.u_B.unique())
    N=field.pivot(index='u_B',columns='u_A',values='n').loc[gy,gx].to_numpy()
    A=field.pivot(index='u_B',columns='u_A',values='a').loc[gy,gx].to_numpy()
    f,aa=plt.subplots(1,2,figsize=(7,3.1));f.subplots_adjust(left=.08,right=.90,bottom=.20,top=.85,wspace=.50)
    for ax,z,title in zip(aa,[100*N,A],['Research labor (%)','Assistance intensity a']):
        im=ax.pcolormesh(100*gx,100*gy,z,cmap='Blues',shading='nearest',rasterized=False)
        cb=f.colorbar(im,ax=ax,pad=.03,fraction=.05);cb.ax.tick_params(labelsize=7.5)
        cb.solids.set_rasterized(False)
        ax.set(title=title,xlabel='Needs A (%)',ylabel='Needs B (%)',xticks=[0,20,40],yticks=[0,20,40]);ax.grid(False)
    finish(f,'fig_r3_action_fields',out,registry)
    f,aa=plt.subplots(1,2,figsize=(7,2.9));f.subplots_adjust(left=.08,right=.97,bottom=.22,top=.84,wspace=.45)
    im=aa[0].pcolormesh(100*gx,100*gy,100*N,cmap='Blues',shading='nearest',rasterized=False)
    cb=f.colorbar(im,ax=aa[0],fraction=.05,pad=.03);cb.set_label('Research (%)',fontsize=7.5)
    cb.solids.set_rasterized(False)
    d=selected(paths,'Germany','planner held optimal control','physical-economy benchmark')
    aa[0].plot(100*d.u_A,100*d.u_B,c=ORANGE,lw=1.6)
    aa[0].scatter(8,8,s=22,facecolors='white',edgecolors=INK,zorder=4)
    aa[0].set(title='A  State-contingent research',xlabel='Needs A (%)',ylabel='Needs B (%)',xticks=[0,20,40],yticks=[0,20,40]);aa[0].grid(False)
    for pol,src,lab,col,ls in ALL:
        d=selected(paths,'Germany',pol,src);aa[1].plot(d.t,d.log_quality,c=col,ls=ls,lw=1.5)
    aa[1].set(title='B  Cumulative quality continues',xlabel='Model time',ylabel='Log-quality gain G(t)');legend(f,ALL,y=1.01)
    finish(f,'fig_r3_system_summary',out,registry)
    f,aa=plt.subplots(1,2,figsize=(7,3.1));f.subplots_adjust(left=.10,right=.98,bottom=.24,top=.84,wspace=.55)
    for row,mark,offset in zip(up.itertuples(),['o','s','D'],[(-32,12),(6,12),(-4,-17)]):
        aa[0].scatter(100*row.upgrade_change_G,100*row.upgrade_change_Umax,s=32,c=BLUE,marker=mark)
        aa[0].annotate(row.country,(100*row.upgrade_change_G,100*row.upgrade_change_Umax),xytext=offset,textcoords='offset points',fontsize=8)
    aa[0].set(xlim=(-.48,0),ylim=(-.045,0),xlabel='Upgrade: 100 Delta G (log points)',ylabel='Upgrade: mean needs change (pp)',title='A  Outcome direction')
    aa[0].grid(False);aa[1].grid(False)
    yy=np.arange(3);aa[1].barh(yy,100*up.upgrade_absolute_bias_change_Umax,color=TEAL,height=.5)
    aa[1].axvline(0,c=INK,lw=.8);aa[1].set(yticks=yy,yticklabels=up.country,xlabel='Change in absolute needs gap (pp)',title='B  Human-reference deviation');aa[1].invert_yaxis()
    finish(f,'fig_r3_upgrade_comparisons',out,registry)
    val=pd.read_csv(DATA/'systems/market-valuation-sheet.csv')
    f=plt.figure(figsize=(7,4));ax=f.add_subplot(111,projection='3d')
    f.subplots_adjust(left=.03,right=.97,bottom=.12,top=.88)
    x=np.sort(val.u_A.unique());y=np.sort(val.u_B.unique());z=val.pivot(index='u_A',columns='u_B',values='patent_value').loc[x,y].to_numpy()
    X,Y=np.meshgrid(100*x,100*y,indexing='ij');ax.plot_surface(X,Y,z,cmap='Blues',edgecolor='#CBD5E1',linewidth=.3,rasterized=False)
    ax.set(xticks=[],yticks=[],zticks=[],title='Germany human-rule market valuation sheet')
    for axis in (ax.xaxis,ax.yaxis,ax.zaxis):axis.pane.set_visible(False)
    ax.grid(False)
    f.text(.16,.18,'X: needs A',fontsize=8)
    f.text(.78,.20,'Y: needs B',fontsize=8)
    f.text(.80,.54,'Z: vM',fontsize=8)
    f.text(.12,.07,'Needs A and B each span 0–80%; vM is normalized patent value.',fontsize=8)
    f.text(.12,.025,f'Sheet range: vM = {z.min():.4f}–{z.max():.4f}. Constant human-rule aid; forward-selected market value.',fontsize=7.5)
    ax.view_init(elev=24,azim=-55)
    finish(f,'fig_r3_market_valuation',out,registry)
    f,aa=plt.subplots(1,2,figsize=(7,3.2));f.subplots_adjust(left=.10,right=.95,bottom=.20,top=.85,wspace=.55)
    du=field.pivot(index='u_B',columns='u_A',values='du_A').loc[gy,gx].to_numpy();dv=field.pivot(index='u_B',columns='u_A',values='du_B').loc[gy,gx].to_numpy()
    aa[0].streamplot(100*gx,100*gy,100*du,100*dv,color=TEAL,density=.8,linewidth=.7)
    dd=paths[paths.country.eq('Germany')&paths.policy.eq('planner held optimal control')]
    for ini,g in dd.groupby(['initial_u_A','initial_u_B']):
        g=g.sort_values('t')
        if max(ini)<=.4:aa[0].plot(100*g.u_A,100*g.u_B,c=BLUE,lw=1.2)
        aa[1].plot(g.log_quality,100*g.u_A,c=BLUE,lw=1.2)
    aa[0].set(xlabel='Needs A (%)',ylabel='Needs B (%)',title='A  Planner needs flow',xlim=(0,40),ylim=(0,40),xticks=[0,20,40],yticks=[0,20,40])
    aa[1].set(xlabel='Cumulative log-quality gain G(t)',ylabel='Needs A (%)',title='B  Growth after needs settle')
    finish(f,'fig_r3_phase_growth',out,registry)
    (out/'publication-figure-manifest.json').write_text(json.dumps({'iconography_mode':'minimal-scientific',
      'palette':{'ink':INK,'primary':BLUE,'secondary':TEAL,'status_accent':ORANGE},
      'data_sources':[str(DATA/p) for p in ['country-paths.csv','matched-sensitivity.csv','country-refinement.csv','three-country-upgrade-comparison.csv']],
      'figures':registry,'minimum_design_font_points':7.5,'width_inches':7},indent=2)+'\n')
    print(json.dumps({'publication_figures':len(registry),'outdir':str(out)}))

if __name__=='__main__':main()
