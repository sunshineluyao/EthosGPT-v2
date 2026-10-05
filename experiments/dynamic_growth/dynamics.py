"""Dimensionless quality-replacement and adjustment model.

The reduced coordination equation is a specified mechanism, not a fitted
economy. b=1 is the supplied fold example; b=-1 is a unique-equilibrium
control. q is mean log quality, never log of expected aggregate technology.
"""
from dataclasses import dataclass
from pathlib import Path
import json
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq, root
from scipy.special import expit


@dataclass(frozen=True)
class Parameters:
    b: float = 1.0
    intercept: float = .70
    aid_coordination: float = .45
    launch_pressure: float = .90
    burden_feedback: float = .35
    quality_multiplier: float = 1.12
    capacity: float = 2.40
    horizon: float = 60.
    margin: float = .94


CONFIG = json.loads((Path(__file__).resolve().parent/'parameters.json').read_text())
P = Parameters(b=CONFIG['coordination_feedback'],intercept=CONFIG['baseline_coordination_tilt'],aid_coordination=CONFIG['aid_coordination_coefficient'],launch_pressure=CONFIG['launch_pressure_coefficient'],burden_feedback=CONFIG['exposure_feedback_coefficient'],quality_multiplier=CONFIG['quality_multiplier'],capacity=CONFIG['innovation_capacity'],horizon=CONFIG['horizon'],margin=CONFIG['adviser_fold_margin'])
D = np.array(CONFIG['exposure_entry'])
R0 = np.array(CONFIG['baseline_recovery'])
R1 = np.array(CONFIG['aid_recovery'])


def steady_exposure(z, nu, aid):
    lam = nu * expit(2*z)
    recovery = R0 + R1*aid
    return D*lam/(D*lam+recovery)


def equilibrium(z, nu, aid, culture=0., p=P):
    return p.b*z-z**3+p.intercept+culture+p.aid_coordination*aid-p.launch_pressure*nu-p.burden_feedback*steady_exposure(z,nu,aid).mean()


def gradient(z, nu, aid, p=P):
    x = expit(2*z)
    recovery = R0+R1*aid
    denom = (D*nu*x+recovery)**2
    uz = D*(2*nu*x*(1-x))*recovery/denom
    un = D*x*recovery/denom
    return np.array([p.b-3*z*z-p.burden_feedback*uz.mean(), -p.launch_pressure-p.burden_feedback*un.mean()])


def jacobian(z, nu, aid, p=P):
    x = expit(2*z)
    u = steady_exposure(z,nu,aid)
    j = np.zeros((3,3))
    j[0,0] = p.b-3*z*z
    j[0,1:] = -p.burden_feedback/2
    j[1:,0] = D*nu*2*x*(1-x)*(1-u)
    j[1:,1:] = np.diag(-(D*nu*x+R0+R1*aid))
    return j


def fold(aid, culture=0., p=P):
    if p.b <= 0:
        raise ValueError('The no-fold control has a strictly decreasing equilibrium equation.')
    f = lambda v: [equilibrium(v[0],v[1],aid,culture,p),gradient(v[0],v[1],aid,p)[0]]
    sol = root(f,[.56,1.2+culture],tol=1e-11)
    if np.max(np.abs(f(sol.x)))>1e-9 or sol.x[1]<=0:
        raise RuntimeError(f'Fold did not converge: aid={aid}, culture={culture}')
    return sol.x


def policy_from_estimate(estimated_culture=0., p=P):
    """Reserve 6% below the estimated fold and exhaust one resource budget."""
    f = lambda aid: p.capacity*(1-aid)-p.margin*fold(aid,estimated_culture,p)[1]
    aid = brentq(f,0.,1.,xtol=2e-12)
    return float(aid),float(p.capacity*(1-aid))


def economic_derivative(z, exposure, nu, aid, culture=0., p=P):
    x = expit(2*z)
    arrival = nu*x
    dz = p.b*z-z**3+p.intercept+culture+p.aid_coordination*aid-p.launch_pressure*nu-p.burden_feedback*np.mean(exposure)
    du = D*arrival*(1-exposure)-(R0+R1*aid)*exposure
    return dz,du,np.log(p.quality_multiplier)*arrival


def simulate(aid, nu, culture=0., p=P, tolerance=1e-9, initial=None, points=601):
    """Accumulate exposure integrals as states; check actual budget at every call."""
    initial = CONFIG['initial_state'] if initial is None else initial
    def rhs(t,y):
        a = aid(t) if callable(aid) else aid
        n = nu(t) if callable(nu) else nu
        c = culture(t) if callable(culture) else culture
        if min(a,n)<-1e-10 or a+n/p.capacity>1+1e-10:
            raise ValueError('Policy exceeds the shared resource budget')
        z,u1,u2,q,_,_ = y
        dz,du,dq = economic_derivative(z,np.array([u1,u2]),n,a,c,p)
        return np.r_[dz,du,dq,[u1,u2]]
    sol = solve_ivp(rhs,[0,p.horizon],initial,method='DOP853',t_eval=np.linspace(0,p.horizon,points),rtol=tolerance,atol=tolerance*.1,max_step=.8)
    if not sol.success: raise RuntimeError(sol.message)
    if sol.y[1:3].min() < -1e-8 or sol.y[1:3].max()>1+1e-8: raise ValueError('Exposure outside share bounds')
    return sol


def metrics(sol):
    ug = sol.y[4:6,-1]/sol.t[-1]
    return {'growth':float((sol.y[3,-1]-sol.y[3,0])/sol.t[-1]),'mean_burden':float(ug.mean()),'worst_burden':float(ug.max()),'burden_gap':float(np.ptp(ug)),'peak_worst':float(sol.y[1:3].max()),'adoption_final':float(expit(2*sol.y[0,-1])),'group_A_burden':float(ug[0]),'group_B_burden':float(ug[1])}


def equilibria(nu,aid,culture=0.,p=P):
    zs = np.linspace(-3,3,801)
    f = np.array([equilibrium(z,nu,aid,culture,p) for z in zs])
    roots = [brentq(lambda z:equilibrium(z,nu,aid,culture,p),zs[k],zs[k+1],xtol=1e-13) for k in range(len(zs)-1) if f[k]*f[k+1]<0]
    return roots


def continue_branch(aid=.3,culture=0.,p=P,step=.014,max_steps=700):
    """Pseudo-arclength predictor/corrector, retaining unstable branches."""
    z0 = 1.1
    nu0 = brentq(lambda nu:equilibrium(z0,nu,aid,culture,p),0,2.4)
    x = np.array([z0,nu0])
    g = gradient(*x,aid,p)
    tangent = np.array([g[1],-g[0]])
    tangent /= np.linalg.norm(tangent)
    if tangent[0]>0: tangent=-tangent
    rows=[]
    for k in range(max_steps):
        z,nu = x
        eig = np.linalg.eigvals(jacobian(z,nu,aid,p))
        rows.append({'step':k,'aid':aid,'culture':culture,'z':z,'nu':nu,'stable':bool(np.max(eig.real)<0),'largest_eigenvalue_real':float(np.max(eig.real)),'residual':abs(equilibrium(z,nu,aid,culture,p))})
        predicted=x+step*tangent
        f = lambda v:[equilibrium(v[0],v[1],aid,culture,p),np.dot(v-predicted,tangent)]
        sol = root(f,predicted,tol=1e-11)
        if np.max(np.abs(f(sol.x)))>1e-9: raise RuntimeError('Arclength correction failed')
        x=sol.x
        if x[1]<0 or x[1]>2.4 or x[0]<-1.7: break
        g=gradient(*x,aid,p)
        t=np.array([g[1],-g[0]]);t/=np.linalg.norm(t)
        if np.dot(t,tangent)<0:t=-t
        tangent=t
    return rows
