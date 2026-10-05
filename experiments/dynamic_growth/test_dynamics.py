"""Physical, algebraic and counterexample checks for the dynamic extension."""
from pathlib import Path
from dataclasses import replace
import unittest
import numpy as np
import pandas as pd
from dynamics import (P, CONFIG, fold, gradient, equilibrium, jacobian,
    equilibria, continue_branch, steady_exposure, economic_derivative,
    simulate, metrics, policy_from_estimate)
from culture import (BLOCKS, load_distributions, culture_projection,
    simplex_tilt, cultural_derivative, simulate_culture)

ROOT=Path(__file__).resolve().parent

class MechanismTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.countries,cls.arrays,cls.coordinates=load_distributions(ROOT/'inputs/culture_distributions.csv')
        cls.reference=cls.arrays['Survey'].mean(axis=0)

    def test_all_six_marginals_have_unit_mass(self):
        for probabilities in self.arrays.values():
            self.assertGreaterEqual(probabilities.min(),0)
            for b in BLOCKS:
                np.testing.assert_allclose(probabilities[:,b].sum(axis=1),1,atol=1e-12)

    def test_zero_error_and_disabled_channel_are_exact_nulls(self):
        for shape in CONFIG['mapping_shapes']:
            np.testing.assert_array_equal(culture_projection(self.arrays['Survey'],self.arrays['Survey'],self.coordinates,shape),0)
            np.testing.assert_array_equal(culture_projection(self.arrays['GPT-5.5'],self.arrays['Survey'],self.coordinates,shape,strength=0),0)
        a,n=policy_from_estimate(0)
        self.assertAlmostEqual(a+n/P.capacity,1,places=12)

    def test_analytic_equilibrium_gradient_against_finite_difference(self):
        z,n,a=.31,1.05,.4;h=1e-6
        numeric=[(equilibrium(z+h,n,a)-equilibrium(z-h,n,a))/(2*h),(equilibrium(z,n+h,a)-equilibrium(z,n-h,a))/(2*h)]
        np.testing.assert_allclose(gradient(z,n,a),numeric,rtol=1e-8,atol=1e-9)

    def test_full_state_jacobian_against_finite_difference(self):
        z,n,a=.31,1.05,.4;state=np.r_[z,steady_exposure(z,n,a)];h=1e-6
        def vector(y):
            dz,du,_=economic_derivative(y[0],y[1:],n,a)
            return np.r_[dz,du]
        numeric=np.column_stack([(vector(state+np.eye(3)[k]*h)-vector(state-np.eye(3)[k]*h))/(2*h) for k in range(3)])
        np.testing.assert_allclose(jacobian(z,n,a),numeric,rtol=1e-8,atol=1e-9)

    def test_fold_has_one_zero_and_two_stable_modes(self):
        for a in [0,.3,.65]:
            z,n=fold(a)
            self.assertLess(abs(equilibrium(z,n,a)),1e-10)
            self.assertLess(abs(gradient(z,n,a)[0]),1e-10)
            eig=np.sort(np.linalg.eigvals(jacobian(z,n,a)).real)
            self.assertLess(abs(eig[-1]),1e-9)
            self.assertLess(eig[-2],0)

    def test_continuation_passes_folds_and_keeps_unstable_states(self):
        branch=pd.DataFrame(continue_branch())
        self.assertTrue(branch.stable.any())
        self.assertTrue((~branch.stable).any())
        self.assertLess(branch.residual.max(),1e-9)
        differences=np.diff(branch.nu)
        self.assertTrue((differences>0).any() and (differences<0).any())

    def test_no_fold_control_has_unique_stable_equilibria(self):
        p=replace(P,b=-1)
        for a in [0,.4,.8]:
            for n in [.1,.8,1.6]:
                roots=equilibria(n,a,p=p)
                self.assertEqual(len(roots),1)
                self.assertLess(gradient(roots[0],n,a,p)[0],0)
                self.assertLess(np.linalg.eigvals(jacobian(roots[0],n,a,p)).real.max(),0)

    def test_mass_preservation_and_inward_probability_flow(self):
        probabilities=np.array([self.reference,self.reference])
        for family in ['C0','C1','C2','C3','C4']:
            dp=cultural_derivative(25,probabilities,[.4,.2],[.3,.2],self.reference,self.coordinates,family)
            for b in BLOCKS:
                np.testing.assert_allclose(dp[:,b].sum(axis=1),0,atol=1e-14)
        tilted=simplex_tilt(self.reference,self.coordinates,-1)
        for b in BLOCKS:self.assertAlmostEqual(tilted[b].sum(),1,places=13)
        self.assertGreaterEqual(tilted.min(),0)

    def test_cultural_feedback_paths_stay_on_each_simplex(self):
        for family in ['C2','C4']:
            _,out,probabilities=simulate_culture(self.reference,self.coordinates,family)
            self.assertLess(out['mass_error'],1e-10)
            self.assertGreaterEqual(probabilities.min(),-1e-12)

    def test_rejects_resource_overspending(self):
        with self.assertRaises(ValueError):simulate(.6,1.1)

    def test_same_error_size_has_positive_negative_and_zero_directions(self):
        d=pd.read_csv(ROOT/'results/equal_distance_directions.csv')
        self.assertLess(d.mean_item_TVD.max()-d.mean_item_TVD.min(),1e-12)
        self.assertTrue((d.projection>0).any() and (d.projection<0).any())
        self.assertTrue(np.isclose(d.projection,0).any())

    def test_rollout_includes_terminal_adoption_and_null_allocations(self):
        d=pd.read_csv(ROOT/'results/rollout_rate_grid.csv')
        expected=(d.growth>=.1)&(d.worst_burden<=.5)&(d.adoption_final>=.5)
        np.testing.assert_array_equal(d.admissible,expected)
        self.assertEqual(int(d[np.isclose(d.adjustment_allocation,.025)].admissible.sum()),3)
        self.assertEqual(int(d[np.isclose(d.adjustment_allocation,0)].admissible.sum()),0)
        self.assertEqual(int(d[np.isclose(d.adjustment_allocation,.05)].admissible.sum()),0)
        np.testing.assert_allclose(d.aid_initial+d.launch_initial/P.capacity,1,atol=1e-12)
        np.testing.assert_allclose(d.aid_final+d.launch_final/P.capacity,1,atol=1e-12)

    def test_capital_benchmark_closes_resources_and_is_stable(self):
        d=pd.read_csv(ROOT/'results/growth_benchmark.csv')
        np.testing.assert_allclose(d.resource_account_share,1,atol=1e-12)
        self.assertGreater(d.capital_ratio_equilibrium.min(),0)
        self.assertLess(d.equilibrium_derivative.max(),0)
        self.assertLess(d.equilibrium_residual.max(),1e-12)

if __name__=='__main__':unittest.main(verbosity=2)
