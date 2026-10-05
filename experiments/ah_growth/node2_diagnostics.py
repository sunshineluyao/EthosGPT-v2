"""Evaluate the Bellman scheme using the same held controls between decisions.

Re-optimizing actions at the actual state avoids interpolation of discontinuous
control maps. State interpolation is still a numerical approximation.
"""
from pathlib import Path
from dataclasses import replace
from types import SimpleNamespace
import gc,json
import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator
from model import burden_step,production,path_metrics
from node2 import OUT,INITIALS,conditional_parameters,js,progress,save_solver
from control import BellmanSolver

class HeldPolicy:
    def __init__(self,p,grid,value,points,dt):
        self.p=p;self.dt=dt;self.iv=RegularGridInterpolator((grid,grid),value)
        maxa=min(1.,p.capacity/p.aid_labor) if p.aid_labor else 1.
        aa,rr=np.meshgrid(np.linspace(0,maxa,points),np.linspace(0,1,points),indexing='ij')
        self.a=aa.ravel();self.n=rr.ravel()*(p.capacity-p.aid_labor*self.a)
        self.disc=np.exp(-(p.rho-p.q*p.chi*self.n)*dt)
        self.nodes,self.weights=np.polynomial.legendre.leggauss(5)
    def action(self,u):
        p=self.p;dt=self.dt
        u=np.asarray(u)[:,None];reward=np.zeros_like(self.n)
        for t,w in zip((self.nodes+1)*dt/2,self.weights*dt/2):
            ut=burden_step(u,self.n,self.a,t,p)
            reward+=w*np.exp(-(p.rho-p.q*p.chi*self.n)*t)*(production(ut,self.n,self.a,p)[1]-p.omega*np.max(ut,axis=0))
        un=burden_step(u,self.n,self.a,dt,p)
        Q=reward+self.disc*self.iv(np.clip(un.T,0,1))
        j=int(np.argmax(Q))
        return self.n[j],self.a[j]
    def value(self,u):return float(self.iv([u])[0])

def rollout(policy,initial,end=100.):
    p=policy.p;dt=policy.dt;state=np.r_[initial,0.,1.,0.,0.,0.,0.]
    times=[0.];states=[state.copy()];controls=[]
    nodes,weights=np.polynomial.legendre.leggauss(7)
    for j in range(int(round(end/dt))):
        t=j*dt;u=state[:2].copy();K=state[3];n,a=policy.action(u);lam=p.chi*n
        controls.append((n,a))
        increments=np.zeros(4)
        for z,w in zip((nodes+1)*dt/2,weights*dt/2):
            uz=burden_step(u,n,a,z,p);Kz=K*np.exp(p.q*lam*z)
            Y=production(uz,n,a,p)[1]
            increments[:2]+=w*uz
            increments[2]+=w*np.exp(-p.rho*(t+z))*Kz*(Y-p.omega*np.max(uz))
            increments[3]+=w*Kz*Y
        state[:2]=burden_step(u,n,a,dt,p)
        state[2]+=np.log(p.gamma)*lam*dt;state[3]*=np.exp(p.q*lam*dt)
        state[4:]+=increments
        times.append(t+dt);states.append(state.copy())
    controls.append(policy.action(state[:2]))
    return SimpleNamespace(t=np.array(times),y=np.array(states).T,controls=np.array(controls))

def metrics(sol,policy):
    m=path_metrics(sol);p=policy.p;H=sol.t[-1]
    tail=np.exp(-p.rho*H)*sol.y[3,-1]*policy.value(sol.y[:2,-1])
    v0=policy.value(sol.y[:2,0]);direct=m['welfare_to_T']+tail
    take=sol.t>=80
    m.update(value_initial=v0,rollout_value_plus_tail=direct,rollout_relative_value_error=abs(direct/v0-1),
        terminal_n_min=sol.controls[take,0].min(),terminal_n_max=sol.controls[take,0].max(),
        terminal_a_min=sol.controls[take,1].min(),terminal_a_max=sol.controls[take,1].max(),
        late_u_A_min=sol.y[0,take].min(),late_u_A_max=sol.y[0,take].max(),
        late_u_B_min=sol.y[1,take].min(),late_u_B_max=sol.y[1,take].max())
    return m

def main():
    refinement=[];paths=[];initials=[]
    for country in ['China','Germany','Kenya']:
        p,_=conditional_parameters(country)
        for size,points,dt in [(41,31,.5),(61,41,.25),(81,61,.25),(101,61,.125)]:
            file=OUT/f'policy-{country}-{size}-{points}-{dt:g}.npz'
            z=np.load(file);policy=HeldPolicy(p,z['grid'],z['value'],points,dt)
            sol=rollout(policy,p.initial)
            refinement.append(dict(country=country,grid=size,control_points=points,dt=dt,**metrics(sol,policy)))
            if size==101:
                for initial in INITIALS:
                    sol=rollout(policy,initial);initials.append(dict(country=country,initial_u_A=initial[0],initial_u_B=initial[1],**metrics(sol,policy)))
                    for j,t in enumerate(sol.t):
                        n,a=sol.controls[j];u=sol.y[:2,j]
                        paths.append(dict(country=country,policy='planner held optimal control',source='physical-economy benchmark',
                            initial_u_A=initial[0],initial_u_B=initial[1],t=t,u_A=u[0],u_B=u[1],n=n,a=a,
                            log_quality=sol.y[2,j],mean_quality=sol.y[3,j],expected_output=sol.y[3,j]*production(u,n,a,p)[1]))
        progress('Bellman-consistent rollout',country=country,latest=refinement[-1])
    pd.DataFrame(refinement).to_csv(OUT/'held-control-refinement.csv',index=False)
    pd.DataFrame(paths).to_csv(OUT/'held-optimal-paths.csv',index=False)
    pd.DataFrame(initials).to_csv(OUT/'held-initial-state-convergence.csv',index=False)
    # Replace coarse sensitivity conclusions with finer, scheme-consistent rollouts.
    sensitivity=[]
    variations=[('q',x) for x in [.06,.08,.12,.16]]+[('theta',x) for x in [.94,.95,.97]]+[
        ('omega',x) for x in [0.,.15,.30,.60,.90]]+[('aid_labor',x) for x in [.02,.04,.06]]+[
        ('recovery_multiplier',x) for x in [.5,1.,2.]]+[('capacity_multiplier',x) for x in [.75,1.,1.25]]
    for country in ['China','Germany','Kenya']:
        p,_=conditional_parameters(country)
        for variable,value in variations:
            pp=replace(p,recovery=tuple(value*np.array(p.recovery))) if variable=='recovery_multiplier' else (
                replace(p,capacity=value*p.capacity) if variable=='capacity_multiplier' else replace(p,**{variable:value}))
            size,points,dt=(101,41,.125) if country=='Kenya' else (61,41,.25)
            s=BellmanSolver(pp,size=size,aid_points=points,research_points=points,dt=dt).solve()
            policy=HeldPolicy(pp,s.grid,s.value,points,dt);n,a=policy.action(pp.initial)
            save_solver(s,OUT/f'refined-sensitivity-policy-{country}-{variable}-{value:g}.npz')
            residual=s.report['bellman_residual'];del s;gc.collect()
            sol=rollout(policy,pp.initial)
            sensitivity.append(dict(country=country,variable=variable,value=value,n_initial=n,a_initial=a,
                grid=size,control_points=points,dt=dt,bellman_residual=residual,**metrics(sol,policy)))
        progress('refined comparative statics',country=country)
    pd.DataFrame(sensitivity).to_csv(OUT/'refined-comparative-statics.csv',index=False)
    (OUT/'held-control-method.json').write_text(json.dumps(dict(
        primary_policy='Re-optimize the discrete Bellman action at the actual state; hold it for dt; integrate physical states exactly and rewards with 7-point quadrature',
        purpose='Avoid artificial attractors introduced by bilinear interpolation of discontinuous control maps',
        limitations=['Finite state/action grids and held-decision time interval remain approximations',
          'Small action switching bands are reported as bands rather than a falsely exact stationary point',
          'Off-grid Bellman value interpolation remains and convergence must be inspected',
          'State-dependent market implementation was priced for the interpolated feedback, not this newly diagnosed held-control policy']),indent=2)+'\n')

if __name__=='__main__':main()
