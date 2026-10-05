"""Run the bounded dynamic extension without API calls or private microdata.

Outputs distinguish measured representation errors, their assumed propagation,
and independent teaching normal forms. All adviser policies are evaluated in
the same actual system, including identical initial states and budget.
"""
from pathlib import Path
from dataclasses import replace
import hashlib,json,platform,time
import numpy as np
import pandas as pd
import scipy
from scipy.optimize import root,brentq
from scipy.stats import norm
from scipy.special import expit
from dynamics import P,fold,gradient,equilibrium,jacobian,equilibria,continue_branch,policy_from_estimate,simulate,metrics,steady_exposure,economic_derivative
from culture import QUESTIONS,BLOCKS,WEIGHTS,load_distributions,culture_projection,simplex_tilt,simulate_culture

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'results'
DATA.mkdir(exist_ok=True)
CONFIG=json.loads((ROOT/'parameters.json').read_text())


def save(name,rows):
    frame=pd.DataFrame(rows)
    frame.to_csv(DATA/name,index=False,float_format='%.17g')
    return frame


def bca(draws,estimate,jack):
    prop=np.clip((np.sum(draws<estimate)+.5*np.sum(draws==estimate))/len(draws),1/(2*len(draws)),1-1/(2*len(draws)))
    z0=norm.ppf(prop);diff=jack.mean()-jack
    denominator=6*np.power(np.square(diff).sum(),1.5)
    acceleration=float(np.power(diff,3).sum()/denominator) if denominator>0 else 0.
    z=norm.ppf([.025,.975])
    qs=norm.cdf(z0+(z0+z)/(1-acceleration*(z0+z)))
    return np.quantile(draws,np.clip(qs,0,1))


def reproduce_audit(countries,arrays):
    reference=arrays['Survey']
    old=pd.read_csv(ROOT/'inputs/country_question_scores.csv')
    rows=[];max_difference=0.
    for model in ['GPT-5.5','GPT-5.6 Sol']:
        for i,country in enumerate(countries):
            for q,block in zip(QUESTIONS,BLOCKS):
                human=reference[i,block];modelp=arrays[model][i,block]
                tvd=.5*np.abs(modelp-human).sum()
                w1=np.abs(np.cumsum(modelp)[:-1]-np.cumsum(human)[:-1]).sum()/(len(human)-1)
                original=old[(old.model==model)&(old.country==country)&(old.question_id==q)].iloc[0]
                max_difference=max(max_difference,abs(tvd-original.tvd),abs(w1-original.w1))
                rows.append({'model':model,'country':country,'question_id':q,'tvd':tvd,'w1':w1})
    frame=save('audit_reproduced.csv',rows)
    country={m:frame[frame.model==m].groupby('country').tvd.mean().reindex(countries).to_numpy() for m in ['GPT-5.5','GPT-5.6 Sol']}
    delta=country['GPT-5.6 Sol']-country['GPT-5.5']
    rng=np.random.default_rng(CONFIG['primary_country_bootstrap_seed'])
    ids=rng.integers(0,len(countries),size=(CONFIG['primary_country_bootstrap_draws'],len(countries)))
    # Match the original arithmetic: difference of paired bootstrap means.
    draws=country['GPT-5.6 Sol'][ids].mean(axis=1)-country['GPT-5.5'][ids].mean(axis=1)
    jack=np.array([np.delete(country['GPT-5.6 Sol'],i).mean()-np.delete(country['GPT-5.5'],i).mean() for i in range(len(countries))])
    low,high=bca(draws,float(delta.mean()),jack)
    report={'countries':len(countries),'questions':len(QUESTIONS),'paired_model_cells':len(frame),'generations_per_cell':5,'mean_TVD_delta':float(delta.mean()),'ci_low':float(low),'ci_high':float(high),'max_point_difference_from_archive':max_difference,'scope':'All 768 cell-level TVD/W1 comparisons and primary paired-country TVD interval; other archived analyses retained unchanged.'}
    if max_difference>2e-12:raise ValueError('Audit inputs or calculations do not match the archive')
    (DATA/'audit_reproduction.json').write_text(json.dumps(report,indent=2))
    return report


def run_static_error_experiments(countries,arrays,coordinates):
    rows=[];projection_rows=[]
    reference=arrays['Survey']
    for clean_items in [False,True]:
        for shape in CONFIG['mapping_shapes']:
            for model in ['GPT-5.5','GPT-5.6 Sol']:
                projected=culture_projection(arrays[model],reference,coordinates,shape,strength=1,clean_items=clean_items)
                for country,c in zip(countries,projected):
                    projection_rows.append({'country':country,'model':model,'shape':shape,'items':'Q48/Q57/Q159' if clean_items else 'all six','projected_error':float(c)})
                for strength in CONFIG['mapping_strengths']:
                    for country,c in zip(countries,projected):
                        actual_error=float(strength*c)
                        aid,nu=policy_from_estimate(actual_error)
                        out=metrics(simulate(aid,nu,points=121))
                        rows.append({'country':country,'model':model,'shape':shape,'items':'Q48/Q57/Q159' if clean_items else 'all six','strength':strength,'estimated_culture':actual_error,'actual_culture':0.,'aid':aid,'nu':nu,'budget_used':aid+nu/P.capacity,**out})
        print('Completed error propagation:', 'restricted items' if clean_items else 'six items',flush=True)
    save('culture_error_projections.csv',projection_rows)
    return save('audit_linked_policy_results.csv',rows)


def run_boundary_and_continuation():
    boundary=[];checks=[]
    for aid in np.linspace(0,.72,145):
        z0,n0=fold(aid,0.)
        z1,n1=fold(aid,.18)
        boundary.append({'aid':aid,'actual_fold':n0,'perceived_fold':n1,'budget_capacity':P.capacity*(1-aid)})
    save('boundary.csv',boundary)
    branches=[]
    for c in [0.,.18]: branches.extend(continue_branch(culture=c))
    save('continuation.csv',branches)
    for aid in [0,.15,.3,.5,.65]:
        for c in [0,.18]:
            z,nu=fold(aid,c)
            h=1e-4
            second=(gradient(z+h,nu,aid)[0]-gradient(z-h,nu,aid)[0])/(2*h)
            eig=np.linalg.eigvals(jacobian(z,nu,aid))
            # Independent root of the full vector field and determinant.
            def full(v):
                zz,u1,u2,nn=v
                dz,du,_=economic_derivative(zz,np.array([u1,u2]),nn,aid,c)
                return np.r_[dz,du,np.linalg.det(jacobian(zz,nn,aid))]
            independent=root(full,np.r_[z,steady_exposure(z,nu,aid),nu],tol=1e-11)
            checks.append({'aid':aid,'culture':c,'z_fold':z,'nu_fold':nu,'fold_residual':float(max(abs(equilibrium(z,nu,aid,c)),abs(gradient(z,nu,aid)[0]))),'zero_eigenvalue':float(np.min(np.abs(eig))),'other_largest_eigenvalue':float(np.sort(eig.real)[-2]),'second_z_derivative':second,'parameter_derivative':gradient(z,nu,aid)[1],'independent_fold_displacement':float(np.max(np.abs(independent.x-np.r_[z,steady_exposure(z,nu,aid),nu]))),'independent_residual':float(np.max(np.abs(full(independent.x))))})
    return save('critical_point_checks.csv',checks)


def run_policy_sets():
    rows=[]
    # Finite deterministic menu, not a certified global optimum.
    for aid in np.linspace(0,.8,41):
        for nu in np.linspace(.12,2.4,58):
            spending=aid+nu/P.capacity
            if spending<=1+1e-12:
                out=metrics(simulate(aid,nu,points=121))
                rows.append({'aid':aid,'nu':nu,'budget_used':spending,**out})
    frame=save('policy_menu.csv',rows)
    exact=[]
    for aid in np.linspace(0,.9,181):
        nu=P.capacity*(1-aid)
        out=metrics(simulate(aid,nu,points=121))
        exact.append({'aid':aid,'nu':nu,'budget_used':aid+nu/P.capacity,**out})
    exact_frame=save('exact_spending_menu.csv',exact)
    policies=[]
    for label,c in [('Reference advice',0.),('Overoptimistic advice',.18)]:
        aid,nu=policy_from_estimate(c)
        policies.append({'policy':label,'estimated_culture':c,'aid':aid,'nu':nu,'budget_used':aid+nu/P.capacity,**metrics(simulate(aid,nu))})
    aid=.56;nu=P.capacity*(1-aid)
    policies.append({'policy':'More adjustment','estimated_culture':None,'aid':aid,'nu':nu,'budget_used':1.,**metrics(simulate(aid,nu))})
    # Computed selection among the exact-spending menu with two explicit bounds.
    eligible=exact_frame[(exact_frame.growth>=CONFIG['growth_floor'])&(exact_frame.worst_burden<=CONFIG['worst_group_exposure_cap'])&(exact_frame.adoption_final>=CONFIG['minimum_final_adoption'])]
    if len(eligible):
        selected=eligible.sort_values('growth',ascending=False).iloc[0]
        policies.append({'policy':'Best admissible menu point','estimated_culture':None,**selected.to_dict()})
    save('selected_policies.csv',policies)
    paths=[]
    for policy in policies:
        sol=simulate(policy['aid'],policy['nu'])
        for k,t in enumerate(sol.t):paths.append({'policy':policy['policy'],'time':t,'z':sol.y[0,k],'adoption':expit(2*sol.y[0,k]),'group_A_exposure':sol.y[1,k],'group_B_exposure':sol.y[2,k],'log_quality':sol.y[3,k]})
    save('selected_policy_paths.csv',paths)
    predicted=policies[1].copy()
    predicted.update(metrics(simulate(predicted['aid'],predicted['nu'],culture=.18)))
    save('predicted_policy_point.csv',[predicted])
    # Disconnected components are retained, including zero feasible settings.
    admissible=[]
    for cap in [.45,.5,.55,.60]:
        for floor in [.08,.10,.12]:
            for ceiling in [0.,.2,.4,.6,.8]:
                feasible=frame[(frame.aid<=ceiling+1e-12)&(frame.growth>=floor)&(frame.worst_burden<=cap)&(frame.adoption_final>=CONFIG['minimum_final_adoption'])]
                admissible.append({'aid_capacity':ceiling,'growth_floor':floor,'exposure_cap':cap,'feasible_policy_count':len(feasible),'max_launch_nu':float(feasible.nu.max()) if len(feasible) else np.nan,'min_launch_nu':float(feasible.nu.min()) if len(feasible) else np.nan,'menu_policy_count':len(frame[frame.aid<=ceiling+1e-12])})
    save('admissible_menu_sets.csv',admissible)
    return frame,policies


def run_error_direction_and_control(reference,coordinates):
    # Exactly equal mean item-TVD: opposite directions and an orthogonal vector.
    eps=min(.025,reference[0]*.8,reference[9]*.8)
    align=reference.copy();align[0]-=eps;align[9]+=eps
    reverse=reference.copy();reverse[0]+=eps;reverse[9]-=eps
    orthogonal=reference.copy();orthogonal[0]-=eps/2;orthogonal[9]-=eps/2;orthogonal[4]+=eps/2;orthogonal[5]+=eps/2
    vectors={'Positive direction':align,'Negative direction':reverse,'Zero projection':orthogonal}
    rows=[]
    for label,v in vectors.items():
        for shape in CONFIG['mapping_shapes']:
            c=float(culture_projection(v,reference,coordinates,shape))
            aid,nu=policy_from_estimate(c)
            tvd=np.mean([.5*np.abs(v[b]-reference[b]).sum() for b in BLOCKS])
            rows.append({'direction':label,'shape':shape,'mean_item_TVD':tvd,'projection':c,'aid':aid,'nu':nu,**metrics(simulate(aid,nu))})
    save('equal_distance_directions.csv',rows)
    controls=[]
    for error in np.linspace(-.20,.20,161):
        aid,nu=policy_from_estimate(error)
        for label,p in [('Fold example',P),('No-fold control',replace(P,b=-1.))]:
            out=metrics(simulate(aid,nu,p=p,points=121))
            controls.append({'assumed_error':error,'system':label,'aid':aid,'nu':nu,**out})
    save('error_sensitivity_controls.csv',controls)
    # Unique roots and stability in a broad no-fold menu.
    root_checks=[]
    p=replace(P,b=-1.)
    for aid in np.linspace(0,.8,9):
        for nu in np.linspace(.1,2.4,12):
            roots=equilibria(nu,aid,p=p)
            if len(roots)!=1:raise ValueError('No-fold control is not unique')
            z=roots[0];eig=np.linalg.eigvals(jacobian(z,nu,aid,p))
            root_checks.append({'aid':aid,'nu':nu,'z':z,'root_count':len(roots),'residual':abs(equilibrium(z,nu,aid,p=p)),'largest_eigenvalue_real':float(np.max(eig.real))})
    save('no_fold_checks.csv',root_checks)
    return rows


def run_cultural_families(reference,coordinates):
    rows=[];paths=[];checks=[]
    aid0,nu0=policy_from_estimate(0.)
    aid1,nu1=policy_from_estimate(.18)
    for family in ['C0','C1','C2','C3','C4']:
        for shape in CONFIG['mapping_shapes']:
            for name,aid,nu in [('Reference advice',aid0,nu0),('Overoptimistic advice',aid1,nu1),('More adjustment',.56,1.056)]:
                sol,out,probs=simulate_culture(reference,coordinates,family,shape,aid,nu)
                rows.append({'family':family,'shape':shape,'policy':name,'aid':aid,'nu':nu,**out})
                if shape=='linear':
                    cs=np.mean(culture_projection(probs,reference,coordinates,shape),axis=1)
                    for k,t in enumerate(sol.t):paths.append({'family':family,'policy':name,'time':t,'culture_projection':cs[k],'adoption':expit(2*sol.y[0,k]),'group_A_exposure':sol.y[1,k],'group_B_exposure':sol.y[2,k]})
                if shape=='linear' and name=='Reference advice':
                    _,strict,_=simulate_culture(reference,coordinates,family,shape,aid,nu,tolerance=1e-11)
                    checks.append({'family':family,'metric_tolerance_difference':max(abs(out[k]-strict[k]) for k in ['growth','mean_burden','worst_burden','burden_gap']),'simplex_mass_error':out['mass_error'],'minimum_probability':out['minimum_probability']})
        print('Completed cultural family',family,flush=True)
    save('cultural_families.csv',rows)
    save('cultural_family_paths.csv',paths)
    return save('cultural_family_checks.csv',checks)


def run_lag_and_rate(reference,coordinates):
    """Exogenous full-distribution paths, identical endpoints for each rate.

    Any failure combines changing culture with delayed policy response. It is
    distinct from the independently reproduced pure rate-tipping normal form.
    """
    target=simplex_tilt(reference,coordinates,CONFIG['cultural_forcing_target_tilt'])
    policy_cs=np.linspace(-.65,.2,401)
    policy_a=np.array([policy_from_estimate(c)[0] for c in policy_cs])
    times=np.linspace(0,60,1201)
    rows=[];paths=[]
    for rate in CONFIG['cultural_forcing_rates']:
        normalizer=np.tanh(P.horizon/2*rate)
        def distribution(t):
            t=np.clip(t,0,P.horizon)
            s=(np.tanh(rate*(t-P.horizon/2))+normalizer)/(2*normalizer)
            return reference+s*(target-reference)
        def actual_c(t):return float(culture_projection(distribution(t),reference,coordinates))
        for lag in CONFIG['adviser_update_lags']:
            def aid(t):return float(np.interp(actual_c(t-lag),policy_cs,policy_a))
            def nu(t):return P.capacity*(1-aid(t))
            sol=simulate(aid,nu,actual_c,points=1201)
            out=metrics(sol)
            rows.append({'forcing_rate':rate,'adviser_lag':lag,'initial_culture_projection':actual_c(0.),'final_culture_projection':actual_c(60.),'budget_used':1.,**out})
            if rate in [.1,1.6] and lag in [0,6]:
                for k,t in enumerate(sol.t):paths.append({'forcing_rate':rate,'adviser_lag':lag,'time':t,'actual_culture':actual_c(t),'estimated_culture':actual_c(t-lag),'aid':aid(t),'nu':nu(t),'adoption':expit(2*sol.y[0,k]),'group_A_exposure':sol.y[1,k],'group_B_exposure':sol.y[2,k]})
    save('lag_rate_grid.csv',rows);save('lag_rate_paths.csv',paths)
    return rows


def quality_replacement_benchmark():
    """Closed resource account on a detrended Cobb-Douglas benchmark.

    Research i and aid a spend the same specified shares of output. Saving,
    depreciation, and quality-replacement growth give a unique positive
    balanced-growth capital ratio. No coordination fold is included.
    """
    rows=[]
    cb=CONFIG['capital_benchmark']
    alpha=cb['capital_elasticity'];consumption=cb['consumption_share'];budget=cb['policy_budget_share'];depreciation=cb['depreciation'];horizon=P.horizon
    from scipy.integrate import solve_ivp
    for aid in [.0,.3,.6,.9]:
        i=1-aid;lam=cb['research_arrival_scale']*i;g=np.log(P.quality_multiplier)*lam
        u=np.array([.75,.38])*lam/(np.array([.75,.38])*lam+np.array([.12,.32])+np.array([1.2,1.])*aid)
        labor=1-u.mean()
        saving=1-consumption-budget*(aid+i)
        kstar=(saving*labor**(1-alpha)/(depreciation+g))**(1/(1-alpha))
        derivative=-(1-alpha)*(depreciation+g)
        def rhs(t,y):
            k,q=y;output=k**alpha*labor**(1-alpha)
            return [saving*output-(depreciation+g)*k,g]
        sol=solve_ivp(rhs,[0,horizon],[1.,0.],rtol=1e-10,atol=1e-12,method='DOP853',t_eval=np.linspace(0,horizon,301))
        if not sol.success or sol.y[0].min()<=0:raise ValueError('Capital benchmark violated positivity')
        residual=saving*kstar**alpha*labor**(1-alpha)-(depreciation+g)*kstar
        rows.append({'aid':aid,'research_share':i,'growth':g,'worst_burden':u.max(),'effective_labor':labor,'capital_ratio_equilibrium':kstar,'equilibrium_derivative':derivative,'equilibrium_residual':abs(residual),'minimum_capital_ratio':sol.y[0].min(),'budget_used':aid+i,'resource_account_share':consumption+budget+saving})
    return save('growth_benchmark.csv',rows)


def run_rollout_rates():
    """Same technological opportunity endpoints and exact spending for all rates.

    An adjustment allocation delta diverts resources from launch to aid.
    Opportunity paths are identical across allocations; implemented launch
    intensities differ because adjustment uses real resources.
    """
    rows=[]
    for rate in CONFIG['cultural_forcing_rates']:
        normalizer=np.tanh(P.horizon/2*rate)
        lo,hi=CONFIG['rollout_opportunity_endpoints']
        def opportunity(t):return lo+(hi-lo)*(np.tanh(rate*(t-P.horizon/2))+normalizer)/(2*normalizer)
        for delta in CONFIG['rollout_adjustment_allocations']:
            def nu(t):return opportunity(t)-P.capacity*delta
            def aid(t):return 1-nu(t)/P.capacity
            sol=simulate(aid,nu,points=601)
            out=metrics(sol)
            rows.append({'rollout_rate':rate,'adjustment_allocation':delta,'opportunity_initial':opportunity(0.),'opportunity_final':opportunity(P.horizon),'budget_used':1.,'launch_initial':nu(0.),'launch_final':nu(P.horizon),'aid_initial':aid(0.),'aid_final':aid(P.horizon),'admissible':out['growth']>=CONFIG['growth_floor'] and out['worst_burden']<=CONFIG['worst_group_exposure_cap'] and out['adoption_final']>=CONFIG['minimum_final_adoption'],**out})
    return save('rollout_rate_grid.csv',rows)


def main():
    start=time.perf_counter()
    countries,arrays,coordinates=load_distributions(ROOT/'inputs/culture_distributions.csv')
    audit=reproduce_audit(countries,arrays)
    print('Audit reproduced',audit,flush=True)
    reference=arrays['Survey'].mean(axis=0)
    save('pooled_reference_probabilities.csv',[{'question_id':q,'category_index':k,'probability':v} for q,b in zip(QUESTIONS,BLOCKS) for k,v in enumerate(reference[b])])
    critical=run_boundary_and_continuation()
    print('Critical points and continuation verified',flush=True)
    policy_menu,selected=run_policy_sets()
    run_error_direction_and_control(reference,coordinates)
    culture_checks=run_cultural_families(reference,coordinates)
    lag=run_lag_and_rate(reference,coordinates)
    benchmark=quality_replacement_benchmark()
    rollout=run_rollout_rates()
    actual=run_static_error_experiments(countries,arrays,coordinates)
    baseline=metrics(simulate(*policy_from_estimate(0.)))
    summary=[]
    for keys,group in actual.groupby(['items','shape','strength','model']):
        summary.append(dict(zip(['items','shape','strength','model'],keys))|{'profiles':len(group),'low_adoption_profiles':int((group.adoption_final<.5).sum()),'mean_growth_change':float(group.growth.mean()-baseline['growth']),'mean_worst_burden_change':float(group.worst_burden.mean()-baseline['worst_burden']),'min_growth_change':float(group.growth.min()-baseline['growth']),'max_growth_change':float(group.growth.max()-baseline['growth'])})
    save('audit_linked_summary.csv',summary)
    tolerance=[]
    for s in selected:
        ordinary=metrics(simulate(s['aid'],s['nu']))
        strict=metrics(simulate(s['aid'],s['nu'],tolerance=1e-11))
        tolerance.append(max(abs(ordinary[k]-strict[k]) for k in ordinary if k!='peak_worst'))
    mass=max(float(np.max(np.abs(a[:,b].sum(axis=1)-1))) for a in arrays.values() for b in BLOCKS)
    report={'status':'passed','scope':'Numerical and algebraic verification of specified mechanisms; no empirical economic calibration.','audit_reproduction':audit,'max_probability_mass_error':mass,'minimum_input_probability':min(float(a.min()) for a in arrays.values()),'max_fold_residual':float(critical.fold_residual.max()),'max_fold_zero_eigenvalue':float(critical.zero_eigenvalue.max()),'max_independent_fold_displacement':float(critical.independent_fold_displacement.max()),'max_independent_fold_residual':float(critical.independent_residual.max()),'max_cultural_mass_error':float(culture_checks.simplex_mass_error.max()),'max_cultural_metric_tolerance_difference':float(culture_checks.metric_tolerance_difference.max()),'max_policy_metric_tolerance_difference':max(tolerance),'common_budget_max_error':float(np.max(np.abs(actual.budget_used-1))),'policy_menu_size':len(policy_menu),'audit_linked_scenarios':len(actual),'culture_family_scenarios':45,'lag_rate_scenarios':len(lag),'rollout_rate_scenarios':len(rollout),'no_fold_control_states':108,'closed_resource_benchmark_residual':float(benchmark.equilibrium_residual.max()),'seconds':time.perf_counter()-start,'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'config_sha256':hashlib.sha256((ROOT/'parameters.json').read_bytes()).hexdigest()}
    assert report['max_fold_residual']<1e-8
    assert report['max_fold_zero_eigenvalue']<1e-7
    assert report['max_independent_fold_displacement']<1e-7
    assert report['max_cultural_mass_error']<1e-7
    assert report['max_cultural_metric_tolerance_difference']<2e-6
    assert report['common_budget_max_error']<1e-10
    (DATA/'numerical_checks.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
