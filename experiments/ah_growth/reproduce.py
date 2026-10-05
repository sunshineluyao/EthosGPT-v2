"""Recompute metrics/paths in isolation; saved Bellman values remain inputs."""
from pathlib import Path
import argparse, json, shutil, subprocess, sys, tempfile
import numpy as np
import pandas as pd
from verify_results import verify

ROOT=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--refresh-metrics',action='store_true')
    parser.add_argument('--receipt',type=Path);args=parser.parse_args();receipt=verify()
    if args.refresh_metrics:
        with tempfile.TemporaryDirectory(prefix='ethos-structural-') as td:
            dst=Path(td)/'ah_growth';shutil.copytree(ROOT,dst,ignore=shutil.ignore_patterns('figures','__pycache__'))
            for f in (dst/'country_revision_results').glob('metrics-*.json'):f.unlink()
            subprocess.run([sys.executable,str(dst/'country_revision_compute.py')],check=True)
            comparisons={}
            specifications={
              'country-policy-comparisons.csv':(['country','policy','source'],['G','g_log','mean_quality','Ubar','Umax','average_output']),
              'matched-sensitivity.csv':(['country','variable','value'],['G','g_log','mean_quality','Ubar','Umax','average_output']),
              'country-refinement.csv':(['country','grid','control_points','dt'],['G','g_log','mean_quality','Ubar','Umax','average_output']),
              'three-country-upgrade-comparison.csv':(['country'],['upgrade_change_G','upgrade_change_Umax','upgrade_absolute_bias_change_G','upgrade_absolute_bias_change_Umax'])}
            for file,(keys,metrics) in specifications.items():
                x=pd.read_csv(ROOT/'country_revision_results'/file).set_index(keys).sort_index()
                y=pd.read_csv(dst/'country_revision_results'/file).set_index(keys).sort_index()
                assert x.index.equals(y.index),(file,'row keys differ')
                err=float(np.max(np.abs(x[metrics].to_numpy()-y[metrics].to_numpy())))
                assert err<1e-8,(file,err);comparisons[file]={'rows':len(x),'max_absolute_metric_difference':err}
            receipt['fresh_path_and_metric_comparisons']=comparisons
            receipt['saved_values_reused']=True
    if args.receipt:args.receipt.parent.mkdir(parents=True,exist_ok=True);args.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
