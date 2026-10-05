"""Full marginal response distributions with mass-preserving cultural dynamics.

Country labels identify the source of measured error vectors only. Two
synthetic adjustment groups are not estimated demographic populations.
"""
import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator
from scipy.special import softmax
from scipy.integrate import solve_ivp
from dynamics import P,CONFIG,economic_derivative,metrics,policy_from_estimate

QUESTIONS=['Q48','Q57','Q106','Q108','Q121','Q159']
WEIGHTS=np.array(CONFIG['mapping_weights'])
SIZES=[10,2,10,10,5,10]
OFFSETS=np.r_[0,np.cumsum(SIZES)]
BLOCKS=[slice(OFFSETS[i],OFFSETS[i+1]) for i in range(6)]
SPLINE=PchipInterpolator(CONFIG['spline_knots'],CONFIG['spline_values'])


def load_distributions(path):
    df=pd.read_csv(path)
    countries=sorted(df.country.unique())
    arrays={}
    coordinates=[]
    for q in QUESTIONS:
        d=df[(df.country==countries[0])&(df.source=='Survey')&(df.question_id==q)].sort_values('category')
        coordinates.append(2*d.normalized_direction.to_numpy()-1)
    for source in ['Survey','GPT-5.5','GPT-5.6 Sol']:
        arrays[source]=np.array([np.concatenate([df[(df.country==c)&(df.source==source)&(df.question_id==q)].sort_values('category').probability.to_numpy() for q in QUESTIONS]) for c in countries])
    return countries,arrays,coordinates


def transform(coordinates,shape):
    if shape=='linear':return coordinates
    if shape=='saturating':return [np.tanh(2*x)/np.tanh(2) for x in coordinates]
    if shape=='spline':return [SPLINE(x) for x in coordinates]
    raise ValueError(shape)


def culture_projection(distributions,anchor,coordinates,shape='linear',strength=1.,clean_items=False):
    """Assumed response channel, centered at its survey reference; not culture rank."""
    coefficients=WEIGHTS.copy()
    if clean_items:
        coefficients[[2,3,4]]=0
        coefficients/=np.abs(coefficients).sum()
    phi=transform(coordinates,shape)
    differences=np.stack([np.sum((distributions[...,block]-anchor[...,block])*v,axis=-1) for block,v in zip(BLOCKS,phi)],axis=-1)
    return strength*np.sum(differences*coefficients,axis=-1)


def simplex_tilt(reference,coordinates,amplitude):
    """Positive, normalized change; no person-level joint distribution assumed."""
    out=reference.copy()
    for block,x in zip(BLOCKS,coordinates):
        v=reference[block]*np.exp(amplitude*x)
        out[block]=v/v.sum()
    return out


def cultural_derivative(t,probabilities,exposures,memory,reference,coordinates,family):
    if family=='C0':return np.zeros_like(probabilities)
    # Continuous-time Markov drift toward a specified distribution.
    targets=np.array([simplex_tilt(reference,coordinates,v) for v in CONFIG['culture_target_tilts']])
    if family=='C4' and CONFIG['culture_shock_interval'][0]<=t<=CONFIG['culture_shock_interval'][1]:
        targets=np.array([simplex_tilt(reference,coordinates,v) for v in CONFIG['culture_shock_tilts']])
    dp=CONFIG['cultural_markov_rate']*(targets-probabilities)
    if family in ['C2','C3','C4']:
        burden=memory if family=='C4' else exposures
        for group in range(2):
            # Exposed groups can change their responses; coefficients are assumed.
            for j,(block,x) in enumerate(zip(BLOCKS,coordinates)):
                sign=-1. if j in [0,4,5] else 1.
                reward=sign*(burden[group]-.25)*x
                pg=probabilities[group,block]
                dp[group,block]+=CONFIG['cultural_feedback_rate']*pg*(reward-np.dot(pg,reward))
    if family in ['C3','C4']:
        dp+=CONFIG['cultural_network_rate']*(probabilities[::-1]-probabilities)
    return dp


def simulate_culture(reference,coordinates,family='C0',shape='linear',aid=.493757,nu=1.214983,tolerance=1e-9,p=P):
    """Shared initial culture/law and resource budget for every compared policy."""
    initial=np.r_[CONFIG['initial_state'],np.tile(reference,2),CONFIG['initial_state'][1:3]]
    count=len(reference)
    def rhs(t,y):
        probs=y[6:6+2*count].reshape(2,count)
        c=float(np.mean(culture_projection(probs,reference,coordinates,shape)))
        dz,du,dq=economic_derivative(y[0],y[1:3],nu,aid,c,p)
        dp=cultural_derivative(t,probs,y[1:3],y[-2:],reference,coordinates,family)
        dm=(y[1:3]-y[-2:])/CONFIG['cultural_memory_time']
        return np.r_[dz,du,dq,y[1:3],dp.ravel(),dm]
    # Split at known shock times so adaptive integration cannot skip the pulse.
    breaks=[0,*CONFIG['culture_shock_interval'],p.horizon] if family=='C4' else [0,p.horizon]
    all_t=[];all_y=[];current=initial
    for start,end in zip(breaks[:-1],breaks[1:]):
        times=np.linspace(start,end,int((end-start)*10)+1)
        sol=solve_ivp(rhs,[start,end],current,t_eval=times,method='DOP853',rtol=tolerance,atol=tolerance*.1,max_step=.5)
        if not sol.success:raise RuntimeError(sol.message)
        all_t.extend(sol.t if not all_t else sol.t[1:]);all_y.extend((sol.y if not all_y else sol.y[:,1:]).T)
        current=sol.y[:,-1]
    from types import SimpleNamespace
    sol=SimpleNamespace(t=np.array(all_t),y=np.array(all_y).T)
    probs=sol.y[6:6+2*count].T.reshape(-1,2,count)
    mass=max(float(np.max(np.abs(probs[:,:,block].sum(axis=-1)-1))) for block in BLOCKS)
    if mass>1e-7 or probs.min()<-1e-9:raise ValueError('Probability simplex violation')
    out=metrics(sol)
    out.update({'mass_error':mass,'minimum_probability':float(probs.min()),'culture_final':float(np.mean(culture_projection(probs[-1],reference,coordinates,shape))),'budget_used':aid+nu/p.capacity})
    return sol,out,probs
