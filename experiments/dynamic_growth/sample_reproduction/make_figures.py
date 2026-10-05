"""Reproducible, uncalibrated mechanism illustrations for the EthosGPT plan.

Model A is a reduced, dimensionless transition model. Models B and C are
separate mathematical normal forms. No survey or economic observations are
used to generate these figures. See MODEL_AND_METRICS.md for definitions.
Run: python make_figures.py
"""
from pathlib import Path
import csv
import json
import platform
import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.optimize import brentq, root
from scipy.special import expit
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "figures"
DATA = ROOT / "data"
FIG.mkdir(exist_ok=True)
DATA.mkdir(exist_ok=True)
P = dict(b0=.7, beta=.45, alpha=.9, chi=.35,
         d=np.array([.75, .38]), r0=np.array([.12, .32]),
         r1=np.array([1.2, 1.0]), gamma=1.12, capacity=2.4)
TEAL, PINK, GOLD = "#007F86", "#B93678", "#C58A14"
INK, GREY, BLUE = "#17293F", "#738194", "#4969BB"
BG = "#FBFCFE"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
    "axes.titlesize": 15, "axes.titleweight": "medium", "axes.labelsize": 11,
    "axes.edgecolor": "#BAC3CF", "axes.labelcolor": INK,
    "text.color": INK, "xtick.color": INK, "ytick.color": INK,
    "axes.facecolor": BG, "figure.facecolor": BG,
    "axes.spines.top": False, "axes.spines.right": False,
    "svg.fonttype": "none", "pdf.fonttype": 42})


def save_csv(name, columns, rows):
    with (DATA / name).open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(columns)
        w.writerows(rows)


def decorate(ax, title, xlabel, ylabel):
    ax.set_title(title, loc="left", pad=13)
    ax.set_xlabel(xlabel, labelpad=8)
    ax.set_ylabel(ylabel, labelpad=8)
    ax.grid(alpha=.14)
    ax.set_axisbelow(True)


def save_fig(fig, name, caption):
    fig.text(.015, .012, caption, fontsize=9, color=GREY)
    for ext in ("png", "svg", "pdf"):
        fig.savefig(FIG / (name + "." + ext), dpi=220)
    plt.close(fig)


def steady_u(z, nu, a):
    lam = nu * expit(2 * z)
    rr = P["r0"] + P["r1"] * a
    return P["d"] * lam / (P["d"] * lam + rr)


def equilibrium_f(z, nu, a, c=0):
    return z-z**3 + P["b0"] + c + P["beta"]*a - P["alpha"]*nu - P["chi"]*np.mean(steady_u(z, nu, a))


def equilibrium_dz(z, nu, a):
    xx = expit(2*z)
    rr = P["r0"] + P["r1"]*a
    lam = nu*xx
    du = P["d"] * (2*lam*(1-xx)) * rr / (P["d"]*lam + rr)**2
    return 1-3*z*z - P["chi"]*np.mean(du)


def fold(a, c=0):
    sol = root(lambda v: [equilibrium_f(v[0], v[1], a, c),
                          equilibrium_dz(v[0], v[1], a)], [.56, 1.2+c])
    if not sol.success or np.max(np.abs(sol.fun)) > 1e-8:
        raise RuntimeError("Fold did not converge")
    return sol.x  # z at fold, innovation launch intensity nu at fold


def equilibria(nu, a, c=0):
    zz = np.linspace(-2.7, 2.7, 1001)
    ff = np.array([equilibrium_f(z, nu, a, c) for z in zz])
    roots = [brentq(lambda z: equilibrium_f(z, nu, a, c), zz[k], zz[k+1], xtol=1e-13)
             for k in range(len(zz)-1) if ff[k]*ff[k+1] < 0]
    return roots


def jacobian(z, nu, a):
    xx = expit(2*z)
    uu = steady_u(z, nu, a)
    rr = P["r0"] + P["r1"]*a
    j = np.zeros((3, 3))
    j[0, 0] = 1-3*z*z
    j[0, 1:] = -P["chi"]/2
    j[1:, 0] = P["d"]*nu*2*xx*(1-xx)*(1-uu)
    j[1:, 1:] = np.diag(-(P["d"]*nu*xx+rr))
    return j


def rhs(t, y, nu, a, c=0):
    z, u1, u2, q = y
    xx = expit(2*z)
    uu = np.array([u1, u2])
    dc = c(t) if callable(c) else c
    return np.r_[z-z**3+P["b0"]+dc+P["beta"]*a-P["alpha"]*nu-P["chi"]*uu.mean(),
                 P["d"]*nu*xx*(1-uu)-(P["r0"]+P["r1"]*a)*uu,
                 np.log(P["gamma"])*nu*xx]


def simulate(nu, a, c=0, tolerance=1e-9, horizon=60):
    if a+nu/P["capacity"] > 1+1e-10:
        raise ValueError("The policy exceeds the common budget")
    tt = np.linspace(0, horizon, 1201)
    sol = solve_ivp(rhs, (0, horizon), [1.25, .08, .08, 0],
                    args=(nu, a, c), t_eval=tt, method="DOP853",
                    rtol=tolerance, atol=tolerance*.1)
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol


def metrics(sol):
    mean_g = sol.y[3, -1]/sol.t[-1]
    group_u = np.trapezoid(sol.y[1:3], sol.t, axis=1)/sol.t[-1]
    return dict(growth=mean_g, mean_burden=group_u.mean(),
                worst_burden=group_u.max(), burden_gap=np.ptp(group_u),
                peak_worst=np.max(sol.y[1:3]), adoption_final=expit(2*sol.y[0, -1]))


def culture_rhs(p, Q, rewards, rho=.3):
    """Simplex-preserving local Markov + replicator module, no causal fit."""
    return Q.T@p + rho*p*(rewards-np.dot(p, rewards))


def plot_boundary():
    aa = np.linspace(0, .72, 181)
    ff0 = np.array([fold(a, 0) for a in aa])
    ff1 = np.array([fold(a, .18) for a in aa])
    cap = P["capacity"]*(1-aa)
    safe = np.minimum(ff0[:, 1], cap)
    save_csv("boundary.csv", ["aid_share", "true_fold_nu", "perceived_fold_nu", "budget_capacity_nu", "true_fold_realized_hazard", "perceived_fold_realized_hazard"],
             zip(aa, ff0[:, 1], ff1[:, 1], cap, ff0[:, 1]*expit(2*ff0[:, 0]), ff1[:, 1]*expit(2*ff1[:, 0])))
    fig, ax = plt.subplots(figsize=(8.8, 5.7))
    fig.subplots_adjust(left=.12, right=.98, top=.86, bottom=.16)
    ax.fill_between(aa, 0, safe, color=TEAL, alpha=.1)
    ax.fill_between(aa, ff0[:, 1], np.minimum(ff1[:, 1], cap),
                    where=cap>ff0[:, 1], color=PINK, alpha=.16)
    ax.fill_between(aa, cap, 2.5, color=GREY, alpha=.09)
    ax.plot(aa, ff0[:, 1], color=TEAL, lw=2.6, label="True fold (c = 0)")
    ax.plot(aa, ff1[:, 1], color=PINK, lw=2.4, ls="--", label="Perceived fold (bias = +0.18)")
    ax.plot(aa, cap, color=INK, lw=1.6, ls=":", label="Common budget capacity")
    ax.text(.06, .48, "High branch exists\nwithin the budget", color=TEAL, fontsize=12)
    ax.text(.56, 1.82, "Over budget", color=GREY, fontsize=11)
    ax.annotate("False-feasible wedge", xy=(.18, 1.17), xytext=(.055, 1.64),
                arrowprops=dict(arrowstyle="->", color=PINK), color=PINK)
    ax.set_xlim(0, .72)
    ax.set_ylim(0, 2.5)
    decorate(ax, "A  |  Belief shifts the predicted transition boundary",
             "Adjustment assistance, a (budget share)", "Innovation launch intensity, ν (normalized)")
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    save_fig(fig, "01_boundary", "MODEL A · Illustrative parameters · Existence of the high branch is not a complete fairness or safety test.")


def plot_bifurcation():
    a = .3
    rows = []
    fig, ax = plt.subplots(figsize=(8.8, 5.7))
    fig.subplots_adjust(left=.12, right=.98, top=.86, bottom=.17)
    for c, color, label in [(0, TEAL, "True system"), (.18, PINK, "Adviser belief")]:
        zs = np.linspace(-1.48, 1.4, 700)
        nus, stability = [], []
        for z in zs:
            try:
                nu = brentq(lambda v: equilibrium_f(z, v, a, c), 0, 2.6)
            except ValueError:
                nu = np.nan
            eig = np.linalg.eigvals(jacobian(z, nu, a)) if np.isfinite(nu) else np.array([np.nan])
            stable = np.all(eig.real<0)
            nus.append(nu)
            stability.append(stable)
            if np.isfinite(nu):
                rows.append([c, a, nu, z, int(stable), float(np.max(eig.real))])
        nus, stability = np.array(nus), np.array(stability)
        ax.plot(nus, np.where(stability, zs, np.nan), color=color, lw=2.6, label=label+" · stable")
        ax.plot(nus, np.where(~stability, zs, np.nan), color=color, lw=1.7, ls="--", label=label+" · saddle")
        zf, nf = fold(a, c)
        ax.scatter([nf], [zf], s=65, marker="D", color=color, zorder=5)
    true_f, perceived_f = fold(a, 0)[1], fold(a, .18)[1]
    ax.axvspan(true_f, perceived_f, color=PINK, alpha=.08)
    ax.annotate("Boundary displacement", xy=((true_f+perceived_f)/2, .58),
                xytext=(1.37, 1.03), arrowprops=dict(arrowstyle="->", color=INK), fontsize=10)
    decorate(ax, "B  |  Stable states, saddles, and fold points",
             "Innovation launch intensity, ν (normalized)", "Coordination state, z (normalized)")
    ax.set_xlim(.55, 1.65)
    ax.set_ylim(-1.55, 1.5)
    ax.legend(loc="lower left", frameon=False, ncol=2, fontsize=9)
    save_csv("bifurcation.csv", ["culture_projection", "aid_share", "nu", "z", "stable", "largest_eigenvalue_real"], rows)
    save_fig(fig, "02_bifurcation", "MODEL A · Fixed assistance a = 0.30 · Solid = stable; dashed = one unstable direction · Symbols = folds.")


def plot_phase():
    # Separate aggregate closure: u is one aggregate burden, not the two-group system.
    nu, a, d, rr = 1.10, .3, .565, .22+1.1*.3
    b = P["b0"]+P["beta"]*a-P["alpha"]*nu
    def field(z, u):
        return z-z**3+b-P["chi"]*u, d*nu*expit(2*z)*(1-u)-rr*u
    zgrid = np.linspace(-1.65, 1.65, 160)
    ugrid = np.linspace(0, 1, 110)
    Z, U = np.meshgrid(zgrid, ugrid)
    DZ, DU = field(Z, U)
    # Vectorized RK4 determines basins for the exact aggregate model.
    zz, uu = Z.copy(), U.copy()
    dt=.07
    for _ in range(500):
        k1=field(zz,uu); k2=field(zz+dt*k1[0]/2,uu+dt*k1[1]/2)
        k3=field(zz+dt*k2[0]/2,uu+dt*k2[1]/2); k4=field(zz+dt*k3[0],uu+dt*k3[1])
        zz+=dt*(k1[0]+2*k2[0]+2*k3[0]+k4[0])/6
        uu+=dt*(k1[1]+2*k2[1]+2*k3[1]+k4[1])/6
    fig, ax = plt.subplots(figsize=(8.8, 5.7))
    fig.subplots_adjust(left=.12, right=.98, top=.86, bottom=.16)
    cmap = LinearSegmentedColormap.from_list("basins", ["#EBD8E2", "#CEE8E9"])
    ax.contourf(Z, U, (zz>0).astype(float), levels=[-.5,.5,1.5], cmap=cmap, alpha=.9)
    ax.streamplot(zgrid, ugrid, DZ, DU, density=.72, linewidth=.65, color=GREY, arrowsize=.75)
    ax.contour(Z,U,DZ,levels=[0],colors=[GOLD],linewidths=1.7)
    ax.contour(Z,U,DU,levels=[0],colors=[BLUE],linewidths=1.7)
    fun = lambda z: z-z**3+b-P["chi"]*(d*nu*expit(2*z)/(d*nu*expit(2*z)+rr))
    roots=[]
    for l,r in zip(zgrid[:-1],zgrid[1:]):
        if fun(l)*fun(r)<0: roots.append(brentq(fun,l,r))
    for z in roots:
        u=d*nu*expit(2*z)/(d*nu*expit(2*z)+rr)
        J=np.array([[1-3*z*z,-P["chi"]],[d*nu*2*expit(2*z)*(1-expit(2*z))*(1-u), -d*nu*expit(2*z)-rr]])
        ev,vec=np.linalg.eig(J)
        stable=np.all(ev.real<0)
        ax.scatter(z,u,marker="o" if stable else "X",s=100,color=TEAL if stable else INK,
                   edgecolors=BG,linewidths=1,zorder=6)
        if not stable:
            v=vec[:,np.argmin(ev.real)].real; v=v/np.linalg.norm(v)
            def stop_at_frame(t,y):
                return min(y[0]-zgrid[0],zgrid[-1]-y[0],y[1],1-y[1])
            stop_at_frame.terminal=True
            stop_at_frame.direction=-1
            for sign in [-1,1]:
                sol=solve_ivp(lambda t,y: -np.array(field(*y)),[0,35],np.array([z,u])+sign*1e-4*v,
                              events=stop_at_frame,max_step=.02,rtol=1e-8,atol=1e-10)
                if not sol.success: raise RuntimeError("Saddle manifold integration failed")
                valid=(sol.y[0]>=zgrid[0])&(sol.y[0]<=zgrid[-1])&(sol.y[1]>=0)&(sol.y[1]<=1)
                ax.plot(np.where(valid,sol.y[0],np.nan),np.where(valid,sol.y[1],np.nan),lw=2,ls="--",color=INK)
    decorate(ax,"C  |  A saddle separates two basins of attraction",
             "Coordination state, z (normalized)","Aggregate transition exposure, u (share)")
    ax.set_xlim(zgrid[0],zgrid[-1]); ax.set_ylim(0,1)
    ax.legend(handles=[Line2D([],[],color=GOLD,label="z nullcline"),Line2D([],[],color=BLUE,label="u nullcline"),
                       Line2D([],[],color=INK,ls="--",label="Saddle stable manifold")],loc="upper left",frameon=False,fontsize=9)
    save_csv("phase_basins.csv",["initial_z","initial_u","high_basin"],zip(Z.ravel(),U.ravel(),(zz>0).astype(int).ravel()))
    save_fig(fig,"03_phase_basins","MODEL A-AGGREGATE · A separate two-state closure · Basin shading is numerical; not a country or cultural classification.")


def policies():
    # Both advisers choose a 6% intensity margin from their estimated fold,
    # while exhausting the SAME normalized resource budget. The adjusted
    # policy also exhausts that budget and trades innovation input for aid.
    a0=brentq(lambda a:P["capacity"]*(1-a)-.94*fold(a,0)[1],.1,.8)
    a1=brentq(lambda a:P["capacity"]*(1-a)-.94*fold(a,.18)[1],.1,.8)
    return [("Benchmark guidance",TEAL,a0,P["capacity"]*(1-a0)),
            ("Biased guidance",PINK,a1,P["capacity"]*(1-a1)),
            ("Adjusted policy",GOLD,.56,P["capacity"]*(1-.56))]


def plot_policy():
    fig,axs=plt.subplots(1,2,figsize=(12.6,5.5))
    fig.subplots_adjust(left=.075,right=.985,top=.85,bottom=.18,wspace=.29)
    rows=[]; summary=[]
    for label,col,a,nu in policies():
        sol=simulate(nu,a); met=metrics(sol)
        summary.append(dict(policy=label,aid=a,nu=nu,budget_used=a+nu/P["capacity"],**met))
        axs[0].plot(sol.t,expit(2*sol.y[0]),color=col,lw=2.5,label=label)
        axs[1].plot(sol.t,sol.y[1],color=col,lw=2.4)
        axs[1].plot(sol.t,sol.y[2],color=col,lw=1.6,ls="--")
        rows.extend([[label,a,nu,t,z,u1,u2,q,expit(2*z)] for t,z,u1,u2,q in zip(sol.t,*sol.y)])
    decorate(axs[0],"Same actual culture; different choices","Time (normalized)","Adoption / coordination share, σ(2z)")
    decorate(axs[1],"Transient burden remains group-specific","Time (normalized)","Transition exposure, u (share)")
    axs[0].legend(loc="center right",frameon=False,fontsize=10)
    axs[1].legend(handles=[Line2D([],[],color=INK,label="Group A · solid"),Line2D([],[],color=INK,ls="--",label="Group B · dashed")],loc="center right",frameon=False,fontsize=9)
    save_csv("policy_trajectories.csv",["policy","aid","nu","time","z","u_A","u_B","q","adoption_share"],rows)
    (DATA/"policy_metrics.json").write_text(json.dumps(summary,indent=2))
    save_fig(fig,"04_policy_trajectories","MODEL A · All three policies spend the same budget · Biased belief affects the choice, not the actual cultural state.")
    return summary


def plot_pareto():
    records=[]
    for a in np.linspace(.1,.8,43):
        for frac in np.linspace(.25,1,19):
            nu=P["capacity"]*(1-a)*frac
            met=metrics(simulate(nu,a,tolerance=3e-8))
            records.append(dict(a=a,nu=nu,**met))
    g=np.array([r["growth"] for r in records]); b=np.array([r["worst_burden"] for r in records])
    idx=[]
    for i in range(len(records)):
        if not np.any((g>=g[i]-1e-12)&(b<=b[i]+1e-12)&((g>g[i]+1e-12)|(b<b[i]-1e-12))): idx.append(i)
    idx=sorted(idx,key=lambda i:b[i])
    fig,ax=plt.subplots(figsize=(8.8,5.7))
    fig.subplots_adjust(left=.12,right=.98,top=.86,bottom=.17)
    ax.scatter(b,g,s=10,c=GREY,alpha=.19,rasterized=False,label="Common feasible policy grid")
    ax.plot(b[idx],g[idx],color=TEAL,lw=2.8,label="Actual grid Pareto envelope")
    for label,col,a,nu in policies():
        actual=metrics(simulate(nu,a)); marker={"Benchmark guidance":"o","Biased guidance":"X","Adjusted policy":"D"}[label]
        ax.scatter(actual["worst_burden"],actual["growth"],color=col,s=95,marker=marker,edgecolor=BG,zorder=5)
        if label=="Biased guidance":
            predicted=metrics(simulate(nu,a,c=.18))
            ax.scatter(predicted["worst_burden"],predicted["growth"],s=100,marker="X",facecolor="none",edgecolor=PINK,lw=1.8,zorder=5)
            ax.annotate("Believed → realized",xy=(actual["worst_burden"],actual["growth"]),
                        xytext=(predicted["worst_burden"],predicted["growth"]),color=PINK,fontsize=9,
                        arrowprops=dict(arrowstyle="->",color=PINK,connectionstyle="arc3,rad=.25"))
    decorate(ax,"D  |  Efficiency and fairness stay separate",
             "Worst-group time-average exposure (share; lower is better)","Mean log-quality growth (per normalized time)")
    handles=[Line2D([],[],color=TEAL,lw=2.5,label="Actual grid Pareto envelope")]
    handles += [Line2D([],[],color=c,marker={"Benchmark guidance":"o","Biased guidance":"X","Adjusted policy":"D"}[l],ls="",label=l) for l,c,_,_ in policies()]
    ax.legend(handles=handles,loc="upper left",frameon=False,fontsize=9)
    save_csv("pareto_grid.csv",list(records[0]),[[r[k] for k in records[0]] for r in records])
    save_fig(fig,"05_efficiency_fairness","MODEL A · Finite-grid envelope, not a certified global optimum · The actual attainable set is common to all advisers.")


def plot_rate():
    tt=np.linspace(-40,40,1801)
    rows=[]
    fig,axs=plt.subplots(1,2,figsize=(12.6,5.5))
    fig.subplots_adjust(left=.075,right=.985,top=.85,bottom=.18,wspace=.29)
    results=[]
    for rate,col,label in [(.10,TEAL,"Slow forcing"),(3.0,PINK,"Fast forcing")]:
        # Normalize over the finite interval so both paths have EXACTLY
        # identical initial and final forcing, rather than just asymptotes.
        shift=lambda t: 1.5*(np.tanh(rate*t)+np.tanh(40*rate))/(2*np.tanh(40*rate))
        sol=solve_ivp(lambda t,y: [-(y[0]-shift(t))**3+(y[0]-shift(t))],(tt[0],tt[-1]),[1],t_eval=tt,rtol=1e-10,atol=1e-11,method="DOP853",max_step=.1)
        if not sol.success: raise RuntimeError("Rate-tipping integration failed")
        ss=shift(tt)
        axs[0].plot(tt,ss,color=col,lw=2.4,label=label)
        axs[1].plot(tt,sol.y[0],color=col,lw=2.6,label=label)
        axs[1].plot(tt,ss+1,color=col,ls=":",lw=1,alpha=.55)
        rows.extend(zip([label]*len(tt),tt,ss,sol.y[0],ss+1,ss-1))
        results.append(float(sol.y[0,-1]))
    axs[1].axhline(2.5,color=GREY,lw=.8,ls=":")
    axs[1].axhline(.5,color=GREY,lw=.8,ls=":")
    axs[1].text(8,2.61,"Final high equilibrium",color=GREY,fontsize=9)
    axs[1].text(8,.62,"Final low equilibrium",color=GREY,fontsize=9)
    decorate(axs[0],"E  |  Same initial and final forcing","Time (normalized)","Moving forcing, ℓ(t) (normalized)")
    decorate(axs[1],"Different rates; different attractors","Time (normalized)","Adjustment state, y (normalized)")
    axs[1].legend(frameon=False,loc="lower left",fontsize=10)
    for ax in axs: ax.set_xlim(-20,30)
    save_csv("rate_tipping.csv",["scenario","time","shift","state_y","instant_high_equilibrium","instant_low_equilibrium"],rows)
    save_fig(fig,"06_rate_tipping","MODEL B · Canonical rate-induced tipping · Stable equilibria persist at every forcing value; no fold is crossed.")
    return results


def plot_cusp():
    y=np.linspace(-1.4,1.4,161)
    aa=np.linspace(-.5,1.7,151)
    A,Y=np.meshgrid(aa,y)
    B=Y**3-A*Y
    eig=A-3*Y**2
    fig=plt.figure(figsize=(9.2,6.2))
    ax=fig.add_subplot(111,projection="3d")
    fig.subplots_adjust(left=.03,right=.98,top=.88,bottom=.12)
    colors=np.empty(A.shape+(4,))
    from matplotlib.colors import to_rgba
    colors[eig<=0]=to_rgba(TEAL,.63)
    colors[eig>0]=to_rgba(PINK,.60)
    ax.plot_surface(A,B,Y,facecolors=colors,rstride=3,cstride=3,linewidth=0,shade=False,antialiased=True)
    af=np.linspace(0,1.7,170)
    for sign in [-1,1]:
        yf=sign*np.sqrt(af/3)
        bf=yf**3-af*yf
        ax.plot(af,bf,yf,color=GOLD,lw=2.5)
    ax.scatter([0],[0],[0],s=60,color=INK,depthshade=False)
    ax.view_init(elev=24,azim=-57)
    ax.set_title("F  |  The geometry of a cusp singularity",loc="left",pad=12)
    ax.set_xlabel("Feedback, α",labelpad=9)
    ax.set_ylabel("Tilt, β",labelpad=9)
    ax.set_zlabel("Equilibrium, y*",labelpad=7)
    ax.tick_params(labelsize=9)
    ax.legend(handles=[Line2D([],[],color=TEAL,lw=5,label="Stable sheet"),Line2D([],[],color=PINK,lw=5,label="Unstable sheet"),
                       Line2D([],[],color=GOLD,lw=2,label="Fold curves")],loc="upper right",frameon=False,fontsize=9)
    save_csv("cusp_surface.csv",["alpha","beta","equilibrium_y","eigenvalue"],zip(A.ravel(),B.ravel(),Y.ravel(),eig.ravel()))
    save_fig(fig,"07_cusp_surface","MODEL C · Mathematical normal form dy/dt = αy − y³ + β · A design example, not an identified economic singularity.")


def contact_sheet():
    filenames=["01_boundary","02_bifurcation","03_phase_basins","05_efficiency_fairness","06_rate_tipping","07_cusp_surface"]
    width,height=3000,2060
    sheet=Image.new("RGB",(width,height),BG)
    draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",38)
    small=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",24)
    draw.text((40,21),"EthosGPT | Transition boundaries, policy, efficiency & fairness",fill=INK,font=font)
    draw.text((40,72),"Computed mechanism samples · Dimensionless, uncalibrated parameters · Not empirical findings",fill=GREY,font=small)
    for k,name in enumerate(filenames):
        im=Image.open(FIG/(name+".png")).convert("RGB")
        # Retain each image's aspect ratio; do not crop captions or axes.
        im.thumbnail((1470,625),Image.Resampling.LANCZOS)
        col,row=k%2,k//2
        sheet.paste(im,(col*1500+(1500-im.width)//2,130+row*640+(625-im.height)//2))
    sheet.save(FIG/"00_sample_atlas.png")


def validate():
    out={"scope":"Numerical checks on uncalibrated sample models; no empirical validation."}
    fold_res=[]; critical_eig=[]
    for a in [.0,.15,.3,.5,.65]:
        for c in [0,.18]:
            z,nu=fold(a,c)
            fold_res.append(max(abs(equilibrium_f(z,nu,a,c)),abs(equilibrium_dz(z,nu,a))))
            critical_eig.append(np.min(np.abs(np.linalg.eigvals(jacobian(z,nu,a)))))
    out["max_fold_residual"]=max(fold_res)
    out["max_fold_near_zero_eigenvalue"]=max(critical_eig)
    root_res=[]
    for nu in [.6,.9,1.1,1.3,1.5]:
        for z in equilibria(nu,.3): root_res.append(abs(equilibrium_f(z,nu,.3)))
    out["max_equilibrium_residual"]=max(root_res)
    diffs=[]; low=1.; high=0.; budgets=[]
    for _,_,a,nu in policies():
        s=simulate(nu,a); strict=simulate(nu,a,tolerance=1e-11)
        diffs.append(np.max(np.abs(s.y-strict.y)))
        low=min(low,float(s.y[1:3].min())); high=max(high,float(s.y[1:3].max()))
        budgets.append(a+nu/P["capacity"])
    out["max_ode_tolerance_difference"]=max(diffs)
    out["exposure_share_min"]=low; out["exposure_share_max"]=high
    out["policy_budget_used"]=budgets
    Q=np.array([[-.08,.04,.04],[.03,-.07,.04],[.02,.05,-.07]])
    cs=solve_ivp(lambda t,p:culture_rhs(p,Q,np.array([.1,.3,-.2])),[0,80],[.25,.45,.30],t_eval=np.linspace(0,80,300),rtol=1e-10,atol=1e-12)
    out["simplex_mass_error"]=float(np.max(np.abs(cs.y.sum(axis=0)-1)))
    out["simplex_probability_min"]=float(cs.y.min())
    assert out["max_fold_residual"]<1e-8
    assert out["max_fold_near_zero_eigenvalue"]<1e-7
    assert out["max_equilibrium_residual"]<1e-9
    assert max(diffs)<1e-5 and low>=-1e-9 and high<=1+1e-9
    assert max(budgets)<=1+1e-10
    assert out["simplex_mass_error"]<1e-8 and cs.y.min()>=-1e-10
    out["status"]="passed"
    (ROOT/"NUMERICAL_CHECKS.json").write_text(json.dumps(out,indent=2))
    return out


if __name__=="__main__":
    validation=validate()
    plot_boundary(); plot_bifurcation(); plot_phase()
    summary=plot_policy(); plot_pareto(); rates=plot_rate(); plot_cusp(); contact_sheet()
    assert abs(rates[0]-2.5)<.01 and abs(rates[1]-.5)<.01
    validation["rate_tipping_final_states"]=rates
    (ROOT/"NUMERICAL_CHECKS.json").write_text(json.dumps(validation,indent=2))
    (ROOT/"RUN_ENVIRONMENT.json").write_text(json.dumps(dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,matplotlib=matplotlib.__version__),indent=2))
    print(json.dumps({"validation":validation,"policy_metrics":summary,"figure_count":7},indent=2))
