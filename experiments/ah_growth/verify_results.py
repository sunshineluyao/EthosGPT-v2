"""Scientific contracts for the released structural model and result tables."""
from pathlib import Path
from dataclasses import replace
import json
import numpy as np
import pandas as pd
from model import section6, burden_step, production, core_equilibrium
from node2 import RULE, conditional_parameters

ROOT=Path(__file__).resolve().parent

def verify():
    paths=pd.read_csv(ROOT/'country_revision_results/country-paths.csv')
    comp=pd.read_csv(ROOT/'country_revision_results/country-policy-comparisons.csv')
    up=pd.read_csv(ROOT/'country_revision_results/three-country-upgrade-comparison.csv')
    sw=pd.read_csv(ROOT/'country_revision_results/matched-sensitivity.csv')
    raw=pd.read_csv(ROOT/'inputs/country_question_scores.csv')
    assert len(up)==3 and len(comp)==15 and len(sw)==27
    assert (sw.grid.eq(101)&sw.control_points.eq(61)&np.isclose(sw.dt,.125)).all()
    max_step=0.;max_budget=0.
    for c in ['China','Germany','Egypt']:
        p,_=conditional_parameters(c,R=.0103 if c=='Egypt' else None)
        d=paths[paths.country.eq(c)]
        budget=np.max(d.n+p.aid_labor*d.a-p.capacity);max_budget=max(max_budget,float(budget))
        assert budget<1e-10 and d.a.between(0,1).all() and d.n.ge(-1e-10).all()
        assert d.u_A.between(0,1).all() and d.u_B.between(0,1).all()
        assert np.allclose(d.instantaneous_g_log,p.chi*d.n*np.log1p(p.q),atol=1e-12)
        for _,g in d[d.policy.eq('planner held optimal control')].groupby(['initial_u_A','initial_u_B']):
            g=g.sort_values('t');u=g[['u_A','u_B']].to_numpy();n=g.n.to_numpy();a=g.a.to_numpy();dt=np.diff(g.t)
            expected=burden_step(u[:-1].T,n[:-1],a[:-1],dt,p).T
            err=float(np.max(np.abs(expected-u[1:])));max_step=max(max_step,err);assert err<1e-10
        z=comp[comp.country.eq(c)&comp.policy.eq('implemented Section 6 market')].set_index('source')
        r=up[up.country.eq(c)].iloc[0]
        for m in ['G','Umax','average_output']:
            h,x,y=(float(z.loc[s,m]) for s in ['Human survey','GPT-5.5','GPT-5.6 Sol'])
            assert abs((y-x)-r['upgrade_change_'+m])<1e-12
            assert abs((abs(y-h)-abs(x-h))-r['upgrade_absolute_bias_change_'+m])<1e-12
        assert p.rho>p.q*p.chi*p.capacity and p.gamma*p.theta>1
        assert abs(core_equilibrium(p)['entry_gap'])<1e-12
    items=['Q48','Q57','Q106','Q108','Q121','Q159']
    for (_,model),d in raw.groupby(['country','model']):
        x=d.set_index('question_id').loc[items,'model_directed'].to_numpy()
        rr=section6(x,RULE);assert .11-1e-12<=rr['arrival_probability']<=.29+1e-12
        assert abs(rr['G_T']-rr['horizon_time']*rr['poisson_intensity']*np.log1p(RULE.quality_jump))<1e-12
    result={'status':'passed','path_rows':len(paths),'comparison_rows':len(comp),'matched_sensitivity_rows':len(sw),
      'max_held_state_step_error':max_step,'max_budget_excess':max_budget,
      'scope':'Frozen aggregate inputs and conditional synthetic paths; no empirical causal validation'}
    print(json.dumps(result,indent=2));return result

if __name__=='__main__':verify()
