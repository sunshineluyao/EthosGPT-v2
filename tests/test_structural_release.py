"""Corrupted scientific contrasts or paths must fail the structural contract."""
from pathlib import Path
import shutil, subprocess, sys
import pandas as pd
import pytest

SOURCE=Path(__file__).resolve().parents[1]/'experiments/ah_growth'

@pytest.mark.parametrize('file,column,change',[
 ('three-country-upgrade-comparison.csv','upgrade_change_G',.01),
 ('country-paths.csv','instantaneous_g_log',.01),
 ('matched-sensitivity.csv','control_points',-1),
])
def test_altered_structural_evidence_is_rejected(tmp_path,file,column,change):
    destination=tmp_path/'ah_growth'
    shutil.copytree(SOURCE,destination,ignore=shutil.ignore_patterns('figures','__pycache__'))
    path=destination/'country_revision_results'/file
    table=pd.read_csv(path);table.loc[0,column]+=change;table.to_csv(path,index=False)
    result=subprocess.run([sys.executable,str(destination/'verify_results.py')],capture_output=True,text=True)
    assert result.returncode!=0,'Altered governed scientific result was accepted'
