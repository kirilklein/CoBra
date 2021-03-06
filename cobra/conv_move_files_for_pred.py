#%%
import shutil
import sys
import os
from os.path import join, split
from pathlib import Path
import pandas as pd
import numpy as np
import gzip
import multiprocessing as mp
from dcm2nii import dcm2nii
from datetime import datetime as dt
import time
import json
import pickle
from utilities import basic, fix_dcm_incomplete_vols
from pydicom import dcmread
from utilities.basic import get_dir, make_dir, remove_file, get_part_of_path, get_proc_id
#%%
# define directories
print("Define directories")
disk_data_dir = join("F:\\", 'CoBra', 'Data')
dcm_base_dir = join(disk_data_dir, 'dcm')
disk_nii_dir = join(disk_data_dir, 'nii')
pred_input_dir = ""#join(disk_data_dir, 'volume_longitudinal_nii', 'input')
nii_base_pred_dir = ""#join(pred_input_dir, 'cases') 
print("gzipped niis will be stored at: ", nii_base_pred_dir)
sif_dir = 'Y:\\' 
script_dir = os.path.realpath(__file__)
base_dir = Path(script_dir).parent
data_dir = join(base_dir, 'data')
table_dir = join(data_dir, 'tables')
pat_groups_dir = join(data_dir, 'patient_groups')

# load helper files
print("Load helper files")
df_volume_dir = pd.read_csv(join(table_dir, 'series_directories.csv')) #contains sif directories for sids
sif_volume_dir_dic = pd.Series(
        df_volume_dir.Directory.values, index=df_volume_dir.SeriesInstanceUID)\
            .to_dict()
with open(join(table_dir, "disk_series_directories.json"), "r") as json_file:
    disk_volume_dir_dic_dcm = json.load(json_file)
with open(join(table_dir, "disk_series_directories_niis.json"), "r") as json_file:
    disk_volume_dir_dic_nii = json.load(json_file)

##################Currently not used#############################################
def check_niis(existing_src_files, src_dir, tgt_path, test, trial):
    """Currently not used. Checks existig_src_files (niis), if 2 files keep the one with _i00002.nii ending,
    else remove all"""
    if trial==0:
        if test:
            log_("Following nii file(s) were found " + str(existing_src_files))
            log_("Move and gz compress these files")
        if len(existing_src_files)==1: # if only 1 file it is probably the 3d vol.
            sys.stdout.flush()
            print(".", end='')
            basic.move_compress(join(src_dir, existing_src_files[0]), tgt_path)
            return 0
        elif len(existing_src_files)==2: # if 2 files, the one with _i00002.nii is probably the 3d vol.
            files3d = [f for f in existing_src_files if f.endswith("_i00002.nii")]
            if len(files3d)==1:
                sys.stdout.flush()
                print(".", end='')
                basic.move_compress(join(src_dir, files3d[0]), tgt_path)
            else: # otherwise remove all the files and call the function again
                for ex_src_file in existing_src_files:
                    remove_file(join(src_dir, ex_src_file))
                return 1
        else: # if more than 2 files, also remove them
            for ex_src_file in existing_src_files:
                    remove_file(join(src_dir, ex_src_file))
            return 1
    else:
        if len(existing_src_files)==1:
            basic.move_compress(join(src_dir, existing_src_files[0]), tgt_path)
        else:
            for i, ex_src_file in enumerate(existing_src_files):
                tgt_path_tmp = tgt_path[:-7] + '_' + str(i) + '.nii.gz'
                basic.move_compress(join(src_dir, ex_src_file), tgt_path_tmp)
        sys.stdout.flush()
        print(".", end='')
        return 0
####################################################################################

#######################Only for test purposes#######################################
dfc = pd.read_csv(join(table_dir, "neg_pos_clean.csv"), 
    usecols=['SeriesInstanceUID', 'PatientID', 'MRAcquisitionType',
    'Sequence', 'NumberOfSlices'])
sids_3d_t1_path = join(data_dir, 't1_longitudinal', 'pairs_3dt1_long_sids.pkl')
with open(sids_3d_t1_path, 'rb') as f:
    sids_3dt1_long = pickle.load(f)
df_3dt1_long = dfc[dfc.SeriesInstanceUID.isin(sids_3dt1_long)]
sids_cases = np.loadtxt(join(pat_groups_dir, 
                't1_pre_post_suid.txt'), dtype=str).tolist()
sids_3d_t1_long_cases = list(set(sids_3dt1_long).intersection(set(sids_cases)))
print('num cases: ',len(sids_3d_t1_long_cases))
sids_3d_t1_long_controls = list(set(sids_3dt1_long).difference(set(sids_cases)))
print('num controls: ',len(sids_3d_t1_long_controls))
df_cases = dfc[dfc.SeriesInstanceUID.isin(sids_3d_t1_long_cases)]
sids_cases_ls = list(df_cases.SeriesInstanceUID)
df_controls = dfc[(dfc.SeriesInstanceUID.isin(sids_3d_t1_long_controls))]
sids_controls_ls = list(df_controls.SeriesInstanceUID)
###################################################################################

########################functions##########################################
def write_problematic_files(file, test):
    """Write path of file to log"""
    if test:
        return 0
    current_proc_id = get_proc_id(test)
    write_file = join(
            pred_input_dir, 'logs', 
            current_proc_id+'nii_conversion_error_sids.txt')
    with open(write_file,'a+') as f:
        f.write(file+'\n')

def dcm2nii_safe(disk_dcm_path, nii_out_path, sid, test,  timeout=2000):
    "Only keeps niis if dcm2nii converter returns 0"
    if test:
            log_(disk_dcm_path + " exists, start nii conversion")
            start=time.time()
    print(get_proc_id(test), " Convert from disk")
    dcm2nii_out = dcm2nii.convert_dcm2nii(
        disk_dcm_path, nii_out_path, verbose=0, op_sys=0,
                output_filename='%j', create_info_json='n', gz_compress='y',
                timeout=timeout)
    if test:
            log_("The conversion took "+str(round(time.time()-start,3))+'s')
            if dcm2nii_out==1:
                log_("conversion from disk fail")
            else:
                log_("conversion from disk success")
    
    if dcm2nii_out==0:
        print(get_proc_id(test), " worked")
        return 0
    else: #if dcm2nii produces error, remove all the output files
        if not test:
                write_problematic_files(disk_dcm_path, test)
        print("Remove output files")
        rm_files = [f for f in os.listdir(nii_out_path) if f.startswith(sid)]
        for rm_file in rm_files:
            remove_file(rm_file)
            return 1 

def summarize_problematic_files():
    """Convert the log files from individual processes to one final log file"""
    dir_ = join(pred_input_dir, 'logs')
    error_log_files = [f for f in basic.list_subdir(dir_) \
        if f.endswith("error_sids.txt")]
    string = ''
    for error_log_file in error_log_files:
        with open(error_log_file, 'r') as f:
            string+=f.read()
    with open(join(dir_, 'nii_conversion_error_sids_all.txt'), 'a+') as f:
        f.write(string)



def log_(str_):
    """Used for testing, writes log to move_files_for_pred_log.txt"""
    with open(join(base_dir, "move_files_for_pred_log.txt"), 'a+') as f:
        f.write(str_+'\n')

def check_tgt_files(tgt_path, sid):
    """Checks tgt dir for files starting with sid"""
    tgt_dir = get_dir(tgt_path)
    if len([f for f in os.listdir(tgt_dir) if f.startswith(sid)])>0:
        return True
    else:
        return False

def check_dicoms(src_path, sif_src_path):
    """Checks whether all the dcm files from sif were downloaded."""
    if len(os.listdir(src_path))==len(os.listdir(sif_src_path)):
        return 0
    else: return 1

def move_missing_files(src_path, sif_src_path):
    """Downloads missing dcm files form sif"""
    assert len(os.listdir(src_path))<len(os.listdir(sif_src_path)), f'There are less files on sif than on disk {src_path}'
    disk_filenames = [f for f in os.listdir(src_path) if f.endswith('.dcm')]
    sif_filenames = [f for f in os.listdir(sif_src_path) if f.endswith('.dcm')]
    add_filenames = list(set(sif_filenames).difference(set(disk_filenames)))
    src_tgt_ls = [(join(sif_src_path, f), join(src_path, f)) for f in add_filenames]
    for src_tgt in src_tgt_ls:
        shutil.copyfile(src_tgt[0], src_tgt[1])
    return 0

def get_value_from_header(dcm_dir, key):
    """Read value from dcm header stored under key"""
    dcm = dcmread(dcm_dir)
    return dcm[key].value

def check_if_philips(src_path):
    """Given the src_path of the dicoms, check if the Manufacturer is Philips"""
    dcm_dirs = [join(src_path, f) for f in os.listdir(src_path)]
    found = False
    n_missing = 0
    manufacturer = 'Unknown'
    while not found and n_missing<=len(dcm_dirs):
        try:
            manufacturer = get_value_from_header(dcm_dirs[n_missing], 'Manufacturer')
            found = True
        except:
            n_missing+=1
    if 'Philips' in manufacturer:
        return True
    else:
        return False

def move_and_gz_files(src_tgt, test=False, trial=0):
    """Move and gzip niis from src_tgt[0] (hdd path of the file), 
    to src_tgt[1] (directory to store the gzipped nii file),
    src_tgt[2] is the sif dcm dir in case src_tgt[0] has missing files."""
    if test:
        log_("trial number "+ str(trial))
    if trial>2:
        return 1
    trial+=1
    sys.stdout.flush()
    src_path, tgt_path, sif_src_path = src_tgt
    tgt_pat_dir = get_dir(tgt_path)
    # create target patient dir
    make_dir(tgt_pat_dir)
    sid = split(sif_src_path)[1] 
    if check_tgt_files(tgt_path, sid):
        print('|', end='')
        if test:
            log_("The file(s) already exists at " + tgt_path)
            log_('Stop')
        return 0
    if split(src_path)[1].endswith('.nii'): #nii is present, we need just to move
        print('->', end='')
        basic.move_compress(src_path, tgt_path)
        return 0
    else: #nii is not present, try to convert dicoms on disk to nii
        if check_dicoms(src_path, sif_src_path)==0: # check if all the dicoms are on the disk
            print('c', end='')
            dcm2nii_out = dcm2nii_safe(src_path, tgt_pat_dir, 
                                    sid, test)
            if dcm2nii_out==0:
                if test:
                    log_("Conversion worked")
                return 0
            else:
                if check_if_philips(src_path)==0:
                    if fix_dcm_incomplete_vols.fix_incomplete_vols(src_path)==0:
                        #now we have to adjust the src dir
                        new_disk_dcm_src = join(src_path, 'corrected_dcm')
                        src_tgt[0] = new_disk_dcm_src
                        return move_and_gz_files(src_tgt, test, trial)
                    else:
                        print('x')
                        return 1
                else:
                    print('x')
                    return 1
        else:    
            print('s->d')
            move_missing_files(src_path, sif_src_path)
            return move_and_gz_files(src_tgt, trial)


def get_source_target_dirs(sids_ls, disk_volume_dir_dic_dcm, disk_volume_dir_dic_nii,
                        sif_volume_dir_dic, 
                        base_nii_target_dir):
    """Creates a list of triplet (source_nii_dir/source_dcm_dir, target_nii_dir, source_sif_dir) 
    with source dir and target dir. 
    If nii is present on disk, use this file as source, 
    elif dicom no disk use dicom dir as source 
    else use dcm dir on sif as src"""
    sids_all = set(sids_ls)
    sids_disk_nii = set(disk_volume_dir_dic_nii.keys())
    sids_disk_dcm = set(disk_volume_dir_dic_dcm.keys())

    sids_nii_disk_ls = list(sids_all.intersection(sids_disk_nii))
    sids_dcm_disk_ls = list((sids_all.difference(sids_disk_nii)).intersection(sids_disk_dcm))
    sids_dcm_sif_ls = list(sids_all.difference(sids_disk_nii.union(sids_disk_dcm)))

    assert len(sids_dcm_sif_ls)==0, f"There are {len(sids_dcm_sif_ls)} sids in sids_ls thate are not in the disk dictionaries"
    disk_src_sif_src_nii_tgt = [(
        disk_volume_dir_dic_nii[sid],
        join(base_nii_target_dir, get_part_of_path(disk_volume_dir_dic_nii[sid], 5) + '.gz'), 
        sif_volume_dir_dic[sid]) \
        for sid in sids_nii_disk_ls]
    disk_src_sif_src_dcm_tgt = [(
        disk_volume_dir_dic_dcm[sid],
        join(base_nii_target_dir, get_part_of_path(disk_volume_dir_dic_dcm[sid], 5) + '.gz'), 
        join(sif_dir, sif_volume_dir_dic[sid])) \
        for sid in sids_dcm_disk_ls]
    disk_src_sif_src_tgt = disk_src_sif_src_nii_tgt + disk_src_sif_src_dcm_tgt
    return disk_src_sif_src_tgt

def postprocessing(pat_dir):
    """Remove json files and move and gzip existing niis."""
    files_paths = basic.list_subdir(pat_dir)
    #nii_vols = [f for f in files_paths if f.endswith('.nii')]
    json_files = [f for f in files_paths if f.endswith('.json')]
    for json_file in json_files:
        if os.path.exists(json_file):
            os.remove(json_file)
    #for nii_vol in nii_vols:
    #    move_compress(nii_vol, nii_vol+'.gz', remove=True)

def postprocessing_parallel(pat_sup_dir, procs=10):
    pat_dirs = basic.list_subdir(pat_sup_dir)
    with mp.Pool(procs) as pool:
                pool.map(postprocessing, pat_dirs)

##########################################main#######################################
def main(base_nii_tgt_dir, procs=8):
    print("Create src_tgt directories list")
    src_tgt_ls = get_source_target_dirs(
        sids_cases_ls, disk_volume_dir_dic_dcm, disk_volume_dir_dic_nii, 
        sif_volume_dir_dic, base_nii_target_dir=base_nii_tgt_dir)
    print('file already exists at destination: |')
    print('nii exists, just move and gzip: ->')
    print('move missing dcms from sif to disk: s->d')
    print('dcm to nii conversion: c')
    print('fail: x')
    print("Move ", len(src_tgt_ls), "files.")
    print(f"Using {procs} processes")
    with mp.Pool(procs) as pool:
                pool.map(move_and_gz_files, 
                        src_tgt_ls)
    summarize_problematic_files()
    print("Remove json files")
    postprocessing_parallel(base_nii_tgt_dir, procs)
    print("Finished at: ", dt.now())

if __name__ == '__main__':
    test=True
    if test:
        print('Test')
        start = time.time()
        src_tgt_ls = get_source_target_dirs(sids_cases_ls, disk_volume_dir_dic_dcm,
                                disk_volume_dir_dic_nii, sif_volume_dir_dic,
                                base_nii_target_dir=join(pred_input_dir,'cases'))
        for i in range(200,201):
            sid_num = i
            move_and_gz_files(src_tgt_ls[sid_num], test=True)
        print("Finished at: ", dt.now())
        print("Total time: ",round(time.time()-start, 3))
        pat_dirs = basic.list_subdir(join(pred_input_dir, 'potential_controls'))
        postprocessing(pat_dirs[102])
    else:
        main(nii_base_pred_dir, procs=12)
           