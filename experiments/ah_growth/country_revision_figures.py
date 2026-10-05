"""Six readable, numerical China/Germany/Egypt review figures, not a release."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
from PIL import Image,ImageOps
from country_revision_compute import DEST,COUNTRIES
from node2 import ROOT,INITIALS

DELIVERY=Path(__file__).resolve().parent/'figures'
INK='#18324A';BLUE='#315EFB';TEAL='#128C80';ORANGE='#D97745';GRAY='#798795';SURFACE='#F5F7FB';DIVIDER='#CBD5E1'
RULES=[('implemented Section 6 market','Human survey','Human',INK,'-'),
       ('implemented Section 6 market','GPT-5.5','GPT-5.5',BLUE,'--'),
       ('implemented Section 6 market','GPT-5.6 Sol','GPT-5.6',TEAL,'-')]
ALLRULES=[('unsubsidized market','Human survey','Market',GRAY,':')]+RULES+[
          ('planner held optimal control','physical-economy benchmark','Planner',ORANGE,'-.')]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.labelsize':11,'axes.titlesize':14,
    'xtick.labelsize':10,'ytick.labelsize':10,'text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,
    'ytick.color':INK,'svg.fonttype':'none','pdf.fonttype':42,'axes.spines.top':False,
    'axes.spines.right':False,'axes.grid':True,'grid.alpha':.13,'figure.facecolor':'white',
    'savefig.facecolor':'white','path.simplify':False})

def frame(number,title,subtitle,height=11.8):
    f=plt.figure(figsize=(16,height))
    f.text(.055,.96,f'{number}. {title}',fontsize=22,weight='bold',gid=f'figure-{number}-title')
    f.text(.055,.918,subtitle,fontsize=12,gid=f'figure-{number}-subtitle')
    return f

def footer(f,conclusion,scope):
    f.text(.055,.057,'Conclusion: '+conclusion,fontsize=12,weight='bold',gid='conclusion')
    f.text(.055,.025,scope,fontsize=10.5,gid='scope')

def axis(f,col,bottom,height):
    a=f.add_axes([.075+.31*col,bottom,.255,height]);a.tick_params(pad=5)
    return a

def table(f,col,cols,rows,widths=None,bottom=.10,height=.18,fontsize=11):
    a=f.add_axes([.067+.31*col,bottom,.279,height]);a.set_axis_off()
    widths=np.asarray(widths if widths else [1/len(cols)]*len(cols));anchors=np.cumsum(np.r_[0,widths[:-1]])+.012
    for x,label in zip(anchors,cols):a.text(x,.96,label,transform=a.transAxes,ha='left',va='center',fontsize=fontsize,weight='bold')
    for i,(y,row) in enumerate(zip(np.linspace(.72,.08,len(rows)),rows)):
        for j,(x,text) in enumerate(zip(anchors,row)):
            a.text(x,y,str(text),transform=a.transAxes,ha='left',va='center',fontsize=fontsize,gid=f'table-{col}-{i}-{j}')
    return a

def legends(f,rules,y=.86):
    hs=[Line2D([0],[0],color=c,lw=2.4,ls=ls,label=label) for _,_,label,c,ls in rules]
    f.legend(handles=hs,loc='center',bbox_to_anchor=(.50,y),ncol=len(rules),frameon=False,
             handlelength=2.7,columnspacing=2.2,fontsize=12)

def selected(paths,country,policy,source):
    d=paths[paths.country.eq(country)&paths.policy.eq(policy)&paths.source.eq(source)&
            np.isclose(paths.initial_u_A,.08)&np.isclose(paths.initial_u_B,.08)].sort_values('t')
    assert len(d)>0,(country,policy,source)
    return d

def main():
    paths=pd.read_csv(DEST/'country-paths.csv');comp=pd.read_csv(DEST/'country-policy-comparisons.csv')
    sweep=pd.read_csv(DEST/'matched-sensitivity.csv');ref=pd.read_csv(DEST/'country-refinement.csv')
    figs=[];names=[];tables={}
    f=frame(1,'An advice update changes growth and transition needs',
            'Same physical economy and initial needs; only the human / GPT-5.5 / GPT-5.6 advice rule changes.',height=13)
    legends(f,RULES,y=.866)
    for j,country in enumerate(COUNTRIES):
        axes=[axis(f,j,y,.145) for y in [.65,.43,.21]]
        axes[0].set_title(country+' | conditional scenario',pad=15)
        for policy,source,label,c,ls in RULES:
            d=selected(paths,country,policy,source)
            for metric,(a,y) in enumerate(zip(axes,[d.instantaneous_g_log,d.log_quality,100*np.maximum(d.u_A,d.u_B)])):
                a.plot(d.t,y,color=c,ls=ls,lw=2.1,gid=f'advice-{j}-{label}-{metric}')
        for a,label in zip(axes,['Log-quality growth rate g(t)','Cumulative log-quality gain G(t)','Current worst-group needs (%)']):a.set_ylabel(label)
        axes[-1].set_xlabel('Model time (not calendar years)')
        dd=comp[comp.country.eq(country)&comp.policy.eq('implemented Section 6 market')].set_index('source')
        rows=[[lab,f'{dd.loc[src,"G"]:.4f}',f'{100*dd.loc[src,"Umax"]:.3f}'] for _,src,lab,_,_ in RULES]
        table(f,j,['Rule','G at H=100','Mean needs (%)'],rows,widths=[.28,.32,.40],bottom=.091,height=.071,fontsize=10.5)
    footer(f,'Stable growth rates can coexist with rising cumulative quality. Advice-version effects are compared within each country.',
           'Conditional simulation. Human advice is a reference, not proven socially optimal; G is an expected log-quality index, not national GDP.')
    figs.append(f);names.append('01_Advice_Growth')

    f=frame(2,'Different starts approach the same tested endpoint',
            'Mechanism check: human-rule market (top) and planner (bottom). Open circles = starts; stars = endpoints.')
    for j,country in enumerate(COUNTRIES):
        for row,(pol,src,title) in enumerate([('implemented Section 6 market','Human survey','Human-rule market'),
                                            ('planner held optimal control','physical-economy benchmark','Planner')]):
            a=axis(f,j,.55 if row==0 else .16,.28)
            d=paths[paths.country.eq(country)&paths.policy.eq(pol)&paths.source.eq(src)]
            endpoints=[]
            for k,(ini,dd) in enumerate(d.groupby(['initial_u_A','initial_u_B'])):
                dd=dd.sort_values('t');x=100*dd.u_A.to_numpy();y=100*dd.u_B.to_numpy()
                a.plot(x,y,color=BLUE,lw=1.6,gid=f'initial-path-{j}-{row}-{k}')
                a.scatter([x[0]],[y[0]],facecolors='white',edgecolors=INK,s=32,zorder=4)
                dist=np.r_[0,np.cumsum(np.hypot(np.diff(x),np.diff(y)))]
                if dist[-1]>.1:
                    i=min(len(x)-2,np.searchsorted(dist,.4*dist[-1]));k2=min(len(x)-1,max(i+1,np.searchsorted(dist,.52*dist[-1])))
                    a.annotate('',xy=(x[k2],y[k2]),xytext=(x[i],y[i]),arrowprops=dict(arrowstyle='-|>',color=BLUE,lw=1.3))
                endpoints.append((x[-1],y[-1]))
            xx,yy=endpoints[0];a.scatter([xx],[yy],marker='*',s=130,color=ORANGE,edgecolors=INK,zorder=5)
            f.text(.075+.31*j,.876 if row==0 else .486,f'{country} | {title}',fontsize=12)
            f.text(.075+.31*j,.849 if row==0 else .459,f'Endpoint ({xx:.2f}%, {yy:.2f}%)',fontsize=10.5)
            a.set(xlim=(-3,85),ylim=(-3,85),xlabel='Group A unresolved needs (%)',ylabel='Group B unresolved needs (%)')
            a.set_xticks([0,20,40,60,80]);a.set_yticks([0,20,40,60,80])
    footer(f,'The six tested starts converge within each reference policy; institutions can have different endpoints.',
           'This panel does not compare advice versions or establish global uniqueness. The two groups are declared transition mechanisms, not observed country groups.')
    figs.append(f);names.append('02_Initial_States')

    f=frame(3,'Different decision rules choose different research and aid',
            'Market = no R&D tax/subsidy; Human / GPT rules are implemented targets; Planner optimizes a stated welfare objective.')
    legends(f,ALLRULES,y=.866)
    for j,country in enumerate(COUNTRIES):
        aa=[axis(f,j,.56,.235),axis(f,j,.29,.20)];aa[0].set_title(country+' | conditional scenario',pad=15)
        rows=[]
        for policy,source,label,c,ls in ALLRULES:
            d=selected(paths,country,policy,source)
            aa[0].plot(d.t,100*d.n,c=c,ls=ls,lw=2,gid=f'research-{j}-{label}')
            aa[1].plot(d.t,d.a,c=c,ls=ls,lw=2,gid=f'assistance-{j}-{label}')
            rows.append([label,f'{100*d.n.iloc[-1]:.3f}',f'{d.a.iloc[-1]:.3f}'])
        aa[0].set_ylabel('Research labor share 100n (%)');aa[1].set_ylabel('Assistance intensity a (index)')
        aa[1].set_xlabel('Model time (not calendar years)')
        table(f,j,['Rule','End n (%)','End a'],rows,widths=[.37,.35,.28],bottom=.09,height=.115,fontsize=10.5)
    footer(f,'The planner optimizes long-run discounted output minus weighted transition needs; it does not maximize every plotted indicator.',
           'Assistance intensity is not the share of people receiving aid. Adviser-version differences and institution differences answer distinct questions.')
    figs.append(f);names.append('03_Research_Assistance')

    f=frame(4,'Valuing transition needs changes the output-needs tradeoff',
            'Each computed point uses one planner penalty weight omega; tables give the actual coordinates.')
    markers=['o','s','D','^','X'];hs=[Line2D([0],[0],color=BLUE,marker=m,ls='None',label=f'omega = {v:.2f}') for m,v in zip(markers,[0.,.15,.3,.6,.9])]
    f.legend(handles=hs,loc='center',bbox_to_anchor=(.5,.857),ncol=5,frameon=False,fontsize=12)
    ff4=sweep[sweep.variable.eq('omega')].copy();ff4['needs_percent']=100*ff4.Umax
    ff4[['country','value','average_output','needs_percent','G','grid','control_points','dt']].to_csv(DEST/'figure4-point-values.csv',index=False)
    for j,country in enumerate(COUNTRIES):
        d=ff4[ff4.country.eq(country)].sort_values('value');a=axis(f,j,.405,.37);a.set_title(country+' | conditional scenario',pad=15)
        a.plot(d.average_output,d.needs_percent,color=BLUE,lw=1.3,gid=f'weight-response-{j}')
        for k,(_,r) in enumerate(d.iterrows()):a.scatter(r.average_output,r.needs_percent,marker=markers[k],s=68,c=BLUE,edgecolors=INK,zorder=4)
        a.set_xlabel('Mean expected output (model units)');a.set_ylabel('Worst-group mean needs (%)')
        rows=[[f'{r.value:.2f}',f'{r.average_output:.4f}',f'{r.needs_percent:.3f}'] for _,r in d.iterrows()]
        table(f,j,['omega','Mean output','Mean needs (%)'],rows,widths=[.23,.36,.41],bottom=.115,height=.20)
    footer(f,'Higher concern for transition needs changes the chosen balance of output and needs; inspect magnitude, not just direction.',
           'Same 101 x 101 state grid, 61 x 61 action grid, dt=0.125. This is a normative-weight scan, not a proven Pareto frontier or an upgrade experiment.')
    figs.append(f);names.append('04_Output_Needs_Values')

    f=frame(5,'Larger innovations change both gains and transition needs',
            'q is the quality improvement from one economic innovation; it is distinct from a ChatGPT version update.')
    ff5=sweep[sweep.variable.eq('q')].copy();ff5['quality_jump_percent']=100*ff5.value;ff5['needs_percent']=100*ff5.Umax
    ff5[['country','quality_jump_percent','G','needs_percent','average_output','grid','control_points','dt']].to_csv(DEST/'figure5-point-values.csv',index=False)
    for j,country in enumerate(COUNTRIES):
        d=ff5[ff5.country.eq(country)].sort_values('value');aa=[axis(f,j,.64,.19),axis(f,j,.36,.19)]
        aa[0].set_title(country+' | conditional scenario',pad=15)
        aa[0].plot(100*d.value,d.G,'o-',c=BLUE,lw=2,gid=f'innovation-gain-{j}')
        aa[1].plot(100*d.value,d.needs_percent,'s-',c=ORANGE,lw=2,gid=f'innovation-needs-{j}')
        for a in aa:a.set_xticks([6,8,12,16]);a.set_xlabel('Quality improvement per innovation 100q (%)')
        aa[0].set_ylabel('Cumulative log-quality gain G');aa[1].set_ylabel('Worst-group mean needs (%)')
        rows=[[f'{100*r.value:.0f}',f'{r.G:.5f}',f'{r.needs_percent:.3f}'] for _,r in d.iterrows()]
        table(f,j,['q (%)','Gain G','Mean needs (%)'],rows,widths=[.23,.36,.41],bottom=.115,height=.17)
    footer(f,'Bigger innovation steps can increase gains and transition needs; optimal choices also change with q.',
           'Within-country chi, theta, capacity and omega=0.30 held fixed; actions reoptimized. Matched 101/61/0.125 settings. q remains a scenario assumption.')
    figs.append(f);names.append('05_Innovation_Values')

    f=frame(6,'Value consistency and path stability are separate checks',
            'Top: rollout welfare versus its Bellman value. Bottom: gain relative to the finest computed run (not an exact solution).')
    for j,country in enumerate(COUNTRIES):
        d=ref[ref.country.eq(country)].sort_values('grid');aa=[axis(f,j,.64,.19),axis(f,j,.35,.19)]
        for a in aa:
            pos=a.get_position();a.set_position([pos.x0,pos.y0,.235,pos.height])
        aa[0].set_title(country+' | joint refinement',pad=15)
        aa[0].semilogy(d.grid,d.rollout_value_error_percent,'o-',c=BLUE,lw=2,gid=f'value-check-{j}')
        aa[0].yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%.4f'))
        aa[0].yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        aa[1].axhline(0,color=GRAY,ls='--',lw=1)
        aa[1].plot(d.grid,d.G_relative_to_finest_percent,'s-',c=ORANGE,lw=2,gid=f'gain-check-{j}')
        aa[0].set_ylabel('Welfare-value discrepancy (%)',labelpad=12);aa[1].set_ylabel('Gain difference from finest (%)')
        for a in aa:a.set_xticks([41,61,81,101]);a.set_xlabel('State points per dimension')
        rows=[[int(r.grid),int(r.control_points),f'{r["dt"]:g}',f'{r.G:.6f}',f'{r.rollout_value_error_percent:.5f}'] for _,r in d.iterrows()]
        table(f,j,['State','Action','dt','Gain G','Error (%)'],rows,widths=[.14,.16,.15,.25,.30],bottom=.105,height=.175,fontsize=10.5)
    footer(f,'A small value discrepancy does not guarantee equally precise growth paths; the last refinements must be assessed separately.',
           'State grid, action grid and dt change together. Differences are numerical diagnostics, not statistical confidence intervals or a global optimality proof.')
    figs.append(f);names.append('06_Numerical_Values')
    refs=ref.copy();refs.to_csv(DEST/'figure6-numerical-values.csv',index=False)

    pdf=DEST/'basic-preview.pdf'
    with PdfPages(pdf) as pp:
        for f,name in zip(figs,names):
            stem='EthosGPT_R3_'+name
            for artist in f.findobj():
                if hasattr(artist,'set_clip_on'):artist.set_clip_on(False)
            f.savefig(DELIVERY/(stem+'.svg'));f.savefig(DELIVERY/(stem+'.png'),dpi=135);pp.savefig(f);plt.close(f)
    ims=[]
    for name in names:
        im=Image.open(DELIVERY/('EthosGPT_R3_'+name+'.png')).convert('RGB');im.thumbnail((1040,830));ims.append(im)
    canvas=Image.new('RGB',(2080,2490),'white')
    for k,im in enumerate(ims):canvas.paste(im,((k%2)*1040,(k//2)*830))
    canvas.save(DELIVERY/'EthosGPT_R3_Basic_Overview.png');ImageOps.grayscale(canvas).save(DEST/'basic-grayscale.png')
    palette=plt.figure(figsize=(7,1));palette.gca().set_axis_off()
    for k,(lab,c) in enumerate([('Human',INK),('GPT-5.5',BLUE),('GPT-5.6',TEAL),('Planner',ORANGE),('Market',GRAY)]):
        palette.gca().plot([.2*k,.2*k+.15],[.7,.7],color=c,lw=6);palette.gca().text(.2*k,.22,lab,fontsize=11)
    palette.savefig(DEST/'palette.png');plt.close(palette)
    graphics=[('Advice comparison','Three time-series sharing the same physical economy',['advice-0-GPT-5.5-0','advice-0-GPT-5.6-0'],'Conditional upgrade comparison, not real-world causality'),
       ('Initial conditions','Computed state trajectories with start circles, time arrows and endpoint stars',['initial-path-0-0-0'],'Six tested starts, not a global stability theorem'),
       ('Research and aid','Separate research-share and assistance-index trajectories',['research-0-GPT-5.5','assistance-0-GPT-5.6'],'Adviser rules versus normative planner'),
       ('Normative tradeoff','Output-needs coordinates and numeric table',['weight-response-0'],'A weight scan, not a Pareto-frontier theorem'),
       ('Innovation size','Two responses to quality jumps and numeric table',['innovation-gain-0','innovation-needs-0'],'Fixed-economy reoptimized planner sensitivity'),
       ('Numerical verification','Value discrepancy and relative path change with settings table',['value-check-0','gain-check-0'],'Joint refinement, not known exact-solution error')]
    manifest=dict(iconography_mode='minimal-scientific',palette=dict(ink=INK,surface=SURFACE,primary=BLUE,secondary=TEAL,status_accent=ORANGE,divider=DIVIDER),
      semantic_graphics=[dict(concept=c,visual_encoding=v,shape_ids=s+[f'figure-{i+1}-title'],origin='Original reproducible Python figures',evidence_implication=e) for i,(c,v,s,e) in enumerate(graphics)],
      composition_mechanism='Advice comparison is primary; physical mechanism and normative sensitivity are secondary; numerical checks are separate.',
      evidence_status='Conditional computed review; interpretation pending',countries=COUNTRIES,
      grayscale_encoding='Adviser line styles, omega marker shapes, direct numerical tables, labeled axes and open starts versus stars preserve meaning without color.',
      outputs=[str(DELIVERY/('EthosGPT_R3_'+n+'.svg')) for n in names],
      source_hashes={n:hashlib.sha256((DEST/n).read_bytes()).hexdigest() for n in ['country-paths.csv','matched-sensitivity.csv','country-refinement.csv']})
    (DEST/'figure-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(PDF=str(pdf),figures=names),indent=2))

if __name__=='__main__':main()
