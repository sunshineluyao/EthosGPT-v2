"""China/Germany/Egypt author-review refresh; existing numerical schemes only.

Replaces the working country case, not the historical Kenya archive. Reuses
valid market paths, recomputes Egypt, and uses matched 101/61/0.125 settings
for the displayed omega and quality-jump sweeps. No empirical identification.
"""
from pathlib import Path
from dataclasses import replace, asdict
import gc, json, hashlib, time
import numpy as np
import pandas as pd
from node2 import OUT, ROOT, RULE, INITIALS, conditional_parameters, adj_subsidy, market_metrics
from model import section6, market_path, jacobian_market, production
from control import BellmanSolver
from node2_diagnostics import HeldPolicy, rollout, metrics

DEST=Path(__file__).resolve().parent/'country_revision_results'
COUNTRIES=['China','Germany','Egypt']

def emit(**kw): print(json.dumps(kw),flush=True)

def solve_policy(p,country,size,points,dt,tag):
    f=DEST/f'policy-{country}-{tag}-{size}-{points}-{dt:g}.npz'
    existing=OUT/f'policy-{country}-{size}-{points}-{dt:g}.npz'
    if f.exists():
        z=np.load(f); hp=HeldPolicy(p,z['grid'],z['value'],points,dt)
        return hp,dict(cache=str(f),bellman_residual=None)
    if tag=='base' and existing.exists():
        z=np.load(existing);np.savez_compressed(f,**{k:z[k] for k in z.files})
        return HeldPolicy(p,z['grid'],z['value'],points,dt),dict(reused=str(existing),bellman_residual=None)
    started=time.monotonic()
    s=BellmanSolver(p,size=size,aid_points=points,research_points=points,dt=dt).solve()
    np.savez_compressed(f,grid=s.grid,value=s.value,n=s.n_grid,a=s.a_grid)
    hp=HeldPolicy(p,s.grid.copy(),s.value.copy(),points,dt);report=s.report.copy()
    f.with_suffix('.solver.json').write_text(json.dumps(report,indent=2)+'\n')
    del s;gc.collect();emit(country=country,stage='policy solved',tag=tag,seconds=round(time.monotonic()-started,2))
    return hp,report

def rows_for_path(sol,p,country,initial,policy,source):
    ans=[]
    for j,t in enumerate(sol.t):
        n,a=sol.controls[j];u=sol.y[:2,j]
        ans.append(dict(country=country,policy=policy,source=source,initial_u_A=initial[0],initial_u_B=initial[1],
                        t=t,u_A=u[0],u_B=u[1],n=n,a=a,log_quality=sol.y[2,j],
                        instantaneous_g_log=p.chi*n*np.log1p(p.q),mean_quality=sol.y[3,j],
                        expected_output=sol.y[3,j]*production(u,n,a,p)[1]))
    return ans

def main():
    DEST.mkdir(exist_ok=True)
    raw=pd.read_csv(Path(__file__).resolve().parent/'inputs/country_question_scores.csv')
    paths=pd.read_csv(OUT/'equilibrium-paths.csv')
    paths=paths.iloc[:0].copy()
    comparisons=pd.read_csv(OUT/'review-policy-comparisons.csv')
    comparisons=comparisons.iloc[:0].copy()
    existing_held=pd.read_csv(OUT/'held-optimal-paths.csv');existing_held=existing_held.iloc[:0].copy()
    refs=pd.read_csv(OUT/'held-control-refinement.csv');refs=refs.iloc[:0].copy()
    solver_refs=pd.read_csv(OUT/'solver-refinement.csv');solver_refs=solver_refs.iloc[:0].copy()
    allpaths=[];allcomparisons=[];allrefs=[];allinitials=[];allsolver=[];sweeps=[];checks=[];parameters={}
    for country in COUNTRIES:
        p,fit=conditional_parameters(country,R=.0103 if country=='Egypt' else None)
        parameters[country]=dict(parameters=asdict(p),resource_match=fit)
        if country in COUNTRIES:
            if country=='Egypt':
                parameters[country]['resource_match'].update(reference_period='2023',source_status='dated rounded WIPO indicator',
                    source_url='https://www.wipo.int/edocs/gii-ranking/2025/eg.pdf',source_location='PDF p.8, indicator 2.3.2',
                    working_country='Egypt focal resource scenario; historical Kenya inputs retained separately')
            items=['Q48','Q57','Q106','Q108','Q121','Q159'];dd=raw[raw.country.eq(country)]
            hh=dd.pivot(index='model',columns='question_id',values='human_directed')[items]
            assert np.max(np.abs(hh.iloc[0]-hh.iloc[1]))<1e-12
            profiles=[('Human survey',hh.iloc[0].to_numpy(float))]
            profiles += [(s,g.set_index('question_id').loc[items,'model_directed'].to_numpy(float)) for s,g in dd.groupby('model')]
            for source,x in profiles:
                rule=section6(x,RULE);a=float(rule['assistance']);n=float(rule['poisson_intensity']/p.chi)
                tau=adj_subsidy(n,a,p); initials=INITIALS if source=='Human survey' else [p.initial]
                assert n+p.aid_labor*a<=p.capacity
                for initial in initials:
                    sol,e=market_path(a,tau,p,initial=initial,end=100.)
                    m,rr=market_metrics(sol,a,tau,replace(p,initial=initial))
                    for r in rr:allpaths.append(dict(country=country,policy='implemented Section 6 market',source=source,
                                                    initial_u_A=initial[0],initial_u_B=initial[1],**r))
                    checks.append(dict(country=country,source=source,initial=list(initial),bvp_residual=float(np.max(sol.rms_residuals)),
                                       terminal_research_target_error=abs(e['n']-n)))
                    if np.allclose(initial,p.initial):allcomparisons.append(dict(country=country,policy='implemented Section 6 market',source=source,**m))
                if source=='Human survey':
                    sol,e=market_path(a,0.,p,end=100.);m,rr=market_metrics(sol,a,0.,p)
                    allcomparisons.append(dict(country=country,policy='unsubsidized market',source=source,**m))
                    for r in rr:allpaths.append(dict(country=country,policy='unsubsidized market',source=source,initial_u_A=.08,initial_u_B=.08,**r))
            for size,points,dt in [(41,31,.5),(61,41,.25),(81,61,.25),(101,61,.125)]:
                hp,report=solve_policy(p,country,size,points,dt,'base');sol=rollout(hp,p.initial);mm=metrics(sol,hp)
                allrefs.append(dict(country=country,grid=size,control_points=points,dt=dt,**mm))
                allsolver.append({**report,'country':country,'grid':size,'control_points':points,'dt':dt})
                if size==101:
                    for initial in INITIALS:
                        si=sol if initial==p.initial else rollout(hp,initial)
                        allinitials.append(dict(country=country,initial_u_A=initial[0],initial_u_B=initial[1],**metrics(si,hp)))
                        allpaths.extend(rows_for_path(si,p,country,initial,'planner held optimal control','physical-economy benchmark'))
                    allcomparisons.append(dict(country=country,policy='planner held optimal control',source='physical-economy benchmark',**mm))
                del hp;gc.collect()
        else:
            hp,_=solve_policy(p,country,101,61,.125,'base')
            base_ref=refs[refs.country.eq(country)&refs.grid.eq(101)].iloc[0].to_dict()
            allcomparisons.append(dict(country=country,policy='planner held optimal control',source='physical-economy benchmark',**{k:v for k,v in base_ref.items() if k!='country'}))
            del hp;gc.collect()
        # One reference mesh throughout the two displayed sensitivity panels.
        for variable,values in [('omega',[0.,.15,.30,.60,.90]),('q',[.06,.08,.12,.16])]:
            for value in values:
                pp=replace(p,**{variable:value});tag='base' if value==getattr(p,variable) else f'{variable}-{value:g}'
                hp,report=solve_policy(pp,country,101,61,.125,tag)
                metricfile=DEST/f'metrics-{country}-{tag}-101-61-0.125.json'
                if metricfile.exists():mm=json.loads(metricfile.read_text())
                else:
                    sol=rollout(hp,pp.initial);mm=metrics(sol,hp)
                    metricfile.write_text(json.dumps(mm,indent=2)+'\n')
                sweeps.append(dict(country=country,variable=variable,value=value,grid=101,control_points=61,dt=.125,
                                   bellman_residual=report.get('bellman_residual'),**mm))
                emit(country=country,stage='sensitivity evaluated',variable=variable,value=value,G=mm['G'],Umax=mm['Umax'],value_error=mm['rollout_relative_value_error'])
                del hp;gc.collect()
    finalpaths=pd.concat([paths,existing_held,pd.DataFrame(allpaths)],ignore_index=True)
    for c in COUNTRIES:
        p=conditional_parameters(c,R=.0103 if c=='Egypt' else None)[0]
        mask=finalpaths.country.eq(c);finalpaths.loc[mask,'instantaneous_g_log']=p.chi*finalpaths.loc[mask,'n']*np.log1p(p.q)
    finalpaths.to_csv(DEST/'country-paths.csv',index=False)
    finalcomp=pd.concat([comparisons,pd.DataFrame(allcomparisons)],ignore_index=True)
    finalcomp.to_csv(DEST/'country-policy-comparisons.csv',index=False)
    finalrefs=pd.concat([refs,pd.DataFrame(allrefs)],ignore_index=True)
    finalrefs['rollout_value_error_percent']=100*finalrefs.rollout_relative_value_error
    for country in COUNTRIES:
        idx=finalrefs.country.eq(country);d=finalrefs[idx].sort_values('grid');last=d.iloc[-1]
        finalrefs.loc[idx,'G_relative_to_finest_percent']=100*(finalrefs.loc[idx,'G']/last.G-1)
    finalrefs.to_csv(DEST/'country-refinement.csv',index=False)
    pd.concat([solver_refs,pd.DataFrame(allsolver)],ignore_index=True).to_csv(DEST/'country-solver-settings.csv',index=False)
    pd.DataFrame(allinitials).to_csv(DEST/'egypt-initial-convergence.csv',index=False)
    sw=pd.DataFrame(sweeps);sw.to_csv(DEST/'matched-sensitivity.csv',index=False)
    updates=[]
    for country in COUNTRIES:
        d=finalcomp[finalcomp.country.eq(country)&finalcomp.policy.eq('implemented Section 6 market')].set_index('source')
        h,a,b=(d.loc[s] for s in ['Human survey','GPT-5.5','GPT-5.6 Sol'])
        r=dict(country=country)
        for key in ['G','Umax','average_output']:
            r[key+'_human']=float(h[key]);r[key+'_55']=float(a[key]);r[key+'_56']=float(b[key])
            r['upgrade_change_'+key]=float(b[key]-a[key])
            r['upgrade_absolute_bias_change_'+key]=float(abs(b[key]-h[key])-abs(a[key]-h[key]))
        updates.append(r)
    pd.DataFrame(updates).to_csv(DEST/'three-country-upgrade-comparison.csv',index=False)
    evidence=dict(status='Recomputed conditional structural-growth results',countries=COUNTRIES,
        source_hashes={n:hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in ['equilibrium-paths.csv','held-optimal-paths.csv','review-policy-comparisons.csv','held-control-refinement.csv']},
        parameters=parameters,egypt_market_checks=checks,
        matched_sweep_settings=dict(state_grid=101,control_points_each_dimension=61,decision_dt=.125),
        max_sweep_value_consistency_error=float(sw.rollout_relative_value_error.max()),
        non_claims=['Conditional mechanisms, not national forecasts','Group parameters and welfare weights remain assumptions',
          'No continuous-control global optimality theorem','Small Bellman/rollout value discrepancy is not a bound on every path indicator',
          'Fixed-q and omega sweeps do not themselves measure GPT upgrade effects'],
        refinement_note='State grid, action grid and dt change together: a joint refinement check, not isolated state-grid convergence')
    (DEST/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    emit(stage='COMPLETE',countries=COUNTRIES,max_value_error=evidence['max_sweep_value_consistency_error'])

if __name__=='__main__':main()
