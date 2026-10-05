"""Node 2 style preview: computed geometry, not a new empirical claim.

Run from anywhere. Approved manuscript files are never edited.
The market sheet is selected by terminal patent pricing. Planner trajectories
use HeldPolicy, never interpolated controls. SVGs retain live text.
"""
from pathlib import Path
import json, hashlib, shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Rectangle
import matplotlib.patheffects as peffects
from mpl_toolkits.mplot3d import proj3d
from PIL import Image, ImageOps, ImageDraw
from node2 import ROOT, OUT, conditional_parameters, INITIALS
from node2_diagnostics import HeldPolicy
from model import market_path, jacobian_market, market_rhs, burden_flow, steady_burden

DELIVERY=Path(__file__).resolve().parent/'figures'
DEST=Path(__file__).resolve().parent/'country_revision_results'/'systems'
INK='#18324A'; BLUE='#315EFB'; TEAL='#128C80'; ORANGE='#D97745'
SURFACE='#F5F7FB'; DIVIDER='#CBD5E1'
CMAP=LinearSegmentedColormap.from_list('aid',[SURFACE,'#ADC6F2',BLUE])
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,
 'axes.labelsize':12,'xtick.labelsize':10,'ytick.labelsize':10,
 'svg.fonttype':'none','pdf.fonttype':42,'text.color':INK,
 'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,
 'savefig.facecolor':'white','figure.facecolor':'white','path.simplify':False})

def page(letter,title,subtitle,three=True):
    fig=plt.figure(figsize=(14,10))
    fig.text(.055,.95,letter+'  '+title,fontsize=23,weight='bold',gid='panel-title')
    fig.text(.055,.898,subtitle,fontsize=12,gid='panel-subtitle')
    ax=fig.add_axes([.10,.29,.73,.55],projection='3d' if three else None)
    if three:
        ax.computed_zorder=False
        ax.view_init(elev=24,azim=-58)
        ax.set_box_aspect((1.25,1,.72))
        for axis in [ax.xaxis,ax.yaxis,ax.zaxis]:
            axis.pane.fill=False
            axis._axinfo['grid'].update(color=DIVIDER,linewidth=.5)
            axis.labelpad=15
        ax.tick_params(pad=5)
    else:
        ax.spines[['top','right']].set_visible(False)
        ax.grid(alpha=.16)
    return fig,ax

def footer(fig,line1,line2,legend):
    # Protected bands: title .89--.97, graph .23--.84,
    # legend .16--.20, captions .055--.13.
    if isinstance(legend,str):
        fig.text(.055,.181,legend,fontsize=10,gid='legend-text')
    else:
        for k,(kind,label) in enumerate(legend):
            sx=.06+.455*(k%2); yy=.216-.035*(k//2)
            if kind in ['path','flow','growth']:
                color=TEAL if kind=='flow' else ORANGE if kind=='growth' else BLUE
                art=Line2D([sx,sx+.034],[yy,yy],transform=fig.transFigure,
                    color=color,lw=2.4,ls='--' if kind=='growth' else '-')
                art.set_gid(f'legend-{kind}-sample-{k}');fig.add_artist(art)
                if kind!='growth':
                    arrow=FancyArrowPatch((sx+.006,yy),(sx+.036,yy),transform=fig.transFigure,
                        arrowstyle='-|>',mutation_scale=12,color=color,lw=1.4)
                    arrow.set_gid(f'legend-{kind}-arrow-{k}');fig.add_artist(arrow)
            elif kind in ['start','target']:
                art=Line2D([sx+.018],[yy],transform=fig.transFigure,linestyle='None',
                    marker='o' if kind=='start' else '*',markersize=8 if kind=='start' else 13,
                    markerfacecolor='white' if kind=='start' else ORANGE,markeredgecolor=INK,markeredgewidth=.8)
                art.set_gid(f'legend-{kind}-sample-{k}');fig.add_artist(art)
            elif kind=='mesh':
                rect=Rectangle((sx+.003,yy-.010),.033,.020,transform=fig.transFigure,
                    facecolor='#DCE5F8',edgecolor='#7C9AC7',lw=.6)
                rect.set_gid(f'legend-mesh-sample-{k}');fig.add_artist(rect)
                for t in [.011,.019,.027]:
                    fig.add_artist(Line2D([sx+t,sx+t],[yy-.010,yy+.010],transform=fig.transFigure,color='#7C9AC7',lw=.5))
                fig.add_artist(Line2D([sx+.003,sx+.036],[yy,yy],transform=fig.transFigure,color='#7C9AC7',lw=.5))
            fig.text(sx+.050,yy,label,fontsize=11,va='center',gid=f'legend-{kind}-label-{k}')
    fig.text(.055,.113,line1,fontsize=11,gid='caption-one')
    fig.text(.055,.072,line2,fontsize=10,gid='caption-two')

def star3(ax,x,y,z):
    ax.scatter([x],[y],[z],s=170,marker='*',c=ORANGE,
               edgecolors=INK,linewidths=.6,depthshade=False,zorder=5,gid='stationary-star')

def time_arrow(ax,xyz,three=True,fraction=.38):
    """Project an arrow along the existing computed path, in forward time."""
    xyz=np.asarray(xyz)
    distance=np.r_[0,np.cumsum(np.linalg.norm(np.diff(xyz,axis=1),axis=0))]
    if distance[-1]<1e-8:return
    lo=np.searchsorted(distance,fraction*distance[-1]);hi=np.searchsorted(distance,min(.9,fraction+.075)*distance[-1])
    lo=min(lo,xyz.shape[1]-2);hi=min(max(hi,lo+1),xyz.shape[1]-1)
    if three:
        x0,y0,_=proj3d.proj_transform(*xyz[:,lo],ax.get_proj())
        x1,y1,_=proj3d.proj_transform(*xyz[:,hi],ax.get_proj())
    else:x0,y0=xyz[:2,lo];x1,y1=xyz[:2,hi]
    ax.annotate('',xy=(x1,y1),xytext=(x0,y0),arrowprops=dict(arrowstyle='-|>',color=BLUE,lw=1.6,mutation_scale=12),zorder=7)

def external_axes(fig,ax,key,xticks,yticks,zticks,axis_labels=('X','Y','Z')):
    """Flat live-text tick gutters avoid diagonal text collisions in 3D exports.

    Tick positions are projected from their actual data coordinates; the frame
    is a genuine coordinate frame, not decorative perspective geometry.
    """
    x0,x1=ax.get_xlim();y0,y1=ax.get_ylim();z0,z1=ax.get_zlim()
    ax.set_axis_off()
    ax.patch.set_facecolor('none')
    fig.text(.055,.845,key,fontsize=11,gid='external-axis-key')
    for x in xticks:
        ax.plot(np.full(61,x),np.linspace(y0,y1,61),np.full(61,z0),c=DIVIDER,lw=.55)
    for y in yticks:
        ax.plot(np.linspace(x0,x1,61),np.full(61,y),np.full(61,z0),c=DIVIDER,lw=.55)
    for xx,yy,zz in [([x0,x1],[y0,y0],[z0,z0]),([x1,x1],[y0,y1],[z0,z0]),([x1,x1],[y1,y1],[z0,z1])]:
        ax.plot(np.linspace(*xx,61),np.linspace(*yy,61),np.linspace(*zz,61),c='#7E8D9C',lw=.9)
    fig.canvas.draw()
    def pos(x,y,z):
        px,py,_=proj3d.proj_transform(x,y,z,ax.get_proj())
        return fig.transFigure.inverted().transform(ax.transData.transform([px,py]))
    for x in xticks:
        px,py=pos(x,y0,z0)
        fig.text(px,py-.03,f'{x:g}',fontsize=10,ha='center',va='top')
    for y in yticks[1:]:
        px,py=pos(x1,y,z0)
        fig.text(px+.021,py-.008,f'{y:g}',fontsize=10,ha='left',va='center')
    for z in zticks[1:]:
        px,py=pos(x1,y1,z)
        fig.text(px+.022,py,f'{z:g}',fontsize=10,ha='left',va='center')
    px,py=pos(x1,y0,z0);fig.text(px,py-.065,axis_labels[0],fontsize=11,ha='center')
    px,py=pos(x1,y1,z0);fig.text(px+.075,py-.025,axis_labels[1],fontsize=11,ha='center')
    px,py=pos(x1,y1,z1);fig.text(px+.038,py+.03,axis_labels[2],fontsize=11,ha='center')

def main():
    DEST.mkdir(exist_ok=True); DELIVERY.mkdir(exist_ok=True)
    p,_=conditional_parameters('Germany')
    eqs=pd.read_csv(OUT/'review-stationary-equilibria.csv')
    e=eqs[(eqs.country=='Germany')&(eqs.policy=='implemented Section 6 market')&(eqs.source=='Human survey')].iloc[0]
    pe=eqs[(eqs.country=='Germany')&(eqs.policy=='planner held optimal control')].iloc[0]
    a=float(e.a); tau=float(e.tax_subsidy); ve=float(e.patent)
    z=np.load(OUT/'policy-Germany-101-61-0.125.npz')
    hp=HeldPolicy(p,z['grid'],z['value'],61,.125)
    held=pd.read_csv(OUT/'held-optimal-paths.csv')
    held=held[held.country=='Germany'].copy()
    paths=[g.sort_values('t') for _,g in held.groupby(['initial_u_A','initial_u_B'])]
    # 121 independently solved BVPs. Values are actual model output.
    grid=np.linspace(0,.85,11); X,Y=np.meshgrid(grid,grid,indexing='ij')
    V=np.empty_like(X); bvp=[]; market_traces=[]
    for i in range(len(grid)):
        for j in range(len(grid)):
            sol,_=market_path(a,tau,p,initial=(X[i,j],Y[i,j]),end=60.)
            V[i,j]=sol.sol(0)[2]
            bvp.append(dict(u_A=X[i,j],u_B=Y[i,j],patent_value=V[i,j],
                bvp_residual=float(np.max(sol.rms_residuals))))
    for initial in INITIALS:
        sol,_=market_path(a,tau,p,initial=initial,end=60.)
        tt=np.r_[np.linspace(0,8,120),np.linspace(8.1,60,100)]
        yy=sol.sol(tt); market_traces.append((tt,yy))
    pd.DataFrame(bvp).to_csv(DEST/'market-valuation-sheet.csv',index=False)
    # Continuous vector field under the re-optimized held-decision action.
    fg=np.linspace(0,.4,27); FX,FY=np.meshgrid(fg,fg)
    N=np.empty_like(FX); A=N.copy(); DU=N.copy(); DV=N.copy()
    flows=[]
    for i in range(len(fg)):
        for j in range(len(fg)):
            u=np.array([FX[i,j],FY[i,j]]); n,aa=hp.action(u)
            du=burden_flow(u,n,aa,p); N[i,j]=n; A[i,j]=aa; DU[i,j]=du[0]; DV[i,j]=du[1]
            flows.append(dict(u_A=u[0],u_B=u[1],n=n,a=aa,du_A=du[0],du_B=du[1]))
    pd.DataFrame(flows).to_csv(DEST/'planner-phase-field.csv',index=False)
    assert np.max(N+p.aid_labor*A-p.capacity)<1e-10
    report={'status':'Computed style preview; human interpretation pending',
      'country':'Germany conditional scenario','market_valuation_grid':11,
      'market_BVP_max_residual':max(r['bvp_residual'] for r in bvp),
      'market_eigenvalues':np.linalg.eigvals(jacobian_market(a,tau,p)).tolist(),
      'planner_policy_grid':101,'control_points_per_dimension':61,'decision_dt':.125,
      'phase_display_grid':27,'phase_domain':[0,.4],
      'market_patent_terminal_horizon':60.,
      'market_sheet_definition':'Initial patent value satisfying the future pricing terminal boundary; finite-horizon numerical approximation to the admissible stable sheet.',
      'planner_flow_definition':'Physical derivative at each node under the Bellman action chosen at that state; streamlines interpolate only the displayed vector field.',
      'planner_paths_definition':'Existing exact physical held-control rollouts, reoptimized at actual state every dt; no control-map interpolation.',
      'non_claims':['No cusp, hysteresis or multiple attractors asserted','No physical potential or energy function','No global uniqueness or all-parameter stability theorem','No national forecast or empirical welfare estimate'],
      'source_hashes':{f:hashlib.sha256((OUT/f).read_bytes()).hexdigest() for f in ['policy-Germany-101-61-0.125.npz','held-optimal-paths.csv','review-stationary-equilibria.csv']}}
    (DEST/'preview-evidence.json').write_text(json.dumps(report,indent=2)+'\n')
    figs=[]; names=[]
    # A: market pricing sheet and convergent paths. z is explicitly magnified.
    fig,ax=page('A','1 Pricing: market values select admissible paths',
        'Germany mechanism preview | Market implements human rule | Six initial need states')
    ax.plot_surface(100*X,100*Y,1000*(V-ve),color='#DCE5F8',alpha=.65,
        linewidth=.6,edgecolor='#7C9AC7',shade=False,zorder=1,gid='valuation-sheet')
    for k,(tt,yy) in enumerate(market_traces):
        ax.plot(100*yy[0],100*yy[1],1000*(yy[2]-ve),c=BLUE,lw=2.2,zorder=3,gid=f'market-path-{k}')
        ax.scatter([100*yy[0,0]],[100*yy[1,0]],[1000*(yy[2,0]-ve)],s=36,
            facecolors='white',edgecolors=INK,depthshade=False,zorder=4)
    star3(ax,100*e.u_A,100*e.u_B,0)
    ax.set_xlabel('Unresolved needs A: 100u_A (%)')
    ax.set_ylabel('Unresolved needs B: 100u_B (%)')
    ax.set_zlabel('Patent deviation: 1000(v - v*)')
    ax.set(xlim=(0,85),ylim=(0,85),zlim=(0,2.7))
    external_axes(fig,ax,'X: unresolved needs A, 100u_A (%)    Y: unresolved needs B, 100u_B (%)    Z: patent value deviation, 1000(v - v*)',
        [0,25,50,85],[0,25,50,85],[0,1,2],('u_A (%)','u_B (%)','1000(v - v*)'))
    for tt,yy in market_traces:time_arrow(ax,np.vstack((100*yy[:2],1000*(yy[2]-ve))))
    footer(fig,f'Conclusion: six tested starts approach the market state: u_A* = {100*e.u_A:.2f}%, u_B* = {100*e.u_B:.2f}%. Patent prices satisfy future pricing.',
        'Local eigenvalues: -0.747, -0.835, +66.325. A saddle has two stable directions and one unstable valuation direction.',
        [('mesh','Compatible initial patent values'),('path','Computed path; arrow = later time'),
         ('start','Starting state (t = 0)'),('target','Stationary market state')])
    figs.append(fig); names.append('A_Market_Valuation_Sheet')
    # B: true physical phase flow, and only four paths whose initial states fit.
    fig,ax=page('B','3 Needs: inflow and recovery balance',
        'Germany | Planner extension after C: controls change the evolution of needs | omega = 0.30',False)
    speed=np.hypot(DU,DV)
    edges=np.r_[0,(100*fg[:-1]+100*fg[1:])/2,40]
    im=ax.pcolormesh(edges,edges,speed,cmap=CMAP,shading='flat',alpha=.65,gid='local-flow-speed')
    ax.streamplot(100*fg,100*fg,100*DU,100*DV,color=TEAL,density=1.15,linewidth=.75,arrowsize=1.15)
    for k,g in enumerate(paths):
        if max(float(g.initial_u_A.iloc[0]),float(g.initial_u_B.iloc[0]))>.4:continue
        ax.plot(100*g.u_A,100*g.u_B,c=BLUE,lw=2.4,gid=f'held-phase-path-{k}')
        time_arrow(ax,np.vstack((100*g.u_A,100*g.u_B)),three=False)
        ax.scatter(100*g.u_A.iloc[0],100*g.u_B.iloc[0],s=42,facecolors='white',edgecolors=INK,zorder=5)
    ax.scatter(100*pe.u_A,100*pe.u_B,marker='*',s=190,c=ORANGE,edgecolors=INK,zorder=6,gid='planner-state-star')
    ax.set(xlim=(0,40),ylim=(0,40),xlabel='Unresolved needs A: 100u_A (%)',ylabel='Unresolved needs B: 100u_B (%)')
    ax.set_aspect('equal');ax.set_xticks([0,10,20,30,40]);ax.set_yticks([0,10,20,30,40])
    cbax=fig.add_axes([.855,.33,.025,.39]);cb=fig.colorbar(im,cax=cbax)
    cb.solids.set_rasterized(False)
    cb.set_label('Adjustment speed ||du/dt|| (fraction / model time)',labelpad=12)
    footer(fig,f'Conclusion: four tested starts approach ({100*pe.u_A:.2f}%, {100*pe.u_B:.2f}%). Darker background = faster change, not better welfare.',
        'Streamlines interpolate the displayed field; solid paths are exact held-action state integrations. This is not a global stability proof.',
        [('path','Computed path; arrow = later time'),('flow','Instantaneous direction of needs'),
         ('start','Starting needs (t = 0)'),('target','Candidate steady needs')])
    figs.append(fig); names.append('B_Controlled_Phase_Flow')
    # C: display exact control decisions on nodes. Face interpolation is rendering only.
    fig,ax=page('C','2 Choices: research and aid share a budget',
        'Germany | Planner extension after A: optimize long-run output minus weighted needs | Height n*, color a*')
    surf=ax.plot_surface(100*FX,100*FY,100*N,facecolors=CMAP(A),
        edgecolor=DIVIDER,linewidth=.3,shade=False,alpha=.94,zorder=1,gid='research-policy-surface')
    for k,g in enumerate(paths):
        if max(float(g.initial_u_A.iloc[0]),float(g.initial_u_B.iloc[0]))>.4:continue
        ax.plot(100*g.u_A,100*g.u_B,100*g.n,c=BLUE,lw=2.4,zorder=3,
            path_effects=[peffects.Stroke(linewidth=4.6,foreground='white'),peffects.Normal()],gid=f'control-path-{k}')
        ax.scatter([100*g.u_A.iloc[0]],[100*g.u_B.iloc[0]],[100*g.n.iloc[0]],s=36,
            facecolors='white',edgecolors=INK,depthshade=False,zorder=4)
    star3(ax,100*pe.u_A,100*pe.u_B,100*pe.n)
    ax.set_xlabel('Unresolved needs A: 100u_A (%)')
    ax.set_ylabel('Unresolved needs B: 100u_B (%)')
    ax.set_zlabel('Research labor: 100n*(u) (%)')
    ax.set_zlim(0,10)
    ax.set(xlim=(0,40),ylim=(0,40))
    external_axes(fig,ax,'X: unresolved needs A, 100u_A (%)    Y: unresolved needs B, 100u_B (%)    Z: optimal research share, 100n*(u) (%)',
        [0,10,20,40],[0,10,20,40],[0,5,10],('u_A (%)','u_B (%)','100n* (%)'))
    for g in paths:
        if max(float(g.initial_u_A.iloc[0]),float(g.initial_u_B.iloc[0]))<=.4:
            time_arrow(ax,np.vstack((100*g.u_A,100*g.u_B,100*g.n)))
    cbax=fig.add_axes([.855,.33,.025,.39]);cb=fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(0,1),cmap=CMAP),cax=cbax)
    cb.solids.set_rasterized(False)
    cb.set_label('Assistance strength a*(u), index [0, 1]',labelpad=12)
    footer(fig,'Conclusion: assistance and research compete for capacity; n + 0.04a <= B = 0.0902.',
        'This is a control map, not an energy or welfare potential. Surface facets connect computed decisions; they do not define the simulated policy.',
        [('mesh','Surface height = research share n*'),('path','Controls along a computed path'),
         ('start','Starting control (t = 0)'),('target','Planner long-run target')])
    figs.append(fig); names.append('C_Optimal_Control_Surface')
    # D: balanced growth rays. All six initial conditions retained.
    fig,ax=page('D','4 Growth: rate settles, cumulative gain rises',
        'Germany | Same planner as C and B | Inset shows the growth rate; 3D axis shows cumulative progress')
    ax.set_position([.025,.30,.61,.53])
    for k,g in enumerate(paths):
        ax.plot(g.log_quality,100*g.u_A,100*g.u_B,c=BLUE,lw=2.1,zorder=3,gid=f'balanced-growth-path-{k}')
        ax.scatter([g.log_quality.iloc[0]],[100*g.u_A.iloc[0]],[100*g.u_B.iloc[0]],
            s=36,facecolors='white',edgecolors=INK,depthshade=False,zorder=5)
    xx=np.linspace(0,float(held.log_quality.max()),50)
    ax.plot(xx,np.full_like(xx,100*pe.u_A),np.full_like(xx,100*pe.u_B),
        c=ORANGE,ls='--',lw=2.2,zorder=4,gid='balanced-growth-reference-ray')
    ax.set_xlabel('Expected log-quality gain G(t)')
    ax.set_ylabel('Unresolved needs A: 100u_A (%)')
    ax.set_zlabel('Unresolved needs B: 100u_B (%)')
    ax.view_init(elev=25,azim=-57)
    ax.set(xlim=(0,1.8),ylim=(0,85),zlim=(0,85))
    external_axes(fig,ax,'X: expected log-quality gain G(t)    Y: unresolved needs A, 100u_A (%)    Z: unresolved needs B, 100u_B (%)',
        [0,.6,1.2,1.8],[0,25,50,85],[0,25,50,85],('G(t)','u_A (%)','u_B (%)'))
    for g in paths:time_arrow(ax,np.vstack((g.log_quality,100*g.u_A,100*g.u_B)))
    g=paths[2];kk=(g.t>=45)&(g.t<=75)
    time_arrow(ax,np.vstack((g.log_quality[kk],100*g.u_A[kk],100*g.u_B[kk])),fraction=.25)
    rateax=fig.add_axes([.735,.48,.205,.22])
    basepath=next(g for g in paths if np.isclose(g.initial_u_A.iloc[0],.08) and np.isclose(g.initial_u_B.iloc[0],.08))
    rateax.plot(basepath.t,p.chi*basepath.n*np.log1p(p.q),color=TEAL,lw=2,gid='growth-rate-inset')
    rateax.axhline(pe.g_log,color=ORANGE,ls='--',lw=1.1)
    rateax.set_ylim(0,.019);rateax.set_yticks([0,.01]);rateax.set_xticks([0,50,100])
    rateax.set_title('Growth RATE g(t)',fontsize=12,pad=13)
    rateax.set_xlabel('Model time',fontsize=10);rateax.set_ylabel('Rate / model time',fontsize=10)
    rateax.tick_params(labelsize=9);rateax.spines[['top','right']].set_visible(False)
    rateax.text(.035,.75,f'Target: {pe.g_log:.5f}',transform=rateax.transAxes,fontsize=10)
    footer(fig,f'Conclusion: the RATE settles at g* = {pe.g_log:.5f} / model time; cumulative G(t) keeps rising.',
        'The model time unit has not been calibrated to a year. A balanced-growth state is stationary in normalized variables, not in technology level A.',
        [('path','Computed path; arrow = later time'),('growth','Steady needs, continuing quality growth'),
         ('start','Starting state (t = 0)'),('flow','Growth rate in the inset')])
    figs.append(fig); names.append('D_Balanced_Growth_Rays')
    # Focal upgrade page precedes the four mechanism previews.
    upgrade=pd.read_csv(Path(__file__).resolve().parent/'upgrade_impact_results/country-upgrade-impact-comparison.csv')
    upgrade=upgrade.set_index('country').loc[['China','Germany','Egypt']].reset_index()
    fig=plt.figure(figsize=(14,10))
    fig.text(.055,.95,'E  The upgrade changes bias and modeled outcomes',fontsize=23,weight='bold',gid='panel-title')
    fig.text(.055,.898,'GPT-5.6 minus GPT-5.5 | Same country, economic parameters, initial state and implementation rule',fontsize=12,gid='panel-subtitle')
    left=fig.add_axes([.105,.32,.40,.48]);right=fig.add_axes([.64,.32,.29,.48])
    for ax in [left,right]:
        ax.spines[['top','right']].set_visible(False);ax.grid(alpha=.14)
    left.set_title('Conditional growth / need effects',fontsize=15,pad=15)
    left.grid(False)
    left.axvline(0,c=DIVIDER,lw=1);left.axhline(0,c=DIVIDER,lw=1)
    markers=['o','s','D'];offsets=[(8,14),(8,14),(8,-24)]
    labels=['China','Germany','Egypt']
    for k,(_,r) in enumerate(upgrade.iterrows()):
        xx=100*r.upgrade_change_G;yy=100*r.upgrade_change_Umax
        left.scatter(xx,yy,s=85,marker=markers[k],c=BLUE,edgecolors=INK,linewidths=.7,gid=f'upgrade-effect-{k}')
        left.annotate(labels[k],(xx,yy),xytext=offsets[k],textcoords='offset points',fontsize=11)
    left.set(xlim=(-.47,.02),ylim=(-.045,.003),
        xlabel='Cumulative log-quality change: 100 Delta G (log points)',
        ylabel='Worst-group mean need change (percentage points)')
    left.set_xticks([-.4,-.2,0]);left.set_yticks([-.04,-.02,0])
    right.set_title('Observed six-item bias change',fontsize=15,pad=15)
    vals=100*upgrade.upgrade_six_item_mean_TVD_change.to_numpy()
    bars=right.barh(np.arange(3),vals,color=BLUE,height=.47)
    for i,bar in enumerate(bars):bar.set_gid(f'upgrade-tvd-change-{i}')
    right.grid(False)
    right.axvline(0,c=INK,lw=1)
    right.set_yticks(np.arange(3),['China','Germany','Egypt']);right.invert_yaxis()
    right.set_xlabel('Change in mean TVD (percentage points)',labelpad=13)
    lo=min(0,float(vals.min()));hi=max(0,float(vals.max()));pad=max(1.,(hi-lo)*.17)
    right.set_xlim(lo-pad,hi+pad)
    for i,x in enumerate(vals):
        right.text(x+(.12 if x>=0 else -.12),i,f'{x:+.2f}',va='center',ha='left' if x>=0 else 'right',fontsize=11)
    footer(fig,'Conclusion: lower response-distribution error can coexist with a larger growth gap from the human-rule baseline.',
        'China, Germany, Egypt: matched within-country market comparison, H=100. Right: archived six-item mean TVD. No national causal effect claimed.',
        'Upgrade effects compare the two advisers. The planner is a separate normative benchmark, not the upgrade treatment.')
    figs=[fig,figs[0],figs[2],figs[1],figs[3]]
    names=['E_Upgrade_Bias_Impacts','A_Market_Valuation_Sheet','C_Optimal_Control_Surface','B_Controlled_Phase_Flow','D_Balanced_Growth_Rays']
    pdf=DEST/'system-preview.pdf'
    staging_pdf=DEST/'preview-build.pdf'
    with PdfPages(staging_pdf) as pp:
        for fig,name in zip(figs,names):
            # Every visible data mark is already bounded by the explicit plot
            # domain. Clipping is unnecessary and obscures source geometry.
            for artist in fig.findobj():
                if hasattr(artist,'set_clip_on'):artist.set_clip_on(False)
            stem='EthosGPT_R3_System_'+name
            fig.savefig(DELIVERY/(stem+'.svg'))
            fig.savefig(DELIVERY/(stem+'.png'),dpi=160)
            pp.savefig(fig)
            plt.close(fig)
    import fitz
    with fitz.open(staging_pdf) as check:
        assert len(check)==5, 'Incomplete preview PDF'
    shutil.copy2(staging_pdf,pdf)
    # Overview for convenient comparison; standalone vector pages are authoritative.
    ims=[]
    for name in names[1:]:
        im=Image.open(DELIVERY/('EthosGPT_R3_System_'+name+'.png')).convert('RGB')
        im.thumbnail((1120,800));ims.append(im)
    canvas=Image.new('RGB',(2240,1600),'white')
    for k,im in enumerate(ims):canvas.paste(im,((k%2)*1120,(k//2)*800))
    canvas.save(DELIVERY/'EthosGPT_R3_System_Overview.png')
    # A grayscale QA preview, never scientific data authority.
    ImageOps.grayscale(canvas).save(DEST/'overview-grayscale.png')
    graphics=[
      ('Compatible market valuations','3D sheet with six convergent equilibrium paths',['valuation-sheet','panel-title'],'Future pricing selects a compatible initial patent value; no physical potential.'),
      ('Controlled state transition','Phase arrows, computed paths and stationary star',['local-flow-speed','planner-state-star'],'One conditional numerical convergence result, not a global proof.'),
      ('State-contingent optimal action','Surface height for research share, ordered face color for assistance',['research-policy-surface','panel-subtitle'],'Computed finite-grid policy; facets are visualization only.'),
      ('Balanced growth','3D trajectories with a stationary-need reference ray',['balanced-growth-path-0','balanced-growth-reference-ray'],'Normalized states stabilize while expected log-quality continues increasing.')]
    graphics.append(('Version-upgrade propagation','Bias-change bars and two-axis outcome displacement',['upgrade-tvd-change-0','upgrade-effect-0'],'Observed adviser bias change is distinct from conditional model consequences. No real-world causal effect.'))
    manifest={'iconography_mode':'minimal-scientific','palette':{'ink':INK,'surface':SURFACE,'primary':BLUE,'secondary':TEAL,'status_accent':ORANGE,'divider':DIVIDER},
      'semantic_graphics':[dict(concept=c,visual_encoding=v,shape_ids=s,origin='original reproducible Python numerical graphics',evidence_implication=e0) for c,v,s,e0 in graphics],
      'composition_mechanism':'Admissible pricing sheet, feedback phase flow, action surface and balanced-growth rays show four different structures of the same conditional model.',
      'grayscale_encoding':'Axes and geometry carry all variables. Solid paths, open starts, star endpoints, dashed reference ray are redundant cues. Numeric colorbar defines assistance in C.',
      'evidence_status':'Numerical conditional-model results; author-facing style preview, interpretation not approved.',
      'title_band':[.89,.97],'viewport_band':[.26,.84],'legend_band':[.16,.235],'caption_band':[.055,.13],
      'legend_revision':'r3: ordered E, A, C, B, D with result conclusions and a rate-versus-cumulative inset;  visible sample glyphs, unified blue computed paths, forward-time arrows, direct variable axis labels, panel-specific color scales, market/planner scope',
      'legend_semantics':{'blue_solid_arrow':'computed path, forward model time; not adviser-version identity',
        'open_circle':'start at t=0','orange_star':'stationary normalized target in A-C',
        'green_arrow':'instantaneous state-change direction in B',
        'orange_dashed':'balanced-growth reference ray in D',
        'background_B':'darker = faster state adjustment','surface_height_C':'research share n*',
        'surface_color_C':'darker = stronger assistance a*'},
      'outputs':[str(pdf),*[str(DELIVERY/('EthosGPT_R3_System_'+x+'.svg')) for x in names]]}
    (DEST/'figure-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'PDF':str(pdf),'panels':names,'evidence':report},indent=2))

if __name__=='__main__':main()
