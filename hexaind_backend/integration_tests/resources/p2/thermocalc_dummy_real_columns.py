import os
import numpy as np
import pandas as pd

def get_input_output_features():
    return [['CASH_PMT', 'HO_Step_3_Time(hr)', 'HB_gauge', 'Prestrain', 'Ge', 'Sn', 'Mg', 'Mn', 'HO_Step_1_Time(hr)', 'HR_Transfer_Slab_Gauge_(IG)', 'PX_Temp(C)', 'Ti', 'Zr', 'HO_Step_1_Temp(C)', 'HO_Step_2_Temp(C)', 'Zn', 'Cr', 'Fe', 'Cu', 'V', 'CASH_Dwell_time_Above_540(sec)', 'HR_Exit(C)', 'CR_Final_Gauge', 'NA_Time(days)', 'AA_Time(min)', 'Si', 'HR_Lay_Down_Temp(C)', 'HO_Step_2_Time(hr)', 'pHR', 'HO_Step_3_Temp(C)', 'pCR', 'AA_Temperature(C)'], 
            ['Cu_ss', 'Q_ALCUMGSI', 'AL2CU_C16', 'Fe_ss', 'Mg_pss', 'DIAMOND_A4', 'AL6MN', 'Si_pss', 'pcpt_radius', 'AL15SI2M4', 'Mg_ss', 'Si_ss', 'ALMG_BETA', 'Mn_pss', 'Fe_pss', 'MG2SI_C1', 'AL13FE4', 'pcpt_volfrac', 'AL9FE2SI2', 'FCC_A1', 'Mn_ss', 'solidus_temp', 'solvus_temp', 'HO_Avg_Temp(C)', 'Cu_pss', 'ys_cal']]

def perform_predictions(input_data):
    
    df = pd.DataFrame(input_data)

    new_columns = ['Cu_ss', 'Q_ALCUMGSI', 'AL2CU_C16', 'Fe_ss', 'Mg_pss', 'DIAMOND_A4', 'AL6MN', 'Si_pss', 'pcpt_radius', 'AL15SI2M4', 'Mg_ss', 'Si_ss', 'ALMG_BETA', 'Mn_pss', 'Fe_pss', 'MG2SI_C1', 'AL13FE4', 'pcpt_volfrac', 'AL9FE2SI2', 'FCC_A1', 'Mn_ss', 'solidus_temp', 'solvus_temp', 'HO_Avg_Temp(C)', 'Cu_pss', 'ys_cal']
    
    # Calculate new columns
    for column in new_columns:
        df[column] = np.random.rand(len(df))
    
    return df.to_dict(orient="records")


    
    
    
