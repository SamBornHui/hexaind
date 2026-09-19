import traceback
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import os
from pathlib import Path
import pandas as pd
from datetime import datetime, timezone
from app.env import *
from app.services.apps.datasheet_gen.schemas import TensileParams
from  app.services.apps.datasheet_gen.dsgen_controller.utils.utils import compile_output_zip, save_to_share
import logging
import sys 
logger = logging.getLogger(__package__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

HEADER_TEMPLATE = """Test procedure\t{test_procedure}
Datasheet ID\t{datasheet}
Test lab\t{test_lab}
Lab ref.no\t{lab_ref}
Test date\t{test_date}
Test operator\t{test_operator}
Age (days)\t{nominal_age}
Pretreatement\t{pretreatement}
Test direction (deg)\t{test_direction}
===
"""

TENSILE_HEADER_TEMPLATE = """Test procedure\tTensile Test ISO 6892-1 method B
Datasheet ID\t{datasheet}
Test lab\tNovelis Sierre NICS
Lab ref. no.\t{lab_ref}{test_date_line}
Test operator\t{operator}
Age (days)\t{nominal_age}
Pretreatement\t{pretreatement}
Sample geometry / standard\tSierre A80, ISO 6892-1
"""

SAMPLE_HEADER_TEMPLATE = TENSILE_HEADER_TEMPLATE + """Sample ID\t{sample_name}
Test direction (deg)\t{test_direction}
Gauge length (mm)\t{gauge_length}
Sample thickness (mm)\t{sample_thickness}
Sample width (mm)\t{sample_width}
"""
async def save_datasheet(projectId:str, userId:str, files: list[UploadFile], filePaths: list[str]):
    try:
        if len(files) == 0:
            return "No files were uploaded"

        tensiles_nominal_ages = set()
        bulge_nominal_ages = set()
        tensile_sample_files = set()
        bulge_sample_files = set()
        flc_sample_files = set()
        for file, file_path in zip(files, filePaths):
                # Create directories based on the file path
                directory_path = os.path.join(IMPORT_PATH,projectId ,os.path.dirname(file_path))
                os.makedirs(directory_path, exist_ok=True)
                contents = await file.read()
                dest_file_path= os.path.join(directory_path, file.filename)
                parts = file_path.split('/')
                for part in parts:
                    if "Tensile" in parts:
                        tensile_sample_files.add(dest_file_path)
                        if "days" in part:
                            # Extract the number before "days"
                            days = int(part.split()[0])  # Get the number
                            tensiles_nominal_ages.add(days)
                    if "Bulge" in parts:
                        bulge_sample_files.add(dest_file_path)
                        if "days" in part:
                            # Extract the number before "days"
                            days = int(part.split()[0])  # Get the number
                            bulge_nominal_ages.add(days)
                    if "FLC" in parts:
                        flc_sample_files.add(dest_file_path)
                    
                with open(dest_file_path, "wb") as f:
                    f.write(contents)
        tensiles_nominal_ages = sorted(tensiles_nominal_ages)
        relative_path = os.path.relpath(directory_path, os.path.join(IMPORT_PATH, projectId))
        datasheet = relative_path.split(os.sep)[0]
        data = {"project_id":projectId, "user_id":userId, "datasheet": datasheet,"tensile_ages":tensiles_nominal_ages, "bulge_ages":bulge_nominal_ages, "datasheet_path": os.path.join(IMPORT_PATH,projectId,datasheet), "tensile_files":tensile_sample_files,  "bulge_files":bulge_sample_files, "flc_files": flc_sample_files, "created_at":datetime.now(timezone.utc) }
        return data
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return e

def gen_flc_plot_data(raw_file, fit_file):

    df_raw = get_raw_df(raw_file)
    df_fit = get_fit_df(fit_file)

    df_raw_filtered = df_raw[df_raw['major strain [-]']>0]
    x_data = df_raw_filtered['minor strain [-]']
    y_data = df_raw_filtered['major strain [-]']
    s_raw = {"x_data":x_data.to_json(), "y_data":y_data.to_json()}

    df_raw_grouped = df_raw_filtered.groupby(['sample geometry', 'sample number']).mean()
    
    x_data = df_raw_grouped['minor strain [-]']
    y_data = df_raw_grouped['major strain [-]']
    raw_points= {
        'x' : x_data.to_json(),
        'y' : y_data.to_json(),
    }

    obj = {
        'df_fit':df_fit.to_json(),
        'raw_points':raw_points,
        's_raw':s_raw
    }
    return obj

def get_fit_df(file_name):

    df_fit = pd.read_excel(file_name, sheet_name='data sheet info', header=10)
    df_fit.columns = ['minor strain [-]', 'major strain [-]', '+ sigma', '- sigma']
    df_fit = df_fit.round(5)
    
    return df_fit

def get_raw_df(file_name):

    df_raw = pd.read_excel(file_name, sheet_name='data sheet info', header=10)
    df_raw.columns = [
        'major strain [-]', 'minor strain [-]', 'sample geometry',
        'sample number', 'section', 'comment'
    ]

    return df_raw
    
async def convert_file(projectId:str, fitFile: UploadFile, rawFile: UploadFile, meatadataFile):
    try:      
        
        # Create directories based on the file path
        directory_path = os.path.join(CONV_IMPORT_PATH,str(projectId))
        os.makedirs(directory_path, exist_ok=True)
        contents = await fitFile.read()
        uploaded_fit_file= os.path.join(directory_path, fitFile.filename)
        with open(uploaded_fit_file, "wb") as f:
            f.write(contents)
        raw_contents = await rawFile.read()
        uploaded_raw_file= os.path.join(directory_path, rawFile.filename)
        with open(uploaded_raw_file, "wb") as f:
            f.write(raw_contents)

        if uploaded_raw_file and uploaded_fit_file:

        # Choose metadata file
            dict_files = {
                rawFile.filename: uploaded_raw_file,
                fitFile.filename: uploaded_fit_file,
            }

        metadata_file_name = meatadataFile
        metadata_file = dict_files[metadata_file_name]
        df_meta_data = get_metadata(metadata_file)
        plot_data= gen_flc_plot_data(uploaded_raw_file, uploaded_fit_file)

        data = {
            'df_meta_data':df_meta_data,
            'plot_data':plot_data,
            'raw_file':uploaded_raw_file,
            'fit_file':uploaded_fit_file
        }
        return data
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return e

async def convert_tensile_file(projectId:str, tensileFile: UploadFile):
    try:      
        
        # Create directories based on the file path
        directory_path = os.path.join(CONV_IMPORT_PATH,str(projectId))
        os.makedirs(directory_path, exist_ok=True)
        contents = await tensileFile.read()
        uploaded_tensile_file= os.path.join(directory_path, tensileFile.filename)
        with open(uploaded_tensile_file, "wb") as f:
            f.write(contents)
       
        if uploaded_tensile_file:
            tensile_params = TensileParams(tensile_file=uploaded_tensile_file, params={}) 
            tensile_params.params['df_meta_data']= {}
            tensile_params.params['cols_names'] = None
            df_results = prepare_results_sheet(tensile_params)
       
        df_results_cleaned_json = df_results['df_results'].to_json(orient='index')
        data = {
            'df_results_cols':df_results['df_results_cols'],
            'df_results': df_results_cleaned_json,
            'tensile_file':uploaded_tensile_file,
            'cols_names':df_results['cols_names'],
        }
        return data
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return e

def get_datasheets(projectId, base_path:str):    
    try:
        if base_path == 'base':
            full_path = os.path.join(IMPORT_PATH, projectId)
        else:
            full_path = os.path.join(IMPORT_PATH, projectId,base_path,'Tensile')

        # Get a list of all directories in the full path
        if not os.path.exists(full_path) or not os.path.isdir(full_path):
            return []
        
        datasheets = [folder for folder in os.listdir(full_path) if os.path.isdir(os.path.join(full_path, folder))]
        
        if not datasheets:
            return []
        
        if base_path != 'base':
            datasheets = [sheet.replace(" days", "") for sheet in datasheets]
        
        return datasheets
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return {"error": str(e)}

def get_datasheets_details(projectId, base_path:str):    
    try:
        if base_path == 'base':
            full_path = os.path.join(IMPORT_PATH, projectId)
        else:
            full_path = os.path.join(IMPORT_PATH, projectId,base_path)

        if not os.path.exists(full_path) or not os.path.isdir(full_path):
            return []
        # Get a list of all files and directories in the full path
        datasheets = [item for item in os.listdir(full_path) if not item.startswith('.')]

        return datasheets
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return {"error": str(e)}
    
def get_metadata(metadata_file):

    # Try populating metadata with info from file
    df_meta = pd.read_excel(
            metadata_file,
            sheet_name='data sheet info',
            header=None,
    )

    df_meta = df_meta.iloc[:9, :2]
    df_meta.columns = ['parameter', 'value']

    df_meta.set_index('parameter', drop=True, inplace=True)
    df_meta.fillna("", inplace=True)
    df_meta_data={}
    if 'test_procedure' not in df_meta_data.keys():
        try:
            df_meta_data['test_procedure'] = df_meta.loc['Test procedure', 'value']
        except (KeyError, TypeError):
            df_meta_data['test_procedure'] = "ISO 12004-2"

    if 'datasheet' not in df_meta_data.keys():
        try:
            df_meta_data['datasheet'] = df_meta.loc['Datasheet ID', 'value']
        except (KeyError, TypeError):
            df_meta_data['datasheet'] = None

    if 'test_lab' not in df_meta_data.keys():
        try:
            df_meta_data['test_lab'] = df_meta.loc['Test lab', 'value']
        except (KeyError, TypeError):
            df_meta_data['test_lab'] = "Novelis Sierre NICS"

    if 'lab_ref' not in df_meta_data.keys():
        try:
            df_meta_data['lab_ref'] = df_meta.loc['Lab ref. no.', 'value']
        except (KeyError, TypeError):
            df_meta_data['lab_ref'] = None

    if 'test_date' not in df_meta_data.keys():
        try:
            if type(df_meta.loc['Test date', 'value']) == datetime:
                df_meta_data['test_date'] = df_meta.loc['Test date', 'value']
            elif type(df_meta.loc['Test date', 'value']) == str:
                df_meta_data['test_date'] = datetime.fromisoformat(df_meta.loc['Test date', 'value'])
            else:
                df_meta_data['test_date'] = datetime.today().date()
        except (KeyError, ValueError):
            # try:
            # # Handle partial date formats (e.g., "2012-08")
            #     df_meta_data['test_date'] = datetime.strptime(df_meta.loc['Test date', 'value'], "%Y-%m").date()
            # except ValueError:
            df_meta_data['test_date'] = ""

    if 'test_operator' not in df_meta_data.keys():
        try:
            df_meta_data['test_operator'] = df_meta.loc['Test operator', 'value']
        except (KeyError, TypeError):
            df_meta_data['test_operator'] = None

    if 'nominal_age' not in df_meta_data.keys():
        try:
            df_meta_data['nominal_age'] = df_meta.loc['Age (days)', 'value']
        except (KeyError, TypeError):
            df_meta_data['nominal_age'] = None

    if 'pretreatement' not in df_meta_data.keys():
        try:
            df_meta_data['pretreatement'] = df_meta.loc['Pretreatement', 'value']
        except (KeyError, TypeError):
            df_meta_data['pretreatement'] = None

    if 'test_direction' not in df_meta_data.keys():
        try:
            df_meta_data['test_direction'] = df_meta.loc['Test direction (deg)', 'value']
        except (KeyError, TypeError):
            df_meta_data['test_direction'] = None
    return df_meta_data

def compile_raw_ascii(raw_file, choices_dict):

    raw_ascii = HEADER_TEMPLATE.format(
        **choices_dict
    )

    # Read raw excel contents
    df_raw = get_raw_df(raw_file)
    # df_raw = pd.read_excel(raw_file, sheet_name='data sheet info', header=10)

    raw_ascii += df_raw.to_csv(sep='\t', index=False, line_terminator='\n')

    return raw_ascii

def compile_fit_ascii(fit_file, choices_dict):

    fit_ascii = HEADER_TEMPLATE.format(
        **choices_dict
    )

    # Read raw excel contents
    df_fit = get_fit_df(fit_file)
    # df_fit = pd.read_excel(fit_file, sheet_name='data sheet info', header=10)

    fit_ascii += df_fit.to_csv(sep='\t', index=False, line_terminator='\n')
    return fit_ascii

def compile_f_dict(raw_ascii, fit_ascii, datasheet, nominal_age):

    raw_file_name = f"{datasheet}_FLC_{nominal_age}_datasheet_raw.tsv"
    fit_file_name = f"{datasheet}_FLC_{nominal_age}_datasheet_fit.tsv"

    f_dict = {
        raw_file_name: raw_ascii,
        fit_file_name: fit_ascii,
    }
    return f_dict

def save_flc_ascii(projectId, userId, flc_params):
    df_meta_data = flc_params.params
    raw_ascii = compile_raw_ascii(flc_params.raw_file, df_meta_data)
    fit_ascii = compile_fit_ascii(flc_params.fit_file, df_meta_data)

        # Compile f_dict
    datasheet = df_meta_data['datasheet']
    nominal_age = df_meta_data['nominal_age']

    f_dict = compile_f_dict(raw_ascii, fit_ascii, datasheet, nominal_age)

    bool_save_to_share = True
    bool_delete_existing = True

    # with st.sidebar:
    datasheet_to_save = df_meta_data['datasheet']
    datasheet_path = Path(IMPORT_PATH,str(projectId), str(datasheet_to_save))
    if bool_save_to_share:
        save_path = Path(IMPORT_PATH,str(projectId), str(datasheet_to_save), "FLC")
        converted_files = save_to_share(save_path, f_dict, bool_delete_existing)
    flc_files = [str(path) for path in converted_files]
    
    return {'path':save_path,'datasheet_path':str(datasheet_path) ,'nominal_age':nominal_age,'flc_files':flc_files,"datasheet":datasheet,'project_id':projectId, 'user_id':userId}


def get_results_col_name(result_cols, possible_variants, col_title):

    col_name = ""
    for i_col_name in possible_variants:
        if i_col_name in result_cols:
            col_name = i_col_name

    try:
        col_idx = result_cols.index(col_name)
    except ValueError:
        col_idx = 0

    # col_name = st.selectbox(f"{col_title} column name", result_cols, col_idx, key=f"{col_title}_col_name")

    return col_name

def prepare_results_sheet(tensile_params):
    
    df_meta_data = tensile_params.params['df_meta_data']
    cols_names = tensile_params.params['cols_names']
    tensile_file = tensile_params.tensile_file
    results_sheet_name = ['Results', 'Résultats']

    for i_results_sheet in results_sheet_name:
        try:
            df_results_excel = pd.read_excel(tensile_file, sheet_name=i_results_sheet)
            break
        except ValueError as e:
            if i_results_sheet == results_sheet_name[-1]:
                raise e

    # Drop the first row, since it doesn't have any info
    df_results_excel = df_results_excel.iloc[1:, :]
    # Set the index to the sample name
    df_results_excel.set_index(keys=df_results_excel.columns[0], inplace=True)

    df_results = df_results_excel.copy()
    df_results_cols = df_results.columns.to_list()

    if cols_names is None:
        cols_names={}
        datetime_names = ['Date/Clock time', 'Date', 'Date/heure']
        cols_names['col_name_date'] = get_results_col_name(df_results_cols, datetime_names, 'Datetime')

        direct_names = ['Direct', 'Direct.', 'Load direction', 'Direction','dir']
        cols_names['col_name_direct'] = get_results_col_name(df_results_cols, direct_names, 'Direction')

        length_names = ['L0']
        cols_names['col_name_length'] = get_results_col_name(df_results_cols, length_names, 'Length')

        thickness_names = ['a0']
        cols_names['col_name_thick'] = get_results_col_name(df_results_cols, thickness_names, 'Thickness')

        width_names = ['b0']
        cols_names['col_name_width'] = get_results_col_name(df_results_cols, width_names, 'Width')
        

    dict_cols_names = {
        'col_name_date': 'Test timestamp',
        'col_name_direct': 'Load direction',
        'col_name_length': 'L0',
        'col_name_thick': 'a0',
        'col_name_width': 'b0',
    }
    if 'timezone' in df_meta_data:
        tz_str = df_meta_data.timezone
    else:
        tz_str = 'Europe/Zurich'
        
    df_results[cols_names['col_name_date']] = pd.to_datetime(df_results[cols_names['col_name_date']], unit='D', origin='1899-12-30')
    df_results.loc[:, cols_names['col_name_date']] = df_results.loc[:, cols_names['col_name_date']].dt.tz_localize(tz_str)
    df_results.loc[:, cols_names['col_name_date']] = df_results.loc[:, cols_names['col_name_date']].apply(lambda x: x.isoformat(timespec='seconds'))

        # Regex Edit direction info
    dict_direction_replace = {
        'L.*': '0',
        'D.*': '45',
        'B.*': '45',
        'T.*': '90',
        r'(\d+)°?': r'\1',
    }

    df_results.replace({cols_names['col_name_direct']: dict_direction_replace}, regex=True, inplace=True)

    cols_to_keep = [
        cols_names['col_name_date'],
        cols_names['col_name_direct'],
        cols_names['col_name_length'],
        cols_names['col_name_thick'],
        cols_names['col_name_width'],
    ]

    # Add potential results and update the rename dict
    potential_col_groups = {
        'E': ['E', 'mE'],
        'Rp02': ['Rp02', 'Rp0.2'],
        'Rm': ['Rm'],
        'Ag': ['Ag'],
        'Agt': ['Agt'],
        'A80': ['A', 'A80']
    }

    df_results.columns = df_results.columns.str.strip()

    for col_name, i_potential_list in potential_col_groups.items():
        for ii_iter in i_potential_list:
            # Check if current column guess is in df_results columns (blank trimmed)
            if ii_iter in df_results.columns:
                cols_to_keep.append(ii_iter)
                dict_cols_names[ii_iter] = col_name

    nr_cols_mask = df_results.columns.str.match(r"[NnRr](\d+)[_-](\d+)(/Ag)?")

    nr_cols_list = df_results.columns[nr_cols_mask].to_list()

    cols_to_keep.extend(nr_cols_list)
    
    columns_to_convert = ['E', 'mE', 'Rp02','Rp0.2', 'Rm', 'Ag', 'A', 'r4-6/Ag', 'r8-12/Ag', 'r2-20/Ag', 'r10-15/Ag', 'n4-6/Ag', 'n10-15/Ag', 'n10-20/Ag', 'n2-20/Ag']

    for col in columns_to_convert:
        if col in df_results.columns:  # Check if the column exists
            # Convert to numeric and round to 5 decimal places
            df_results[col] = pd.to_numeric(df_results[col], errors='coerce').round(5)

    df_results_cleaned = df_results.loc[:, cols_to_keep]
    df_results_cleaned.rename_axis('Sample ID', axis=0, inplace=True)

    # Drop rows where Sample ID is empty
    df_results_cleaned = df_results_cleaned.loc[df_results_cleaned.index.dropna(), :]
    df_results_cleaned.rename(columns=dict_cols_names, inplace=True)

    df_results_cleaned.dropna(axis=0, how='all', inplace=True)
    df_results_cleaned.dropna(axis=1, how='all', inplace=True)
    
    return {'df_results':df_results_cleaned, 'df_results_cols':df_results_cols, 'cols_names':cols_names}

def compile_results_ascii(df_results,choices_dict):
    datasheet = choices_dict['datasheet']
    nominal_age = choices_dict['nominal_age']
    lab_ref = choices_dict['lab_ref']
    operator = choices_dict['operator']
    pretreatement = choices_dict['pretreatement']

    # Format Header
    results_ascii = TENSILE_HEADER_TEMPLATE.format(
        datasheet=datasheet,
        lab_ref=lab_ref,
        test_date_line="",
        operator=operator,
        nominal_age=nominal_age,
        pretreatement=pretreatement,
    )
    results_ascii += "===\n"
    # Append formatted dataframe

    df_results = df_results.rename_axis("Sample ID", axis=0)
    
    results_ascii += df_results.to_csv(sep='\t', index=True, line_terminator='\n')

    return results_ascii

def compile_sample_ascii(uploaded_file, df_results, sample_name, choices_dict,cols_names):

    datasheet = choices_dict['datasheet']
    nominal_age = choices_dict['nominal_age']
    lab_ref = choices_dict['lab_ref']
    operator = choices_dict['operator']
    pretreatement = choices_dict['pretreatement']
        
    date_col =  cols_names['col_name_date']
    direct_col = cols_names['col_name_direct']
    length_col = cols_names['col_name_length']
    thick_col =  cols_names['col_name_thick']
    width_col = cols_names['col_name_width']

    time_str = df_results.loc[sample_name, date_col]
    test_direction = df_results.loc[sample_name, direct_col]
    gauge_length = df_results.loc[sample_name, length_col]
    sample_thickness = df_results.loc[sample_name, thick_col]
    sample_width = df_results.loc[sample_name, width_col]

    # Try reading the corresponding sheet from excel. Raises ValueError when sheet doesn't exist
    df_data = pd.read_excel(uploaded_file, sheet_name=sample_name, header=1)
    # Time, delta L, delta T, Force, strain L, strain T, stress
    selected_cols = [0, 2, 3, 4, 5, 7, 8]
    # Keep only the necessary columns, drop the first row
    df_data = df_data.iloc[1:, selected_cols]
    # Rename the columns to the proper text name
    df_data.columns = ['time (s)', 'elongation L (mm)', 'elongation T (mm)', 'force (N)', 'eng. strain L (%)', 'eng. strain T (%)', 'eng. stress (MPa)']

    df_data = df_data.apply(pd.to_numeric, errors='coerce')
    df_data = df_data.round(8)

    sample_ascii = SAMPLE_HEADER_TEMPLATE.format(
        datasheet=datasheet,
        lab_ref=lab_ref,
        test_date_line=f"\nTest date\t{time_str}",
        operator=operator,
        nominal_age=nominal_age,
        pretreatement=pretreatement,
        sample_name=sample_name,
        test_direction=test_direction,
        gauge_length=gauge_length,
        sample_thickness=sample_thickness,
        sample_width=sample_width,
    )

    sample_ascii += "===\n"
    sample_ascii += df_data.to_csv(sep='\t', index=False, line_terminator='\n')

    return sample_ascii

def compile_f_dict_tensile(uploaded_file, df_results, choices_dict,cols_names):

    datasheet = choices_dict['datasheet']
    nominal_age = choices_dict['nominal_age']

    f_dict = {}

    f_results_name = f"{datasheet}_Tensile_{nominal_age}_results.tsv"
    results_ascii = compile_results_ascii(df_results,choices_dict)
    
    f_dict[f_results_name] = results_ascii

    nb_samples = len(df_results.index.to_list())

    for s_idx, sample_name in enumerate(df_results.index):

        # Parse info needed for file name
        direct_col = cols_names['col_name_direct']
        test_direction = df_results.loc[sample_name, direct_col]
        f_sample_name = f"{datasheet}_Tensile_{nominal_age}_{test_direction}_{sample_name}.tsv"

        # Compile sample ascii
        try:
            sample_ascii = compile_sample_ascii(uploaded_file, df_results, sample_name, choices_dict, cols_names)
        except ValueError:
    
            continue

        # Add to dict
        f_dict[f_sample_name] = sample_ascii

    return f_dict

def tensile_file_convert(tensile_params):
    try:
        cols_names = tensile_params.params['cols_names']
        tensile_file = tensile_params.tensile_file

        if tensile_file is not None:
            df_results = prepare_results_sheet(tensile_params)
        
        df_results_cleaned_json = df_results['df_results'].to_json(orient='index')
        data = {
                'df_results_cols':df_results['df_results_cols'],
                'df_results':df_results_cleaned_json,
                'tensile_file':tensile_file,
                'cols_names':df_results['cols_names'],
            }
        return data
    except Exception as e:

        return e

def save_tensile_ascii(projectId, userId, tensile_params):
    df_meta_data = tensile_params.params['df_meta_data']
    delete_existing = tensile_params.params['delete_existing']
    cols_names = tensile_params.params['cols_names']
    df_results = pd.read_json(tensile_params.params['df_results'], orient='index')
    tensile_file = tensile_params.tensile_file
    df_results = df_results.round(5)
    # if tensile_file is not None:
    #     df_results = prepare_results_sheet(tensile_params)

    f_dict = compile_f_dict_tensile(tensile_file, df_results, df_meta_data,cols_names)
        # Compile f_dict

    bool_save_to_share = True
    bool_delete_existing = delete_existing

    # with st.sidebar:
    datasheet_to_save = df_meta_data['datasheet']

    if bool_save_to_share:
        datasheet = df_meta_data['datasheet']
        nominal_age = df_meta_data['nominal_age']

        nominal_age_str = f"{nominal_age} days"
        datasheet_path = Path(IMPORT_PATH, str(projectId) ,str(datasheet))
        samples_folder = Path(IMPORT_PATH, str(projectId) ,str(datasheet), 'Tensile', nominal_age_str)
        
        converted_files_paths = save_to_share(samples_folder, f_dict, bool_delete_existing)
        tensile_files = [str(path) for path in converted_files_paths]
    return {'path':samples_folder,'datasheet_path':str(datasheet_path) ,'tensile_files':tensile_files,"tensile_age":int(nominal_age),"datasheet":datasheet,'project_id':projectId, 'user_id':userId}
