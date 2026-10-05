"""Aghion--Howitt Cobb--Douglas equilibrium with a declared transition extension.

The original core uses risk-neutral households, Poisson research, monopoly
intermediates and free entry. Capacity, assistance and fluid transition needs
are extensions. Section 6 is recovered by holding its decision rule fixed.
No cubic coordination state is present.
"""
from dataclasses import dataclass, replace
import numpy as np
from scipy.optimize import brentq
from scipy.integrate import solve_bvp, solve_ivp


@dataclass(frozen=True)
class Parameters:
    theta: float = .97
    q: float = .04
    chi: float = 12.
    rho: float = .10
    capacity: float = .07
    aid_labor: float = .04
    lost_capacity: float = .18
    entry: tuple = (.75,.38)
    recovery: tuple = (.12,.32)
    aid_recovery: tuple = (1.2,1.)
    horizon: float = 20.
    omega: float = .30
    initial: tuple = (.08,.08)

    @property
    def gamma(self): return 1+self.q

P = Parameters()  # Legacy smoke-test scenario; not a country calibration.


@dataclass(frozen=True)
class RuleParameters:
    """General Section 6 rule. Every number is supplied by a dated scenario."""
    innovation_intercept: float
    innovation_loading: float
    aid_intercept: float
    aid_loading: float
    cooperation_intercept: float
    cooperation_loading: float
    arrival_base: float
    arrival_innovation: float
    arrival_cooperation: float
    quality_jump: float
    rounds: float
    round_duration: float

    def validate(self):
        for intercept,loading in [(self.innovation_intercept,self.innovation_loading),
                                  (self.aid_intercept,self.aid_loading),
                                  (self.cooperation_intercept,self.cooperation_loading)]:
            if not (0<=intercept-abs(loading)<=intercept+abs(loading)<=1):
                raise ValueError('Support or aid rule can leave [0,1]')
        low=self.arrival_base;high=self.arrival_base
        for coefficient,intercept,loading in [(self.arrival_innovation,self.innovation_intercept,self.innovation_loading),
                                               (self.arrival_cooperation,self.cooperation_intercept,self.cooperation_loading)]:
            endpoints=coefficient*np.array([intercept-abs(loading),intercept+abs(loading)])
            low+=endpoints.min();high+=endpoints.max()
        if not 0<=low<=high<=1:raise ValueError('Discrete innovation probability can leave [0,1]')
        if self.quality_jump<=0 or self.rounds<=0 or self.round_duration<=0:
            raise ValueError('Quality jump, horizon and round duration must be positive')


LEGACY_RULE=RuleParameters(.5,.30,.5,.30,.5,.30,.05,.20,.10,.04,20.,1.)


def section6(profile,rule=LEGACY_RULE):
    """Input order Q48,Q57,Q106,Q108,Q121,Q159.

    The default explicitly names the retained historical scenario. U is a
    weighted replacement-pressure index, not an observed count of people or
    unassisted events. A Poisson process matches its expected-log first moment,
    not the entire discrete Bernoulli process or its mean-quality level.
    """
    rule.validate()
    x=np.asarray(profile,float)
    if x.shape[-1]!=6 or not np.isfinite(x).all() or np.any((x<0)|(x>1)):
        raise ValueError('Six finite directed scores in [0,1] are required')
    i=rule.innovation_intercept+rule.innovation_loading*(x[...,0]+x[...,5]-1)
    a=rule.aid_intercept+rule.aid_loading*(x[...,2]-x[...,3])
    s=rule.cooperation_intercept+rule.cooperation_loading*(x[...,1]+x[...,4]-1)
    probability=rule.arrival_base+rule.arrival_innovation*i+rule.arrival_cooperation*s
    rate=probability/rule.round_duration
    pressure=100*probability*(1-a)
    gain=rule.rounds*probability*np.log1p(rule.quality_jump)
    return {'innovation_support':i,'assistance':a,'cooperation':s,
            'arrival':probability,'G20':gain,'Uflow':pressure,
            'arrival_probability':probability,'poisson_intensity':rate,
            'G_T':gain,'weighted_pressure_per_round':pressure,
            'weighted_pressure_rate':pressure/rule.round_duration,
            'horizon_time':rule.rounds*rule.round_duration}


def active_labor(u,a,p=P):
    return 1-p.aid_labor*np.asarray(a)-p.lost_capacity*np.mean(u,axis=0)


def production(u,n,a,p=P):
    m=active_labor(u,a,p)-n
    if np.any(m<=0): raise ValueError('Nonpositive manufacturing labor')
    y=m**p.theta
    w=p.theta**2*m**(p.theta-1)
    price=p.theta*m**(p.theta-1)
    profit=p.theta*(1-p.theta)*y
    return m,y,w,price,profit


def burden_flow(u,n,a,p=P):
    u=np.asarray(u)
    shape=(2,)+(1,)*(u.ndim-1)
    entry=np.asarray(p.entry).reshape(shape)*p.chi*n*(1-a)
    r=np.asarray(p.recovery).reshape(shape)+np.asarray(p.aid_recovery).reshape(shape)*a
    return entry*(1-u)-r*u


def steady_burden(n,a,p=P):
    e=np.asarray(p.entry)*p.chi*n*(1-a)
    r=np.asarray(p.recovery)+np.asarray(p.aid_recovery)*a
    return e/(e+r)


def burden_step(u,n,a,dt,p=P):
    u=np.asarray(u)
    shape=(2,)+(1,)*(u.ndim-1)
    e=np.asarray(p.entry).reshape(shape)*p.chi*n*(1-a)
    r=np.asarray(p.recovery).reshape(shape)+np.asarray(p.aid_recovery).reshape(shape)*a
    k=e+r
    return e/k+(u-e/k)*np.exp(-k*dt)


def core_equilibrium(p=P, labor=1.):
    """Exact original unconstrained baseline, without transition/assistance."""
    k=p.gamma*(1-p.theta)/p.theta
    n=max(0.,(p.chi*k*labor-p.rho)/(p.chi*(1+k)))
    m=labor-n
    pi=p.theta*(1-p.theta)*m**p.theta
    w=p.theta**2*m**(p.theta-1)
    v=pi/(p.rho+p.chi*n)
    return dict(n=n,m=m,arrival=p.chi*n,wage=w,profit=pi,patent=v,
                g_log=p.chi*n*np.log(p.gamma),g_mean=p.q*p.chi*n,
                entry_gap=p.chi*p.gamma*v-w)


def core_social_optimum(p=P,labor=1.):
    """Original linear-utility planner; finite-value condition is mandatory."""
    eta=p.chi*p.q
    if p.rho<=eta*labor: raise ValueError('Unconstrained original planner has unbounded value')
    n=np.clip((eta*labor-p.theta*p.rho)/(eta*(1-p.theta)),0,labor)
    value=(labor-n)**p.theta/(p.rho-eta*n)
    return dict(n=float(n),value=float(value))


def market_steady(a=.5,tax_subsidy=0.,p=P):
    cap=p.capacity-p.aid_labor*a
    if cap<0 or not 0<=a<=1 or tax_subsidy>=1: raise ValueError('Invalid policy')
    def gap(n):
        u=steady_burden(n,a,p)
        _,_,w,_,pi=production(u,n,a,p)
        v=pi/(p.rho+p.chi*n)
        return p.chi*p.gamma*v-(1-tax_subsidy)*w
    if gap(0)<=0: n=0.;regime='no research'
    elif gap(cap)>=0: n=cap;regime='capacity constrained'
    else: n=brentq(gap,0,cap,xtol=1e-14);regime='interior free entry'
    u=steady_burden(n,a,p);m,y,w,price,pi=production(u,n,a,p)
    v=pi/(p.rho+p.chi*n)
    return dict(n=n,a=a,u_A=u[0],u_B=u[1],m=m,output=y,wage=w,
                price=price,profit=pi,patent=v,arrival=p.chi*n,
                g_log=p.chi*n*np.log(p.gamma),g_mean=p.q*p.chi*n,
                free_entry_gap=gap(n),regime=regime)


def market_allocation(u,v,a=.5,tax_subsidy=0.,p=P):
    """Monopoly labor demand + research free-entry complementarity."""
    M=active_labor(u,a,p);cap=p.capacity-p.aid_labor*a
    ratio=np.maximum(p.chi*p.gamma*v/((1-tax_subsidy)*p.theta**2),1e-250)
    logm=np.log(ratio)/(p.theta-1)
    m=np.exp(np.clip(logm,-50,50))
    m=np.minimum(M,np.maximum(M-cap,m))
    n=M-m
    return n,m


def market_rhs(t,y,a=.5,tax_subsidy=0.,p=P):
    u=y[:2];v=y[2]
    n,m=market_allocation(u,v,a,tax_subsidy,p)
    pi=p.theta*(1-p.theta)*m**p.theta
    return np.vstack((burden_flow(u,n,a,p),(p.rho+p.chi*n)*v-pi))


def jacobian_market(a=.5,tax_subsidy=0.,p=P):
    e=market_steady(a,tax_subsidy,p);y=np.array([e['u_A'],e['u_B'],e['patent']])
    eps=1e-6
    J=np.column_stack([(market_rhs(0,(y+eps*np.eye(3)[j])[:,None],a,tax_subsidy,p)-
                        market_rhs(0,(y-eps*np.eye(3)[j])[:,None],a,tax_subsidy,p)).ravel()/(2*eps)
                       for j in range(3)])
    return J


def market_path(a=.5,tax_subsidy=0.,p=P,initial=None,end=60.,tol=1e-8):
    e=market_steady(a,tax_subsidy,p)
    initial=np.array(p.initial if initial is None else initial)
    us=np.array([e['u_A'],e['u_B']]);vs=e['patent']
    tt=np.linspace(0,end,181)
    guess=np.vstack((us[:,None]+(initial-us)[:,None]*np.exp(-tt[None,:]),np.full_like(tt,vs)))
    def bc(ya,yb):return np.r_[ya[:2]-initial,yb[2]-vs]
    sol=solve_bvp(lambda t,y:market_rhs(t,y,a,tax_subsidy,p),bc,tt,guess,
                  tol=tol,max_nodes=12000)
    if not sol.success:raise RuntimeError(sol.message)
    return sol,e


def welfare_rate(u,n,a,p=P):
    return production(u,n,a,p)[1]-p.omega*np.max(u,axis=0)


def controlled_path(policy,p=P,initial=None,end=None):
    end=p.horizon if end is None else end
    initial=p.initial if initial is None else initial
    def rhs(t,y):
        u=y[:2];n,a=policy(u)
        if min(n,a)<-1e-10 or a>1+1e-10 or n+p.aid_labor*a>p.capacity+1e-10:
            raise ValueError('Policy violates the trained-labor budget')
        lam=p.chi*n;du=burden_flow(u,n,a,p)
        _,Y,_,_,_=production(u,n,a,p)
        return np.r_[du,np.log(p.gamma)*lam,p.q*lam*y[3],u,
                     np.exp(-p.rho*t)*y[3]*welfare_rate(u,n,a,p),y[3]*Y]
    sol=solve_ivp(rhs,[0,end],np.r_[initial,0.,1.,0.,0.,0.,0.],
                  t_eval=np.linspace(0,end,401),method='DOP853',rtol=2e-9,atol=2e-11,max_step=.10)
    if not sol.success:raise RuntimeError(sol.message)
    return sol


def path_metrics(sol):
    t=sol.t[-1];ug=sol.y[4:6,-1]/t
    return dict(G=sol.y[2,-1],g_log=sol.y[2,-1]/t,
                mean_quality=sol.y[3,-1],Ubar=float(ug.mean()),Umax=float(ug.max()),
                final_u_A=sol.y[0,-1],final_u_B=sol.y[1,-1],
                welfare_to_T=sol.y[6,-1],average_output=sol.y[7,-1]/t)
