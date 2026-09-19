import numpy as np
import joblib
import pickle
from typing import Dict
import os

DEMOS_DIR = os.path.dirname(__file__)

def cone_areas(recommendation: Dict[str, float]):
    r = recommendation['r']
    h = recommendation['h']
    S = np.pi*r*np.sqrt(r**2+h**2)
    T = np.pi*r**2 + np.pi*r*np.sqrt(r**2+h**2)
    B = np.pi*r**2
    V = np.pi*r**2*h/3
    return  {"S": (S, None), "T": (T, None), "B": (B, None), "V": (V, None)}

def can_fem(recommendation: Dict[str, float]):
    
    if 'dcpSpacerThickness' in recommendation:
        dcpSpacerThickness = recommendation['dcpSpacerThickness']
        ppSpacerThickness = recommendation['ppSpacerThickness']
        ipsPressure = recommendation['ipsPressure']
        upPressure = recommendation['upPressure']
        frictionCf = recommendation['frictionCf']
        buckle_key = 'bucklingPressure'
        max_thin_key = 'maxThinning'
    else:
        dcpSpacerThickness = recommendation['dcp_spacer']
        ppSpacerThickness = recommendation['pp_spacer']
        ipsPressure = recommendation['ips_pressure']
        upPressure = recommendation['up_pressure']
        frictionCf = recommendation['friction_coeff']
        buckle_key = 'buckle_pressure'
        max_thin_key = 'max_thinning'

    buckling_pressure_model = joblib.load(f"{DEMOS_DIR}/models/5b8f283e-5f8d-11ed-9317-00224829d8eerec_model.joblib") #TODO please make them as env variables
    max_thinning_model = joblib.load(f"{DEMOS_DIR}/models/5c3aad1c-5f8d-11ed-8ef3-00224829d8eerec_model.joblib") #TODO please make them as env variables

    inputs = np.array((dcpSpacerThickness, ppSpacerThickness, ipsPressure, upPressure, frictionCf))
    inputs = inputs.reshape(1, -1)
    bucklingPressure = buckling_pressure_model.predict(inputs)
    maxThinning = max_thinning_model.predict(inputs)

    return  {buckle_key: (bucklingPressure[0], None), max_thin_key: (maxThinning[0], None)}

def bced_v1(recommendation: Dict[str, float]):
    t_0 = recommendation['t_0']
    t_1 = recommendation['t_1']
    t_2 = recommendation['t_2']
    t_3 = recommendation['t_3']
    t_4 = recommendation['t_4']
    t_5 = recommendation['t_5']
    t_6 = recommendation['t_6']
    t_7 = recommendation['t_7']
    t_8 = recommendation['t_8']
    r_0 = recommendation['r_0']
    r_1 = recommendation['r_1']
    r_2 = recommendation['r_2']
    r_3 = recommendation['r_3']
    r_4 = recommendation['r_4']
    r_5 = recommendation['r_5']
    r_6 = recommendation['r_6']
    r_7 = recommendation['r_7']
    r_8 = recommendation['r_8']
    
    buckle_pressure_model = joblib.load(f"{DEMOS_DIR}/models/c5d5cd60-3633-11ee-ab5d-0242ac11000arec_model_buckle_mpr1.joblib")
    weight_model = joblib.load(f"{DEMOS_DIR}/models/9a8b4b74-3676-11ee-9b10-0242ac11000arec_model_weight_mpr1.joblib")

    inputs = np.array((t_0, t_1, t_2, t_3, t_4, t_5, t_6, t_7, t_8, r_0, r_1, r_2, r_3, r_4, r_5, r_6, r_7, r_8))
    inputs = inputs.reshape(1, -1)
    buckle_pressure = buckle_pressure_model.predict(inputs)
    weight = weight_model.predict(inputs)

    #make sure that "Weight" in dict has capital W (according to problem data)
    return  {"buckle_pressure": (buckle_pressure[0], None), "Weight": (weight[0], None)}

def bced_v2(recommendation: Dict[str, float]):
    t_0 = recommendation['t_0']
    t_1 = recommendation['t_1']
    t_2 = recommendation['t_2']
    t_3 = recommendation['t_3']
    t_4 = recommendation['t_4']
    t_5 = recommendation['t_5']
    t_6 = recommendation['t_6']
    t_7 = recommendation['t_7']
    t_8 = recommendation['t_8']
    t_9 = recommendation['t_9']
    r_1 = recommendation['r_1']
    r_2 = recommendation['r_2']
    r_3 = recommendation['r_3']
    r_4 = recommendation['r_4']
    r_5 = recommendation['r_5']
    r_6 = recommendation['r_6']
    r_7 = recommendation['r_7']
    r_8 = recommendation['r_8']
    r_9 = recommendation['r_9']
    r_10 = recommendation['r_10']
    
    buckle_pressure_model = joblib.load(f"{DEMOS_DIR}/models/89340886-37c8-11ee-b15c-0242ac11000arec_model_buckle_gpr_40up.joblib")
    weight_model = joblib.load(f"{DEMOS_DIR}/models/9d7adfe4-37c9-11ee-83c4-0242ac11000arec_model_weight_gpr.joblib")

    inputs = np.array((t_0, t_1, t_2, t_3, t_4, t_5, t_6, t_7, t_8, t_9, r_1, r_2, r_3, r_4, r_5, r_6, r_7, r_8, r_9, r_10))
    inputs = inputs.reshape(1, -1)
    buckle_pressure = buckle_pressure_model.predict(inputs)
    weight = weight_model.predict(inputs)

    #make sure that "Weight" in dict has capital W (according to problem data)
    return  {"buckle_pressure": (buckle_pressure[0], None), "Weight": (weight[0], None)}

def ai_physics(recommendation: Dict[str, float]):
    Si=recommendation['Si']
    Fe=recommendation['Fe']
    Cu=recommendation['Cu']
    Mn=recommendation['Mn']
    Mg=recommendation['Mg']
    Cr=recommendation['Cr']
    Ti=recommendation['Ti']
    Zn=recommendation['Zn']
    Zr=recommendation['Zr']
    Sn=recommendation['Sn']
    V=recommendation['V']
    Ge=recommendation['Ge']
    Temp1=recommendation['HO_Step_1_Temp(C)']
    Time1=recommendation['HO_Step_1_Time(hr)']
    Temp2=recommendation['HO_Step_2_Temp(C)']
    Time2=recommendation['HO_Step_2_Time(hr)']
    Temp3=recommendation['HO_Step_3_Temp(C)']
    Time3=recommendation['HO_Step_3_Time(hr)']
    lay_down=recommendation['HR_Lay_Down_Temp(C)']
    transfer=recommendation['HR_Transfer_Slab_Gauge_(IG)']
    HB_gauge=recommendation['HB_gauge']
    HR_exit=recommendation['HR_Exit(C)']
    phr=recommendation['pHR']
    CR_Final=recommendation['CR_Final_Gauge']
    pcr=recommendation['pCR']
    CASH_PMT=recommendation['CASH_PMT']
    CASH_Dwell=recommendation['CASH_Dwell_time_Above_540(sec)']
    PX_temp=recommendation['PX_Temp(C)']
    NA_Time=recommendation['NA_Time(days)']
    AA_temp=recommendation['AA_Temperature(C)']
    AA_Time=recommendation['AA_Time(min)']
    prestrain=recommendation['Prestrain']
    
    #The following inputs will be provided by Thermo-Calc. These features are
    #automatically added to the same dataframe as the original inputs by the 
    #Thermo-Calc python script (see tc_features_mp.py)
    
    al15si2m4=recommendation['AL15SI2M4']
    diamond_a4=recommendation['DIAMOND_A4']
    fcc_a1=recommendation['FCC_A1']
    mg2si_c1=recommendation['MG2SI_C1']
    al9fe2si2=recommendation['AL9FE2SI2']
    q_alcumgsi=recommendation['Q_ALCUMGSI']
    si_ss=recommendation['Si_ss']
    fe_ss=recommendation['Fe_ss']
    cu_ss=recommendation['Cu_ss']
    mn_ss=recommendation['Mn_ss']
    mg_ss=recommendation['Mg_ss']
    pcpt_radius=recommendation['pcpt_radius']
    pcpt_volfrac=recommendation['pcpt_volfrac']
    solvus_temp=recommendation['solvus_temp']
    si_pss=recommendation['Si_pss']
    fe_pss=recommendation['Fe_pss']
    cu_pss=recommendation['Cu_pss']
    mn_pss=recommendation['Mn_pss']
    mg_pss=recommendation['Mg_pss']
          
    dict_YS=joblib.load(f'{DEMOS_DIR}/models/saved_model_YS.joblib')
    YS_model=dict_YS[0]
    YS_mean=dict_YS[1]
    YS_std=dict_YS[2]
    dict_UTS=joblib.load(f'{DEMOS_DIR}/models/saved_model_UTS.joblib')
    UTS_model=dict_UTS[0]
    UTS_mean=dict_UTS[1]
    UTS_std=dict_UTS[2]
    dict_UE=joblib.load(f'{DEMOS_DIR}/models/saved_model_UE.joblib')
    UE_model=dict_UE[0]
    UE_mean=dict_UE[1]
    UE_std=dict_UE[2]
    dict_TE=joblib.load(f'{DEMOS_DIR}/models/saved_model_TE.joblib')
    TE_model=dict_TE[0]
    TE_mean=dict_TE[1]
    TE_std=dict_TE[2]
    dict_R=joblib.load(f'{DEMOS_DIR}/models/saved_model_R.joblib')
    R_model=dict_R[0]
    R_mean=dict_R[1]
    R_std=dict_R[2]
    dict_Beta=joblib.load(f'{DEMOS_DIR}/models/saved_model_Beta.joblib')
    Beta_model=dict_Beta[0]
    Beta_mean=dict_Beta[1]
    Beta_std=dict_Beta[2]
    dict_IGC=joblib.load(f'{DEMOS_DIR}/models/saved_model_IGC.joblib')
    IGC_model=dict_IGC[0]
    IGC_mean=dict_IGC[1]
    IGC_std=dict_IGC[2]
    dict_inputs=joblib.load(f'{DEMOS_DIR}/models/input_parameters.joblib')
    inputs_mean=dict_inputs[0]
    inputs_std=dict_inputs[1]
    
    inputs = np.array((Si,Fe,Cu,Mn,Mg,Cr,Ti,Zn,Zr,Sn,V,Ge,Temp1,Time1,Temp2,Time2,Temp3,Time3,
                       lay_down,transfer,HB_gauge,HR_exit,phr,CR_Final,pcr,CASH_PMT,CASH_Dwell,
                       PX_temp,NA_Time,AA_temp,AA_Time,prestrain,al15si2m4,diamond_a4,
                       fcc_a1,mg2si_c1,al9fe2si2,q_alcumgsi,si_ss,fe_ss,cu_ss,mn_ss,mg_ss,pcpt_radius,pcpt_volfrac,
                       solvus_temp,si_pss,fe_pss,cu_pss,mn_pss,mg_pss))
    inputs = inputs.reshape(1, -1)
    inputs2 = np.array((Si,Fe,Cu,Mn,Mg,Cr,Ti,Zn,Zr,Sn,V,Ge,Temp1,Time1,Temp2,Time2,Temp3,Time3,
                       lay_down,transfer,HB_gauge,HR_exit,phr,CR_Final,pcr,CASH_PMT,CASH_Dwell,
                       PX_temp,NA_Time,AA_temp,AA_Time,prestrain))
    inputs2 = inputs2.reshape(1,-1)
    inputs=(inputs-inputs_mean)/inputs_std
    inputs_mean2=inputs_mean[0:inputs2.shape[1]]
    inputs_std2=inputs_std[0:inputs2.shape[1]]
    inputs2=(inputs2-inputs_mean2)/inputs_std2
    
    yield_strength = YS_model.predict(inputs)*YS_std+YS_mean
    uts = UTS_model.predict(inputs)*UTS_std+UTS_mean
    elongation = UE_model.predict(inputs)*UE_std+UE_mean
    tot_elongation = TE_model.predict(inputs)*TE_std+TE_mean
    r_value = R_model.predict(inputs)*R_std+R_mean
    beta = Beta_model.predict(inputs)*Beta_std+Beta_mean
    igc = IGC_model.predict(inputs2)*IGC_std+IGC_mean
    
    # return  {"Yield_Strength": (yield_strength[0], None),
    #          "Ultimate_Tensile_Strength": (uts[0], None),
    #          "Uniform_Elongation": (elongation[0], None),
    #          "Total_Elongation": (tot_elongation[0], None),
    #          "R-value": (r_value[0], None),
    #          "Beta_Bending": (beta[0], None),
    #          "IGC_Max": (igc[0], None)}

    data = {"Yield_Strength": (yield_strength[0], None),
                "Uniform_Elongation": (elongation[0], None),}
    
    return data
# example function
# def multiply_vals_by_2(recommendation: Dict[str, float]):
#     for k, v in recommendation.items():
#         recommendation[k] = v*2
#     return recommendation


def ai_physics_v2(recommendation: Dict[str, float]):
    Si=recommendation['Si']
    Fe=recommendation['Fe']
    Cu=recommendation['Cu']
    Mn=recommendation['Mn']
    Mg=recommendation['Mg']
    Cr=recommendation['Cr']
    Ti=recommendation['Ti']
    Zn=recommendation['Zn']
    Zr=recommendation['Zr']
    Sn=recommendation['Sn']
    V=recommendation['V']
    Ge=recommendation['Ge']
    Temp1=recommendation['HO_Step_1_Temp(C)']
    Time1=recommendation['HO_Step_1_Time(hr)']
    Temp2=recommendation['HO_Step_2_Temp(C)']
    Time2=recommendation['HO_Step_2_Time(hr)']
    Temp3=recommendation['HO_Step_3_Temp(C)']
    Time3=recommendation['HO_Step_3_Time(hr)']
    lay_down=recommendation['HR_Lay_Down_Temp(C)']
    transfer=recommendation['HR_Transfer_Slab_Gauge_(IG)']
    HB_gauge=recommendation['HB_gauge']
    HR_exit=recommendation['HR_Exit(C)']
    phr=recommendation['pHR']
    CR_Final=recommendation['CR_Final_Gauge']
    pcr=recommendation['pCR']
    CASH_PMT=recommendation['CASH_PMT']
    CASH_Dwell=recommendation['CASH_Dwell_time_Above_540(sec)']
    PX_temp=recommendation['PX_Temp(C)']
    NA_Time=recommendation['NA_Time(days)']
    AA_temp=recommendation['AA_Temperature(C)']
    AA_Time=recommendation['AA_Time(min)']
    # prestrain=recommendation['Prestrain']
    
    #The following inputs will be provided by Thermo-Calc. These features are
    #automatically added to the same dataframe as the original inputs by the 
    #Thermo-Calc python script (see tc_features_mp.py)
    
    al15si2m4=recommendation['AL15SI2M4']
    diamond_a4=recommendation['DIAMOND_A4']
    fcc_a1=recommendation['FCC_A1']
    # mg2si_c1=recommendation['MG2SI_C1']
    al9fe2si2=recommendation['AL9FE2SI2']
    q_alcumgsi=recommendation['Q_ALCUMGSI']
    si_ss=recommendation['Si_ss']
    fe_ss=recommendation['Fe_ss']
    cu_ss=recommendation['Cu_ss']
    mn_ss=recommendation['Mn_ss']
    mg_ss=recommendation['Mg_ss']
    pcpt_radius=recommendation['pcpt_radius']
    pcpt_volfrac=recommendation['pcpt_volfrac']
    solvus_temp=recommendation['solvus_temp']
    si_pss=recommendation['Si_pss']
    fe_pss=recommendation['Fe_pss']
    cu_pss=recommendation['Cu_pss']
    mn_pss=recommendation['Mn_pss']
    mg_pss=recommendation['Mg_pss']
          
    dict_YS=joblib.load(f'{DEMOS_DIR}/models/new_ai_physics_models/saved_model_YS.joblib')
    YS_model=dict_YS[0]
    YS_mean=dict_YS[1]
    YS_std=dict_YS[2]
    dict_UTS=joblib.load(f'{DEMOS_DIR}/models/new_ai_physics_models/saved_model_UTS.joblib')
    UTS_model=dict_UTS[0]
    UTS_mean=dict_UTS[1]
    UTS_std=dict_UTS[2]
    dict_UE=joblib.load(f'{DEMOS_DIR}/models/new_ai_physics_models/saved_model_UE.joblib')
    UE_model=dict_UE[0]
    UE_mean=dict_UE[1]
    UE_std=dict_UE[2]
    dict_TE=joblib.load(f'{DEMOS_DIR}/models/new_ai_physics_models/saved_model_TE.joblib')
    TE_model=dict_TE[0]
    TE_mean=dict_TE[1]
    TE_std=dict_TE[2]
    dict_R=joblib.load(f'{DEMOS_DIR}/models/new_ai_physics_models/saved_model_R.joblib')
    R_model=dict_R[0]
    R_mean=dict_R[1]
    R_std=dict_R[2]
    dict_Beta=joblib.load(f'{DEMOS_DIR}/models/new_ai_physics_models/saved_model_Beta.joblib')
    Beta_model=dict_Beta[0]
    Beta_mean=dict_Beta[1]
    Beta_std=dict_Beta[2]
    # dict_IGC=joblib.load(f'{DEMOS_DIR}/models/saved_model_IGC.joblib')
    # IGC_model=dict_IGC[0]
    # IGC_mean=dict_IGC[1]
    # IGC_std=dict_IGC[2]
    # dict_inputs=joblib.load(f'{DEMOS_DIR}/models/input_parameters.joblib')
    # inputs_mean=dict_inputs[0]
    # inputs_std=dict_inputs[1]
    
    inputs = np.array((Si,Fe,Cu,Mn,Mg,Cr,Ti,Zn,Zr,Sn,V,Ge,Temp1,Time1,Temp2,Time2,Temp3,Time3,
                       lay_down,transfer,HB_gauge,HR_exit,phr,CR_Final,pcr,CASH_PMT,CASH_Dwell,
                       PX_temp,NA_Time,AA_temp,AA_Time,al15si2m4,diamond_a4,
                       fcc_a1,al9fe2si2,q_alcumgsi,si_ss,fe_ss,cu_ss,mn_ss,mg_ss,pcpt_radius,pcpt_volfrac,
                       solvus_temp,si_pss,fe_pss,cu_pss,mn_pss,mg_pss))
    inputs = inputs.reshape(1, -1)
    inputs2 = np.array((Si,Fe,Cu,Mn,Mg,Cr,Ti,Zn,Zr,Sn,V,Ge,Temp1,Time1,Temp2,Time2,Temp3,Time3,
                       lay_down,transfer,HB_gauge,HR_exit,phr,CR_Final,pcr,CASH_PMT,CASH_Dwell,
                       PX_temp,NA_Time,AA_temp,AA_Time))
    inputs2 = inputs2.reshape(1,-1)
    # inputs=(inputs-inputs_mean)/inputs_std
    # inputs_mean2=inputs_mean[0:inputs2.shape[1]]
    # inputs_std2=inputs_std[0:inputs2.shape[1]]
    # inputs2=(inputs2-inputs_mean2)/inputs_std2
    
    yield_strength = YS_model.predict(inputs)*YS_std+YS_mean
    uts = UTS_model.predict(inputs)*UTS_std+UTS_mean
    elongation = UE_model.predict(inputs)*UE_std+UE_mean
    tot_elongation = TE_model.predict(inputs)*TE_std+TE_mean
    r_value = R_model.predict(inputs)*R_std+R_mean
    beta = Beta_model.predict(inputs)*Beta_std+Beta_mean
    # igc = IGC_model.predict(inputs2)*IGC_std+IGC_mean
    
    # return  {"Yield_Strength": (yield_strength[0], None),
    #          "Ultimate_Tensile_Strength": (uts[0], None),
    #          "Uniform_Elongation": (elongation[0], None),
    #          "Total_Elongation": (tot_elongation[0], None),
    #          "R-value": (r_value[0], None),
    #          "Beta_Bending": (beta[0], None),
    #          "IGC_Max": (igc[0], None)}

    data = {"Yield_Strength": (yield_strength[0], None),
                "Uniform_Elongation": (elongation[0], None),}
    
    return data