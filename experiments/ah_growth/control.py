"""Discounted Poisson Bellman equation, solved by monotone policy iteration.

V(A,u)=A v(u); innovation contributes (gamma-1)*chi*n*v, NOT
log(gamma)*chi*n*v. Transition needs use the declared fluid law.
The control discretization is refined and verified; it is not a global
continuous-control theorem or a static-policy grid comparison.
"""
from dataclasses import replace
import time
import numpy as np
from scipy.sparse import coo_matrix,eye
from scipy.sparse.linalg import spsolve
from scipy.interpolate import RegularGridInterpolator
from model import P,burden_step,production


class BellmanSolver:
    def __init__(self,p=P,size=41,aid_points=31,research_points=31,dt=.5):
        self.p=p;self.size=size;self.dt=dt
        self.grid=np.linspace(0,1,size)
        self.uv=np.array(np.meshgrid(self.grid,self.grid,indexing='ij')).reshape(2,-1)
        if p.capacity<=0 or p.aid_labor<0 or not dt>0:
            raise ValueError('Positive capacity/time step and nonnegative aid cost required')
        max_a=min(1.,p.capacity/p.aid_labor) if p.aid_labor else 1.
        aa,rr=np.meshgrid(np.linspace(0,max_a,aid_points),np.linspace(0,1,research_points),indexing='ij')
        self.a=aa.ravel();self.n=rr.ravel()*(p.capacity-p.aid_labor*self.a)
        self.discount=np.exp(-(p.rho-p.q*p.chi*self.n)*dt)
        if np.max(self.discount)>=1:raise ValueError('Bellman contraction fails under declared control bounds')
        self.S=size**2;self.C=len(self.a)
        u1=burden_step(self.uv[:,None,:],self.n[:,None],self.a[:,None],dt,p)
        pos=u1*(size-1)
        ij=np.minimum(np.maximum(np.floor(pos).astype(int),0),size-2)
        f=pos-ij
        self.indices=np.stack((ij[0]*size+ij[1],(ij[0]+1)*size+ij[1],
                               ij[0]*size+ij[1]+1,(ij[0]+1)*size+ij[1]+1),axis=-1).astype(np.int32)
        self.weights=np.stack(((1-f[0])*(1-f[1]),f[0]*(1-f[1]),
                               (1-f[0])*f[1],f[0]*f[1]),axis=-1)
        # Three-point Gaussian quadrature for the one-step running reward.
        nodes,weights=np.polynomial.legendre.leggauss(3)
        self.reward=np.zeros((self.C,self.S));self.output_reward=self.reward.copy();self.exposure_reward=self.reward.copy()
        for t,w in zip((nodes+1)*dt/2,weights*dt/2):
            u=burden_step(self.uv[:,None,:],self.n[:,None],self.a[:,None],t,p)
            Y=production(u,self.n[:,None],self.a[:,None],p)[1]
            fac=np.exp(-(p.rho-p.q*p.chi*self.n[:,None])*t)*w
            self.output_reward+=fac*Y
            self.exposure_reward+=fac*np.max(u,axis=0)
        self.reward=self.output_reward-p.omega*self.exposure_reward
        self.rows=np.repeat(np.arange(self.S),4)

    def action_values(self,v,reward=None):
        reward=self.reward if reward is None else reward
        cont=sum(self.weights[:,:,k]*v[self.indices[:,:,k]] for k in range(4))
        return reward+self.discount[:,None]*cont

    def evaluate(self,policy,reward=None,discount=None):
        reward=self.reward if reward is None else reward
        discount=self.discount if discount is None else discount
        col=self.indices[policy,np.arange(self.S)].ravel()
        w=self.weights[policy,np.arange(self.S)]*discount[policy,None]
        trans=coo_matrix((w.ravel(),(self.rows,col)),shape=(self.S,self.S)).tocsr()
        return spsolve(eye(self.S,format='csr')-trans,reward[policy,np.arange(self.S)])

    def solve(self,tolerance=1e-9,maxiter=100):
        started=time.perf_counter();v=np.zeros(self.S);policy=np.argmax(self.reward,axis=0)
        for it in range(maxiter):
            v=self.evaluate(policy)
            Q=self.action_values(v);new=np.argmax(Q,axis=0)
            residual=float(np.max(np.abs(Q.max(axis=0)-v)))
            if residual<tolerance:break
            policy=new
        else:raise RuntimeError('Howard policy iteration failed')
        self.value=v.reshape(self.size,self.size);self.policy=policy
        self.n_grid=self.n[policy].reshape(self.size,self.size)
        self.a_grid=self.a[policy].reshape(self.size,self.size)
        self.interp_n=RegularGridInterpolator((self.grid,self.grid),self.n_grid,bounds_error=False,fill_value=None)
        self.interp_a=RegularGridInterpolator((self.grid,self.grid),self.a_grid,bounds_error=False,fill_value=None)
        self.interp_v=RegularGridInterpolator((self.grid,self.grid),self.value,bounds_error=False,fill_value=None)
        self.report=dict(grid=self.size,controls=self.C,dt=self.dt,iterations=it+1,
                         bellman_residual=residual,max_discount=float(self.discount.max()),
                         value_initial=float(self.interp_v([self.p.initial])[0]),seconds=time.perf_counter()-started,
                         maximum_research_budget_violation=float(np.max(self.n+self.p.aid_labor*self.a-self.p.capacity)),
                         minimum_interpolation_weight=float(self.weights.min()),
                         maximum_interpolation_row_sum_error=float(np.max(np.abs(self.weights.sum(axis=-1)-1))))
        return self

    def controls(self,u):
        u=np.clip(np.asarray(u),0,1)
        return float(self.interp_n([u])[0]),float(self.interp_a([u])[0])

    def patent_values(self):
        """Linear asset-pricing equation along the solved feedback controls."""
        p=self.p;reward=np.zeros((self.C,self.S));nodes,weights=np.polynomial.legendre.leggauss(3)
        for t,w in zip((nodes+1)*self.dt/2,weights*self.dt/2):
            u=burden_step(self.uv[:,None,:],self.n[:,None],self.a[:,None],t,p)
            pi=production(u,self.n[:,None],self.a[:,None],p)[4]
            reward+=np.exp(-(p.rho+p.chi*self.n[:,None])*t)*w*pi
        discount=np.exp(-(p.rho+p.chi*self.n)*self.dt)
        v=self.evaluate(self.policy,reward,discount).reshape(self.size,self.size)
        return v


if __name__=='__main__':
    import json
    s=BellmanSolver().solve();print(json.dumps(s.report,indent=2))
    print('initial controls',s.controls(P.initial))
