import pandas as pd
import numpy as np
#from tc_python import *
import scipy.optimize as opt
#import multiprocessing
#from multiprocessing import Pool
from random import Random
from time import time
from time import sleep
import math
import os
import sys
import json
import logging
import concurrent.futures
sys.setrecursionlimit(10000)

# Generate population within bounds
# helper function

def get_unique_phases(rlist):

    uni_phases = []
    for mixture in rlist.keys():
        phases = mixture.split(' + ')
        for ph in phases: 
            if ph not in ['LIQUID']+uni_phases:
                uni_phases.append(ph)
    
    return uni_phases

def scheil_calc(params):
    elements = ['Si','Fe','Cu','Mn','Mg']
    errcode=0
    t_start=1000.0
    t_step=1.0
    min_liq=0.01
    # List of all phases in the ML models
    phaselist=['FCC_A1','DIAMOND_A4','AL15SI2M4','MG2SI_C1','AL9FE2SI2','AL2CU_C16','Q_ALCUMGSI','AL13FE4','ALMG_BETA','AL6MN']
    phasefrac_dict={}
    try:

        with TCPython():
            #Scheil calculation setup
            scheil_calc = (SetUp()
                           .select_database_and_elements("TCAL8", ["Al","Si","Fe","Cu","Mn","Mg"])
                           .without_default_phases()
                           .select_phase('LIQUID')
                           .select_phase('FCC_A1')
                           .select_phase('DIAMOND_A4')
                           .select_phase('AL15SI2M4')
                           .select_phase('MG2SI_C1')
                           .select_phase('AL9FE2SI2')
                           .select_phase('AL2CU_C16')
                           .select_phase('Q_ALCUMGSI')
                           .select_phase('AL13FE4')
                           .select_phase('ALMG_BETA')
                           .select_phase('AL6MN')
                           .get_system()
                           .with_scheil_calculation()
                           .with_options(ScheilOptions().set_temperature_step(t_step))
                           .with_options(ScheilOptions().terminate_on_fraction_of_liquid_phase(min_liq))
                           .enable_global_minimization()
                           .set_start_temperature(t_start)
                           .set_composition_unit(CompositionUnit.MASS_PERCENT) 
                           )
      
                # Using the solid solution composition, run the precipitation calculation. 
                # Composition in MASS FRACTION
            for el in elements:
                scheil_calc.set_composition(el,params[el])
    
            scheil_result=scheil_calc.calculate()
            
            # Get the list of phases in the system
            rlist = scheil_result.get_values_grouped_by_stable_phases_of(ScheilQuantity.temperature(),ScheilQuantity.mole_fraction_of_all_solid_phases())
            phases = get_unique_phases(rlist)
            
            for ph in phaselist:
                if ph in phases: # Check if the phase is available 
                    # get fractions of each phase at different T
                    phasefrac=scheil_result.get_values_of(ScheilQuantity.mass_fraction_of_a_solid_phase(ph),ScheilQuantity.temperature())
                    phasefrac = np.asarray(phasefrac)

                    # find mole fraction at lowest T
                    f = phasefrac[0,:]
                    t = phasefrac[1,:]
                    idx = np.argmin(t)

                    # add value to dataframe
                    phasefrac_dict[ph] = f[idx]
                else:
                    phasefrac_dict[ph] = 0

    
    except UnrecoverableCalculationException:
        errcode=1
        print("Could not calculate PCPT unrecoverable")
    except DatabaseException:
        #precipitate_radius.append(10)
        #precipitate_volfrac.append(0)
        errcode=-1  
        print("Database error")
    except LicenseException:
        #precipitate_radius.append(0)
        #precipitate_volfrac.append(0)
        errcode=-2
        print("License exception")
    except CalculationException:
        #precipitate_radius.append(0)
        #precipitate_volfrac.append(0)
        errcode=-3
        print("License busy Calc exception")    
        
    ## If there is error code, return None value for the function 
    
    if errcode==1:
        for ph in phaselist:
            phasefrac_dict[ph]=1E-10
        return phasefrac_dict
    elif errcode < 0:
        for ph in phaselist:
            phasefrac_dict[ph]=0
        return phasefrac_dict
    else:    
        return phasefrac_dict
    
def solidus(params):
    elements = ['Si','Fe','Cu','Mn','Mg']
    errcode=0

    try:
        with TCPython():
            #Eqm calculation setup
            eqm_calc = (SetUp()
                           .select_database_and_elements("TCAL8", ["Al","Si","Fe","Cu","Mn","Mg"])
                           .get_system()
                           .with_single_equilibrium_calculation()
                           .enable_global_minimization()
                           )
            if (float(params['Mg'])+float(params['Si'])+float(params['Cu'])) < 1.2:
                eqm_calc.set_condition(ThermodynamicQuantity.temperature(), 900.0)
            else:
                eqm_calc.set_condition(ThermodynamicQuantity.temperature(), 850.0)
            # Composition in MASS FRACTION
            for el in elements:
                eqm_calc.set_condition(ThermodynamicQuantity.mass_fraction_of_a_component(el),float(params[el])/100.0)
            
            eqm_result = eqm_calc.calculate()
            
            #calculate liquidus temperature and list stable phases
            eqm_result = (eqm_calc
                  .remove_condition(ThermodynamicQuantity.temperature())
                  .set_phase_to_fixed("LIQUID", 0.0)
                  .calculate())
            solidustemp=eqm_result.get_value_of(ThermodynamicQuantity.temperature())     

    except UnrecoverableCalculationException:
        errcode=4
        solidustemp=273
        print("Could not calculate PCPT unrecoverable")
    except DatabaseException:
        errcode=1
        solidustemp=0        
        print("Database error")
    except LicenseException:
        errcode=3
        solidustemp=0
        print("License exception")
    except CalculationException:
        errcode=2
        print("Calculation exception")
        solidustemp=850.0
    
    return solidustemp


def solvus(params):
    elements = ['Si','Fe','Cu','Mn','Mg']
    errcode=0

    try:
        with TCPython():
            #Eqm calculation setup
            eqm_calc = (SetUp()
                           .select_database_and_elements("TCAL8", ["Al","Si","Fe","Cu","Mn","Mg"])
                           .get_system()
                           .with_single_equilibrium_calculation()
                           .enable_global_minimization()
                           .with_options(SingleEquilibriumOptions().set_required_accuracy(1e-4))
                           )
            
            if float(params['Mg']) < 0.6:
                eqm_calc.set_condition(ThermodynamicQuantity.temperature(), 700.0)
            elif float(params['Mg']) > 1.0:
                eqm_calc.set_condition(ThermodynamicQuantity.temperature(), 820.0)
            else:
                eqm_calc.set_condition(ThermodynamicQuantity.temperature(), 770.0)
            
            # Composition in MASS FRACTION
            for el in elements:
                eqm_calc.set_condition(ThermodynamicQuantity.mass_fraction_of_a_component(el),float(params[el])/100.0)
            
            eqm_result = eqm_calc.calculate()
            
            # calculate solidus temperature
            eqm_result = (eqm_calc
                   .remove_condition(ThermodynamicQuantity.temperature())
                   .set_phase_to_fixed("MG2SI_C1", 0.0)
                   .calculate())
            solvtemp=eqm_result.get_value_of(ThermodynamicQuantity.temperature())   
    
    except UnrecoverableCalculationException:
        errcode=4
        solvtemp=273
        print("Could not calculate PCPT unrecoverable")
    except DatabaseException:
        errcode=1  
        print("Database error")
        solvtemp=0
    except LicenseException:
        errcode=3
        solvtemp=0
        print("License exception")
    except CalculationException:
        errcode=2
        print("Calculation exception")
        print(params)
        solvtemp=720.0
            
    return solvtemp

# Calculation of solid solution concentration at solutionizing temperature (CASH_PMT)
def cash_ss(params):
    elements = ['Si','Fe','Cu','Mn','Mg']
    errcode=0

    try:
        with TCPython():
            #Eqm calculation setup
            eqm_calc = (SetUp()
                           .select_database_and_elements("TCAL8", ["Al","Si","Fe","Cu","Mn","Mg"])
                           .get_system()
                           .with_single_equilibrium_calculation()
                           .enable_global_minimization()
                           )
            
            eqm_calc.set_condition(ThermodynamicQuantity.temperature(), float(params['temp']+273.15))
            
            # Composition in MASS FRACTION
            for el in elements:
                eqm_calc.set_condition(ThermodynamicQuantity.mass_fraction_of_a_component(el),float(params[el])/100)
            
            eqm_result = eqm_calc.calculate()
            
            # calculate eqm composition in solid solution
            eqm_composition={}
            for el in elements:
                eqm_composition[el]=eqm_result.get_value_of(ThermodynamicQuantity.composition_of_phase_as_weight_fraction("FCC_A1",el))
    
    except UnrecoverableCalculationException:
        errcode=4
        eqm_composition={}
        for el in elements:
            eqm_composition[el]=0.00001
        print("Could not calculate PCPT unrecoverable")
    except DatabaseException:
        errcode=1
        eqm_composition={}
        for el in elements:
            eqm_composition[el]=0        
        print("Database error")
    except LicenseException:
        errcode=2
        eqm_composition={}
        for el in elements:
            eqm_composition[el]=0
        print("License exception")
    except CalculationException:
        errcode=3
        eqm_composition={}
        for el in elements:
            eqm_composition[el]=float(params[el]/100)  # If there is a problem with calculation return the original composition
        print("Calculation exception")
    return eqm_composition
    
# Precipitation calculation
def pcpt_calc(params):
  
    errcode=0
    ## Calculation setup
    dependent_element = "Al"
    elements = ['Si','Fe','Cu','Mn','Mg'] #,'Cr','Ti','Zn','Zr','Sn','V']
    try:

        with TCPython():
            #Precipitation calculation setup
            precipitate_calc = (SetUp()
                           .select_thermodynamic_and_kinetic_databases_with_elements("TCAL8","MOBAL7", ["Al","Si","Fe","Cu","Mn","Mg"])
                           .get_system()
                           .with_isothermal_precipitation_calculation()
                           .set_composition_unit(CompositionUnit.MASS_FRACTION) 
                           .with_matrix_phase(MatrixPhase("FCC_A1")
                                             .set_mobility_enhancement_prefactor(params['mobfact'])
                                             .with_elastic_properties_cubic(108.2,61.3,28.5)
                                             .add_precipitate_phase(PrecipitatePhase("BETA_DPRIME")
                                                                   .set_interfacial_energy(params['inten1'])  #in J/m2
                                                                   .set_nucleation_in_bulk(params['nsites'])
                                                                   .with_growth_rate_model(GrowthRateModel.SIMPLIFIED)
                                                                   )
                                              )
	    
                           )
	       
            precipitate_calc.set_temperature(params['aa_temp'])
            precipitate_calc.set_simulation_time(params['aa_time'])
                # Using the solid solution composition, run the precipitation calculation. 
                # Composition in MASS FRACTION
            for el in elements:
                precipitate_calc.set_composition(el,params[el])
	    
            precipitate_result=precipitate_calc.calculate()
	    
            time_1, volfrac = precipitate_result.get_volume_fraction_of("BETA_DPRIME")
            time_1, mean_radius = precipitate_result.get_mean_radius_of("BETA_DPRIME")
            
            time1,sipss=precipitate_result.get_matrix_composition_in_weight_fraction_of("Si")
            if len(sipss) > 0:
                Si_pss=sipss[-1]*float(100) # convert mass fraction to wt%
            else:
                Si_pss=0
            time1,fepss=precipitate_result.get_matrix_composition_in_weight_fraction_of("Fe")
            if len(fepss)>0:
                Fe_pss=fepss[-1]*float(100)
            else:
                Fe_pss=0
            time1,cupss=precipitate_result.get_matrix_composition_in_weight_fraction_of("Cu")
            if len(cupss)>0:
                Cu_pss=cupss[-1]*float(100)
            else:
                Cu_pss=0
            time1,mnpss=precipitate_result.get_matrix_composition_in_weight_fraction_of("Mn")
            if len(mnpss)>0:
                Mn_pss=mnpss[-1]*float(100)
            else:
                Mn_pss=0
            time1,mgpss=precipitate_result.get_matrix_composition_in_weight_fraction_of("Mg")
            if len(mgpss)>0:
                Mg_pss=mgpss[-1]*float(100)
            else:
                Mg_pss=0
                
        if len(mean_radius)> 0:
            precipitate_radius=mean_radius[-1]
        else:
            precipitate_radius=0
            
        if len(volfrac) > 0:
            precipitate_volfrac=volfrac[-1]
        else:
            precipitate_volfrac=0

	    
    except UnrecoverableCalculationException:
        print("Could not calculate PCPT unrecoverable")
    except DatabaseException:
        #precipitate_radius.append(10)
        #precipitate_volfrac.append(0)
        errcode=1  
        print("Database error")
    except LicenseException:
        #precipitate_radius.append(0)
        #precipitate_volfrac.append(0)
        errcode=3
        print("License exception")
    except CalculationException:
        #precipitate_radius.append(0)
        #precipitate_volfrac.append(0)
        errcode=2
        print("Calculation exception")        

## If there is error code, return None value for the function 
    if errcode==2:
        return 1E-20,1E-20,0,0,0,0,0    
    elif errcode>0:
        return 0,0,0,0,0,0,0
    else:
    #if errcode==0:
	#precipitate_calc.invalidate()  
        #datapcp={'pcpt_radius1':precipitate_radius,'pcpt_volfrac1':precipitate_volfrac,'pcpt_radius2':precipitate_radius_2,'pcpt_volfrac2':precipitate_volfrac_2}
        #df_pcpt=pd.DataFrame(datapcp)
        return precipitate_radius,precipitate_volfrac,Si_pss,Fe_pss,Cu_pss,Mn_pss,Mg_pss


def orowan(volfrac,radius):
    pi=3.141592653589793
    M=3.06 # Mean matrix orientation factor for Al
    G=25.4e9 # Shear modulus of Al at RT in GPa
    b=2.86e-10 # Burger's vector for Al in nm
    v=0.34 # Matrix Possion ratio
    lamda=(math.sqrt(3*pi/4/volfrac)-1.64)*radius
    return (M*(0.4/pi)*(G*b)/math.sqrt(1-v)*math.log(2*radius/b)/lamda)/1e6

def shearing(volfrac,radius,m,apb,alpha,pcptno):
    pi=3.141592653589793
    G=25.4e9 # Shear modulus of Al at RT in GPa
    b=2.86e-10 # Burger's vector for Al in nm
    
    G_beta=34.2e9 # shear modulus of Beta'' - Mg5Si6 . Zhang, B., et. al J Mater Sci 50, 6498–6509 (2015). Another paper reports G of Beta'' as 25 GPa. R. Yu et al. Computer Physics Communications 181 (2010) 671–675
    G_Q=43.6e9 # Shear modulus of Q-phase - Al5Cu2Mg8Si6 Y. Ouyang et al Comp. Mater. Sci. 67 (2013) 334.
    if pcptno == 1:
        deltaG=float(G_beta - G) # Shear modulus mismatch between matrix and precipitates
        eps=(2/3)*0.01 # lattice mismatch btw Beta'' and Al is 3.8% and 5.3% along a and c axes, 0% in b axis respectively.  
    if pcptno == 2:
        deltaG=float(G_Q - G)
        eps=(2/3)*0.01 # 0.012 is the lattice mismatch btw Al/Q-phase lattice mismatch is 1.1 and 1.3% along a and c directions respectively. Taking the average. 
    
    M=3.06 # Mean matrix orientation factor for Al
    s1=(0.81*M*apb/2/b*math.sqrt(3*pi*volfrac/8))/1e6
    s2=(M*alpha*((G*eps)**(3/2))*math.sqrt(radius*volfrac/0.5/G/b))/1e6
    s3=(0.0055*M*deltaG**(3/2)*math.sqrt(2*volfrac/G)*(radius/b)**(3*m/2 - 1))/1e6
    if s1 > s2+s3:
        return s1
    else:
        return s2+s3
    
def rcritic(radius,volfrac,apb,m,alpha,pcptno):
    #apb=0.5 # Anti-phase boundary energy for Al3Sc in J/m2
    #m=0.85 # Constant
    #alpha=2.6 #constant
    #volfrac=0.0075 # 0.75% taken as constant
    ow=orowan(volfrac,radius)
    shr=shearing(volfrac,radius,m,apb,alpha,pcptno)
    return ow - shr

def ysfunc(params):

    #Parameters in Seidman's strength model
    sd_apb1=0.28821681 #float(x[3]) #0.129573475   #Antiphase boundary energy of Beta'' from TCAL8
    sd_m1=0.97033686 #float(x[4])  #0.85   # constant
    sd_alpha1=3.66810248 #float(x[5])  #2.6  # constant
    
    [precipitate_radius,precipitate_volfrac,si_pss,fe_pss,cu_pss,mn_pss,mg_pss] = pcpt_calc(params)
    
    ## For Beta''
    pcptno=1
    
    volf= precipitate_volfrac
    radi= precipitate_radius
    if volf < 1e-20:
        volf=1e-20
        ys_cal=0.1
    else: 
        rc = opt.brentq(lambda xi: rcritic(xi,volf,sd_apb1,sd_m1,sd_alpha1,pcptno), 5e-10, 2e-8)
        if radi > rc:
            ys_cal=orowan(volf,radi)
        else:
            ys_cal=shearing(volf,radi,sd_m1,sd_apb1,sd_alpha1,pcptno)

    datays={'ys_cal':ys_cal,'pcpt_radius':precipitate_radius,'pcpt_volfrac':precipitate_volfrac,'Si_pss':si_pss,'Fe_pss':fe_pss,'Cu_pss':cu_pss,'Mn_pss':mn_pss,'Mg_pss':mg_pss}    
    
    return datays   

def actual_fun():
    aa_temp = param['AA_Temperature(C)'] # in Celcius
    aa_time = param['AA_Time(min)'] # in mints
    temper = param['temper']
    elements = ['Si','Fe','Cu','Mn','Mg']

    # Set elemental compositions for Scheil calculations, Mg2Si solvus and Liquidus temperatures
    scheilparams = {el: param[el] for el in elements}

    # Calculate phase fractions from Scheil calculations
    scheil_phase_frac = scheil_calc(scheilparams)

    # Calculate Mg2Si solvus and solidus temperatures
    solvus_temp = float(solvus(scheilparams) - 273.15)
    solidus_temp = float(solidus(scheilparams) - 273.15)

    # Set Homogenization temperature based on solvus and liquidus
    ho_temp = float(solidus_temp - 20)
    cash_temp = param['CASH_PMT']

    # Set elemental compositions for equilibrium calculation at solutionizing (CASH) temperature
    cashssparams = {el: param[el] for el in elements}

    # Calculate solid solution concentration at CASH temperature
    cashssparams['temp'] = cash_temp
    cashss = cash_ss(cashssparams)

    if temper == 'T4':
        yscalc = {'ys_cal': 0, 'pcpt_radius': 0, 'pcpt_volfrac': 0, 'Si_pss': 0, 'Fe_pss': 0, 'Cu_pss': 0, 'Mn_pss': 0, 'Mg_pss': 0}
    else:
        ysparams={}
        # Set elemental compositions based on the solid solution concentration at CASH temperature
        for el in elements:
            ysparams[el]=cashss[el]
        # Set precipitation calculation parameters for TC-PRISMA
        ysparams['aa_temp']=float(aa_temp)+273.15
        ysparams['aa_time'] = float(aa_time)*60  # convert to seconds
        ysparams['mobfact'] = 11.95228622   # mobility enhancement factor
        ysparams['inten1']=0.10771376    # interface energy of Al/Beta''
        ysparams['nsites']=float(9.11660705E28) #Number of nucleation sites

        yscalc=ysfunc(ysparams)

    # Add all the TC calculated features to a new dictionary
    param_output = param.copy()
    param_output['HO_Avg_Temp(C)'] = ho_temp
    param_output['FCC_A1'] = scheil_phase_frac['FCC_A1']
    param_output['DIAMOND_A4']=scheil_phase_frac['DIAMOND_A4']
    param_output['AL15SI2M4']=scheil_phase_frac['AL15SI2M4']
    param_output['MG2SI_C1']=scheil_phase_frac['MG2SI_C1']
    param_output['AL9FE2SI2']=scheil_phase_frac['AL9FE2SI2']
    param_output['AL2CU_C16']=scheil_phase_frac['AL2CU_C16']
    param_output['Q_ALCUMGSI']=scheil_phase_frac['Q_ALCUMGSI']
    param_output['AL13FE4']=scheil_phase_frac['AL13FE4']
    param_output['ALMG_BETA']=scheil_phase_frac['ALMG_BETA']
    param_output['AL6MN']=scheil_phase_frac['AL6MN']

    for el in elements:
        param_output[el + '_ss'] = float(cashss[el] * 100)

    param_output['ys_cal'] = yscalc['ys_cal']
    param_output['pcpt_radius']=yscalc['pcpt_radius']
    param_output['pcpt_volfrac']=yscalc['pcpt_volfrac']
    param_output['solvus_temp']=solvus_temp
    param_output['solidus_temp']=solidus_temp

    for el in elements:
        param_output[el+'_pss']=yscalc[el+'_pss']

    return param_output
    
    
def perform_operations(params):
    df = pd.DataFrame(params)
    df['Mean'] = df.mean(axis=1)
    df['Sum'] = df.sum(axis=1)
    df['Product'] = df.prod(axis=1)
    df_return=df.to_dict(orient='records')
    return df_return
    
    
#def perform_prediction2(params):
#   output_list= [{""}]
    

    
def perform_predictions(params):
    output_list = []
    for param in params:
        
        aa_temp = param['AA_Temperature(C)'] # in Celcius
        aa_time = param['AA_Time(min)'] # in mints
        temper = param['temper']
        elements = ['Si','Fe','Cu','Mn','Mg']

        # Set elemental compositions for Scheil calculations, Mg2Si solvus and Liquidus temperatures
        scheilparams = {el: param[el] for el in elements}

        # Calculate phase fractions from Scheil calculations
        scheil_phase_frac = scheil_calc(scheilparams)

        # Calculate Mg2Si solvus and solidus temperatures
        solvus_temp = float(solvus(scheilparams) - 273.15)
        solidus_temp = float(solidus(scheilparams) - 273.15)

        # Set Homogenization temperature based on solvus and liquidus
        ho_temp = float(solidus_temp - 20)
        cash_temp = param['CASH_PMT']

        # Set elemental compositions for equilibrium calculation at solutionizing (CASH) temperature
        cashssparams = {el: param[el] for el in elements}

        # Calculate solid solution concentration at CASH temperature
        cashssparams['temp'] = cash_temp
        cashss = cash_ss(cashssparams)

        if temper == 'T4':
            yscalc = {'ys_cal': 0, 'pcpt_radius': 0, 'pcpt_volfrac': 0, 'Si_pss': 0, 'Fe_pss': 0, 'Cu_pss': 0, 'Mn_pss': 0, 'Mg_pss': 0}
        else:
            ysparams={}
            # Set elemental compositions based on the solid solution concentration at CASH temperature
            for el in elements:
                ysparams[el]=cashss[el]
            # Set precipitation calculation parameters for TC-PRISMA
            ysparams['aa_temp']=float(aa_temp)+273.15
            ysparams['aa_time'] = float(aa_time)*60  # convert to seconds
            ysparams['mobfact'] = 11.95228622   # mobility enhancement factor
            ysparams['inten1']=0.10771376    # interface energy of Al/Beta''
            ysparams['nsites']=float(9.11660705E28) #Number of nucleation sites

            yscalc=ysfunc(ysparams)

        # Add all the TC calculated features to a new dictionary
        param_output = param.copy()
        param_output['HO_Avg_Temp(C)'] = ho_temp
        param_output['FCC_A1'] = scheil_phase_frac['FCC_A1']
        param_output['DIAMOND_A4']=scheil_phase_frac['DIAMOND_A4']
        param_output['AL15SI2M4']=scheil_phase_frac['AL15SI2M4']
        param_output['MG2SI_C1']=scheil_phase_frac['MG2SI_C1']
        param_output['AL9FE2SI2']=scheil_phase_frac['AL9FE2SI2']
        param_output['AL2CU_C16']=scheil_phase_frac['AL2CU_C16']
        param_output['Q_ALCUMGSI']=scheil_phase_frac['Q_ALCUMGSI']
        param_output['AL13FE4']=scheil_phase_frac['AL13FE4']
        param_output['ALMG_BETA']=scheil_phase_frac['ALMG_BETA']
        param_output['AL6MN']=scheil_phase_frac['AL6MN']

        for el in elements:
            param_output[el + '_ss'] = float(cashss[el] * 100)
        
        param_output['ys_cal'] = yscalc['ys_cal']
        param_output['pcpt_radius']=yscalc['pcpt_radius']
        param_output['pcpt_volfrac']=yscalc['pcpt_volfrac']
        param_output['solvus_temp']=solvus_temp
        param_output['solidus_temp']=solidus_temp
        
        for el in elements:
            param_output[el+'_pss']=yscalc[el+'_pss']

        output_list.append(param_output)

    return output_list

def get_input_output_features():

    return [['Si', 'Fe', 'Cu', 'Mn', 'Mg', 'AA_Temperature(C)', 'AA_Time(min)', 'CASH_PMT', 'temper'], ['Si', 'Fe', 'Cu', 'Mn', 'Mg', 'AA_Temperature(C)', 'AA_Time(min)',

       'CASH_PMT', 'temper', 'HO_Avg_Temp(C)', 'FCC_A1', 'DIAMOND_A4',

       'AL15SI2M4', 'MG2SI_C1', 'AL9FE2SI2', 'AL2CU_C16', 'Q_ALCUMGSI',

       'AL13FE4', 'ALMG_BETA', 'AL6MN', 'Si_ss', 'Fe_ss', 'Cu_ss', 'Mn_ss',

       'Mg_ss', 'ys_cal', 'pcpt_radius', 'pcpt_volfrac', 'solvus_temp',

       'solidus_temp', 'Si_pss', 'Fe_pss', 'Cu_pss', 'Mn_pss', 'Mg_pss']]
