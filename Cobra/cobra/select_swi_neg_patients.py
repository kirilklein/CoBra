# -*- coding: utf-8 -*-
"""
Created on Mon Nov  15 12:06:00 2021

@author: neusRodeja
"""

import numpy as np
import pandas as pd 
from utilities.utils import load_scan_csv,df_unique_values,find_n_slices,save_nscans
from stats_tools.vis import create_1d_hist,create_2d_hist,create_boxplot
import matplotlib.pyplot as plt 


main_folder = "/home/neus/Documents/09.UCPH/MasterThesis/github/Thesis/Cobra/cobra"
figs_folder = f'{main_folder}/figs/cmb_stats'
csv_folder = f"{main_folder}/tables"
csv_swi_file_name = "swi_neg_scans"
csv_file_name = "neg_pos_clean"

table_all = load_scan_csv(f'{csv_folder}/{csv_file_name}.csv')
###### Inspect quality for SWI positive scans.
mask_nan_values =  (table_all['InstanceCreationDate'].notna()&table_all['DateTime'].notna())
swi_neg_scans = table_all[(table_all['Positive']==0)&(table_all['Sequence']=='swi')&mask_nan_values]
#swi_pos_patients = swi_neg_scans.drop_duplicates(substet=['PatientID'])

n_scans = swi_neg_scans.shape[0]
n_patients = swi_neg_scans.drop_duplicates(subset='PatientID').shape[0]
print(f'Number of scans:\t{n_scans}\nNumber of patients:\t{n_patients}')

scans_groupedbyPatient = swi_neg_scans.groupby(['PatientID'])
# Scans per patient distribution
scans_perPatient = scans_groupedbyPatient.size()
scans_min,scans_max = np.min(scans_perPatient),np.max(scans_perPatient)
fig,ax = plt.subplots()
ax.set(ylabel='Counts',xlabel='#Scans per patient')
hist_data = create_1d_hist(ax,scans_perPatient,14,(-0.5,13.5),'Negative patients with SWI scans',display_counts=True)
fig.savefig(f'{figs_folder}/swi_scans_per_patient.png')

#Take patients that have only 1,2 or 3 scans
patients_id = scans_perPatient[scans_perPatient<4].keys()
swi_neg_scans = swi_neg_scans[swi_neg_scans['PatientID'].isin(patients_id)]
swi_neg_scans = swi_neg_scans.sort_values('DateTime',ascending=True)
swi_neg_scans = swi_neg_scans.groupby('PatientID').first().reset_index() ###TAKING THE FIRST SCAN 

#Save the number of slices per scan and save the table
swi_neg_scans = save_nscans(swi_neg_scans,f'{csv_folder}/{csv_swi_file_name}.csv',print_level=1)

#Save extra files to send to computerome
swi_neg_scans['PatientID'].to_csv(f'{csv_folder}/swi_neg_patientIds.csv')
