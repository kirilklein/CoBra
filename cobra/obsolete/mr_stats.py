# -*- coding: utf-8 -*-
"""
Created on Thu Sep  9 11:06:00 2021

@author: klein
"""
# %%
import pandas as pd
import matplotlib.pyplot as plt
import os
from os.path import join
from pathlib import PurePath as Path
import numpy as np
from stats_tools import vis as svis
from vis import mri_vis as mvis
import seaborn as sns
from utilities import stats, utils, mri_stats, basic
from utilities.basic import DotDict, p, sort_dict
import importlib


# %%
# In[Usefule keys]
TE_k = 'EchoTime'
TR_k = 'RepetitionTime'
TI_k = 'InversionTime'
FA_k = 'FlipAngle'
SD_k = 'SeriesDescription'
PID_k = 'PatientID'
time_k = 'InstanceCreationTime'
date_k = 'InstanceCreationDate'
DT_k = 'DateTime'
SID_k = 'SeriesInstanceUID'
SS_k = 'ScanningSequence'
SV_k = 'SequenceVariant'
SN_k = 'SequenceName'
SO_k = 'ScanOptions'
ETL_k = 'EchoTrainLength'
MFS_k = 'MagneticFieldStrength'

# %%
# In[Test functions]
masks = [np.array([1, 0, 0]), np.array([0, 0, 0]), np.array([1, 1, 0])]
mask = masks[0]
for i in range(1, len(masks)):
    mask = mask | masks[i]
print(mask)

# %%
# In[tables directories]
script_dir = os.path.realpath(__file__)
base_dir = Path(script_dir).parent
fig_dir = f"{base_dir}/figs"
table_dir = f"{base_dir}/data/tables"

# %%
# In[load positive csv]
#pos_tab_dir = f"{table_dir}/pos_nn.csv"
#neg_tab_dir = f"{table_dir}/neg_all.csv"
#df_p = utils.load_scan_csv(pos_tab_dir)
#df_n = utils.load_scan_csv(neg_tab_dir)
all_tab_dir = f"{table_dir}/neg_pos.csv"
df_all = utils.load_scan_csv(all_tab_dir)
print(f"All scans in df_all ={len(df_all)}")
exclude_other = False
if exclude_other:
    mask_other = df_all.Sequence=='other'
    df_all = df_all[~mask_other] 
    fig_dir = f"{base_dir}/figs/basic_stats/exclude_other"
    print(f"All scans in df_all after excluding 'other' sequences ={len(df_all)}")
pred_seq = utils.load_scan_csv(f"{base_dir}/data/share/pred_seq.csv")
# %%
# In[how many have scanner manufacturer, scanner type, b0 field strength]
print(df_all.keys())
print(df_all.Manufacturer.isna().sum())
print(df_all.ManufacturerModelName.isna().sum())
print(df_all[MFS_k].isna().sum())
print(len(df_all))
# %%
# In[adding columns and merging]

#pos_patients = df_p.PatientID.unique()
#pos_mask = df_all.PatientID.isin(pos_patients)
#df_all["Pos"] = np.where(pos_mask, 1, 0)
#df_all.to_csv(all_tab_dir, index=False)
#df_all = pd.merge(
#    df_all, pred_seq[[SID_k, 'Sequence', 'TrueSequenceType']], on=SID_k)
#print(df_all.keys())

# %%
# In[Volume Count by Sequences]
print("For now we are not interested in 't2s', 'flair_ce', 'swi_mip'")
true_mask = df_all.TrueSequenceType==1
df_all.Sequence = np.where(
    df_all.Sequence.isin(['t2s', 'flair_ce', 'swi_mip']), 
    'other', df_all.Sequence )
true_seq_counts = df_all[true_mask].Sequence.value_counts()
to_append = pd.Series([0],index=['t2s_gre'] )
pred_seq_counts = df_all[~true_mask].Sequence.value_counts().append(to_append)
# %%
# In[Plot Volume Count]
fig, ax = svis.bar(true_seq_counts.keys(), true_seq_counts.values, label='true',)
svis.bar(pred_seq_counts.keys(), pred_seq_counts.values, fig=fig, ax=ax,
         bottom=true_seq_counts.values, label='pred', color=(0,1),
         kwargs={'lgd':True, 'xlabel':'Sequence Type',
                  'yrange':(0,130000),'title':'Volume Count - All Patients',
                  'ylabel':'Volume Count',
                  },
         save=True, 
         figname=f"{fig_dir}/sequence_pred/seq_dist_volume_count.png",)
# %%
# In[Patient Count by Sequences]
pos_mask = df_all.Positive==1
pos_pat_count_seq = df_all[pos_mask].groupby(by='Sequence')\
    .PatientID.nunique().sort_values(ascending=False)
neg_pat_count_seq = df_all[~pos_mask].groupby(by='Sequence')\
    .PatientID.nunique().sort_values(ascending=False)
fig, ax = svis.bar(neg_pat_count_seq.keys(), neg_pat_count_seq.values, 
                   label='neg')
svis.bar(pos_pat_count_seq.keys(),pos_pat_count_seq.values, fig=fig, ax=ax,
         bottom=neg_pat_count_seq.values, label='pos',
         color=svis.Color_palette(0)[1], 
         kwargs={'lgd':True, 'xlabel':'Sequence Type','title':'All Patients',
                 'ylabel':'Patient Count'},
         save=True, 
         figname=f"{fig_dir}/sequence_pred/seq_dist_patient_count.png",)

# %%
# In[Plot patient count]
labels = ['2019', 'positive']
pos_mask = df_all.Pos==1
pos_pat_count = df_all[PID_k][pos_mask].nunique()
neg_pat_count = df_all[PID_k][~pos_mask].nunique()
counts = np.array([neg_pat_count, pos_pat_count])
kwargs={'xlabel':'', 'show':False, 'yrange':(0,26000),
        'ylabel':'Patient Count', 'title':'Number of Patients with MRI scans'}
fig, ax = svis.bar(labels, counts, kwargs=kwargs)
ax.text(1-.05, pos_pat_count+300, pos_pat_count, fontsize=22)
ax.text(0-.1, neg_pat_count+300, neg_pat_count, fontsize=22)
fig.savefig(f"{fig_dir}/pat_count.png", dpi=100)
# %%
# In[Plot MR field strength]

neg_value_counts = sort_dict(
    df_all[MFS_k][~pos_mask].value_counts().sort_values().iloc[2:])
pos_value_counts = sort_dict(
    df_all[MFS_k][pos_mask].value_counts())
print(neg_value_counts.values())
fig, ax = svis.bar(neg_value_counts.keys(), neg_value_counts.values(),
                   label='neg', )
svis.bar(pos_value_counts.keys(), pos_value_counts.values(), 
         bottom=[v for v in neg_value_counts.values()], 
         color=(0,1), label='pos', 
         fig=fig, ax=ax, kwargs={'ylabel':'Volume Count',
                                 'xlabel': 'B0',
                                 'lgd_loc':2}, save=True,
         figname=join(fig_dir, 'B0.png'))
# %%
# In[Plot distribution of Rows and Columns]
fig, g = svis.plot_decorator(sns.jointplot, plot_func_kwargs={
    'data':df_all[df_all.Rows<3000],
    'x':"Rows", 'y':"Columns", 'hue':"Positive"},
    )
g.figure.savefig(f"{fig_dir}/basic_stats/scan_sizes.png", dpi=80)
#%%
g = sns.scatterplot(data=df_all[df_all.Rows<3000], x='Rows', y='Columns', hue='Positive')
g.figure.savefig(f"{fig_dir}/basic_stats/scan_sizes_scatter.png", dpi=400)

# %%
#sns.displot(df_all, x="Rows", y="Columns", hue="Pos", alpha=1)

# In[Write Patient IDs to text]
neg_pat_ids = list(df_n[PID_k].unique())
with open(f'{base_dir}/results/neg_ids.txt', 'w') as filehandle:
    for listitem in neg_pat_ids:
        filehandle.write('%s\n' % listitem)

# In[Count the number of studies]
num_studies_all = stats.count_number_of_studies(df_all)
print(f"The number of studies is {num_studies_all}")
# In[Convert time and date to datetime for efficient access]
df_all = stats.add_datetime(df_all)
#df_p.to_csv(pos_tab_dir, index = False, header = True)

# In[]
p(f"first study {df_p.DateTime.min()}")
p(f"last study {df_p.DateTime.max()}")
studies_all = stats.check_tags(df_all, 'all', date_k).sum()
print(f"Number of scans in 2021 {studies_2021}")
# In[Sort the the scans by time and count those that are less than 2 hours apart]
time_diff_studies_all, _ = stats.time_between_studies(df_all)
# In[]
print(len(time_diff_studies_all))
# In[]
svis.hist(np.array(time_diff_studies_all)/24, 100, ylog_scale=(True),
                    show_plot=True, xlabel='Days between studies',
                    save=True, title='All Patients',
                    figname=f"{fig_dir}/time_between_studies.png")

# In[Store the results]
patient_ids = df_p['PatientID'].unique()
ppatient_df = pd.DataFrame(
    {'PatientId': [], 'NumStudies': []})  # storing results
ppatient_df['PatientID'] = patient_ids
ppatient_df['NumStudies'] = num_studies_l

# In[Show distribution of the studies]
num_studies_a = np.array(num_studies_l)
max_studies = max(num_studies_a)
svis.hist(num_studies_a, np.arange(.5, max_studies+.5),
                    show_plot=True, xlabel='Number of studies',
                    save=True, title='Positive Patients',
                    figname=f"{fig_dir}/pos/num_studies.png")

#%%
# In[Get number of acquired volumes per patient]
scans_per_patient = df_all.groupby('PatientID').size()
figure = svis.hist(
    scans_per_patient, np.arange(1, 110, 2),
    show=True,kwargs={'xlabel':'# volumes per patient',
    'title':'All Patients'},
    save=True, figname=f"{fig_dir}/basic_stats/volumes_per_patient.png",
    )

#%%
scans_per_patient = df_all[df_all.Positive==0].groupby('PatientID').size()
figure = svis.hist(
    scans_per_patient, np.arange(1, 110, 2),
    show=True,kwargs={'xlabel':'# volumes per patient',
    'title':'Negative Patients'},
    save=True, figname=f"{fig_dir}/basic_stats/volumes_per_patient_neg.png",
    )

#%%
# In[Sort scans by manufacturer]
manufactureres = df_all['Manufacturer'].unique()
p(manufactureres)
philips_t = ['Philips Healthcare', 'Philips Medical Systems',
             'Philips']
philips_c = stats.check_tags(df_all, philips_t, 'Manufacturer').sum()
siemens_c = stats.mask_sequence_type(df_all, 'SIEMENS', 'Manufacturer').sum()
gms_c = stats.mask_sequence_type(
    df_all, 'GE MEDICAL SYSTEMS', 'Manufacturer').sum()
agfa_c = stats.mask_sequence_type(df_all, 'Agfa', 'Manufacturer').sum()
none_c = df_all['Manufacturer'].isnull().sum()
#%%
df_all.Manufacturer.unique()
#%%
# In[re]
# Replace manufacturers
df_all.Manufacturer[stats.check_tags(df_all, philips_t, 'Manufacturer')] = 'Philips'
df_all.Manufacturer[stats.check_tags(df_all,['Siemens'], 'Manufacturer')] = 'Siemens'
#%%
import matplotlib as mpl
# In[Plot sequence counts]
mpl.rcParams['figure.dpi'] = 400
plt.style.use('ggplot')
#labels = ['Siemens', 'Philips', 'GE', 'Other', 'other']
g = sns.countplot(x="Manufacturer", hue="Positive", data=df_all, hue_order=[1,0],
    order = df_all['Manufacturer'].value_counts().iloc[:3].index)
#g.set(xlabel=('Manufacturer'), ylabel=('Volume Count'), xticklabels=labels)
fig = g.get_figure()
fig.tight_layout()
fig.savefig(f"{fig_dir}/basic_stats/manufacturer.png")
#%%
# In[visualize scanner manufacturer counts]
fig, ax = plt.subplots(1, figsize=(10, 6))
manufacturers_unq = ['Philips', 'SIEMENS', 'GE']
counts = np.array([philips_c, siemens_c, gms_c])
svis.bar(manufacturers_unq, counts, 
        kwargs={'xlabel':'Manufacturer', 'title':'All Patients'},
              save=True, 
              figname=f"{fig_dir}/basic_stats/manufacturers_count_all.png",
              )

#%%
# In[Model Name]
philips_m = stats.check_tags(df_p, philips_t, 'Manufacturer')
siemens_m = stats.mask_sequence_type(df_p, 'SIEMENS', 'Manufacturer')
gms_m = stats.mask_sequence_type(df_p, 'GE MEDICAL SYSTEMS', 'Manufacturer')

model_k = 'ManufacturerModelName'
philips_models_vc = df_p[philips_m][model_k].value_counts().to_dict()
siemens_models_vc = df_p[siemens_m][model_k].value_counts().to_dict()
gms_models_vc = df_p[gms_m][model_k].value_counts().to_dict()

# In[summarize small groups]
philips_models_vc_new = stats.group_small(philips_models_vc, 1000)
siemens_models_vc_new = stats.group_small(siemens_models_vc, 200)
gms_models_vc_new = stats.group_small(gms_models_vc, 200)

# In[visualize]
fig, ax = plt.subplots(2, 2, figsize=(10, 10))
ax = ax.flatten()

lbls_ph = philips_models_vc_new.keys()
szs_ph = philips_models_vc_new.values()
lbls_si = siemens_models_vc_new.keys()
szs_si = siemens_models_vc_new.values()
lbls_gm = gms_models_vc_new.keys()
szs_gm = gms_models_vc_new.values()

ax[0].pie(szs_ph,  labels=lbls_ph, autopct='%1.1f%%',
          shadow=True, startangle=90)
# Equal aspect ratio ensures that pie is drawn as a circle.
ax[0].axis('equal')
ax[0].set_title('Philips', fontsize=20)
ax[1].pie(szs_si,  labels=lbls_si, autopct='%1.1f%%',
          shadow=True, startangle=90)
# Equal aspect ratio ensures that pie is drawn as a circle.
ax[1].axis('equal')
ax[1].set_title('Siemens', fontsize=20)
ax[2].pie(szs_gm,  labels=lbls_gm, autopct='%1.1f%%',
          shadow=True, startangle=90)
# Equal aspect ratio ensures that pie is drawn as a circle.
ax[2].axis('equal')
ax[2].set_title('GMS', fontsize=20)
ax[-1].axis('off')

fig.suptitle('Positive Patients', fontsize=20)
fig.tight_layout()
plt.subplots_adjust(wspace=.5, hspace=None)
plt.show()
fig.savefig(f"{fig_dir}/pos/model_name_pie_chart.png")

# In[Keys that are relevant]
rel_key_list = ['t1', 'gd', 't2', 't2s', 't2_flair', 'swi']
# In[Save Patient pos IDs]
mask_dict_p, tag_dict_p = mri_stats.get_masks_dict(df_p)
posids_dict = DotDict({key: df_p[mask][PID_k] for key, mask
                       in mask_dict_p.items()})
for key in rel_key_list:
    print(key)
    pat_ids = list(posids_dict[key])
    print(len(pat_ids))
    with open(f"{base_dir}/results/pos_IDs_{key}.txt", "w") as f:
        for pat_id in pat_ids:
            f.write("%s\n" % pat_id)

# In[Save Patient neg IDs]
mask_dict_n = mri_stats.get_masks_dict(df_n, return_tags=False)
negids_dict = DotDict({key: df_n[mask][PID_k] for key, mask
                       in mask_dict_n.items()})
for key in rel_key_list:
    pat_ids = list(negids_dict[key])
    with open(f"{base_dir}/results/neg_IDs_{key}.txt", "w") as f:
        for pat_id in pat_ids:
            f.write("%s\n" % pat_id)


# In[Look at 'other' group] combine all the relevant masks to get others
seq_vars = [SD_k, TE_k, TR_k, FA_k, TI_k, ETL_k, SS_k, SV_k, SN_k]
ids_vars = [PID_k, SID_k]
comb_vars = seq_vars + ids_vars
nid_seq = df_p[mask_dict_p.none_nid]
nid_seq_sort = nid_seq[comb_vars].dropna(thresh=3).sort_values(by=SD_k,
                                                               axis=0,
                                                               ascending=True)
nid_seq_sort = nid_seq_sort.loc[nid_seq_sort.astype(
    str).drop_duplicates().index]

nid_seq_sort_ids = nid_seq_sort[ids_vars]
nid_seq_sort_ids.to_csv(f"{base_dir}/tables/non_identified_seq_ids.csv",
                        index=False)
nid_seq_sort[seq_vars].to_csv(f"{base_dir}/tables/non_identified_seq.csv",
                              index=False)
p(nid_seq_sort)


# In[Look at 'other' group for all mris]
mask_dict_all = mri_stats.get_masks_dict(df_all, False)
seq_vars = [SD_k, TE_k, TR_k, FA_k, TI_k,
            ETL_k, SS_k, SV_k, SN_k, PID_k, SID_k]

nid_seq = df_all[mask_dict_all.none_nid]
print(f"All not identified sequences {len(nid_seq)}")
nid_seq_sort = nid_seq[seq_vars].dropna(thresh=5).sort_values(by=SD_k,
                                                              axis=0,
                                                              ascending=True)
print(f"dropping missing columns {len(nid_seq_sort)}")
nid_seq_sort = nid_seq_sort.loc[nid_seq_sort.astype(
    str).drop_duplicates().index]
print(f"drop duplicates {len(nid_seq_sort)}")
nid_seq_sort = nid_seq_sort.drop_duplicates(subset=[SD_k])
print(f"drop some more duplicates {len(nid_seq_sort)}")
nid_seq_sort.to_csv(f"{base_dir}/tables/non_identified_seq_all.csv",
                    index=False)
# In[]
unique_sequence_names = df_all['SequenceName'].unique()
np.savetxt(f"{base_dir}/tables/unique_seq_names.txt",
           unique_sequence_names, fmt="%s")

# In[Show some scans]
mvis.show_series('a0be3bf699294420053eb3c6ca7d7f6c',
                '2e2caa22443d04a2d42bfc4e7dc9d6bb')
# p(nid_seq_sort)

# In[Save corresponding patient and scan ids]
ids_vars = [PID_k, SID_k]
nid_seq = df_p[mask_dict_p.none_nid]
nid_seq_sort = nid_seq[ids_vars].sort_values(by=PID_k, axis=0, ascending=True)
nid_seq_sort = nid_seq_sort.loc[nid_seq_sort.astype(
    str).drop_duplicates().index]
nid_seq_sort.to_csv(
    f"{base_dir}/tables/non_identified_seq_pid.csv", index=False)
p(nid_seq_sort)

# In[Get counts]
counts_dict = DotDict({key: mask.sum() for key, mask in mask_dict_p.items()})
print(counts_dict)

# In[visualize basic sequences]
sequences_names = ['T1+\nMPRAGE', 'FLAIR', 'T2', 'T2*', 'DWI', 'SWI',
                   'angio', 'ADC', 'Other', 'None or \n not identified']
seq_counts = np.array([counts_dict.t1, counts_dict.flair, counts_dict.t2,
                       counts_dict.t2s, counts_dict.dwi,
                       counts_dict.swi, counts_dict.angio, counts_dict.adc,
                       counts_dict.other, counts_dict.none_nid])
svis.bar(sequences_names, seq_counts, figsize=(13, 6), xlabel='Sequence',
              xtickparams_ls=16, save_plot=True, title='Positive Patients',
              figname=f"{fig_dir}/pos/basic_sequences_count.png")

# In[Visualize other sequences]
sequences_names = ['DTI', 'TRACEW', 'ASL', 'CEST', 'Survey', 'STIR',
                   'screensave', 'autosave']
seq_counts = np.array([counts_dict.dti, counts_dict.tracew, counts_dict.asl,
                       counts_dict.cest, counts_dict.survey,
                       counts_dict.stir,
                       counts_dict.screensave, counts_dict.autosave,
                       ])
svis.bar(sequences_names, seq_counts, figsize=(13, 6), xlabel='Sequence',
              xtickparams_ls=16, save_plot=True, title='Positive Patients',
              figname=f"{fig_dir}/pos/other_sequences_count.png")

# In[Look at the distributions of TE and TR for different seq]
df_p.loc[mask_dict_p.t1, 'Sequence'] = 'T1'
df_p.loc[mask_dict_p.t2, 'Sequence'] = 'T2'
df_p.loc[mask_dict_p.t2s, 'Sequence'] = 'T2S'
df_p.loc[mask_dict_p.flair, 'Sequence'] = 'FLAIR'
df_p_clean = df_p.dropna(subset=[TE_k, TR_k])

# In[visualize sequences scatter]
fig, ax = plt.subplots(2, 2, figsize=(10, 10))
ax = ax.flatten()
sns.scatterplot(x=TE_k, y=TR_k,
                hue='Sequence', data=df_p_clean, ax=ax[0])
sns.scatterplot(x=TE_k, y=TI_k, legend=None,
                hue='Sequence', data=df_p_clean,
                ax=ax[1])
sns.scatterplot(x=TI_k, y=TR_k, legend=None,
                hue='Sequence', data=df_p_clean,
                ax=ax[2])
sns.scatterplot(x=TI_k, y=FA_k, legend=None,
                hue='Sequence', data=df_p_clean,
                ax=ax[3])
fig.suptitle('Identified Sequences (positive patients)', fontsize=20)
fig.tight_layout()
plt.show()
fig.savefig(f"{fig_dir}/pos/scatter_training.png")

# In[Extract dates from series description if not present in InstanceCreationData]
# p(df_p['InstanceCreationDate'].dropna())
p(f"number of scans without date {df_p['InstanceCreationDate'].isnull().sum()}\
  out of {len(df_p)}")
date_mask = df_p['SeriesDescription'].str.contains('2020', na=False)
# p(df_p[date_mask]['SeriesDescription'].count())
# these are not that many

# In[Search for combinations of FLAIR, SWI, T1]
gb_pat = df_p.groupby(PID_k)
# grouped masks followd by
flair_m = stats.check_tags(gb_pat, tag_dict_p.flair).groupby(PID_k).any()
swi_m = stats.check_tags(gb_pat, tag_dict_p.swi).groupby(PID_k).any()
t1_m = stats.check_tags(gb_pat, tag_dict_p.t1).groupby(PID_k).any()
t2_m = stats.check_tags(gb_pat, tag_dict_p.t2).groupby(PID_k).any()

flair_swi_t1_m = flair_m & swi_m & t1_m
p(f"{flair_swi_t1_m.sum()} patients have\
  the sequences flair, swi and t1")
flair_swi_t1_t2_m = flair_m & swi_m & t1_m & t2_m
p(f"{flair_swi_t1_t2_m.sum()} patients have\
  the sequences flair, swi,t1 and t2")


# In[Number of studies per month/year]

ps_datetime_count = df_p.groupby(
    [df_p[DT_k].dt.year, df_p[DT_k].dt.month]).count()[SID_k]
year_month_keys = [str(int(key[1]))+'/'+str(key[0])[:4]
                   for key in ps_datetime_count.keys()]
year_month_keys.insert(-1, '5/2021')  # this month is missing
year_month_counts = ps_datetime_count.values
year_month_counts = np.insert(year_month_counts, -1, 0)
svis.bar(year_month_keys[:-3], year_month_counts[:-3], figsize=(13, 7),
              xtickparams_rot=70,
              xlabel='month/year', save_plot=(True), ylabel='Frequency',
              title='Number of acquired volumes for positive patients',
              figname=f"{fig_dir}/pos/scans_months_years.png")

# In[when is the date present but not a time]
p(f"{pd.isnull(df_p[date_k]).sum()} scans dont have a time or date")

# In[Study months distribution]
importlib.reload(stats)
_, study_dates = stats.time_between_studies(df_p)

# In[Studies distr]
year_month_study_dates = [str(date.year)+'/'+str(date.month)
                          for date in study_dates]
year_month_unique, year_month_counts = np.unique(
    np.array(year_month_study_dates), return_counts=True)
svis.bar(year_month_unique[:-2], year_month_counts[:-2], figsize=(13, 7),
              xtickparams_rot=70, xlabel='study month/year', save_plot=(True),
              ylabel='Frequency', title='Studies for positive patients',
              figname=f"{fig_dir}/pos/studies_months_years.png")




# In[Find intersection of FLAIR, DWI, SWI or T2*]
comb0 = ['dwi', 'flair', 'swi',]
comb1 = comb0 + ['t1']
comb2 = ['dwi', 'flair', 't2s_gre',]
comb3 = comb2 + ['t1']
comb_list = [comb0, comb1, comb2, comb3]
comb_labels = ['dwi, flair, swi', 'dwi, flair, swi\n +t1',
          'dwi, flair, t2* gre', 'dwi, flair, t2* gre\n +t1',]
dfp = df_all[df_all.Pos==1]
dfn = df_all[df_all.Pos==0]
Pos_combs_list = []
Neg_combs_list = []

for comb in comb_list:
    pos_setlist = []
    neg_setlist = []
    for tag in comb:
        pos_setlist.append(set(dfp[dfp.Sequence==tag].PatientID.unique()))
        neg_setlist.append(set(dfn[dfn.Sequence==tag].PatientID.unique()))
    pos_intersection = len(set.intersection(*pos_setlist))
    neg_intersection = len(set.intersection(*neg_setlist))
    Pos_combs_list.append(pos_intersection)
    Neg_combs_list.append(neg_intersection)
    
fig, ax = svis.bar(comb_labels, Neg_combs_list, figsize=(14,6), width=.6, 
                   label='neg')
fig, ax = svis.bar(comb_labels, Pos_combs_list, label='pos', bottom=Neg_combs_list, 
         width=.6, color=(0,1), fig=fig, ax=ax, 
         kwargs={'xlabel':'Sequence Type Combinations', 
                 'ylabel':'Patient Count', 'yrange':(0,7000)},
         ) 
                  
for i in range(4):
    ax.text(i-.1, Pos_combs_list[i]+Neg_combs_list[i]+200, 
            Pos_combs_list[i]+Neg_combs_list[i], fontsize=20)
    ax.text(i+.35, Neg_combs_list[i]+50, Pos_combs_list[i],
            color=svis.Color_palette(0)[1],
            fontsize=20, ha='left')
    
fig.savefig(fname=f"{fig_dir}/basic_stats/sequence_comb_pat_count.png", dpi=100)
# In[Write to files]
write_dir = f"{base_dir}/share/Cerebriu/download_patients"
with open(f"{write_dir}/dwi_flair_t2s.txt", 'w') as f:
    for item in dwi_flair_t2s:
        f.write("%s\n" % item)
# In[Count number of relevant patients in 2019]
print(len(df_2019[mask_dict.t1 | mask_dict.t2 | mask_dict.t2s | mask_dict.t1gd
                  | mask_dict.t2gd | mask_dict.gd | mask_dict.swi | mask_dict.flair
                  | mask_dict.dwi][PID_k].unique()))
print(len(df_2019[PID_k].unique()))
