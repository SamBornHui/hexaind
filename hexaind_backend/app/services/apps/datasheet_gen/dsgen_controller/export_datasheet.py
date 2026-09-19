import glob
from pathlib import Path
import json
import os
import pickle
import traceback
import pandas as pd
import numpy as np
import datetime as dt
from fpdf import FPDF
import app.services.apps.datasheet_gen.dsgen_controller.datasheet_report as dsr
from  app.services.apps.datasheet_gen.dsgen_controller.fitting import models, objectives
from  app.services.apps.datasheet_gen.dsgen_controller.utils.mech_properties import compute_bulge_scaling_factor
from app.env import *
import zipfile
import io
import logging
import sys 
logger = logging.getLogger(__package__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

def read_csv(projectId,datasheet,nominal_age,file_name):

    output_directory = os.path.join(EXPORT_PATH, str(projectId), str(datasheet), str(nominal_age))
    csv_file_path = os.path.join(output_directory, file_name)
    df_data = pd.read_csv(csv_file_path)
    return df_data

def read_json(projectId,datasheet,nominal_age,file_name):
    output_directory = os.path.join(EXPORT_PATH, str(projectId), str(datasheet), str(nominal_age))
    json_file_path = os.path.join(output_directory, file_name)
    with open(json_file_path, 'r') as json_file:
        data_str_keys = json.load(json_file)
    return data_str_keys

def read_pkl(projectId, datasheet,nominal_age,file_name):
    output_directory = os.path.join(EXPORT_PATH, str(projectId), str(datasheet), str(nominal_age))
    pkl_file_path = os.path.join(output_directory, file_name)
    with open(pkl_file_path, 'rb') as pkl_file:
       loaded_data = pickle.load(pkl_file)

    return loaded_data

def get_tensile_results(df_data):
    df_data.loc[:, 'Ag'] *= 100
    df_data.loc[:, 'A80'] *= 100
    df_data['load_direction'] = df_data['load_direction'].astype(float)
    col_multiindex = [
        ('Aging', 'days'),
        ('Test direction', 'deg'),
        ('Rp02', 'MPa'),
        ('Rm', 'MPa'),
        ('Ag', '%'),
        ('A80', '%'),
        ('n4-6', '-'),
        ('n10-20', '-'),
        ('r8-12', '-')
    ]

    df_data.columns = pd.MultiIndex.from_tuples(col_multiindex)

    # Cast age to integer
    df_data = df_data.astype(
        {
            ('Aging', 'days'): int
        }
    )
    # Cast test direction to integer if all values are integers
    test_dir_integer = df_data[('Test direction', 'deg')].apply(float.is_integer).all()

    if test_dir_integer:
        df_data = df_data.astype(
            {
                ('Test direction', 'deg'): int
            }
        )
    df_data
    # Group by age/direction and take the mean
    df_tensile_results = df_data.groupby([('Aging', 'days'), ('Test direction', 'deg')]).mean()

    # Convert columns to numeric types before formatting
    
        # # Format Rp02 and Rm to no decimals
    df_tensile_results.loc[:, ('Rp02', 'MPa')] = df_tensile_results.loc[:, ('Rp02', 'MPa')].apply(lambda x: f"{x:.0f}")
    df_tensile_results.loc[:, ('Rm', 'MPa')] = df_tensile_results.loc[:, ('Rm', 'MPa')].apply(lambda x: f"{x:.0f}")

    # Format Ag and A80 to one decimal
    df_tensile_results.loc[:, ('Ag', '%')] = df_tensile_results.loc[:, ('Ag', '%')].apply(lambda x: f"{x:.1f}")
    df_tensile_results.loc[:, ('A80', '%')] = df_tensile_results.loc[:, ('A80', '%')].apply(lambda x: f"{x:.1f}")

    # Format n and r-values to 2 decimals
    df_tensile_results.loc[:, ('n4-6', '-')] = df_tensile_results.loc[:, ('n4-6', '-')].apply(lambda x: f"{x:.2f}")
    df_tensile_results.loc[:, ('n10-20', '-')] = df_tensile_results.loc[:, ('n10-20', '-')].apply(lambda x: f"{x:.2f}")
    df_tensile_results.loc[:, ('r8-12', '-')] = df_tensile_results.loc[:, ('r8-12', '-')].apply(lambda x: f"{x:.2f}")

    # Convert everything to str to preserve correct formatting when showing on the page
    df_tensile_results = df_tensile_results.astype(str)
    return df_tensile_results

def get_model_parameters(dict_params_to_insert,selected_datasheet, selected_nominal_age):
    model_name = 'hocket_sherby_swift'
    dict_params_to_insert
    param_values = {}
    desired_key = (selected_datasheet, selected_nominal_age, model_name)
    # Check if the key is present in the modelParams dictionary
    if desired_key in dict_params_to_insert:
        # Get the dictionary corresponding to the desired key
        desired_dict = dict_params_to_insert[desired_key]

        # Iterate through the inner dictionary and extract parameter values
        for subkey, subvalue in desired_dict.items():
            param_values[subkey] = subvalue.get('param_value')
    df_model_params = pd.DataFrame([param_values])
    param_values['Aging days']=selected_nominal_age
    # Display the extracted parameter values
    
    df_model_params = pd.DataFrame([param_values])
    df_model_params.set_index('Aging days', inplace=True)
    return df_model_params

def get_model_latex(model_name):

    # TODO: Dynamically compute latex formula with sympy (or something else)
    if model_name == 'hocket_sherby_swift':

        model_latex =\
            r"\sigma = \left( 1 - \alpha \right)" +\
            r"C \left( \varepsilon_{pl}  + \varepsilon_{0} \right)^{m}" +\
            r"+ \alpha \left( \sigma_{sat} - \left(\sigma_{sat} - \sigma_{i}\right)e^{-a\varepsilon_{pl}^{p}} \right)"
        
    return model_latex

def get_flc_raw(flc_raw):
    flc_raw_df = flc_raw[0]['df']
    
    # Convert 's_major' and 's_minor' columns to numeric, handling None values
    flc_raw_df['s_major'] = pd.to_numeric(flc_raw_df['s_major'], errors='coerce')
    flc_raw_df['s_minor'] = pd.to_numeric(flc_raw_df['s_minor'], errors='coerce')
    
    # Filter rows where 's_major' > 0
    df_raw_filtered = flc_raw_df[flc_raw_df['s_major'] > 0]
    
    # Group by 'spl_geom' and 'spl_nr' and calculate the mean for 's_major' and 's_minor'
    df_raw_grouped = df_raw_filtered.groupby(['spl_geom', 'spl_nr'])[['s_major', 's_minor']].mean().reset_index()
    
    # Filter rows where s_major > 0
    df_flc_raw = df_raw_grouped[df_raw_grouped['s_major'] > 0][['s_minor', 's_major']]
    
    return df_flc_raw

def get_flc_fit(flc_fit):
    flc_fit_df = flc_fit[0]['df']

    # Convert 's_major' and 's_minor' columns to numeric, handling None values
    flc_fit_df['s_major'] = pd.to_numeric(flc_fit_df['s_major'], errors='coerce')
    flc_fit_df['s_minor'] = pd.to_numeric(flc_fit_df['s_minor'], errors='coerce')
    flc_fit_df['s_major_plus_sigma'] = pd.to_numeric(flc_fit_df['s_major_plus_sigma'], errors='coerce')
    flc_fit_df['s_major_minus_sigma'] = pd.to_numeric(flc_fit_df['s_major_minus_sigma'], errors='coerce')

    # Filter rows where s_major > 0
    # df_flc_raw = flc_df[flc_df['s_major'] > 0][['s_minor', 's_major']]
    df_flc_fit = flc_fit_df

    return df_flc_fit

def get_scale_factor(test,E, Rp02, Rm, Ag, Agt):
    k = compute_bulge_scaling_factor(E, Rm, Ag, test.data.sig_1, test.data.eps_1)
    k_mean = k
    return k_mean

def get_yield_surface_data(com_df_data, df_scale_factor):
    df_yield= com_df_data

    df_yield['load_direction'] = df_yield['load_direction'].astype(float)

    df_yield = df_yield[['Rp02', 'r8_12','load_direction','nominal_age']]


    test_dir_integer = df_yield['load_direction'].apply(float.is_integer).all()
    if test_dir_integer:
        df_yield = df_yield.astype(
            {
                'load_direction': int
            }
        )
    df_yield = df_yield.groupby(['nominal_age', 'load_direction']).mean()
    df_yield = df_yield.reset_index().set_index('nominal_age')
    df_yield_pivot = pd.pivot_table(
        df_yield,
        values=['r8_12', 'Rp02'],
        index=df_yield.index,
        columns=['load_direction']
    )

    sigma_scaled = df_yield_pivot.loc[:, 'Rp02'].divide(df_yield_pivot.loc[:, ('Rp02', 0)], axis='index').values
    df_yield_pivot.loc[:, 'Rp02'] = sigma_scaled
    # Rearrange and rename columns
    df_yield_pivot = df_yield_pivot.loc[:, ['r8_12', 'Rp02']]
    df_yield_pivot = df_yield_pivot.rename(columns={'r8_12': 'r8-12'})
    # NOTE: THE ORDER IS IMPORTANT AND CORRECTLY SET LIKE THIS (why?)
    # Setting levels like ['σi/σ0', 'r8-12'] will result in 'r8-12' being in front of 'σi/σ0' in the df
    df_yield_pivot.columns = df_yield_pivot.columns.set_levels(['σi/σ0', 'r8-12'], level=0)
    
    df_yield_pivot.loc[:, ('σb/σ0', '')] = df_scale_factor.values
    # Insert rbi column
    nb_rcols = df_yield_pivot['r8-12'].shape[1]
    df_yield_pivot.insert(nb_rcols, 'rbi', 1.0)
    df_yield_pivot.index = df_yield_pivot.index.astype(int)

    df_yield_pivot.index.names = [('Aging', 'days')]
    # Format the dataframe code changed can be removed after testing by client
    # df_yield_pivot.loc[:, 'r8-12'] = df_yield_pivot.loc[:, 'r8-12'].apply(
    # lambda series: series.apply(lambda x: f"{x:.2f}")
    # ).values
    # df_yield_pivot.loc[:, 'rbi'] = df_yield_pivot.loc[:, 'rbi'].apply(lambda x: f"{x:.2f}")
    # df_yield_pivot.loc[:, 'σi/σ0'] = df_yield_pivot.loc[:, 'σi/σ0'].apply(
    # lambda series: series.apply(lambda x: f"{x:.3f}")
    # ).values
    # df_yield_pivot.loc[:, ('σb/σ0', '')] = df_yield_pivot.loc[:, ('σb/σ0', '')].apply(lambda x: f"{x:.3f}")
    df_yield_pivot['r8-12'] = df_yield_pivot['r8-12'].apply(lambda x: [float(i) for i in x.strip('[]').split(', ')] if isinstance(x, str) else x)
    df_yield_pivot['r8-12'] = df_yield_pivot['r8-12'].apply(lambda series: [f"{x:.2f}" for x in series])

    # Ensure that 'rbi' values are floats before formatting
    df_yield_pivot['rbi'] = df_yield_pivot['rbi'].apply(lambda x: f"{float(x):.2f}" if not pd.isnull(x) else x)

    # Ensure that 'σi/σ0' values are lists of floats before formatting
    df_yield_pivot['σi/σ0'] = df_yield_pivot['σi/σ0'].apply(lambda x: [float(i) for i in x.strip('[]').split(', ')] if isinstance(x, str) else x)
    df_yield_pivot['σi/σ0'] = df_yield_pivot['σi/σ0'].apply(lambda series: [f"{x:.3f}" for x in series])

    # Ensure that 'σb/σ0' values are floats before formatting
    df_yield_pivot[('σb/σ0', '')] = df_yield_pivot[('σb/σ0', '')].apply(lambda x: f"{float(x):.3f}" if not pd.isnull(x) else x)

    df_yield_pivot = df_yield_pivot.round(3)
    
    return df_yield_pivot

def compile_ds_data(
    ds_meta, model_name,
    df_tensile_results,
    df_flc_raw, df_flc_fit,
    df_model_params, df_model_data, model_latex,
    df_yield
):

    ds_data = {}

    # Add the meta information
    ds_data.update(ds_meta)

    # Add the datasheeet data
    ds_data.update({

        # Tensile test results
        'df_tensile_results': df_tensile_results,

        # FLC data
        'df_flc_raw': df_flc_raw,
        'df_flc_fit': df_flc_fit,

        # Hardening and aging plot data
        'df_model_data': df_model_data,

        # Model fitting
        'model_name': model_name,
        'model_latex': model_latex,
        'df_model_params': df_model_params,

        # Yield surface
        'df_yield': df_yield
    })

    return ds_data

def create_datasheet_report(ds_data, selected_nominal_age, projectId):
    datasheet = ds_data['datasheet']
    nominal_age = selected_nominal_age
    
    comm_name = ds_data['commercial_name'].replace(" ", "_")
    if ds_data['gauge'] == int(ds_data['gauge']):
        gauge = f"{ds_data['gauge']:.1f}mm"  
    else:
        gauge = f"{ds_data['gauge']}mm"  
    gauge = gauge.replace(".", "-")
    source_map = {
        "Europe": "NE",
        "North America": "NNA",
        "Asia": "NA"
    }
    m_source = source_map.get(ds_data['m_source'], ds_data['m_source'])

    file_name = f"Internal_Simulationdata_{comm_name}_{gauge}_{m_source}{datasheet}.pdf"
    
    pdf_path = Path(EXPORT_PATH, str(projectId), str(datasheet), 'results', file_name)
    pdf_path2 = Path(EXPORT_PATH, 'pdf_files', str(projectId), file_name)

    Path(EXPORT_PATH, str(projectId), str(datasheet), 'results').mkdir(parents=True, exist_ok=True)
    Path(EXPORT_PATH, 'pdf_files', str(projectId)).mkdir(parents=True, exist_ok=True)

    pdf = dsr.DatasheetReport(ds_data)
    pdf.create()
    pdf.output(pdf_path)
    pdf.output(pdf_path2)

    return pdf_path


def create_customer_datasheet_report(ds_data, selected_nominal_age, projectId):
    datasheet = ds_data['datasheet']
    nominal_age = selected_nominal_age
    
    comm_name = ds_data['commercial_name'].replace(" ", "_")
    if ds_data['gauge'] == int(ds_data['gauge']):
        gauge = f"{ds_data['gauge']:.1f}mm"  
    else:
        gauge = f"{ds_data['gauge']}mm"  
    gauge = gauge.replace(".", "-")
    source_map = {
        "Europe": "NE",
        "North America": "NNA",
        "Asia": "NA"
    }
    m_source = source_map.get(ds_data['m_source'], ds_data['m_source'])

    file_name = f"Simulationdata_{comm_name}_{gauge}_{m_source}{datasheet}.pdf"
    output_path = Path(EXPORT_PATH, str(projectId), str(datasheet), 'results', file_name)

    Path(EXPORT_PATH, str(projectId), str(datasheet), 'results').mkdir(parents=True, exist_ok=True)

    pdf = dsr.DatasheetReport(ds_data)
    pdf.create_customer_pdf()
    pdf.output(output_path)

    return output_path


def create_datacard_report(ds_data, projectId):
    nominal_ages = set(ds_data['df_tensile_results'].index.get_level_values(0))

    # Placeholder params
    commercial_name = ds_data['commercial_name']
    comm_name = ds_data['commercial_name'].replace(" ", "_").replace(".", "-")
    
    # Map material source to abbreviations
    source_map = {
        "Europe": "NE",
        "North America": "NNA",
        "Asia": "NA"
    }
    material_source = ds_data['m_source']
    m_source = source_map.get(ds_data['m_source'], ds_data['m_source'])
    
    ds_number = ds_data['datasheet']
    revalid_date = ds_data['latest_revalidation']
    
    # Modify the gauge, replace the dot with a dash
    if ds_data['gauge'] == int(ds_data['gauge']):
        gauge = f"{ds_data['gauge']:.1f} mm"  # Add .0 if it's a whole number
    else:
        gauge = f"{ds_data['gauge']} mm"  
    ds_gauge = gauge.replace(".", "-")
    ds_gauge = ds_gauge.replace(" ", "")
    dsheet_gauge = gauge
    comm_name_w_gauge = f"{ds_data['commercial_name']} {gauge}"
    valid_date = ds_data['valid_until']
    hardening_true_stress = hardening_data_calc(ds_data)
    df = hardening_true_stress.reset_index()

    for nominal_age in nominal_ages:
        dict_mp = ds_data['df_model_params'].loc[nominal_age, :].to_dict()
        C = dict_mp['C']
        m = dict_mp['m']
        eps_0 = dict_mp['eps_0']
        sig_i = dict_mp['sig_i']
        sig_sat = dict_mp['sig_sat']
        a = dict_mp['a']
        p = dict_mp['p']
        alpha = dict_mp['alpha']

        r_values = ds_data['df_tensile_results'].loc[nominal_age, ('r8-12', '-')].loc[[0,45,90]].to_list()
        m_value = 8
        sig_rel = ds_data['df_yield'].loc[nominal_age, [ ('σi/σ0', 45), ('σi/σ0', 90), ('σb/σ0', "")]].to_list()
        rbi = ds_data['df_yield'].loc[nominal_age, ('rbi', '')]

        formatted_data = "\n".join(
            f"{i:<3} {row['plastic_strain']:<6}  {row[nominal_age]:<6}"
            for i, row in df.iterrows()
        )
        
        autoform_datacard_template = f"""
##########################################################
## NOTE:                                                ##
## Material description generated by a user with help of##
## the AutoForm R10 Material Generator or exported      ##
## from an AutoForm R10 design.                         ##
##########################################################

#StandardDesignation                 {comm_name_w_gauge} 
#AccordingToStandard
#AdditionalDesignations              NE{ds_number} issued {revalid_date}
#InternalDesignations                Validity date {valid_date}
#MaterialSupplier                    Novelis ({material_source})
#RawDataMeasurementBy                Novelis 
#RawDataMeasurementDate              {nominal_age} days nominal aging
#RawDataMeasurementSpecimenThickness {dsheet_gauge}
#MtbFileGenerationBy                 Novelis Datasheet Generator
#MtbFileGenerationDate               {dt.date.today().isoformat()}
#GeneralCommentStart
#Novelis Inc. (“Novelis”) wishes to provide this material Data Card (“Data Card”) to the Receiving Party (“Party”). Novelis is not responsible for (i) any processing done by the Party to any materials that are related to the Data Card, and (ii) the use of the Data Card for compliance validation by a third party. The Data Card is being provided for simulation only. Therefore, Novelis makes no representations and extends no warranties of any kind, express or implied, concerning the Data Card, which is provided “as is.”  There are no express or implied warranties of merchantability or fitness for a particular purpose, or that the use of the Data Card will not infringe any patent, copyright, trademark, or other proprietary right of any third party. Novelis will not be liable to the Party whether in contract, tort, equity or otherwise, for any indirect, incidental, special, punitive, or consequential damages arising out of or related to the Data Card, including, without limitation, damages for loss of anticipated business profits, business interruption, and the like, even if the Party is notified of the possibility of such damages. By accepting the Data Card, the Party hereby accepts the terms and conditions.
#
#The material properties contained within this data card describe a typical, as supplied material and as such may not be representative of a specific batch. The material properties are based on mechanical tests according to the following standards: ISO 6892-1, and ISO 10113 for tensile data, ISO 12004-2 for FLC and ISO 16808 for bulge tests.
#
#Please check: www.novelis.com/automotive/ for further information.
#GeneralCommentEnd

YoungsModulus 70000
PoissonsRatio 0.33
SpecificWeight 2.7e-005
SpecificHeatCapacity 2.461
ThermalConductivity 0
HardeningCurve
{formatted_data}

R-Values {r_values[0]} {r_values[1]} {r_values[2]}

M-Value {m_value}
RelativeSigma45 {sig_rel[0]}
RelativeSigma90 {sig_rel[1]}
RelativeSigmaBiaxial {sig_rel[2]}
R-ValueBiaxial {rbi}

FailureCurve
"""

        # Generate the new file name based on the updated format
        file_name = f"{comm_name}_{ds_gauge}_{m_source}{ds_number}-{nominal_age}d.mat"

        # Path to save the datacard
        datacard_path = Path(EXPORT_PATH, str(projectId), str(ds_number), 'results', file_name)

        # Write the data to the file
        with open(datacard_path, 'w') as f:
            f.write(autoform_datacard_template)
            ds_data['df_flc_fit'].to_string(buf=f, columns=['s_minor', 's_major'], header=False)

    return datacard_path


def true_stress_calc(plast_strain_values, fit_params_df):
    true_stress_dict = {}
    aging_days = fit_params_df.index.tolist()
    
    for plast_strain in plast_strain_values:
        true_stress_values = []
        
        for aging_day in aging_days:
            row = fit_params_df.loc[aging_day] # Get the row corresponding to the aging day
            sig_i = row['sig_i']
            sig_sat = row['sig_sat']
            a = row['a']
            p = row['p']
            C = row['C']
            eps_0 = row['eps_0']
            m = row['m']
            alpha = row['alpha']
            
            true_stress = ((1-alpha)*C*(plast_strain+eps_0)**m) + alpha*(sig_sat-(sig_sat-sig_i)*np.exp(-a*(plast_strain**p)))
            true_stress_values.append(true_stress)
        
        true_stress_dict[plast_strain] = true_stress_values
    
    result_df = pd.DataFrame(true_stress_dict, index=aging_days).T
    result_df.index.name = 'plastic_strain'
    # result_df.columns.name = 'Aging (days)'
    
    # Set the 'plastic_strain' column as the index
    result_df = result_df.reset_index().rename(columns={'index': 'plastic_strain'}).set_index('plastic_strain')
    
    return result_df

def hardening_data_calc(ds_data):
    ps_file =  Path(RESOURCES_PATH, 'true_plast_strain_array.txt')
    plast_strain = np.loadtxt(ps_file,skiprows=1)
    hardening_true_stress = true_stress_calc(plast_strain, ds_data['df_model_params'])
    return hardening_true_stress

def create_hardening_data_file(ds_data, projectId):
    ds_number = ds_data['datasheet']
    
    # Modify commercial name and gauge for the file name
    comm_name = ds_data['commercial_name'].replace(" ", "_")
    if ds_data['gauge'] == int(ds_data['gauge']):
        gauge = f"{ds_data['gauge']:.1f} mm" 
    else:
        gauge = f"{ds_data['gauge']} mm" 
    comm_name_w_gauge = f"{ds_data['commercial_name']} {gauge}"
    # Map material source to abbreviations
    source_map = {
        "Europe": "NE",
        "North America": "NNA",
        "Asia": "NA"
    }
    m_source = source_map.get(ds_data['m_source'], ds_data['m_source'])

    header_info = {
        "Material":             comm_name_w_gauge,
        "Material Source":      ds_data["m_source"],
        "Datasheet no.":        ds_data['datasheet'],
        "Issue Date":           ds_data['latest_revalidation'],
        "Validity Date":        ds_data['valid_until'],
        "Age (days)":           "90"
    }

    output_dir = Path(EXPORT_PATH, str(projectId), str(ds_number), 'results')
    hardening_true_stress = hardening_data_calc(ds_data)

    os.makedirs(output_dir, exist_ok=True)
    
    for col in hardening_true_stress.columns:
        if col != 'plastic_strain':
            df = pd.DataFrame({
                'true plast. strain (-)': hardening_true_stress.index,
                'true stress (MPa)': hardening_true_stress[col]
            })
            
            # Write the DataFrame to a TSV file
            df['true stress (MPa)'] = df['true stress (MPa)'].round(5)
            
            # Modify the file name based on the new format
            aging_days = col  # Assuming the column name contains the aging days
            ds_gauge = gauge.replace(" ", "")
            ds_gauge = ds_gauge.replace(".", "-")
            file_name = f"Simulationdata_{comm_name}_{ds_gauge}_{m_source}{ds_number}-{aging_days}d_hardening_data.tsv"
            file_path = os.path.join(output_dir, file_name)
            
            with open(file_path, 'w') as file:
                header_info['Age (days)'] = aging_days
                max_key_length = max(len(key) for key in header_info.keys())
                file.write(f"Simulation Data Novelis\n")
                for key, value in header_info.items():
                    padding = ' ' * (max_key_length - len(key))
                    file.write(f"{key}:{padding}\t{value}\n")
                file.write("=" * 3 + "\n")  
                file.write("Hardening curve" + "\n")  
                df.to_csv(file, sep='\t', index=False, mode='a', line_terminator='\n')

    return file_path

def create_params_tsv_files(ds_data, projectId):
    ds_number = ds_data['datasheet']
    
    # Modify commercial name and gauge for the file name
    comm_name = ds_data['commercial_name'].replace(" ", "_")
    if ds_data['gauge'] == int(ds_data['gauge']):
        gauge = f"{ds_data['gauge']:.1f} mm" 
    else:
        gauge = f"{ds_data['gauge']} mm" 
    comm_name_w_gauge = f"{ds_data['commercial_name']} {gauge}"
    # Map material source to abbreviations
    source_map = {
        "Europe": "NE",
        "North America": "NNA",
        "Asia": "NA"
    }
    m_source = source_map.get(ds_data['m_source'], ds_data['m_source'])

    header_info = {
        "Material":             comm_name_w_gauge,
        "Material Source":      ds_data["m_source"],
        "Datasheet no.":        ds_data['datasheet'],
        "Issue Date":           ds_data['latest_revalidation'],
        "Validity Date":        ds_data['valid_until'],
    }

    output_dir = Path(EXPORT_PATH, str(projectId), str(ds_number), 'results')

    os.makedirs(output_dir, exist_ok=True)

    df_model_params = ds_data['df_model_params']
    df_yield = ds_data['df_yield']
    df_yield.columns = df_yield.columns.set_names(["Aging","days"])
    df_yield.index.names = [('')]
    df_mech_props = ds_data['df_tensile_results']
    df_mech_props = df_mech_props.reset_index()

    ds_gauge = gauge.replace(" ", "")
    ds_gauge = ds_gauge.replace(".", "-")
    hardening_params_file = f"Simulationdata_{comm_name}_{ds_gauge}_{m_source}{ds_number}_hardening_params.tsv"
    yield_surface_file = f"Simulationdata_{comm_name}_{ds_gauge}_{m_source}{ds_number}_yield_surface.tsv"
    mech_props_file = f"Simulationdata_{comm_name}_{ds_gauge}_{m_source}{ds_number}_mechanical_properties.tsv"
    file_path = os.path.join(output_dir, hardening_params_file)
    tsv_files = [{"file_name":hardening_params_file,
                  "file_path":os.path.join(output_dir, hardening_params_file),
                  "title":"Hardening curve parameters"},
                  {"file_name":yield_surface_file,
                  "file_path":os.path.join(output_dir, yield_surface_file),
                  "title":"Yield surface"},
                  {"file_name":mech_props_file,
                  "file_path":os.path.join(output_dir, mech_props_file),
                  "title":"Mechanical properties"},
                  ]
    for tsv_file in tsv_files:
        with open(tsv_file['file_path'], 'w') as file:
            max_key_length = max(len(key) for key in header_info.keys())
            file.write(f"Simulation Data Novelis\n")
            for key, value in header_info.items():
                padding = ' ' * (max_key_length - len(key))
                file.write(f"{key}:{padding}\t{value}\n")
            file.write("=" * 3 + "\n")  
            file.write(tsv_file['title'] + "\n")  
            if tsv_file['title'] =="Hardening curve parameters":
                df_model_params.to_csv(file, sep='\t', index=True, mode='a', line_terminator='\n', index_label="Aging days")
            if tsv_file['title'] =="Yield surface":
                df_yield.to_csv(file, sep='\t', index=True, mode='a', line_terminator='\n')
            if tsv_file['title'] =="Mechanical properties": 
                df_mech_props.to_csv(file, sep='\t', index=False, mode='a', line_terminator='\n')


#######################
#      create json    #
#######################
def create_json(projectId,data,selected_datasheet, selected_nominal_age, file_name):
    output_directory = os.path.join(EXPORT_PATH, str(projectId), str(selected_datasheet),str(selected_nominal_age))

    # Create the directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Create a sample DataFrame (replace this with your actual DataFrame)

    # Create the full path for the CSV file within the new directory
    json_file_path = os.path.join(output_directory, file_name)

    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    return json_file_path

def get_datasheet_ages(project_id:str, base_path:str):    
    try:
        
        full_path = os.path.join(EXPORT_PATH,project_id,base_path)

        # Get a list of all directories in the full path
        datasheet_ages = [folder for folder in os.listdir(full_path) if os.path.isdir(os.path.join(full_path, folder))]
        if 'results' in datasheet_ages:
            datasheet_ages.remove('results')
        
        # Sort the list in ascending order
        datasheet_ages.sort(key=int)
        return datasheet_ages
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return {"error": str(e)}

def export_datasheet_workflow(metadata,projectId,selected_datasheet,selected_nominal_age):
    try:
        model_name = 'hocket_sherby_swift'
        ds_meta= metadata
        com_df_data = read_csv(projectId,selected_datasheet, selected_nominal_age , 'pdf_tensile_combined_results_list.csv')
        data_str_keys = read_json(projectId,selected_datasheet, selected_nominal_age , 'model_dict_params.json')
        dict_params_to_insert = {eval(key): value for key, value in data_str_keys.items()}

        mech_data_params = read_json(projectId,selected_datasheet, selected_nominal_age , 'mech_data_params.json')
        ts_tests = read_pkl(projectId,selected_datasheet, selected_nominal_age , 'ts_tests_data.pkl')
        bg_tests = read_pkl(projectId,selected_datasheet, selected_nominal_age , 'ts_bulge_data.pkl')
        flc_raw = read_pkl(projectId,selected_datasheet, selected_nominal_age , 'flc_raw_data.pkl')
        flc_fit = read_pkl(projectId,selected_datasheet, selected_nominal_age , 'flc_fit_data.pkl')
        selected_columns = ['nominal_age', 'load_direction', 'Rp02', 'Rm', 'Ag', 'A80', 'n4_6', 'n10_20', 'r8_12']

        df_data = com_df_data[selected_columns]
        df_tensile_results = get_tensile_results(df_data)
        df_model_params = get_model_parameters(dict_params_to_insert,int(selected_datasheet), int(selected_nominal_age))

        nb_model_pts = 1000
        model = getattr(models, model_name)
        model_data = {}
        avg_mech = mech_data_params['avg_mech']
        eps_min,eps_max = mech_data_params['eps_range']
        for i_nominal_age in df_model_params.index:
            i_dict_params = df_model_params.loc[i_nominal_age, :].to_dict()
    

        x_model = np.linspace(eps_min, eps_max, nb_model_pts)
        model_data['eps_pl'] = x_model
        model_data[f'{i_nominal_age} days'] = model(x_model, **i_dict_params)
        df_model_data = pd.DataFrame(model_data)
        df_model_data.set_index('eps_pl', inplace=True, drop=True)
        model_latex = get_model_latex(model_name)
        df_flc_raw = get_flc_raw(flc_raw)
        df_flc_fit = get_flc_fit(flc_fit)
        scale_factor =[]
        E, Rp02, Rm, Ag, Agt = avg_mech
        for test in bg_tests:
            if str(test.nominal_age) == str(selected_nominal_age):
                k = get_scale_factor(test,E, Rp02, Rm, Ag, Agt)
                if not np.isnan(k):
                    scale_factor.append(k)
                
        if scale_factor:
            average_scale_factor = 1 / (sum(scale_factor) / len(scale_factor))
        else:
            average_scale_factor = 0  
        df_scale_factor = pd.DataFrame([{'nominal_age':selected_nominal_age, '1/AVG(scale_factor)':average_scale_factor}])
        df_scale_factor.set_index('nominal_age', inplace=True)
        df_yield = get_yield_surface_data(com_df_data,df_scale_factor)
        ds_data = compile_ds_data(
            ds_meta, model_name,
            df_tensile_results,
            df_flc_raw, df_flc_fit,
            df_model_params, df_model_data, model_latex,
            df_yield
        )
        create_datasheet_report_task = create_datasheet_report(ds_data,selected_nominal_age,projectId)
        create_customer_datasheet_report_task = create_customer_datasheet_report(ds_data,selected_nominal_age,projectId)
        create_datacard_report_task = create_datacard_report(ds_data,projectId)
        path_hardening_data_file = create_hardening_data_file(ds_data,projectId)

        metadata_path = create_json(projectId,metadata,selected_datasheet, selected_nominal_age,'metadata.json')
           
        path = {'datasheet':create_datasheet_report_task, 'datacard': create_datacard_report_task}
        path = {'datasheet':create_datasheet_report_task, 'datacard': ''}
        return path
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return e

def export_new_datasheet_workflow(metadata,projectId,selected_datasheet,selected_nominal_age):
    try:
        nominal_ages = get_datasheet_ages(str(projectId),str(selected_datasheet))
        all_com_df_data=[]
        data_str_keys={}
        all_mech_data_params={}
        all_df_model_params=[]
        all_df_scale_factor=[]
        model_name = 'hocket_sherby_swift'
        ds_meta= metadata
        for selected_nominal_age in nominal_ages:
            
            com_df_data = read_csv(projectId,selected_datasheet, selected_nominal_age , 'pdf_tensile_combined_results_list.csv')
            
            data_str_keys.update(read_json(projectId,selected_datasheet, selected_nominal_age , 'model_dict_params.json'))
            dict_params_to_insert = {eval(key): value for key, value in data_str_keys.items()}
            mech_data_params = read_json(projectId,selected_datasheet, selected_nominal_age , 'new_mech_data_params.json')
            datasheet_local_fit_params = read_json(projectId,selected_datasheet, selected_nominal_age , 'datasheet_local_fit_params.json')
            datasheet_local_fit_params = json.loads(datasheet_local_fit_params) 
            all_mech_data_params.update({selected_nominal_age: mech_data_params})
            df_model_params = get_model_parameters(dict_params_to_insert,int(selected_datasheet), int(selected_nominal_age))
            all_df_model_params.append(df_model_params)
            tensile_excluded_files = datasheet_local_fit_params['excluded_tensile']
            if tensile_excluded_files:
                com_df_data = com_df_data[~com_df_data['file_name'].str.contains('|'.join(tensile_excluded_files), regex=True)]
            
            all_com_df_data.append(com_df_data)

        df_model_params = pd.concat(all_df_model_params)
        for selected_nominal_age in nominal_ages:
            file_name ='datasheet_local_fit_results.json'
            output_directory = os.path.join(EXPORT_PATH, str(projectId), str(selected_datasheet), str(selected_nominal_age))
            json_file_path = os.path.join(output_directory, file_name)
            if os.path.exists(json_file_path):
                json_data = read_json(projectId,selected_datasheet,selected_nominal_age,file_name)
                dict_data = json.loads(json_data) 
                newfit= dict_data['df_model_params']['new local fit']
                df_new_fit = pd.DataFrame([newfit])
                df_results_new = pd.DataFrame(dict_data['df_results'])
                df_results_new = df_results_new.drop(columns=['filename_only'])
                # matching_rows = df_results_new[df_results_new['file_name'].isin(com_df_data['file_name'])]  # commented by ali can be used later on if want to add the new fit data
                # Replace the corresponding rows in df1 with the matching rows from df2
                # com_df_data.loc[com_df_data['file_name'].isin(matching_rows['file_name']), :] = matching_rows.values  # commented by ali can be used later on if want to add the new fit data
                df_model_params.loc[int(selected_nominal_age)] = df_new_fit.loc[0]

        ts_tests = read_pkl(projectId, selected_datasheet, selected_nominal_age , 'ts_tests_data.pkl')
        bg_tests = read_pkl(projectId, selected_datasheet, selected_nominal_age , 'ts_bulge_data.pkl')
        flc_raw = read_pkl(projectId, selected_datasheet, selected_nominal_age , 'flc_raw_data.pkl')
        flc_fit = read_pkl(projectId, selected_datasheet, selected_nominal_age , 'flc_fit_data.pkl')
        selected_columns = ['nominal_age', 'load_direction', 'Rp02', 'Rm', 'Ag', 'A80', 'n4_6', 'n10_20', 'r8_12']
        
        com_df_data = pd.concat(all_com_df_data, ignore_index=True)
        
        
        df_data = com_df_data[selected_columns]

        df_tensile_results = get_tensile_results(df_data)
        
        nb_model_pts = 1000
        model = getattr(models, model_name)
        model_data = {}

        for i_nominal_age in df_model_params.index:
            i_dict_params = df_model_params.loc[i_nominal_age, :].to_dict()
            avg_mech = all_mech_data_params[str(i_nominal_age)]['avg_mech']
            eps_min,eps_max = all_mech_data_params[str(i_nominal_age)]['eps_range']
            x_model = np.linspace(eps_min, eps_max, nb_model_pts)
            model_data['eps_pl'] = x_model
            model_data[f'{i_nominal_age} days'] = model(x_model, **i_dict_params)
        df_model_data = pd.DataFrame(model_data)
        df_model_data.set_index('eps_pl', inplace=True, drop=True)     
        model_latex = get_model_latex(model_name)
        df_flc_raw = get_flc_raw(flc_raw)
        df_flc_fit = get_flc_fit(flc_fit)
        for selected_nominal_age in nominal_ages:
            scale_factor =[]

            avg_mech = all_mech_data_params[selected_nominal_age]['avg_mech']
            E, Rp02, Rm, Ag, Agt = avg_mech
            for test in bg_tests:
                if str(test.nominal_age) == str(selected_nominal_age):
                    k = get_scale_factor(test,avg_mech['E'], avg_mech['Rp02'], avg_mech['Rm'], avg_mech['Ag'], avg_mech['Agt'])
                    if not np.isnan(k):
                        scale_factor.append(k)

            if scale_factor:
                average_scale_factor = 1 / (sum(scale_factor) / len(scale_factor))
            else:
                average_scale_factor = 0  
            df_scale_factor = pd.DataFrame([{'nominal_age':selected_nominal_age, '1/AVG(scale_factor)':average_scale_factor}])
            df_scale_factor.set_index('nominal_age', inplace=True)
            all_df_scale_factor.append(df_scale_factor)
            df_scale_factor = pd.concat(all_df_scale_factor)
        df_yield = get_yield_surface_data(com_df_data,df_scale_factor)
        
        ds_data = compile_ds_data(
            ds_meta, model_name,
            df_tensile_results,
            df_flc_raw, df_flc_fit,
            df_model_params, df_model_data, model_latex,
            df_yield
        )
        files_genration_path = Path(EXPORT_PATH, str(projectId), str(selected_datasheet), 'results')
        delete_previously_genrated_files(files_genration_path)
        create_datasheet_report_task = create_datasheet_report(ds_data,selected_nominal_age,projectId)
        create_customer_datasheet_report_task = create_customer_datasheet_report(ds_data,selected_nominal_age,projectId)
        create_datacard_report_task = create_datacard_report(ds_data,projectId)
        path_hardening_data_file = create_hardening_data_file(ds_data,projectId)
        path_tsv_file = create_params_tsv_files(ds_data,projectId)
           
        path = {'datasheet':create_datasheet_report_task, 'datacard': ''}
        return path
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return e

def delete_previously_genrated_files(path):
    files = glob.glob(os.path.join(path, '*'))
    for file in files:
        try:
            os.remove(file)
        
        except Exception as e:
            logger.error(f"Error deleting {file}: {e}")


def export_combined_datasheet_workflow(metadata,projectId,selected_datasheet,selected_nominal_age):
    try:
        nominal_ages = get_datasheet_ages(str(projectId),str(selected_datasheet))
        all_com_df_data=[]
        data_str_keys={}
        all_mech_data_params={}
        all_df_model_params=[]
        all_df_scale_factor=[]
        model_name = 'hocket_sherby_swift'
        ds_meta= metadata
        for selected_nominal_age in nominal_ages:
            com_df_data = read_csv(projectId, selected_datasheet, selected_nominal_age , 'pdf_tensile_combined_results_list.csv')
            params_data = read_json(projectId, selected_datasheet, selected_nominal_age , 'datasheet_local_fit_params.json')
            fit_params = json.loads(params_data) 
            all_com_df_data.append(com_df_data)
            data_str_keys.update(read_json(projectId, selected_datasheet, selected_nominal_age , 'model_dict_params.json'))
            dict_params_to_insert = {eval(key): value for key, value in data_str_keys.items()}
            mech_data_params = read_json(projectId, selected_datasheet, selected_nominal_age , 'mech_data_params.json')
            all_mech_data_params.update({selected_nominal_age: mech_data_params})
            df_model_params = get_model_parameters(dict_params_to_insert,int(selected_datasheet), int(selected_nominal_age))
            all_df_model_params.append(df_model_params)

        ts_tests = read_pkl(projectId, selected_datasheet, selected_nominal_age , 'ts_tests_data.pkl')
        bg_tests = read_pkl(projectId, selected_datasheet, selected_nominal_age , 'ts_bulge_data.pkl')
        flc_raw = read_pkl(projectId, selected_datasheet, selected_nominal_age , 'flc_raw_data.pkl')
        flc_fit = read_pkl(projectId, selected_datasheet, selected_nominal_age , 'flc_fit_data.pkl')
        selected_columns = ['nominal_age', 'load_direction', 'Rp02', 'Rm', 'Ag', 'A80', 'n4_6', 'n10_20', 'r8_12']

        com_df_data = pd.concat(all_com_df_data, ignore_index=True)
        df_data = com_df_data[selected_columns]
        df_tensile_results = get_tensile_results(df_data)
        df_model_params = pd.concat(all_df_model_params)

        nb_model_pts = 1000
        model = getattr(models, model_name)
        model_data = {}

        for i_nominal_age in df_model_params.index:
            i_dict_params = df_model_params.loc[i_nominal_age, :].to_dict()
            avg_mech = all_mech_data_params[str(i_nominal_age)]['avg_mech']
            eps_min,eps_max = all_mech_data_params[str(i_nominal_age)]['eps_range']
            x_model = np.linspace(eps_min, eps_max, nb_model_pts)
            model_data['eps_pl'] = x_model
            model_data[f'{i_nominal_age} days'] = model(x_model, **i_dict_params)
        df_model_data = pd.DataFrame(model_data)
        df_model_data.set_index('eps_pl', inplace=True, drop=True)     
        model_latex = get_model_latex(model_name)
        df_flc_raw = get_flc_raw(flc_raw)
        df_flc_fit = get_flc_fit(flc_fit)
        for selected_nominal_age in nominal_ages:
            scale_factor =[]
            avg_mech = all_mech_data_params[str(i_nominal_age)]['avg_mech']
            E, Rp02, Rm, Ag, Agt = avg_mech
            for test in bg_tests:
                if str(test.nominal_age) == str(selected_nominal_age)and test.file_name not in fit_params['excluded_bulge']:
                    if str(test.nominal_age) == str(selected_nominal_age):
                        k = get_scale_factor(test,E, Rp02, Rm, Ag, Agt)
                        if not np.isnan(k):
                            scale_factor.append(k)
            if scale_factor:
                average_scale_factor = 1 / (sum(scale_factor) / len(scale_factor))
            else:
                average_scale_factor = 0  
            df_scale_factor = pd.DataFrame([{'nominal_age':selected_nominal_age, '1/AVG(scale_factor)':average_scale_factor}])
            df_scale_factor.set_index('nominal_age', inplace=True)
            all_df_scale_factor.append(df_scale_factor)
            df_scale_factor = pd.concat(all_df_scale_factor)
           
        df_yield = get_yield_surface_data(com_df_data,df_scale_factor)
        
        ds_data = compile_ds_data(
            ds_meta, model_name,
            df_tensile_results,
            df_flc_raw, df_flc_fit,
            df_model_params, df_model_data, model_latex,
            df_yield
        )
        files_genration_path = Path(EXPORT_PATH, str(projectId), str(selected_datasheet), 'results')
        delete_previously_genrated_files(files_genration_path)
        create_datasheet_report_task = create_datasheet_report(ds_data,selected_nominal_age,projectId)
        create_customer_datasheet_report_task = create_customer_datasheet_report(ds_data,selected_nominal_age,projectId)
        create_datacard_report_task = create_datacard_report(ds_data,projectId)
        path_tsv_file = create_params_tsv_files(ds_data,projectId)
        path_hardening_data_file = create_hardening_data_file(ds_data,projectId)

        metadata_path = create_json(projectId, metadata, selected_datasheet, selected_nominal_age,'metadata.json')
        path = {'datasheet':create_datasheet_report_task, 'datacard': create_datacard_report_task}
        # path = {'datasheet':'', 'datacard': ''}
        return path
    except Exception as e:
        raise Exception(f"Datasheet export failed: {str(e)}")

