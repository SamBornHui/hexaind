import json
import pickle
from pathlib import Path
from decouple import config
import numpy as np
import re
import os
import sys
import pandas as pd
import datetime as dt
# sys.path.append('../src/')
from copy import deepcopy
from datetime import datetime as dtime
import typing
# import prefect
# from prefect import task, Flow
from typing import Tuple
from copy import deepcopy
import lmfit
from autograd import elementwise_grad
import matplotlib.pyplot as plt
# from bokeh.palettes import Category20_20 as palette
from fpdf import FPDF
from io import BytesIO
import math
import traceback
from concurrent.futures import ThreadPoolExecutor
import functools
import shutil
import app.services.apps.datasheet_gen.dsgen_controller.spl_dataclasses as dcl
from  app.services.apps.datasheet_gen.dsgen_controller.utils.utils import sha256_sum
from  app.services.apps.datasheet_gen.dsgen_controller.spl_dataclasses import TensileMetadata, TensileGeometry, TensileResult ,TensileResults, TensileData, TensileSample,BulgeMetadata, BulgeData
from  app.services.apps.datasheet_gen.dsgen_controller.utils.mech_properties import compute_df_tensile_values, compute_elastic_modulus, compute_poisson_ratio, compute_Rp02, compute_bulge_scaling_factor
from  app.services.apps.datasheet_gen.dsgen_controller.fitting import models, objectives
from app.services.apps.datasheet_gen.dsgen_controller.utils.model_fitting import get_rp_rm_plot_points
from app.utils.file_utils import FileUtils
from app.env import *
import logging
logging.getLogger('matplotlib').setLevel(logging.WARNING)
def get_all_file_paths(directory):
    file_paths = []
    # Walk through the directory and its subdirectories
    for foldername, subfolders, filenames in os.walk(directory):
        # Iterate over all filenames in the current directory
        for filename in filenames:
            # Build the full file path
            file_path = os.path.join(foldername, filename)
            # Normalize the path and replace backslashes with forward slashes
            normalized_path = os.path.normpath(file_path).replace('\\', '/')
            # Append the normalized file path to the list
            file_paths.append( normalized_path)
            # file_paths.append('./' + normalized_path)

    # file_paths = [file for file in file_paths if ("Tensile" in file and "_0" in file) or "tensile" not in file.lower()]
    return file_paths

###############
#   Tensile   #
###############
def parse_relative_path(file_path):

    fp_local = Path(file_path)
    path_elements = [None] * 5
    path_elements[-1] = fp_local.name
    parents = [parent.name for parent in fp_local.parents]
    parents = parents[:-1][::-1]
    for idx, parent_name in enumerate(parents):
        path_elements[idx] = parent_name
    if path_elements[1]:
        path_elements[1] = int(path_elements[1])
    if path_elements[3]:
        ans = re.match(r"(\d+) days$", path_elements[3])
        try:
            nominal_age = int(ans[1])
        except (TypeError, ValueError):
            # Could not parse nominal age integer. Folder structure not correct
            nominal_age = None
        finally:
            path_elements[3] = nominal_age
    dict_path_elements = {
        'datasheet': path_elements[1],
        'test_type': path_elements[2],
        'nominal_age': path_elements[3],
        'file_name': path_elements[4]
    }
    return dict_path_elements


def parse_absolute_path(f):
    f_rel = Path(f).relative_to(IMPORT_PATH)
    f_params = parse_relative_path(f_rel)
    
    return f_params

def parse_tensile_paths(files_to_import):
    dict_tensile_sample_paths = {}
    dict_result_paths = {}

    for i_str_path in files_to_import:
        # Get file's Path obj (for easier manipulation)
        i_path = Path(i_str_path)
        if i_path.name == '.DS_Store':
            continue
        # Parse sample/result params
        f_params = parse_absolute_path(i_str_path)
        test_type = f_params['test_type']
        datasheet = f_params['datasheet']
        nominal_age = f_params['nominal_age']
        res_key = (datasheet, nominal_age)
    
        if test_type == 'Tensile':
            if 'result' in i_path.name:
                if res_key not in dict_result_paths.keys():
                    dict_result_paths[res_key] = i_path
            else:
                # Assume it's a sample file.
                # Get corresponding results file
                if res_key in dict_result_paths.keys():
                    res_path = dict_result_paths[res_key]
                else:
                    # Results file not yet imported. Force the import now
                    
                    base_folder = r'{}'.format(i_path.parents[0])
                    # base_folder = i_path.parents[0]
                    _, _, base_files = next(os.walk(base_folder))
                    for b_f in base_files:
                        # Check if the file name contains the word
                        # 'results' and add it to the dict
                        
                        if 'results' in b_f:
                            res_path = Path(base_folder, b_f)
                            dict_result_paths[res_key] = res_path
                # Add sample/result paths to the dictionary
                dict_tensile_sample_paths[i_path] = Path(res_path)
    # Create a list from the dictionary items, parallelize iteration of reading/transforming
    list_tensile_paths = [*dict_tensile_sample_paths.items()]
    # Skip running the rest of the tasks if there are no tensile samples to import

    return list_tensile_paths

def extract_header_tensile_results(results_path: Path):
    tensile_results_meta = {}
    head_ctr = 0
    with open(results_path, 'r', encoding="utf-8") as f:
        regex = r'Test procedure\t(.*)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_results_meta['test_procedure'] = matches[0]
        regex = r'Datasheet ID\t(\d+)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_results_meta['datasheet'] = int(matches[0])
        regex = r'Test lab\t(.*)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_results_meta['test_lab'] = matches[0]
        regex = r'Lab ref. no.\t(.*)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_results_meta['lab_ref'] = matches[0]
        regex = r'Test operator\t(.*)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_results_meta['operator'] = matches[0]
        regex = r'Age \(days\)\t(\d+)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        try:
            tensile_results_meta['age'] = int(matches[0])
        except IndexError:
            pass
        regex = r'Pretreatement\t(.*)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_results_meta['pretreatment'] = matches[0]
        regex = r'Sample geometry / standard\t(.*)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_results_meta['sample_geometry'] = matches[0]
        tensile_results_meta['header_rows'] = head_ctr + 1
    return tensile_results_meta

def extract_data_tensile_results(results_path, ts_meta):
    head_ctr = ts_meta['header_rows']
    df_results = pd.read_csv(results_path, sep='\t', header=head_ctr, index_col=False)
    df_results.set_index("Sample ID", drop=True, inplace=True)
    return df_results

def extract_header_tensile_sample(sample_path):
    tensile_data_meta = {}
    head_ctr = 0
    with open(sample_path, 'r', encoding="utf-8") as f:
        regex = r'Test procedure\t(.*)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_data_meta['test_procedure'] = matches[0]
        regex = r'Datasheet ID\t(\d+)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_data_meta['datasheet'] = int(matches[0])
        regex = r'Test lab\t(.*)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_data_meta['test_lab'] = matches[0]
        regex = r'Lab ref. no.\t(.*)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_data_meta['lab_ref'] = matches[0]
        regex = r'Test date\t(.*)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_data_meta['test_date'] = dt.datetime.fromisoformat(matches[0])
        regex = r'Test operator\t(.*)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_data_meta['operator'] = matches[0]
        regex = r'Age \(days\)\t(\d+)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_data_meta['age'] = int(matches[0])
        regex = r'Pretreatement\t(.*)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_data_meta['pretreatment'] = matches[0]
        regex = r'Sample geometry / standard\t(.*)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_data_meta['sample_geometry'] = matches[0]
        regex = r'Sample ID\t(.*)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_data_meta['sample_name'] = matches[0]
        regex = r'Test direction \(deg\)\t(.*)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_data_meta['load_direction'] = matches[0]
        regex = r'Gauge length \(mm\)\t(.*)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_data_meta['L0'] = float(matches[0])
        regex = r'Sample thickness \(mm\)\t(.*)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_data_meta['a0'] = float(matches[0])
        regex = r'Sample width \(mm\)\t(.*)$'
        head_ctr += 1
        matches = _parse_line(f, regex)
        tensile_data_meta['b0'] = float(matches[0])
    tensile_data_meta['header_rows'] = head_ctr + 1
    return tensile_data_meta


def extract_data_tensile_sample(sample_path, ts_meta):
    head_ctr = ts_meta['header_rows']
    df_data = pd.read_csv(sample_path, sep='\t', header=head_ctr, index_col=False)
    return df_data

def merge_tensile_results_data(sample_path, ts_meta_results, df_results, ts_meta_sample, df_data):
    # Parse necessary info from sample_path
    f_params = parse_absolute_path(sample_path)
    datasheet = f_params['datasheet']
    nominal_age = f_params['nominal_age']
    # Check if the results and data metadata header is matching
    if ts_meta_results['datasheet'] != ts_meta_sample['datasheet']:
        raise AssertionError("Datasheet field for results file different from sample data")
    if ts_meta_results['lab_ref'] != ts_meta_sample['lab_ref']:
        raise AssertionError("Lab. ref. field for results file different from sample data")
    dict_meta_local = deepcopy(ts_meta_sample)
    dict_geom = {}
    for key in ['L0', 'a0', 'b0']:
        dict_geom[key] = dict_meta_local[key]
        del dict_meta_local[key]
    # Delete unneded element
    del dict_meta_local['header_rows']
    ts_meta = TensileMetadata(**dict_meta_local)
    ts_geom = TensileGeometry(**dict_geom)
    sample_name = ts_meta_sample['sample_name']
    # Compile TensileResults
    # Copy df_results and rename the N and R fields to TensileResults format
    df_results_loc = df_results.rename(columns=lambda x: re.sub(r'([rn])(\d+)[-_](\d+)/Ag', r'\1\2_\3', x))
    result_keys = ['Rp02', 'Rm', 'Ag', 'A80', 'Agt', 'E', 'E_c', 'nu', 'nu_c', 'r4_6', 'r8_12', 'r2_20', 'r10_15',
                   'n4_6', 'n10_15', 'n10_20', 'n2_20']
    dict_results = df_results_loc.loc[sample_name, :].to_dict()
    dict_results = {k: v for k, v in dict_results.items() if k in result_keys}

    ts_results = TensileResults(**dict_results)
    # Compile TensileDatas
    ts_data = TensileData(
        time=df_data['time (s)'].to_numpy(),
        delta_l=df_data['elongation L (mm)'].to_numpy(),
        delta_b=df_data['elongation T (mm)'].to_numpy(),
        load=df_data['force (N)'].to_numpy(),
        s=df_data['eng. stress (MPa)'].to_numpy(),
        e=df_data['eng. strain L (%)'].to_numpy()/100,
        e_lat=df_data['eng. strain T (%)'].to_numpy()/100
    )
    # Compile everything into the TensileTest object
    ts_test = TensileSample(
        # File path info
        datasheet=datasheet,
        nominal_age=nominal_age,
        file_name=sample_path,
        # file_name=sample_path.name,
        sha256_hash=sha256_sum(sample_path),
        # Sample meta/data
        metadata=ts_meta,
        initial_geometry=ts_geom,
        original_results=ts_results,
        recomputed_results=None,
        data=ts_data,
    )
    return ts_test

def _parse_line(f, regex):
    # Compile regex match pattern
    re_match = re.compile(regex, re.UNICODE)
    # Read the next line from the file
    line = f.readline()
    # Match the pattern in the line
    matches = re_match.findall(line)
    return matches

def extract_tensile(tensile_path):
    sample_path, result_path = tensile_path
    header_results = extract_header_tensile_results(result_path)
    df_results = extract_data_tensile_results(result_path, header_results)
    header_sample = extract_header_tensile_sample(sample_path)
    df_sample = extract_data_tensile_sample(sample_path, header_sample)
    ts_test = merge_tensile_results_data(sample_path, header_results, df_results, header_sample, df_sample)
    # logger.info(f"Finished extracting tensile file for {ts_test.datasheet}/{ts_test.nominal_age}/{ts_test.file_name}")
    return ts_test

def transform_tensile(ts_test: dcl.TensileSample) -> dcl.TensileSample:
    # """Prefect task to compute the mechanical results from tensile data.
    # Args:
    #     ts_test (TensileSample): Object containing the Raw data of the tensile test
    # Returns:
    #     TensileSample: Object containing raw data and computed mechanical values of the test
    # """
    # Scale original results
    # Ag from [%] to [-]
    ts_test.original_results.Ag /= 100
    # A80 from [%] to [-]
    ts_test.original_results.A80 /= 100
    # Scale Elastic Modulus from Ga to MPa
    ts_test.original_results.E *= 1000
    # Initial area
    a0 = ts_test.initial_geometry.a0
    b0 = ts_test.initial_geometry.b0
    L0 = ts_test.initial_geometry.L0
    A0 = np.round(a0 * b0, 2)
    # Engineering stress/ strain
    ts_test.data.s = ts_test.data.load/A0
    ts_test.data.e = ts_test.data.delta_l/L0
    # Lateral engineering strain
    ts_test.data.e_lat = ts_test.data.delta_b/b0
    # Compute elastic modulus and Poisson ratio
    # Elastic modulus is fitted in the stress range [10% Rp02 ~ 60% Rp02]
    s_min = 0.1 * ts_test.original_results.Rp02
    s_max = 0.6 * ts_test.original_results.Rp02
    E, E_c = compute_elastic_modulus(ts_test.data.e, ts_test.data.s, s_min, s_max)
    nu, n_fit = compute_poisson_ratio(ts_test.data.e_lat, ts_test.data.s, E, s_min, s_max)
    # Toe compensation
    ts_test.data.e_toe = ts_test.data.e + E_c/E
    # ts_test_data_df = pd.DataFrame(ts_test.data.e)
    e = ts_test.data.e
    e_toe = e + E_c/E
    ts_test.data.eps =  np.log(1 + e_toe)

    s = ts_test.data.s
    ts_test.data.sig = s * (1 + e_toe)

    ts_test.data.eps_pl = ts_test.data.eps - ts_test.data.sig/E

    # Compute Rp02
    try:
        Rp02 = compute_Rp02(ts_test.data.e_toe, ts_test.data.s, E)
    except ArithmeticError:
        # logger.warning(f"Could not compute Rp02 for {ts_test.metadata.sample_name}. Setting no nan")
        Rp02 = np.nan
    res_recomputed = dcl.TensileResults(
        Rp02=Rp02,
        E=E,
        E_c=E_c,
        nu=nu,
        nu_c=n_fit,
    )
    ts_test.recomputed_results = res_recomputed
   
    return ts_test


def handle_failed_tensile(tensile_paths, ts_tests):
    ts_tests_filtered = []
    for i_tensile_path, i_ts_test in zip(tensile_paths, ts_tests):
        sample_path = i_tensile_path[0]
        # Rename failed files
        if isinstance(i_ts_test, (BaseException, ValueError)):
            base_folder = sample_path.parents[0]
            new_path = Path(base_folder, f"[IMPORT ERROR]{sample_path.name}")
            sample_path.rename(new_path)
        else:
            # Append correctly parsed files to filtered list
            ts_tests_filtered.append(i_ts_test)
    # Skip loading if there are no successful tests
    return ts_tests_filtered


###############
#    Bulge    #
###############
def parse_bulge_paths(files_to_import):
    # List of all bulge samples Paths
    list_bulge_paths = []

    for i_str_path in files_to_import:
        # Get file's Path obj (for easier manipulation)
        i_path = Path(i_str_path)

        # Parse sample/result params
        f_params = parse_absolute_path(i_str_path)
        test_type = f_params['test_type']
        # datasheet = f_params['datasheet']
        # nominal_age = f_params['nominal_age']

        if test_type == 'Bulge':
            list_bulge_paths.append(i_path)

    # Skipping if no bulge files to import
    # if not list_bulge_paths:
    #     raise signals.SKIP

    return list_bulge_paths

def extract_bulge(sample_path):

    # Parse necessary info from sample_path
    f_params = parse_absolute_path(sample_path)
    datasheet = f_params['datasheet']
    nominal_age = f_params['nominal_age']

    bg_meta = extract_header_bulge(sample_path)
    bg_data = extract_data_bulge(sample_path)

    # Merge all info
    bg_test = dcl.BulgeSample(
        # path info
        datasheet=datasheet,
        nominal_age=nominal_age,
        file_name=sample_path.name,
        sha256_hash=sha256_sum(sample_path),
        # file meta/data
        metadata=bg_meta,
        data=bg_data
    )

    return bg_test


def extract_header_bulge(bulge_path):

    bulge_meta_kwargs = {}
    # Read file contents
    head_ctr = 0
    
    with open(bulge_path, 'r') as f:

        # Read first lines that don't contain stuff
        for _ in range(2):
            head_ctr += 1
            _ = _parse_bulge_line(f, r"")

        # Read test date and stuff
        regex = r'^#(.*),(.*):(.*)\/\/[ ]+(\d{1,2})[\.\/](\d{1,2})[\.\/](\d{4})$'
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        test_date_str = ".".join(matches[0][3:])
        bulge_meta_kwargs['test_date'] = dtime.strptime(test_date_str, "%d.%m.%Y")

        # Read material
        regex = r'^# Material:[ ]*(.*)$'
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['material'] = None if matches[0] == '' else matches[0]

        # Read initial thickness
        regex = r'^# Initial thickness:[ ]?(\d+\.?\d*) mm$'
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['initial_thickness'] = float(matches[0])

        # Skip two uninteresting lines
        for _ in range(2):
            head_ctr += 1
            _ = _parse_bulge_line(f, r"")

        # Read grid spacing
        regex = r'^# Estimated grid spacing:[ ]?(\d+\.?\d*) mm$'
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['grid_spacing'] = float(matches[0])

        # Start reading parameters
        head_ctr += 1
        _ = _parse_bulge_line(f, r'')

        regex = r'^# d_die:[ ]?(\d+.?\d*)'
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['d_die'] = float(matches[0])

        regex = r'^# r_1:[ ]?(\d+.?\d*)'
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['r_1'] = float(matches[0])

        regex = r'^# r_2:[ ]?(\d+.?\d*)'
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['r_2'] = float(matches[0])

        regex = r'^# Type of geometry for shape fit:[ ]?(.*)$'
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['type_geom'] = None if matches[0] == '' else matches[0]

        regex = r"^# Type of pole's strain evaluation:[ ]?(.*)$"
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['type_pole'] = None if matches[0] == '' else matches[0]

        regex = r"^# Type of selection:[ ]?(.*)$"
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['type_selection'] = None if matches[0] == '' else matches[0]

        regex = r"^# Elastic strain compensation:[ ]?(.*)$"
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['el_str_comp'] = None if matches[0] == '' else matches[0]

        regex = r"^#[ ]*Young's modulus:[ ]?(\d+.?\d*)MPa$"
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['E'] = float(matches[0])

        regex = r"^#[ ]*Poisson's ratio:[ ]?(\d+.?\d*)$"
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['nu'] = float(matches[0])

        regex = r"^# Bending strain compensation:[ ]?(.*)$"
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['ben_str_comp'] = None if matches[0] == '' else matches[0]

        regex = r"^# Radius compensation:[ ]?(.*)$"
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['rad_comp'] = None if matches[0] == '' else matches[0]

        regex = r"^# Strain rate compensation:[ ]?(.*)$"
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['str_rate_comp'] = None if matches[0] == '' else matches[0]

        regex = r"^#[ ]*C:[ ]?(\d+.?\d*)$"
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['C'] = float(matches[0])

        regex = r"^#[ ]*p:[ ]?(\d+.?\d*)$"
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['p'] = float(matches[0])

        regex = r"^#[ ]*Fit width:[ ]?(\d+.?\d*)$"
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['fit_width'] = float(matches[0])

        regex = r"^# Extend uniaxial yield curve:[ ]?(.*)$"
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['extend_uniaxial_curve'] = None if matches[0] == '' else matches[0]

        regex = r"^#[ ]*Tensile test yield curve file:[ ]?(.*)$"
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['ts_test_yield_curve_file'] = None if matches[0] == '' else matches[0]

        regex = r"^#[ ]*True strain column:[ ]?(.*)$"
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['true_strain_col'] = None if matches[0] == '' else matches[0]

        regex = r"^#[ ]*True stress column:[ ]?(.*)$"
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        bulge_meta_kwargs['true_stress_col'] = None if matches[0] == '' else matches[0]

        regex = r"^#[ ]*Bi-axial stress ratio:[ ]?(.*)$"
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        try:
            biaxial_stress_ratio = float(matches[0])
        except ValueError:
            biaxial_stress_ratio = None
            # print("WARNING: Could not parse biaxial_stress_ratio from bulge file")
        bulge_meta_kwargs['biaxial_stress_ratio'] = biaxial_stress_ratio

        # Skip two unneeded rows
        for idx in range(2):
            head_ctr += 1
            _parse_bulge_line(f, regex)

        # Parse column names
        regex = r'# Stage; .*$'
        head_ctr += 1
        matches = _parse_bulge_line(f, regex)
        if matches:
            res = matches[0][2:]  # Cut the '# ' initial chars
            cols = res.rstrip('').split(";")
        bulge_meta_kwargs['columns'] = cols

        bulge_meta_kwargs['header_rows'] = head_ctr

        # Instantiate the BulgeMetadata object with all the parsed info
        bulge_meta = BulgeMetadata(**bulge_meta_kwargs)

    return bulge_meta


def _parse_bulge_line(f: typing.TextIO, regex: str):

    line = f.readline()
    matches = re.findall(regex, line)

    return matches


def extract_data_bulge(sample_path):

    # NOTE: Header is hardcorded because extract_header_bulge assumes fixed header size (for now?)
    header_ctr = 32

    # Read the sample buldge file
    # df_bulge = pd.read_csv(sample_path, sep=';')
    df_bulge = pd.read_csv(sample_path, sep=';', header= header_ctr - 1,index_col=False)
    df_bulge.rename(columns={"# Stage": 'Stage'}, inplace=True)
    # Strip whitespace columns
    df_bulge.rename(columns=lambda x: x.strip(), inplace=True)
    df_bulge.set_index('Stage', drop=True, inplace=True)
    # Replace None values with np.nan's
    df_bulge.replace({
        ' None': np.nan,
        'None': np.nan,
    }, inplace=True)

    # Cast values to float for operations
    df_bulge = df_bulge.astype(float)

    # Only keep the columns we are interested in (for computation)
    dict_bulgecols = {
        'Time': 'time',
        'Radius': 'radius',
        'Pressure': 'pressure',
        'True Strain (YC1)': 'eps_1',
        'True Stress (YC1)': 'sig_1',
    }
    df_bulge.rename(columns=dict_bulgecols, inplace=True)
    df_bulge = df_bulge.loc[:, dict_bulgecols.values()]

    bulge_data = BulgeData(
        exp_time=df_bulge['time'].values,
        radius=df_bulge['radius'].values,
        pressure=df_bulge['pressure'].values,

        eps_1=df_bulge['eps_1'].values,
        sig_1=df_bulge['sig_1'].values
    )

    return bulge_data

def handle_failed_imports(file_paths, file_outputs):

    files_filtered = []

    for i_file_path, i_output in zip(file_paths, file_outputs):

        # Rename failed files
        if isinstance(i_output, (BaseException, ValueError)):

            base_folder = i_file_path.parents[0]

            new_path = Path(base_folder, f"[IMPORT ERROR]{i_file_path.name}")
            i_file_path.rename(new_path)
        else:
            # Append correctly parsed files to filtered list
            files_filtered.append(i_output)

    # Skip loading if there are no successful tests

    return files_filtered

###########
#   FLC   #
###########

def parse_flc_raw_paths(files_to_import):

    # {datasheet -> sample_path}
    list_flc_samples = []

    for i_str_path in files_to_import:
        i_path = Path(i_str_path)

        # Parse sample params
        f_params = parse_absolute_path(i_str_path)
        test_type = f_params['test_type']
        # datasheet = f_params['datasheet']
        # nominal_age = f_params['nominal_age']

        if (test_type == 'FLC') and \
           ('raw' in i_path.name):
            list_flc_samples.append(i_path)

    # Skipping if no flc raw files to import
    # if not list_flc_samples:
    #     raise signals.SKIP

    return list_flc_samples

def extract_flc_raw(raw_path):

    df_flc_raw = pd.read_csv(raw_path, sep='\t', header=10)

    flc_raw = {
        'path': raw_path,
        'df': df_flc_raw,
    }

    return flc_raw

def transform_flc_raw(flc_raw):

    df = flc_raw['df'].copy()

    df.columns = ['s_major', 's_minor', 'spl_geom', 'spl_nr', 'section', 'comment']

    df.dropna(how='all', inplace=True)
    df.replace({np.nan: None}, inplace=True)

    flc_raw['df'] = df

    return flc_raw

def parse_flc_fit_paths(files_to_import):

    # {datasheet -> sample_path}
    list_flc_fits = []

    for i_str_path in files_to_import:
        i_path = Path(i_str_path)

        # Parse sample params
        f_params = parse_absolute_path(i_str_path)
        test_type = f_params['test_type']
        # datasheet = f_params['datasheet']
        # nominal_age = f_params['nominal_age']

        if (test_type == 'FLC') and \
           ('fit' in i_path.name):
            list_flc_fits.append(i_path)

    # Skipping if no flc fit files to import
    # if not list_flc_fits:
    #     raise signals.SKIP

    return list_flc_fits

def extract_flc_fit(fit_path):

    df_flc_fit = pd.read_csv(fit_path, sep='\t', header=10)

    flc_fit = {
        'path': fit_path,
        'df': df_flc_fit
    }

    return flc_fit

def transform_flc_fit(flc_fit):

    df = flc_fit['df'].copy()

    df.columns = ['s_minor', 's_major', 's_major_plus_sigma', 's_major_minus_sigma']

    df.dropna(how='all', inplace=True)
    df.replace({np.nan: None}, inplace=True)

    flc_fit['df'] = df

    return flc_fit

# 
####################
# Combined Results #
####################


def combine_results(test):
    original_results = test.original_results
    recomputed_results = test.recomputed_results
    
    combined = {
        'Rp02': original_results.Rp02 if not math.isnan(original_results.Rp02) else recomputed_results.Rp02,
        'Rm': original_results.Rm if not math.isnan(original_results.Rm) else recomputed_results.Rm,
        'Ag': original_results.Ag if not math.isnan(original_results.Ag) else recomputed_results.Ag,
        'Agt': original_results.Agt if not math.isnan(original_results.Agt) else recomputed_results.Agt,
        'A80': original_results.A80 if not math.isnan(original_results.A80) else recomputed_results.A80,
        'E': original_results.E if not math.isnan(original_results.E) else recomputed_results.E,
        'E_c': recomputed_results.E_c if not math.isnan(recomputed_results.E_c) else original_results.E_c,
        'nu': recomputed_results.nu if not math.isnan(recomputed_results.nu) else original_results.nu,
        'nu_c': recomputed_results.nu_c if not math.isnan(recomputed_results.nu_c) else original_results.nu_c,
        'r4_6': recomputed_results.r4_6 if not math.isnan(recomputed_results.r4_6) else original_results.r4_6,
        'r8_12': recomputed_results.r8_12 if not math.isnan(recomputed_results.r8_12) else original_results.r8_12,
        'r2_20': recomputed_results.r2_20 if not math.isnan(recomputed_results.r2_20) else original_results.r2_20,
        'r10_15': recomputed_results.r10_15 if not math.isnan(recomputed_results.r10_15) else original_results.r10_15,
        'n4_6': recomputed_results.n4_6 if not math.isnan(recomputed_results.n4_6) else original_results.n4_6,
        'n10_15': recomputed_results.n10_15 if not math.isnan(recomputed_results.n10_15) else original_results.n10_15,
        'n10_20': recomputed_results.n10_20 if not math.isnan(recomputed_results.n10_20) else original_results.n10_20,
        'n2_20': recomputed_results.n2_20 if not math.isnan(recomputed_results.n2_20) else original_results.n2_20,
        'file_name': test.file_name,
        'datasheet': test.datasheet,
        'nominal_age': test.nominal_age,
        'load_direction':test.metadata.load_direction
    }
    return combined

def handle_nan_null_inf(df):
    df = df.fillna(0)

    return df

#####################
# Tensile Corrected #
#####################

def correct_tensile(projectId, selected_sample, s_min, s_max, df_ten_data, combined_results_list , combined_results_list_initial, recompute_Rp02,corrected_params):
    try:    
        df_tensile= df_ten_data
        df_tensile.rename(columns={
                'xdata': 'e',
                'ydata': 's'
            },
            inplace=True,
        )
        s_min = s_min
        s_max = s_max
        data_lines = (df_tensile['file_name'] == selected_sample)
        df_data_sample = df_tensile[data_lines][['e', 's']]
        df_all_sample_results = pd.DataFrame(combined_results_list)
        if corrected_params:
            df_sample_results = pd.DataFrame(corrected_params, index=[0])
            # E = corrected_params['E'] In case if donot want this to be changed by user
            # E_c = corrected_params['E_c']    In case if donot want this to be changed by user
        else:            
            df_sample_results = df_all_sample_results[df_all_sample_results['file_name'].astype(str).str.contains(selected_sample)].copy()
        
        E, E_c = compute_elastic_modulus(df_data_sample['e'], df_data_sample['s'], s_min, s_max)
        df_sample_results.loc[:, 'E'] = E
        df_sample_results.loc[:, 'E_c'] = E_c

        if recompute_Rp02:
            Rp02 = compute_Rp02(df_data_sample['e'], df_data_sample['s'], E)
            df_sample_results.loc[:, 'Rp02'] = Rp02

        df_sample_results.loc[:, 'Ag'] = df_sample_results['Agt'] - df_sample_results['Rm']/df_sample_results['E']
        df_sample_results = handle_nan_null_inf(df_sample_results)

        if combined_results_list_initial is not None and len(combined_results_list_initial) > 0:
            df_all_initail_sample_results = pd.DataFrame(combined_results_list_initial)
            df_initail_sample_results = df_all_initail_sample_results[df_all_initail_sample_results['file_name'].astype(str).str.contains(selected_sample)].copy()
            s_min_i = 20
            s_max_i = 60
            E, E_c = compute_elastic_modulus(df_data_sample['e'], df_data_sample['s'], s_min_i, s_max_i)
            df_initail_sample_results.loc[:, 'E'] = E
            df_initail_sample_results.loc[:, 'E_c'] = E_c
            if recompute_Rp02:
                Rp02 = compute_Rp02(df_data_sample['e'], df_data_sample['s'], E)
                df_initail_sample_results.loc[:, 'Rp02'] = Rp02
            df_initail_sample_results.loc[:, 'Ag'] = df_initail_sample_results['Agt'] - df_initail_sample_results['Rm']/df_initail_sample_results['E']
            df_initail_sample_results = handle_nan_null_inf(df_initail_sample_results)
        else:
            df_initail_sample_results = []

        if corrected_params:
            df_list = df_sample_results.to_dict(orient='records')
            df_all_sample_results.loc[df_all_sample_results['file_name'] == df_list[0]['file_name']]= list(df_list[0].values())
            tensile_computed_results_path = create_csv(projectId, df_all_sample_results,corrected_params['datasheet'], corrected_params['nominal_age'],'tensile_combined_results_list.csv')           
            
        df_tensile_computed = compute_df_tensile_values(df_data_sample, df_sample_results)
        
        corrected_tesile_plot = _plot_tensile_with_results(df_tensile_computed, df_sample_results, df_initail_sample_results, selected_sample, s_min, s_max)
        
        if corrected_params:
            file_name ='datasheet_workflow_results.json'
            s_datasheet= corrected_params['datasheet']
            s_nominal_age = corrected_params['nominal_age']
            output_directory = os.path.join(EXPORT_PATH,str(projectId), str(s_datasheet), str(s_nominal_age))
            json_file_path = os.path.join(output_directory, file_name)
            if os.path.exists(json_file_path):
                json_data = read_json(projectId,s_datasheet,s_nominal_age,file_name)
                datasheet_detail = json.loads(json_data) 
                datasheet_detail['corrected_tensile_results'] = corrected_tesile_plot
                json_datasheet_detail = json.dumps(datasheet_detail, indent=4)
                datasheet_workflow_results = create_json(projectId, json_datasheet_detail,s_datasheet, s_nominal_age,'datasheet_workflow_results.json')
            
        return corrected_tesile_plot
    except Exception as e:
        print(e)
        print(traceback.format_exc())

def _plot_tensile_with_results(df_tensile_computed, df_results, df_initial_results, sample_name, s_min, s_max):

    E = float(df_results['E'])
    E_c = float(df_results['E_c'])
    Rp02 = float(df_results['Rp02'])

    xdata = df_tensile_computed['e_toe']
    ydata = df_tensile_computed['s']
    
    # Elastic modulus
    x_E = np.array([0, 1.1 * Rp02/E])
    y_E = E * x_E
    
    # Rp02 and tangent modulus
    x_E_Rp02 = x_E + 0.2/100
    sig_Rp02 = df_results['Rp02']
    x_E_Rp02 = 0.2/100 + sig_Rp02/E
    
    # Agt/Rm
    Agt = float(df_results['Agt'])
    Rm = float(df_results['Rm'])
 
    df_results['file_name'] = df_results['file_name'].apply(str)
    df_results = df_results.to_dict(orient='records')

    if df_initial_results is not None and len(df_initial_results) > 0:
        df_initial_results['file_name'] = df_initial_results['file_name'].apply(str)
        df_initial_results = df_initial_results.to_dict(orient='records')
    else:
        df_initial_results = df_results
    corrected_result={'xdata':xdata.tolist(), 'ydata':ydata.tolist(),'x_E':x_E.tolist(),'y_E':y_E.tolist(),'x_E_Rp02':x_E_Rp02.tolist(),'sig_Rp02':sig_Rp02.tolist(),'Agt':Agt,'Rm':Rm, 'df_results':df_results ,'df_initial_results':df_initial_results,
                      'sample_name':sample_name, 's_min':s_min, 's_max':s_max}
    return corrected_result

#####################
#   Model fitting   #
#####################
def get_fitting_strain_range(avg_mech):
    # Compute the resulting strain range for fitting
    eps_range = get_tensile_eps_range(*avg_mech)
    return eps_range


def get_tensile_eps_range(E, Rp02, Rm, Ag, Agt) -> Tuple[float, float]:
    e_02 = 0.2/100
    # True values
    sig_02 = Rp02 * (1 + e_02 + Rp02/E)
    eps_pl_02 = np.log(1 + e_02 + Rp02/E) - sig_02/E
    sig_ag = Rm * (1 + Ag + Rm/E)
    eps_pl_ag = np.log(1 + Ag + Rm/E) - sig_ag/E
    # eps_agt = np.log(1 + Agt)
    return eps_pl_02, eps_pl_ag

def get_fitting_strain_range(avg_mech):
    # Compute the resulting strain range for fitting
    eps_range = get_tensile_eps_range(*avg_mech)
    return eps_range

def get_tensile_fitting_data(test,eps_min,eps_max):
    eps_list =[]
    sig_list=[]
    eps_pl_list=[]
    file_name=test.file_name.name
    e_toe_l =test.data.e_toe.tolist()
    s_l =test.data.s.tolist()
  
    for etoe,s in zip(e_toe_l,s_l):

        eps_list.append(math.log(1 + etoe))
        
        
        eps_pl = (math.log(1 + etoe))-(s* (1 + etoe))/test.original_results.E
        if(eps_min < eps_pl and eps_pl <eps_max):
            eps_pl_list.append(eps_pl)
            sig_list.append(s* (1 + etoe))
            

    return eps_pl_list, sig_list, file_name

def calculate_k_mean(selected_nominal_age, tests, avg_mech,list_excluded_bulge):
    
    k_values =[]
    scale_factor_bulge=[]
    for test in tests:
        if test.nominal_age == selected_nominal_age and test.file_name not in list_excluded_bulge:
            E, Rp02, Rm, Ag, Agt = avg_mech
            k = compute_bulge_scaling_factor(E, Rm, Ag, test.data.sig_1, test.data.eps_1)
            if not np.isnan(k):
                k_values.append(k)
                scale_factor_bulge.append({"file":test.file_name, "k":k})
    k_mean = np.mean(k_values)
    return k_mean, scale_factor_bulge

def get_bulge_fitting_data(test,eps_range,k_mean):
    
    eps_sc=[]
    sig_sc=[]
    file_name=test.file_name
    
    for eps1,sig1 in zip (test.data.eps_1, test.data.sig_1):    
         if(eps_range < eps1 / k_mean):
            eps_sc.append(eps1 / k_mean)
            sig_sc.append(sig1 * k_mean)
                   
    return eps_sc, sig_sc, file_name

########
# Voce #
########

def get_voce_params_dict(avg_mech, datasheet, nominal_age):
    model_name = 'voce'
    # Set default parameter values
    params_dict = {
        'sig_0': {
            'param_init': avg_mech[1],
            'param_min': -np.inf,
            'param_max': np.inf,
            'param_variable': True,
        },
        'sig_inf': {
            'param_init': 1.2 * avg_mech[2],
            'param_min': -np.inf,
            'param_max': np.inf,
            'param_variable': True,
        },
        'n': {
            'param_init': 1,
            'param_min': -np.inf,
            'param_max': np.inf,
            'param_variable': True,
        },
    }
    # overwritten_params_dict = overwrite_local_parameters(
    #     params_dict,
    #     datasheet,
    #     nominal_age,
    #     model_name
    # )
    return params_dict


def get_lmfit_params_from_dict(params_dict):
    params = lmfit.Parameters()
    for param_key, param_values in params_dict.items():
        params.add(
            param_key,
            value=param_values['param_init'],
            min=param_values['param_min'],
            max=param_values['param_max'],
            vary=param_values['param_variable'],
            )
    return params


def merge_params(dict_init_params, dict_out_params):
    assert dict_init_params.keys() == dict_out_params.keys()
    dict_merged_params = deepcopy(dict_init_params)
    for key, out_value in dict_out_params.items():
        dict_merged_params[key]['param_value'] = out_value
    return dict_merged_params


def get_lmfit_params_dict(params):
    dict_params = {}
    for key, value in params.items():
        dict_params[key] = value.value
    return dict_params

def fit_model_parameters(model_name, lmfit_params, model_weights, data_tensile, data_bulge, eps_range):
    model = getattr(models, model_name)
    model_grad = elementwise_grad(model)
    np_tensile = np.array(data_tensile)
    np_bulge = np.array(data_bulge)
    eps_pl_02, eps_pl_ag = eps_range
    tensile_weight = model_weights[0]
    bulge_weight = model_weights[1]

    # if model_weights[2]:  # scaled_residue == True
    tensile_weight /= int(np.sqrt(np_tensile.shape[0]))
    bulge_weight /= int(np.sqrt(np_bulge.shape[0]))
    considere_weight = model_weights[3]
    weights = [tensile_weight, bulge_weight, considere_weight]
    fit_methods = ['leastsq', 'least_squares']
    method_idx = 0
    successful_opt = False

    while not successful_opt:
        try:
            out = lmfit.minimize(
                objectives.obj_ls_considere,
                lmfit_params,
                args=(model, model_grad, eps_pl_ag),
                kws={'weights': weights, 'np_tensile': np_tensile, 'np_bulge': np_bulge},
                method=fit_methods[method_idx],
            )
            successful_opt = True
        except ValueError as e:
            logging.warning(f"Could not fit {model_name} with {fit_methods[method_idx]}")
            if method_idx < len(fit_methods) - 1:
                method_idx += 1
            else:
                raise e
 
    model_out_params = get_lmfit_params_dict(out.params)
    return model_out_params


def add_params_to_insert(dict_params_to_insert, datasheet, nominal_age, model_name, complete_params):
    local_dict = deepcopy(dict_params_to_insert)
    local_dict[(datasheet, nominal_age, model_name)] = complete_params
    return local_dict

###############
#    Swift    #
###############

def get_swift_params_dict(avg_mech, datasheet, nominal_age):
    model_name = 'swift'
    # Set default parameter values
    params_dict = {
        'C': {
            'param_init': 1.5 * avg_mech[2],
            'param_min': 0.001,
            'param_max': 1000,
            'param_variable': True
        },
        'eps_0': {
            'param_init': 0.01,
            'param_min': 0,
            'param_max': 1000,
            'param_variable': True
        },
        'm': {
            'param_init': 0.2,
            'param_min': 0,
            'param_max': 1000,
            'param_variable': True
        }
    }
    # overwritten_params_dict = overwrite_local_parameters(
    #     params_dict,
    #     datasheet,
    #     nominal_age,
    #     model_name
    # )
    return params_dict

#################
# hpcket sherby #
#################

def get_hocket_sherby_params_dict(voce_params, datasheet, nominal_age):
    model_name = 'hocket_sherby'
    # Set default parameter values
    params_dict = {
        'sig_i': {
            'param_init': voce_params['sig_0'],
            'param_min': -np.inf,
            'param_max': np.inf,
            'param_variable': True
        },
        'sig_sat': {
            'param_init': voce_params['sig_inf'],
            'param_min': -np.inf,
            'param_max': np.inf,
            'param_variable': True
        },
        'a': {
            'param_init': voce_params['n'],
            'param_min': -np.inf,
            'param_max': np.inf,
            'param_variable': True
        },
        'p': {
            'param_init': 1,
            'param_min': -np.inf,
            'param_max': np.inf,
            'param_variable': True
        },
        # 'c': {
        #     'param_init': 1,
        #     'param_min': -np.inf,
        #     'param_max': np.inf,
        #     'param_variable': True
        # }
    }
    # overwritten_params_dict = overwrite_local_parameters(
    #     params_dict,
    #     datasheet,
    #     nominal_age,
    #     model_name
    # )
    return params_dict


#######################
# Hocket Sherby Swift #
#######################

def get_hocket_sherby_swift_params_dict(hs_params, swift_params, datasheet, nominal_age):
    model_name = 'hocket_sherby_swift'
    # Set default parameter values
    params_dict = {
        # Hocket-Sherby part
        'sig_i': {
            'param_init': hs_params['sig_i'],
            'param_min': 0,
            'param_max': 10000,
            'param_variable': True
        },
        'sig_sat': {
            'param_init': hs_params['sig_sat'],
            'param_min': 0,
            'param_max': 10000,
            'param_variable': True
        },
        'a': {
            'param_init': hs_params['a'],
            'param_min': 0,
            'param_max': 10000,
            'param_variable': True
        },
        'p': {
            'param_init': hs_params['p'],
            'param_min': 0,
            'param_max': 10000,
            'param_variable': True
        },
        # Swift part
        'C': {
            'param_init': swift_params['C'],
            'param_min': 0,
            'param_max': 10000,
            'param_variable': True
        },
        'eps_0': {
            'param_init': swift_params['eps_0'],
            'param_min': 0,
            'param_max': 10000,
            'param_variable': True
        },
        'm': {
            'param_init': swift_params['m'],
            'param_min': 0,
            'param_max': 10000,
            'param_variable': True
        },
        'alpha': {
            'param_init': 0.75,
            'param_min': 0,
            'param_max': 1,
            'param_variable': False
        }
    }
    # overwritten_params_dict = overwrite_local_parameters(
    #     params_dict,
    #     datasheet,
    #     nominal_age,
    #     model_name
    # )
    return params_dict

#######################
#       create csv    #
#######################
def create_csv(projectId, df_data,selected_datasheet, selected_nominal_age,file_name):
    output_directory = os.path.join(EXPORT_PATH, str(projectId), str(selected_datasheet), str(selected_nominal_age))

    # Create the directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Create a sample DataFrame (replace this with your actual DataFrame)

    # Create the full path for the CSV file within the new directory
    csv_file_path = os.path.join(output_directory, file_name)

    # Write the DataFrame to the CSV file
    df_data.to_csv(csv_file_path, index=False)

    return csv_file_path
#######################
#      create json    #
#######################
def create_json(projectId, data, selected_datasheet, selected_nominal_age, file_name):
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
#######################
#   create pkl file   #
#######################

def create_pkl(projectId, ts_tests,selected_datasheet, selected_nominal_age,file_name):
    output_directory = os.path.join(EXPORT_PATH,str(projectId),str(selected_datasheet),str(selected_nominal_age))

    # Create the directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Create a sample DataFrame (replace this with your actual DataFrame)

    # Create the full path for the CSV file within the new directory
    pkl_file_path = os.path.join(output_directory, file_name)
    with open(pkl_file_path, 'wb') as file:
        pickle.dump(ts_tests, file)
    return pkl_file_path
#########################
#   Export Datasheet   #
#########################
def get_model_and_grad_plot_data(xdata, model_name, model_params):
    model = getattr(models, model_name)
    model_grad = elementwise_grad(model)
    # Compute new model data and grad
    df_model = pd.DataFrame(
        {
            'xdata': xdata,
            'mdata': model(xdata, **model_params),
            'm_grad_data': model_grad(xdata, **model_params),
        }
    )
    # Compute n-value stuff for the model
    n_value = df_model['m_grad_data'] * df_model['xdata']/df_model['mdata']
    df_model.insert(3, 'n_value', n_value)
    return df_model

def compile_nvalues_df(df_results, avg_mech):

    n_vals_regex = r"n(\d+)_(\d+)"
    n_cols = df_results.columns.str.contains(n_vals_regex, regex=True)
    # Only get the n-value columns
    df_nvalues = df_results.loc[:, n_cols]
    df_nranges = df_nvalues.columns.str.extract(n_vals_regex).T.astype(float)

    # Compile v_values dataframe (for easier calculations)
    df_nvalues = pd.DataFrame({
        'value': df_nvalues.mean(),
        'strain_min': df_nranges.loc[0, :].values/100,
        'strain_max': df_nranges.loc[1, :].values/100,
    }).T

    # Clip n-value range to Ag
    df_nvalues.loc['strain_ag', :] = avg_mech['Ag']
    df_nvalues.loc['strain_max_clipped', :] = df_nvalues.loc[['strain_max', 'strain_ag'], :].min()

    # Compute the average strain
    df_nvalues.loc['strain_avg', :] = df_nvalues.loc[['strain_min', 'strain_max_clipped'], :].mean()
    df_nvalues.loc['log_strain_avg', :] = np.log(1 + df_nvalues.loc['strain_avg', :])

    return df_nvalues

###############
#  read_json  #
###############
def read_json(projectId,datasheet,nominal_age,file_name):
    output_directory = os.path.join(EXPORT_PATH, str(projectId), str(datasheet), str(nominal_age))
    json_file_path = os.path.join(output_directory, file_name)
    with open(json_file_path, 'r') as json_file:
        data_str_keys = json.load(json_file)
    return data_str_keys

def read_metadata(projectId,datasheet,file_name):
    output_directory = os.path.join(EXPORT_PATH, str(projectId), str(datasheet))
    json_file_path = os.path.join(output_directory, file_name)
    with open(json_file_path, 'r') as json_file:
        data_str_keys = json.load(json_file)
    return data_str_keys

def save_metadata_async(metadata,projectId,selected_datasheet):
    output_directory = os.path.join(EXPORT_PATH, str(projectId), str(selected_datasheet))
    # Create the directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Create a sample DataFrame (replace this with your actual DataFrame)

    # Create the full path for the CSV file within the new directory
    metadata_path = os.path.join(output_directory, 'metadata.json')

    with open(metadata_path, 'w') as json_file:
        json.dump(metadata, json_file, indent=4)
    path = {'metadata_path':metadata_path}
    return path

def read_csv(projectId,datasheet,nominal_age,file_name):

    output_directory = os.path.join(EXPORT_PATH, str(projectId), str(datasheet), str(nominal_age))
    csv_file_path = os.path.join(output_directory, file_name)
    df_data = pd.read_csv(csv_file_path)
    return df_data


###############
#  run flow   #
###############

def run_workflow(projectId,s_datasheet, s_nominal_age,reset):
    try:
        output_directory = os.path.join(EXPORT_PATH, str(projectId), str(s_datasheet), str(s_nominal_age))
        if reset:
            FileUtils.remove_path(output_directory)
        results_file_name ='datasheet_workflow_results.json'
        params_file_name ='datasheet_local_fit_params.json'
        metadata_file_name ='metadata.json'
        pdf_path = Path(EXPORT_PATH, str(projectId), str(s_datasheet),'results', f'{s_datasheet}_datasheet.pdf')
        
        results_file_path = os.path.join(output_directory, results_file_name)
        params_file_path = os.path.join(output_directory, params_file_name)
        metadata_file_path = os.path.join(EXPORT_PATH, str(projectId), str(s_datasheet), metadata_file_name)
        if os.path.exists(results_file_path):
            json_data = read_json(projectId,s_datasheet,s_nominal_age,results_file_name)
            datasheet_detail = json.loads(json_data) 
            if os.path.exists(params_file_path):
                params_data = read_json(projectId,s_datasheet,s_nominal_age,params_file_name)
                params_d = json.loads(params_data) 
                datasheet_detail['hss_weights_object'] = params_d['model_weights']
                # datasheet_detail['hss_complete_params'] = params_d['model_params']
                datasheet_detail['new_fit_params'] = {
                    'excluded_tensile':params_d['excluded_tensile'],
                    'excluded_bulge':params_d['excluded_bulge'],
                    'gradients':params_d['gradients'],
                    'recompute':params_d['recompute'],
                    'bulgeExcludedData':params_d['bulgeExcludedData'],
                    'tensileExcludedData': params_d['tensileExcludedData'],
                    'hss_weights_object':params_d['model_weights'],
                    'hss_complete_params':params_d['model_params']
                    }
                
                if 'initial_fit_params' not in datasheet_detail or not datasheet_detail['initial_fit_params']:
                    datasheet_detail['initial_fit_params'] = datasheet_detail['new_fit_params']
            if not isinstance(datasheet_detail['corrected_tensile_results'], str):
                serializable_corrected_tensile = json.dumps(datasheet_detail['corrected_tensile_results'])
                datasheet_detail['corrected_tensile_results']= serializable_corrected_tensile
            if os.path.exists(pdf_path):
                datasheet_detail['preview'] = True
                datasheet_detail['pdf_path'] = os.path.join(EXPORT_PATH, str(projectId), str(s_datasheet),'results', f'{s_datasheet}_internal_datasheet.pdf')
                # str(Path(EXPORT_PATH, str(s_datasheet),'results', f'{s_datasheet}_internal_datasheet.pdf'))
            else:
                datasheet_detail['preview'] = False
                datasheet_detail['pdf_path']='none'

            if os.path.exists(metadata_file_path):
                metadata = read_metadata(projectId,s_datasheet,metadata_file_name)
                datasheet_detail['metadata'] = metadata
            return datasheet_detail
        else:
            metadata = {}
            m_weights = (5.0, 1.0, 1, 0.005)
            if os.path.exists(metadata_file_path):
                metadata = read_metadata(projectId,s_datasheet,metadata_file_name)
                metadata = metadata

            selected_nominal_age = s_nominal_age
            selected_datasheet = s_datasheet
            s_min = 20.00
            s_max = 60.00
            selected_sample = ''

            # datasheetpath = os.path.join(DIR_PATH,str(selected_datasheet)) 
            datasheetpath = os.path.join(DIR_PATH, str(projectId),str(selected_datasheet)) 
            files_to_import = get_all_file_paths(datasheetpath)
            # Tensile #
            tensile_paths = parse_tensile_paths(files_to_import)
            if not tensile_paths:
                raise Exception("Tensile data is not present. Please add the Tensile data.")
            extracted_ts_tests=[]
            ts_tests=[]
            for sample_path, result_path in tensile_paths:
                ts_test = extract_tensile((sample_path, result_path))
                ts_tests.append(transform_tensile(ts_test))
 
            ts_tests = handle_failed_tensile(tensile_paths, ts_tests)

            # Bulge #
            bulge_paths = parse_bulge_paths(files_to_import)
            if not bulge_paths:
                raise Exception("Bulge data is not present. Please add the bulge data.")
                    
            bg_tests =[]
            for b_path in bulge_paths:
                if b_path.suffix == '.txt':
                    bg_tests.append(extract_bulge(b_path))
#-----------------using filtered test data----------------
            bg_tests = handle_failed_imports(bulge_paths, bg_tests)


            # FLC #
            flc_raw_paths = parse_flc_raw_paths(files_to_import)
            flc_raw =[]
            for flc_path in flc_raw_paths:
                flc_r = extract_flc_raw(flc_path)
                flc_raw.append(transform_flc_raw(flc_r))
            flc_raw_filtered = handle_failed_imports(flc_raw_paths, flc_raw)
        

            flc_fit_paths = parse_flc_fit_paths(files_to_import)
            flc_fit =[]
            for flc_fit_path in flc_fit_paths:
                flc_fit_file = extract_flc_fit(flc_fit_path)
                flc_fit.append(transform_flc_fit(flc_fit_file))

            # dict_params_fit = {'datasheet': [ 888, 888, 888, ], 'nominal_age': [30, 90, 180]}
            datasheet = selected_datasheet
            nominal_age = selected_nominal_age
            
            # Tensile data graph #
            t_data=[]
            
            for test in ts_tests:
                if test.nominal_age == selected_nominal_age:
                    for e,s in zip (test.data.e, test.data.s):    
                        t_data.append({'file_name':test.file_name.name, 'e':e, 's':s })

            df_ten_data =pd.DataFrame(t_data)
            df_ten_data.rename(columns={
                    'e': 'xdata',
                    's': 'ydata',
                },
                inplace=True,
            )
            
            all_ten_samples = list(df_ten_data['file_name'].unique())
            all_ten_samples.sort() 
            # df_data

            included_samples = all_ten_samples
            # tensile_plot=_plot_included_files(df_ten_data, all_ten_samples, included_samples)
            tensile_plot= df_ten_data
            # Bulge Data graph #
            t_data=[]
            for test in bg_tests:
                if test.nominal_age == selected_nominal_age:
                    for eps1,sig1 in zip (test.data.eps_1, test.data.sig_1):      
                        t_data.append({'file_name':test.file_name, 'eps_1':eps1, 'sig_1':sig1 })
            df_bul_data =pd.DataFrame(t_data)

            df_bul_data.rename(columns={
                    'eps_1': 'xdata',
                    'sig_1': 'ydata',
                },
                inplace=True,
            )
            if 'file_name' not in df_bul_data.columns:
                raise FileNotFoundError("The 'file_name' column is not present in the Bulge data. Please update the bulge data.")
            all_bul_samples = list(df_bul_data['file_name'].unique())
            all_bul_samples.sort()
            included_samples = all_bul_samples
            # bulge_plot=_plot_included_files(df_bul_data, all_bul_samples, included_samples)
            bulge_plot= df_bul_data

            # Combined results #

            combined_results_list=[]
            tensile_combined_results_list=[]
            combined_results_list_initial=[]

            for test in ts_tests:
                if str(test.nominal_age) == str(selected_nominal_age):
                    tensile_combined_results_list.append(combine_results(test))
                if str(test.nominal_age) == str(selected_nominal_age) and "_0" in  test.file_name.name:
                    combined_results_list.append(combine_results(test))
        
            selected_sample = all_ten_samples[0]
            corrected_params = {}
            recompute_Rp02 = False
            df_tensile_computed = correct_tensile(projectId, selected_sample,s_min,s_max,df_ten_data,combined_results_list,combined_results_list_initial,recompute_Rp02,corrected_params)
            
            corrected_tensile_results = df_tensile_computed
            

        # Model Fittings #
            # tensile fitting
            # Extract E, RP02, Rm, Ag, and Agt values from combined_results_list
            E_values = [result['E'] for result in combined_results_list]
            RP02_values = [result['Rp02'] for result in combined_results_list]
            Rm_values = [result['Rm'] for result in combined_results_list]
            Ag_values = [result['Ag'] for result in combined_results_list]
            Agt_values = [result.get('Agt', 0) for result in combined_results_list]  # Default value 0 if 'Agt' is not present

            # Calculate average values
            avg_mech = (
                sum(E_values) / len(E_values),
                sum(RP02_values) / len(RP02_values),
                sum(Rm_values) / len(Rm_values),
                sum(Ag_values) / len(Ag_values),
                sum(Agt_values) / len(Agt_values)
            )

            sig_list=[]
            eps_pl_list=[]
            all_eps_pl =[]
            all_sig =[]
            eps_range_fitting = get_fitting_strain_range(avg_mech)
            eps_min, eps_max_fitting = eps_range_fitting

            #bulge fitting 

            eps_sc=[]
            sig_sc=[]
            all_eps_sc=[]
            all_sig_sc=[]
            all_file_name=[]
            bg_tests
            E, Rp02, Rm, Ag, Agt = avg_mech
            list_excluded_bulge=[]
            # k_mean, scale_factor_bulge = calculate_k_mean(selected_nominal_age, bg_tests, avg_mech, list_excluded_bulge)
            try:
                k_mean, scale_factor_bulge = calculate_k_mean(selected_nominal_age, bg_tests, avg_mech, list_excluded_bulge)
            except Exception as e:
                logging.error(f"Error calculating bulge_scale_factor: {str(e)}")
                k_mean, scale_factor_bulge = 1.0, []
            bulge_scale_factor = {"k_mean": k_mean, "scale_factor_bulge":scale_factor_bulge}
            for test in bg_tests:
                if test.nominal_age == selected_nominal_age:
                    eps_sc_l,sig_sc_l, file_name = get_bulge_fitting_data(test,eps_min,k_mean)
                    all_eps_sc.append(eps_sc_l)
                    all_sig_sc.append(sig_sc_l)
            eps_sc = np.concatenate(all_eps_sc)
            sig_sc = np.concatenate(all_sig_sc)
            data_bulge = list(zip(eps_sc, sig_sc))
            eps_max = np.max(eps_sc)
            eps_range = [eps_min,eps_max]
            
            #tensile fitting
            for test in ts_tests:
                
                filename = test.file_name.name
                if test.nominal_age == selected_nominal_age and "_0" in filename:
                    eps_pl, sig, file_name = get_tensile_fitting_data(test,eps_min,eps_max_fitting)
                    all_eps_pl.append(eps_pl)
                    all_sig.append(sig)
                    all_file_name.append(file_name)

            eps_pl_list = np.concatenate(all_eps_pl)
            sig_list = np.concatenate(all_sig)
            data_tensile = list(zip(eps_pl_list, sig_list))
            # voce model fitting 
            model_name = 'voce'
            voce_weights = m_weights
            voce_init_params_dict = get_voce_params_dict(avg_mech,selected_datasheet,selected_nominal_age)
            voce_lmfit_params = get_lmfit_params_from_dict(voce_init_params_dict)
        
            voce_out_params =fit_model_parameters(model_name, voce_lmfit_params, voce_weights, data_tensile, data_bulge, eps_range_fitting)
            voce_complete_params = merge_params(voce_init_params_dict, voce_out_params)
            dict_params_to_insert = {}
            dict_params_to_insert = add_params_to_insert(
                dict_params_to_insert,
                selected_datasheet,
                selected_nominal_age,
                model_name,
                voce_complete_params,
            )

            # swift

            model_name = 'swift'
            # Get model weights
            swift_weights = m_weights
            # Get lmfit parameters
            swift_init_params_dict = get_swift_params_dict(avg_mech, datasheet, nominal_age)
            swift_lmfit_params = get_lmfit_params_from_dict(swift_init_params_dict)
            # Fit model parameters
            swift_out_params = fit_model_parameters(
                                model_name,
                                swift_lmfit_params,
                                swift_weights,
                                data_tensile,
                                data_bulge,
                                eps_range_fitting
                        )
            swift_complete_params = merge_params(swift_init_params_dict, swift_out_params)
            dict_params_to_insert = add_params_to_insert(
                dict_params_to_insert,
                selected_datasheet,
                selected_nominal_age,
                model_name,
                swift_complete_params,
            )

            # hocket Sherby

            model_name = 'hocket_sherby'
            # Get model weights
            hs_weights = m_weights
            # Get lmfit parameters
            hs_init_params_dict = get_hocket_sherby_params_dict(voce_out_params, datasheet, nominal_age)
            hs_lmfit_params = get_lmfit_params_from_dict(hs_init_params_dict)
            # hs_lmfit_params = get_hocket_sherby_lmfit_params.map(voce_out_params)
            # Fit model parameters
            hs_out_params = fit_model_parameters(
                                model_name,
                                hs_lmfit_params,
                                hs_weights,
                                data_tensile,
                                data_bulge,
                                eps_range_fitting
                        )
            hs_complete_params = merge_params(hs_init_params_dict, hs_out_params)
            dict_params_to_insert = add_params_to_insert(
                dict_params_to_insert,
                selected_datasheet,
                selected_nominal_age,
                model_name,
                hs_complete_params
                )
            
            # Hocket Sherby Swift

            model_name = 'hocket_sherby_swift'
            # Get model weights
            hss_weights = m_weights
            # Get lmfit parameters
            hss_init_params_dict = get_hocket_sherby_swift_params_dict(hs_out_params, swift_out_params, datasheet, nominal_age)
            hss_lmfit_params = get_lmfit_params_from_dict(hss_init_params_dict)
            # hss_lmfit_params = get_hocket_sherby_swift_lmfit_params.map(hs_out_params, swift_out_params)
            # Fit model parameters
            hss_out_params = fit_model_parameters(
                model_name,
                hss_lmfit_params,
                hss_weights,
                data_tensile,
                data_bulge,
                eps_range_fitting
            )
            hss_complete_params = merge_params(hss_init_params_dict, hss_out_params)
            dict_params_to_insert = add_params_to_insert(
                dict_params_to_insert,
                selected_datasheet,
                selected_nominal_age,
                model_name,
                hss_complete_params,
            )
            tensile_plot.rename(columns={
                    'e': 'xdata',
                    's': 'ydata',
                },
                inplace=True,
            )
            
            hss_weights_object = {
                'tensile_weight': hss_weights[0],
                'bulge_weight': hss_weights[1],
                'scaled_residue': hss_weights[2],
                'considere_weight': hss_weights[3]
            }

            ##################fit graph
            # min_value = np.min(eps_pl_list)
            # max_value = np.max(eps_pl_list)
            # x_range_tensile = np.array([min_value, max_value])
            
            # b_min_value = np.min(eps_sc)
            # b_max_value = np.max(eps_sc)
            # x_range_bulge = np.array([b_min_value, b_max_value])

            
            # # x_range_bulge = data_bulge['eps_sc'].describe()[['min', 'max']].values
            # x_range = [min(x_range_tensile[0], x_range_bulge[0]), max(x_range_tensile[1], x_range_bulge[1])]
            # x_model = np.linspace(*x_range, num=200)
            
            # df_model_params = get_model_parameters(dict_params_to_insert,int(selected_datasheet), int(selected_nominal_age))
            # df_model_params = df_model_params.to_dict(orient='records')[0]
            # model_name = 'hocket_sherby_swift'
            # df_model_current = get_model_and_grad_plot_data(x_model, model_name, df_model_params)
            # smoothing_windows = {}
            # # Update smoothing_windows dictionary with the new values
            # smoothing_windows['diff_window_side_grad_tensile'] = 15
            # smoothing_windows['diff_window_side_grad_bulge'] = 10
            # smoothing_windows["diff_window_side_n_tensile"] = 15
            # smoothing_windows["diff_window_side_n_bulge"] = 10

            # E, Rp02, Rm, Ag, Agt = avg_mech
            # avg_mech2 = {'E':E, 'Rp02':Rp02, 'Rm':Rm, 'Ag':Ag, 'Agt':Agt}
            # # df_tensile_plot, df_bulge_plot = add_measurements_nvalues(df_tensile_computed, df_bulge_plot, smoothing_windows)
            # df_nvalues = compile_nvalues_df(pd.DataFrame(combined_results_list), avg_mech2)

            # df_models = pd.DataFrame(
            # {
            #     'x_model': x_model,
            #     'm_current': df_model_current['mdata'],
            #     'm_grad_current': df_model_current['m_grad_data'],
            #     'n_value_current': df_model_current['n_value'],
            # })
            
            
            # (eps_pl_02, sig_02), (eps_pl_ag, sig_ag) = get_rp_rm_plot_points(**avg_mech2)
            # eps_sig_pl_02 = (eps_pl_02, sig_02)
            # eps_sig_pl_ag = (eps_pl_ag, sig_ag)
            # df_models = json.loads(df_models.to_json(orient='records'))
            # df_nvalues = json.loads(df_nvalues.to_json(orient='index'))
            # curr_fit_graph = {
            #     'df_models':df_models,
            #     'eps_sig_pl_02': eps_sig_pl_02,
            #     'eps_sig_pl_ag': eps_sig_pl_ag,
            #     'df_nvalues':df_nvalues,
            #     'df_results':combined_results_list
            # }
            
            tensile_plot_data_path = create_csv(projectId, tensile_plot,selected_datasheet,selected_nominal_age, 'tensile_plot_data.csv')
            bulge_plot_data_path = create_csv(projectId, bulge_plot,selected_datasheet, selected_nominal_age,'bulge_plot_data.csv')
            dict_params_to_insert_str_keys = {str(key): value for key, value in dict_params_to_insert.items()}
            mech_data_params = {'avg_mech':avg_mech, 'eps_range':eps_range, 'eps_range_fitting':eps_range_fitting}
            mech_data_params_path = create_json(projectId, mech_data_params,selected_datasheet, selected_nominal_age,'mech_data_params.json')
            model_dict_params_path = create_json(projectId, dict_params_to_insert_str_keys,selected_datasheet, selected_nominal_age,'model_dict_params.json')

            pdf_tensile_computed_results_path = create_csv(projectId, pd.DataFrame(tensile_combined_results_list),selected_datasheet, selected_nominal_age,'pdf_tensile_combined_results_list.csv')
            tensile_computed_results_path = create_csv(projectId, pd.DataFrame(combined_results_list),selected_datasheet, selected_nominal_age,'tensile_combined_results_list.csv')
            initial_tensile_computed_results_path = create_csv(projectId, pd.DataFrame(combined_results_list),selected_datasheet, selected_nominal_age,'initial_tensile_combined_results_list.csv')
            ts_test_data_path = create_pkl(projectId, ts_tests, selected_datasheet, selected_nominal_age, 'ts_tests_data.pkl')
            ts_bulge_data_path =create_pkl(projectId, bg_tests, selected_datasheet, selected_nominal_age, 'ts_bulge_data.pkl')
            flc_raw_data_path = create_pkl(projectId, flc_raw, selected_datasheet, selected_nominal_age,'flc_raw_data.pkl')
            flc_fit_data_path = create_pkl(projectId, flc_fit, selected_datasheet, selected_nominal_age,'flc_fit_data.pkl')
            serializable_corrected_tensile = json.dumps(corrected_tensile_results)
            datasheet_detail = dict(
                
            tensile_files = all_ten_samples,
            tensile_sample_data= pdf_tensile_computed_results_path,
            tensile_combined_data= tensile_computed_results_path,
            tensile_plot_data_path = tensile_plot_data_path,
            bulge_files =  all_bul_samples,
            bulge_plot_data_path = bulge_plot_data_path,
            hss_complete_params = hss_complete_params,
            # corrected_tensile_results = corrected_tensile_results,
            corrected_tensile_results = serializable_corrected_tensile,
            bulge_scale_factor = bulge_scale_factor,
            hss_weights_object = hss_weights_object,
            initial_fit_params ={},
            new_fit_params = {},
            metadata = metadata
            )
            
            datasheet_detail_save = dict(
                
            tensile_files = all_ten_samples,
            tensile_sample_data= pdf_tensile_computed_results_path,
            tensile_combined_data= tensile_computed_results_path,
            tensile_plot_data_path = tensile_plot_data_path,
            bulge_files =  all_bul_samples,
            bulge_plot_data_path = bulge_plot_data_path,
            hss_complete_params = hss_complete_params,
            # corrected_tensile_results = corrected_tensile_results,
            corrected_tensile_results = corrected_tensile_results,
            bulge_scale_factor = bulge_scale_factor,
            hss_weights_object = hss_weights_object,
            initial_fit_params ={},
            new_fit_params = {},
            metadata = metadata
            )
            json_datasheet_detail = json.dumps(datasheet_detail_save, indent=4)
            datasheet_workflow_results = create_json(projectId, json_datasheet_detail,selected_datasheet, selected_nominal_age,'datasheet_workflow_results.json')
            return datasheet_detail
            
    except Exception as e:
        raise Exception(f"Datasheet computation failed: {str(e)}")
    
def set_initial_fit(project_id, datasheet, nominal_age, new_fit_params):
    try:
        
        
        output_directory = os.path.join(EXPORT_PATH, str(project_id), str(datasheet), str(nominal_age))
        
        model_name = 'hocket_sherby_swift'

        com_df_data = read_csv(project_id, datasheet, nominal_age , 'tensile_combined_results_list.csv')
        data_str_keys = read_json(project_id, datasheet, nominal_age , 'model_dict_params.json')
        dict_params_to_insert = {eval(key): value for key, value in data_str_keys.items()}

        results_file_name ='datasheet_workflow_results.json'
        params_file_name ='datasheet_local_fit_params.json'
        metadata_file_name ='metadata.json'
        
        results_file_path = os.path.join(output_directory, results_file_name)
        params_file_path = os.path.join(output_directory, params_file_name)
        metadata_file_path = os.path.join(EXPORT_PATH, str(project_id), str(datasheet), metadata_file_name)
        if os.path.exists(results_file_path):
            json_data = read_json(project_id,datasheet,nominal_age,results_file_name)
            datasheet_detail = json.loads(json_data) 
            if os.path.exists(params_file_path):
                params_data = read_json(project_id,datasheet,nominal_age,params_file_name)
                params_d = json.loads(params_data) 
                datasheet_detail['hss_weights_object'] = params_d['model_weights']
                datasheet_detail['hss_complete_params'] = params_d['model_params']
                datasheet_detail['initial_fit_params'] = {
                    'excluded_tensile':params_d['excluded_tensile'],
                    'excluded_bulge':params_d['excluded_bulge'],
                    'gradients':params_d['gradients'],
                    'recompute':params_d['recompute'],
                    'bulgeExcludedData':params_d['bulgeExcludedData'],
                    'tensileExcludedData': params_d['tensileExcludedData'],
                    'hss_weights_object':params_d['model_weights'],
                    'hss_complete_params':params_d['model_params']
                    
                    }
                model_params =  params_d['model_params']
                for key, value in model_params.items():
                    value["param_value"] = new_fit_params.get(key, value.get("param_value"))

                dict_params_to_insert = add_params_to_insert(
                    dict_params_to_insert,
                    int(datasheet),
                    int(nominal_age),
                    model_name,
                    model_params,
                )
        dict_params_to_insert_str_keys = {str(key): value for key, value in dict_params_to_insert.items()}
        model_dict_params_path = create_json(project_id, dict_params_to_insert_str_keys , datasheet, nominal_age,'model_dict_params.json')

        tensile_computed_results_path = create_csv(project_id, com_df_data, datasheet, nominal_age,'initial_tensile_combined_results_list.csv')           
        file_name ='datasheet_local_fit_results.json'
        output_directory = os.path.join(EXPORT_PATH, str(project_id), str(datasheet), str(nominal_age))
        json_file_path = os.path.join(output_directory, file_name)
        os.remove(json_file_path)
        json_datasheet_detail = json.dumps(datasheet_detail, indent=4)
        datasheet_workflow_results = create_json(project_id, json_datasheet_detail,datasheet, nominal_age,'datasheet_workflow_results.json')
        datasheet_detail['corrected_tensile_results'] = json.dumps(datasheet_detail['corrected_tensile_results'])
        return datasheet_detail
    except Exception as e:
        raise Exception(f"Setting initial fit failed: {str(e)}")
    