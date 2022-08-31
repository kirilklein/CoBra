#%%
import os
from os.path import join, split
import shutil
import pandas as pd
#%%
csv_path = "C:\\Users\\kiril\\OneDrive - University of Copenhagen\\Cobra\\CMB_paper"
df = pd.read_csv(join(csv_path,"included_nii_v5_names.csv"))
for idx, row in df.iterrows():
    old_path = split(split(row.old_path)[0])[0]
    src_path = join('Y:\\', old_path, 'DOC')
    mri_name = row.new_name
    dst_path = join("G:\\CoBra\\Data\\swi_nii\\cmb_study\\reports", 
                    mri_name[:-7])
    #if not os.path.exists(dst_path):
    #    os.makedirs(dst_path)
    try:
        shutil.copytree(src_path, dst_path)
    except: pass
    # copy all files from src_path to dst_path 
    #
    # if dst_path does not exist, create it
    
#%%
df_cases = pd.read_csv(join(csv_path,"cases_v5.csv"))
