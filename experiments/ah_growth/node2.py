"""Node 2 review computations. No changes to the approved manuscript.

All country results are conditional scenarios, not estimates/forecasts.
The one-moment resource match is kept distinct from independent validation.
Run: python figure_sources/ah_growth/node2.py
"""
from pathlib import Path
from dataclasses import replace, asdict
import gc, json, time, hashlib, platform
import numpy as np
import pandas as pd
import scipy
from scipy.integrate import solve_ivp
from scipy.interpolate import RegularGridInterpolator
from scipy.optimize import root, minimize_scalar
from model import (Parameters, LEGACY_RULE, section6, core_equilibrium,
                   core_social_optimum, market_steady, market_path,
                   market_allocation, jacobian_market, steady_burden,
                   burden_flow, production, controlled_path, path_metrics)
from control import BellmanSolver

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'node2_results'
COUNTRY_R={'China':.0258,'Germany':.031,'Kenya':.008}
INITIALS=[(0.,0.),(.08,.08),(.30,.05),(.05,.30),(.45,.35),(.80,.80)]
RULE=replace(LEGACY_RULE,quality_jump=.08,rounds=20.,round_duration=5.)

def js(obj):
    if isinstance(obj,np.ndarray):return obj.tolist()
    if isinstance(obj,np.generic):return obj.item()
    if isinstance(obj,complex):return {'real':obj.real,'imaginary':obj.imag}
    raise TypeError(type(obj).__name__)

def write_json(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,default=js)+'\n')

def progress(stage,**kw):
    print(json.dumps(dict(stage=stage,**kw),default=js),flush=True)

def conditional_parameters(country,q=.08,theta=.95,xi=.75,rho=.1,headroom=2.,R=None):
    R=COUNTRY_R[country] if R is None else R
    nref=xi*R/(theta**2+xi*R)
    k=(1+q)*(1-theta)/theta
    denominator=k-(1+k)*nref
    if denominator<=0:raise ValueError('No positive research productivity can match this resource moment')
    if (1+q)*theta<=1:raise ValueError('Drastic-innovation restriction gamma*theta>1 fails')
    chi=rho/denominator
    p=Parameters(theta=theta,q=q,chi=chi,rho=rho,capacity=.04+headroom*nref,
                 horizon=100.)
    if rho<=q*chi*p.capacity:raise ValueError('Bounded-planner sufficient condition fails')
    return p,dict(country=country,RD_GDP=R,xi_assumed=xi,n_ref=nref,
                  chi_conditionally_matched=chi,headroom_multiplier_assumed=headroom,
                  source_status='dated revised observation' if country=='China' else
                    ('dated rounded observation' if country=='Germany' else 'undated approximate official benchmark'),
                  reference_period='2023' if country!='Kenya' else 'unspecified',
                  status='conditional resource match under assumed q, theta, xi, rho; not an independent estimate')

class SavedPolicy:
    def __init__(self,p,grid,value,n,a):
        self.p=p;self.grid=grid;self.value=value;self.n_grid=n;self.a_grid=a
        self.iv=RegularGridInterpolator((grid,grid),value)
        self.inn=RegularGridInterpolator((grid,grid),n)
        self.ia=RegularGridInterpolator((grid,grid),a)
    def controls(self,u):
        u=np.clip(np.asarray(u),0,1)
        return float(self.inn([u])[0]),float(self.ia([u])[0])
    def value_at(self,u):return float(self.iv([np.clip(u,0,1)])[0])

def save_solver(s,path):
    np.savez_compressed(path,grid=s.grid,value=s.value,n=s.n_grid,a=s.a_grid)
    return SavedPolicy(s.p,s.grid.copy(),s.value.copy(),s.n_grid.copy(),s.a_grid.copy())

def adj_subsidy(n,a,p):
    u=steady_burden(n,a,p)
    _,_,w,_,pi=production(u,n,a,p)
    v=pi/(p.rho+p.chi*n)
    return 1-p.chi*p.gamma*v/w

def market_metrics(sol,a,tau,p):
    def policy(u,t):
        v=sol.sol(t)[2]
        return float(market_allocation(u,v,a,tau,p)[0]),a
    def rhs(t,y):
        u=sol.sol(t)[:2];n,a0=policy(u,t);lam=p.chi*n
        Y=production(u,n,a0,p)[1]
        return np.r_[np.log(p.gamma)*lam,p.q*lam*y[1],u,
                     np.exp(-p.rho*t)*y[1]*(Y-p.omega*np.max(u)),y[1]*Y]
    end=p.horizon
    z=solve_ivp(rhs,[0,end],[0.,1.,0.,0.,0.,0.],t_eval=np.linspace(0,end,401),
                method='DOP853',rtol=2e-9,atol=2e-11,max_step=.25)
    if not z.success:raise RuntimeError(z.message)
    ug=z.y[2:4,-1]/end
    metrics=dict(G=z.y[0,-1],g_log=z.y[0,-1]/end,mean_quality=z.y[1,-1],
                 Ubar=float(ug.mean()),Umax=float(ug.max()),
                 final_u_A=sol.sol(end)[0],final_u_B=sol.sol(end)[1],
                 welfare_to_T=z.y[4,-1],average_output=z.y[5,-1]/end)
    rows=[]
    for j,t in enumerate(z.t):
        u=sol.sol(t)[:2];n,a0=policy(u,t)
        rows.append(dict(t=t,u_A=u[0],u_B=u[1],n=n,a=a0,log_quality=z.y[0,j],
                         mean_quality=z.y[1,j],expected_output=z.y[1,j]*production(u,n,a0,p)[1]))
    return metrics,rows

def controlled_rows(sol,policy,p):
    rows=[]
    for j,t in enumerate(sol.t):
        u=sol.y[:2,j];n,a=policy(u)
        rows.append(dict(t=t,u_A=u[0],u_B=u[1],n=n,a=a,log_quality=sol.y[2,j],
                         mean_quality=sol.y[3,j],expected_output=sol.y[3,j]*production(u,n,a,p)[1]))
    return rows

def analytic_checks():
    p=Parameters(theta=.6,q=.8,chi=.09,rho=.1)
    ce=core_equilibrium(p);sp=core_social_optimum(p)
    objective=lambda n:-(1-n)**p.theta/(p.rho-p.q*p.chi*n)
    opt=minimize_scalar(objective,bounds=(0,1),method='bounded',options={'xatol':1e-13})
    assert abs(opt.x-sp['n'])<1e-7
    assert abs(ce['entry_gap'])<1e-12
    unbounded=False
    try:core_social_optimum(Parameters())
    except ValueError:unbounded=True
    assert unbounded
    return dict(finite_core_scenario=asdict(p),core_market=ce,core_planner=sp,
                independent_scalar_optimum=opt.x,planner_control_error=abs(opt.x-sp['n']),
                legacy_unconstrained_planner_correctly_rejected=unbounded)

def stationary_feedback(policy,p):
    def f(u):return burden_flow(u,*policy.controls(u),p)
    roots=[]
    for seed in INITIALS+[(x,y) for x in [.025,.1,.25,.5,.9] for y in [.025,.1,.25,.5,.9]]:
        r=root(f,seed,tol=1e-10)
        if r.success and np.min(r.x)>=0 and np.max(r.x)<=1 and np.linalg.norm(f(r.x))<1e-8:
            if not any(np.linalg.norm(r.x-z)<1e-5 for z in roots):roots.append(r.x)
    out=[]
    for u in roots:
        n,a=policy.controls(u);eps=1e-5
        J=np.column_stack([(f(u+eps*np.eye(2)[i])-f(u-eps*np.eye(2)[i]))/(2*eps) for i in range(2)])
        eig=np.linalg.eigvals(J)
        eps2=eps/2
        J2=np.column_stack([(f(u+eps2*np.eye(2)[i])-f(u-eps2*np.eye(2)[i]))/(2*eps2) for i in range(2)])
        out.append(dict(u_A=u[0],u_B=u[1],n=n,a=a,flow_residual=np.linalg.norm(f(u)),
                        eigenvalues=eig,jacobian_step_change=np.max(np.abs(J-J2)),
                        locally_stable=bool(np.max(eig.real)<0),
                        g_log=p.chi*n*np.log(p.gamma),g_mean=p.q*p.chi*n))
    return out

def main():
    started=time.time();OUT.mkdir(exist_ok=True)
    checks={'analytic_core':analytic_checks(),'scope':'Node 2 conditional numerical review; approved manuscript untouched'}
    parameters=[];fits={};policies={};refinements=[];implementation=[]
    profiles=pd.read_csv(Path(__file__).resolve().parent/'design_results/three-country-directed-profiles.csv')
    checks['candidate_source_sha256']={f:hashlib.sha256((Path(__file__).resolve().parent/f).read_bytes()).hexdigest()
                                       for f in ['model.py','control.py','node2.py','country_design.py']}
    # Reject inadmissible joint scenarios explicitly instead of forcing a fit.
    regimes=[]
    for country in COUNTRY_R:
        p,fit=conditional_parameters(country);fits[country]=fit
        parameters.append(dict(**fit,**{k:v for k,v in asdict(p).items() if k!='initial'}))
        for q,theta in [(.02,.985),(.04,.97),(.08,.95),(.16,.90)]:
            try:
                pp,ff=conditional_parameters(country,q,theta)
                regimes.append(dict(country=country,q=q,theta=theta,status='admissible conditional scenario',
                                    chi=pp.chi,capacity=pp.capacity,n_ref=ff['n_ref'],
                                    contraction_margin=pp.rho-pp.q*pp.chi*pp.capacity))
            except ValueError as e:regimes.append(dict(country=country,q=q,theta=theta,status='rejected',reason=str(e)))
    pd.DataFrame(parameters).to_csv(OUT/'reference-parameter-ledger.csv',index=False)
    pd.DataFrame(regimes).to_csv(OUT/'joint-innovation-regimes.csv',index=False)
    progress('resource scenarios',admissible=sum(x['status']!='rejected' for x in regimes),rejected=sum(x['status']=='rejected' for x in regimes))
    configs=[(31,21,1.),(41,31,.5),(61,41,.5),(61,41,.25),(81,41,.25),(81,61,.25),
             (101,41,.25),(101,61,.125)]
    pricing_report={}
    for country in COUNTRY_R:
        p,_=conditional_parameters(country)
        useconfigs=configs if country=='China' else [configs[1],configs[3],*configs[-3:]]
        prev=None
        for size,c,dt in useconfigs:
            s=BellmanSolver(p,size=size,aid_points=c,research_points=c,dt=dt).solve()
            n,a=s.controls(p.initial)
            rec=dict(country=country,aid_points=c,research_points=c,**s.report,n_initial=n,a_initial=a)
            if prev is not None:rec['relative_value_change_from_previous']=abs(rec['value_initial']/prev-1)
            prev=rec['value_initial'];refinements.append(rec)
            progress('Bellman refinement',**rec)
            pol=save_solver(s,OUT/f'policy-{country}-{size}-{c}-{dt:g}.npz')
            if (size,c,dt)==configs[-1]:
                policies[country]=pol
                patent=s.patent_values()
                np.savez_compressed(OUT/f'patent-{country}.npz',grid=s.grid,patent=patent)
                # Independently verify the discretized asset-pricing identity.
                from scipy.sparse import coo_matrix,eye
                pp=s.policy;ss=np.arange(s.S);disc=np.exp(-(p.rho+p.chi*s.n)*s.dt)
                nodes,weights=np.polynomial.legendre.leggauss(3)
                reward=np.zeros(s.S)
                from model import burden_step
                for t,w in zip((nodes+1)*s.dt/2,weights*s.dt/2):
                    u=burden_step(s.uv,s.n[pp],s.a[pp],t,p)
                    reward+=np.exp(-(p.rho+p.chi*s.n[pp])*t)*w*production(u,s.n[pp],s.a[pp],p)[4]
                continuation=np.sum(s.weights[pp,ss]*patent.ravel()[s.indices[pp,ss]],axis=1)*disc[pp]
                residual=float(np.max(np.abs(patent.ravel()-reward-continuation)))
                pricing_report[country]={'discrete_asset_pricing_residual':residual,
                    'interpretation':'Patent value along planner controls; a state-dependent subsidy is a new implementing institution, not original Aghion--Howitt policy'}
                ip=RegularGridInterpolator((s.grid,s.grid),patent)
                for u in [p.initial,(.3,.05),(.05,.3),(.8,.8)]:
                    n,a=pol.controls(u);v=float(ip([u])[0]);_,_,w,_,_=production(u,n,a,p)
                    tau=1-p.chi*p.gamma*v/w
                    implementation.append(dict(country=country,u_A=u[0],u_B=u[1],n=n,a=a,
                        patent=v,implementing_subsidy=tau,net_policy_wage_finance_per_quality=w*(tau*n+p.aid_labor*a),
                        status='interior free-entry implementation if lump-sum finance and patent pricing are adopted; corner shadow rents require complementarity'))
            del s;gc.collect()
    pd.DataFrame(refinements).to_csv(OUT/'solver-refinement.csv',index=False)
    pd.DataFrame(implementation).to_csv(OUT/'planner-market-implementation.csv',index=False)
    checks['planner_asset_pricing']=pricing_report
    allrows=[];comparisons=[];eqrows=[];marketchecks=[];initialrows=[]
    checks['feedback_fixed_points']={};checks['continuous_policy_validation']={}
    for country in COUNTRY_R:
        p,fit=conditional_parameters(country);pol=policies[country]
        fpoints=stationary_feedback(pol,p);checks['feedback_fixed_points'][country]=fpoints
        for e in fpoints:eqrows.append(dict(country=country,policy='planner feedback',source='physical-economy benchmark',**{k:v for k,v in e.items() if k!='eigenvalues'},eigenvalues=json.dumps(e['eigenvalues'],default=js)))
        for initial in INITIALS:
            sol=controlled_path(pol.controls,p,initial=initial)
            nend,aend=pol.controls(sol.y[:2,-1]);metrics=path_metrics(sol)
            initialrows.append(dict(country=country,policy='planner feedback',initial_u_A=initial[0],initial_u_B=initial[1],
                                    **metrics,terminal_flow_residual=np.linalg.norm(burden_flow(sol.y[:2,-1],nend,aend,p))))
            for row in controlled_rows(sol,pol.controls,p):allrows.append(dict(country=country,policy='planner feedback',source='physical-economy benchmark',initial_u_A=initial[0],initial_u_B=initial[1],**row))
            if initial==p.initial:
                comparisons.append(dict(country=country,policy='planner feedback',source='physical-economy benchmark',**metrics))
                tail=np.exp(-p.rho*p.horizon)*sol.y[3,-1]*pol.value_at(sol.y[:2,-1])
                direct=sol.y[6,-1]+tail;v0=pol.value_at(initial)
                checks['continuous_policy_validation'][country]=dict(discrete_value=v0,continuous_feedback_value_plus_tail=direct,
                    absolute_error=abs(direct-v0),relative_error=abs(direct/v0-1),tail=tail,
                    note='The ODE uses interpolated feedback; residual measures agreement with a step-held-control Bellman scheme, not an exact continuous HJB proof')
        for _,row in profiles[profiles.country==country].iterrows():
            source=row.source;x=row[['Q48','Q57','Q106','Q108','Q121','Q159']].to_numpy(float)
            decision=section6(x,RULE);a=float(decision['assistance']);n=float(decision['poisson_intensity']/p.chi)
            if n+p.aid_labor*a>p.capacity+1e-10:
                comparisons.append(dict(country=country,policy='frozen Section 6 rule',source=source,status='infeasible labor budget'));continue
            fixed=lambda u,n=n,a=a:(n,a)
            z=controlled_path(fixed,p);metrics=path_metrics(z)
            comparisons.append(dict(country=country,policy='frozen Section 6 rule',source=source,**metrics,
                                    section6_G=decision['G_T'],bridge_error=abs(metrics['G']-decision['G_T']),
                                    section6_pressure=decision['weighted_pressure_per_round']))
            for rr in controlled_rows(z,fixed,p):allrows.append(dict(country=country,policy='frozen Section 6 rule',source=source,initial_u_A=.08,initial_u_B=.08,**rr))
            tau=adj_subsidy(n,a,p);e=market_steady(a,tau,p)
            assert abs(e['n']-n)<1e-10
            eig=np.linalg.eigvals(jacobian_market(a,tau,p))
            eqrows.append(dict(country=country,policy='implemented Section 6 market',source=source,**e,
                               tax_subsidy=tau,eigenvalues=json.dumps(eig,default=js)))
            initials=INITIALS if source=='Human survey' else [p.initial]
            for initial in initials:
                sol,e=market_path(a,tau,p,initial=initial,end=100.)
                metrics,rr=market_metrics(sol,a,tau,p)
                initialrows.append(dict(country=country,policy='implemented Section 6 market',source=source,
                    initial_u_A=initial[0],initial_u_B=initial[1],**metrics,
                    terminal_flow_residual=np.linalg.norm(burden_flow(sol.sol(100)[:2],float(market_allocation(sol.sol(100)[:2],sol.sol(100)[2],a,tau,p)[0]),a,p))))
                for rrow in rr:allrows.append(dict(country=country,policy='implemented Section 6 market',source=source,initial_u_A=initial[0],initial_u_B=initial[1],**rrow))
                tt=np.linspace(0,100,1001);yy=sol.sol(tt);nn=market_allocation(yy[:2],yy[2],a,tau,p)[0]
                _,_,ww,_,_=production(yy[:2],nn,a,p)
                gap=p.chi*p.gamma*yy[2]-(1-tau)*ww
                interior=(nn>1e-9)&(nn<p.capacity-p.aid_labor*a-1e-9)
                # Complementarity: zero n => entry return <= cost; cap => return >= cost.
                violation=np.maximum(np.where(interior,np.abs(gap),np.where(nn<=1e-9,np.maximum(gap,0),np.maximum(-gap,0))),0)
                marketchecks.append(dict(country=country,source=source,initial=initial,
                    bvp_max_residual=float(np.max(sol.rms_residuals)),free_entry_or_corner_error=float(np.max(violation)),
                    initial_state_error=float(np.max(np.abs(sol.sol(0)[:2]-initial))),
                    terminal_patent_error=abs(sol.sol(100)[2]-e['patent']),
                    minimum_research=float(nn.min()),maximum_budget_violation=float(np.max(nn+p.aid_labor*a-p.capacity))))
                if initial==p.initial:
                    comparisons.append(dict(country=country,policy='implemented Section 6 market',source=source,**metrics,
                                            implementing_subsidy=tau,stationary_n_error=abs(e['n']-n)))
                    if source=='Human survey':
                        longer,_=market_path(a,tau,p,end=150.)
                        err=np.max(np.abs(longer.sol(np.linspace(0,100,401))-sol.sol(np.linspace(0,100,401))))
                        checks.setdefault('market_terminal_horizon',{})[country]=dict(H100_vs_H150_max_path_error=err)
            if source=='Human survey':
                base=market_steady(a,0,p);sol,_=market_path(a,0,p,end=100.)
                metrics,rr=market_metrics(sol,a,0,p)
                comparisons.append(dict(country=country,policy='unsubsidized market',source=source,**metrics))
                eqrows.append(dict(country=country,policy='unsubsidized market',source=source,**base,
                                  tax_subsidy=0,eigenvalues=json.dumps(np.linalg.eigvals(jacobian_market(a,0,p)),default=js)))
                for rrow in rr:allrows.append(dict(country=country,policy='unsubsidized market',source=source,initial_u_A=.08,initial_u_B=.08,**rrow))
        progress('country paths complete',country=country,feedback_fixed_points=len(fpoints))
    pd.DataFrame(comparisons).to_csv(OUT/'policy-comparisons.csv',index=False)
    pd.DataFrame(eqrows).to_csv(OUT/'stationary-equilibria.csv',index=False)
    pd.DataFrame(initialrows).to_csv(OUT/'initial-state-convergence.csv',index=False)
    pd.DataFrame(allrows).to_csv(OUT/'equilibrium-paths.csv',index=False)
    checks['market_path_validation']=marketchecks
    # One-at-a-time comparisons hold chi and capacity at their reference values.
    sensitivities=[]
    variations=[('q',x) for x in [.06,.08,.12,.16]]+[('theta',x) for x in [.94,.95,.97]]+[
        ('omega',x) for x in [0.,.15,.30,.60,.90]]+[('aid_labor',x) for x in [.02,.04,.06]]+[
        ('recovery_multiplier',x) for x in [.5,1.,2.]]+[('capacity_multiplier',x) for x in [.75,1.,1.25]]
    for country in COUNTRY_R:
        p,_=conditional_parameters(country)
        for variable,value in variations:
            pp=replace(p,recovery=tuple(value*np.array(p.recovery))) if variable=='recovery_multiplier' else (
                replace(p,capacity=value*p.capacity) if variable=='capacity_multiplier' else replace(p,**{variable:value}))
            if pp.gamma*pp.theta<=1 or pp.rho<=pp.q*pp.chi*pp.capacity:
                sensitivities.append(dict(country=country,variable=variable,value=value,status='inadmissible'));continue
            s=BellmanSolver(pp,size=41,aid_points=31,research_points=31,dt=.5).solve()
            pol=save_solver(s,OUT/f'sensitivity-policy-{country}-{variable}-{value:g}.npz')
            n,a=pol.controls(pp.initial);sol=controlled_path(pol.controls,pp)
            nend,aend=pol.controls(sol.y[:2,-1])
            sensitivities.append(dict(country=country,variable=variable,value=value,status='conditional one-at-a-time scenario',
                n_initial=n,a_initial=a,n_terminal=nend,a_terminal=aend,value_initial=s.report['value_initial'],
                stationary_flow_residual=np.linalg.norm(burden_flow(sol.y[:2,-1],nend,aend,pp)),
                bellman_residual=s.report['bellman_residual'],**path_metrics(sol)))
            del s;gc.collect()
        progress('comparative statics complete',country=country)
    pd.DataFrame(sensitivities).to_csv(OUT/'comparative-statics.csv',index=False)
    # Source uncertainty in xi and Kenya's undated monetary anchor is separate from pure comparative statics.
    resource=[]
    for country in COUNTRY_R:
        for xi in [.5,.75,1.]:
            try:
                p,fit=conditional_parameters(country,xi=xi)
                resource.append({**fit,'status':'admissible conditional resource conversion','capacity':p.capacity})
            except ValueError as e:resource.append(dict(country=country,xi_assumed=xi,status='rejected',reason=str(e)))
    for R in [.004,.008,.012]:
        p,fit=conditional_parameters('Kenya',R=R)
        resource.append({**fit,'status':'Kenya undated-anchor sensitivity; endpoints are assumptions','capacity':p.capacity})
    pd.DataFrame(resource).to_csv(OUT/'resource-uncertainty.csv',index=False)
    preserved={}
    for name in ['main.tex','sections/appendix.tex']:
        preserved[name]=((ROOT/name).read_bytes()==(ROOT/'audit/approved-baseline'/name).read_bytes())
    assert all(preserved.values())
    checks['approved_manuscript_preserved']=preserved
    checks['round_rule']=asdict(RULE)
    checks['reference_parameter_ledger']=parameters
    checks['evidence_ceiling']='Conditional mechanisms and numerically solved scenarios; no country forecast, causality, comprehensive cultural measurement, or data-identified innovation/aid/justice parameters'
    checks['non_claims']=['No universal empirical q=4% or 8%',
        'Model time units are not calendar years; delta=5 is an assumed normalization',
        'GERD/GDP is not observed research labor or the policy capacity budget',
        'A one-moment match does not independently validate chi or the model',
        'Fluid transition-need states are not measured unemployment or full inequality',
        'Purposive countries do not represent whole cultures',
        'Low Bellman residual is not continuous-control global optimality or a uniqueness theorem',
        'Multiple initial trajectories approaching one root do not prove global stability',
        'Full original unconstrained planner can be unbounded under otherwise plausible assumptions']
    checks['open_method_gaps']=['Kenyan approximate R&D/GDP statement lacks statistical reference year and Frascati scope; UNESCO 2021 annex has missing Kenya R&D observations for 2015--2018',
        'q, theta, wage fraction, time scale, assistance/recovery effects and capacity headroom need independent evidence',
        'Two hypothetical groups are not independently estimated population groups',
        'Grid feedback and asset-pricing implementation remain a numerical approximation with corner policy issues',
        'No independently qualified growth economist has reviewed this candidate']
    checks['runtime_seconds']=time.time()-started
    checks['software']={'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'pandas':pd.__version__}
    write_json('numerical-validation.json',checks)
    progress('all computations complete',seconds=checks['runtime_seconds'],comparisons=len(comparisons),paths=len(allrows),sensitivity_scenarios=len(sensitivities))

if __name__=='__main__':main()
