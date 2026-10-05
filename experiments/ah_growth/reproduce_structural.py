"""Current China/Germany/Egypt reproduction; no historical computed dependencies.

--verify recomputes market paths and rollouts using released value arrays.
--full solves all value arrays from zero and repeats matched scans/refinements.
"""
from pathlib import Path
from dataclasses import replace
import argparse, gc, json, hashlib
import numpy as np
import pandas as pd
from model import section6, market_path
from node2 import RULE, INITIALS, conditional_parameters, adj_subsidy, market_metrics
from control import BellmanSolver
from node2_diagnostics import HeldPolicy, rollout, metrics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REF = HERE / 'country_revision_results'

def parameters(country):
    return conditional_parameters(country, R=.0103 if country == 'Egypt' else None)[0]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--verify',action='store_true')
    ap.add_argument('--full',action='store_true'); ap.add_argument('--output',type=Path,default=ROOT/'.build/structural')
    args=ap.parse_args(); out=args.output; out.mkdir(parents=True,exist_ok=True)
    scores=ROOT/'figure_sources/dynamic_growth/inputs/country_question_scores.csv'
    if not scores.exists(): scores=HERE/'inputs/country_question_scores.csv'
    raw=pd.read_csv(scores); comparisons=[]; sweeps=[]; refinements=[]; starts=[]; checks=[]
    items=['Q48','Q57','Q106','Q108','Q121','Q159']
    for country in ['China','Germany','Egypt']:
        p=parameters(country); d=raw[raw.country.eq(country)]
        h=d.pivot(index='model',columns='question_id',values='human_directed')[items]
        if not np.allclose(h.iloc[0],h.iloc[1],atol=1e-12): raise ValueError('Unmatched human baseline')
        profiles=[('Human survey',h.iloc[0].to_numpy(float))]+[(s,g.set_index('question_id').loc[items,'model_directed'].to_numpy(float)) for s,g in d.groupby('model')]
        for source,x in profiles:
            rule=section6(x,RULE); a=float(rule['assistance']); target=float(rule['poisson_intensity']/p.chi)
            subsidy=adj_subsidy(target,a,p); sol,e=market_path(a,subsidy,p,end=100.)
            mm,_=market_metrics(sol,a,subsidy,p)
            comparisons.append(dict(country=country,source=source,policy='implemented Section 6 market',**mm))
            checks.append(dict(country=country,source=source,bvp_residual=float(np.max(sol.rms_residuals)),stationary_target_error=abs(e['n']-target)))
        specs=[('base',p,101,61,.125)]
        if args.full:
            specs += [('base',p,s,c,dt) for s,c,dt in [(41,31,.5),(61,41,.25),(81,61,.25)]]
            specs += [(f'{v}-{x:g}',replace(p,**{v:x}),101,61,.125) for v,xx in [('omega',[0.,.15,.60,.90]),('q',[.06,.12,.16])] for x in xx]
        for tag,pp,size,points,dt in specs:
            if args.full:
                solver=BellmanSolver(pp,size=size,aid_points=points,research_points=points,dt=dt).solve()
                hp=HeldPolicy(pp,solver.grid.copy(),solver.value.copy(),points,dt)
                np.savez_compressed(out/f'policy-{country}-{tag}-{size}-{points}-{dt:g}.npz',grid=solver.grid,value=solver.value,n=solver.n_grid,a=solver.a_grid)
                residual=solver.report['bellman_residual']; del solver;gc.collect()
            else:
                z=np.load(REF/f'policy-{country}-{tag}-{size}-{points}-{dt:g}.npz')
                hp=HeldPolicy(pp,z['grid'],z['value'],points,dt);residual=None
            sol=rollout(hp,pp.initial); mm=metrics(sol,hp)
            if tag=='base':
                refinements.append(dict(country=country,grid=size,control_points=points,dt=dt,**mm))
                if size==101:
                    comparisons.append(dict(country=country,source='physical-economy benchmark',policy='planner held optimal control',**mm))
                    if args.full:
                        for initial in INITIALS:
                            si=sol if initial==pp.initial else rollout(hp,initial)
                            starts.append(dict(country=country,initial_u_A=initial[0],initial_u_B=initial[1],**metrics(si,hp)))
            if size==101:
                scan=[('omega',pp.omega),('q',pp.q)] if tag=='base' else [(tag.split('-')[0],float(tag.split('-')[1]))]
                for variable,value in scan:sweeps.append(dict(country=country,variable=variable,value=value,bellman_residual=residual,**mm))
            print(json.dumps(dict(country=country,tag=tag,grid=size,G=mm['G'],Umax=mm['Umax'])),flush=True)
            del hp;gc.collect()
    cc=pd.DataFrame(comparisons); cc.to_csv(out/'policy-comparisons.csv',index=False)
    upgrades=[]
    for country in ['China','Germany','Egypt']:
        d=cc[cc.country.eq(country)&cc.policy.eq('implemented Section 6 market')].set_index('source');h,a,b=(d.loc[x] for x in ['Human survey','GPT-5.5','GPT-5.6 Sol']);r={'country':country}
        for key in ['G','Umax','average_output']:
            r['upgrade_change_'+key]=float(b[key]-a[key]);r['upgrade_absolute_bias_change_'+key]=float(abs(b[key]-h[key])-abs(a[key]-h[key]))
        upgrades.append(r)
    uu=pd.DataFrame(upgrades).set_index('country'); expected=pd.read_csv(REF/'three-country-upgrade-comparison.csv').set_index('country')
    err=max(float(np.max(np.abs(uu[k]-expected[k]))) for k in uu.columns)
    if err>1e-10:raise AssertionError(f'Upgrade mismatch {err}')
    ss=pd.DataFrame(sweeps);rr=pd.DataFrame(refinements);max_scan=max_ref=0.
    if args.full:
        ex=pd.read_csv(REF/'matched-sensitivity.csv')
        for row in ss.to_dict('records'):
            match=ex[ex.country.eq(row['country'])&ex.variable.eq(row['variable'])&np.isclose(ex.value,row['value'])].iloc[0]
            max_scan=max(max_scan,max(abs(row[k]-match[k]) for k in ['G','Umax','average_output']))
        ex=pd.read_csv(REF/'country-refinement.csv')
        for row in rr.to_dict('records'):
            match=ex[ex.country.eq(row['country'])&ex.grid.eq(row['grid'])].iloc[0]
            max_ref=max(max_ref,max(abs(row[k]-match[k]) for k in ['G','Umax','value_initial']))
        if max(max_scan,max_ref)>1e-9:raise AssertionError('Full reference mismatch')
        ss.to_csv(out/'matched-sensitivity.csv',index=False);rr.to_csv(out/'joint-refinements.csv',index=False);pd.DataFrame(starts).to_csv(out/'initial-state-results.csv',index=False)
    report=dict(status='passed',mode='full' if args.full else 'verify',upgrade_max_absolute_difference=err,sensitivity_rows=len(ss) if args.full else None,refinement_settings=len(rr),sensitivity_max_difference=max_scan,refinement_max_difference=max_ref,market_checks=checks,aggregate_input_sha256=hashlib.sha256(scores.read_bytes()).hexdigest(),evidence_ceiling='Conditional structural scenarios, not identified national effects')
    (out/'reproduction-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

if __name__=='__main__':main()
