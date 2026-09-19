from pathlib import Path
import json
import os
import pickle
import traceback
import pandas as pd
import numpy as np
import datetime as dt
from fpdf import FPDF
from typing import Tuple
from copy import deepcopy
import lmfit
from lmfit import Parameters
from typing import Callable, Tuple
from autograd import elementwise_grad
import logging
import matplotlib.pyplot as plt
from app.services.apps.datasheet_gen.dsgen_controller.fitting import models, objectives
from app.services.apps.datasheet_gen.dsgen_controller.export_datasheet import *
from app.services.apps.datasheet_gen.dsgen_controller.fitting.objectives import _obj_ls_considere, _obj_ls_considere_local_fit
from app.services.apps.datasheet_gen.dsgen_controller.datasheet_workflow import calculate_k_mean, get_tensile_fitting_data, get_bulge_fitting_data, get_tensile_eps_range, get_lmfit_params_dict,create_csv,create_json
from app.services.apps.datasheet_gen.dsgen_controller.utils.mech_properties import compute_df_tensile_values, compute_elastic_modulus, compute_poisson_ratio, compute_Rp02, compute_bulge_scaling_factor
from app.services.apps.datasheet_gen.dsgen_controller.utils.model_fitting import get_lmfit_params_dict, get_tensile_eps_range, get_rp_rm_plot_points
logging.getLogger('matplotlib').setLevel(logging.WARNING)

def compute_scaled_bulge(df_bulge, df_results):

    E = df_results['E'].mean()
    Rm = df_results['Rm'].mean()
    Ag = df_results['Ag'].mean()

    df_bulge_scaled = df_bulge.copy()
    bulge_samples = df_bulge_scaled['file_name'].unique()

    ks = []
    # Compute scaling factor for each sample individually
    for bulge_sample in bulge_samples:
        sample_idx = (df_bulge['file_name'] == bulge_sample)
        k = compute_bulge_scaling_factor(
            E, Rm, Ag,
            df_bulge.loc[sample_idx, 'sig_1'],
            df_bulge.loc[sample_idx, 'eps_1']
        )
        # Append k to list if it's not null
        if not np.isnan(k):
            ks.append(k)

    k_mean = np.mean(ks)
    df_bulge_scaled.loc[:, 'eps_sc'] = df_bulge_scaled['eps_1'] / k_mean
    df_bulge_scaled.loc[:, 'sig_sc'] = df_bulge_scaled['sig_1'] * k_mean

    return df_bulge_scaled

def _fit_model_to_data(model_name, model_weights, df_params, data_tensile, data_bulge, eps_range):

    eps_pl_02, eps_pl_ag = eps_range
    # Compile tensile fitting data
    # tensile_eps_idx = (df_tensile['eps_pl'] > eps_pl_02) & (df_tensile['eps_pl'] < eps_pl_ag)
    # np_tensile = df_tensile.loc[tensile_eps_idx, ['eps_pl', 'sig']].to_numpy()
    np_tensile = np.array(data_tensile)
    np_bulge = np.array(data_bulge)
    # np_bulge= df_bulge.loc[bulge_eps_idx, ['eps_sc', 'sig_sc']].to_numpy()

    # Compile bulge fitting data
    # bulge_eps_idx = (df_bulge['eps_sc'] > eps_pl_ag)
    # np_bulge = df_bulge.loc[bulge_eps_idx, ['eps_sc', 'sig_sc']].to_numpy()

    # eps_pl_02, eps_pl_ag = eps_range

    lmfit_params = lmfit.Parameters()

    for i_param in df_params.columns:
        i_value = df_params.loc['param_init', i_param]
        i_min = df_params.loc['param_min', i_param]
        i_max = df_params.loc['param_max', i_param]
        i_var = df_params.loc['param_variable', i_param]

        lmfit_params.add(i_param, value=i_value, min=i_min, max=i_max, vary=i_var)

    #########################################################################
    # TODO: REWRITE THIS PART TO USE fit_model_parameters FROM fitting_flow #
    #########################################################################

    model = getattr(models, model_name)
    model_grad = elementwise_grad(model)

    tensile_weight = model_weights['tensile_weight']
    bulge_weight = model_weights['bulge_weight']
    # if model_weights['scaled_residue']:

    tensile_weight /= int(np.sqrt(np_tensile.shape[0]))
    bulge_weight /= int(np.sqrt(np_bulge.shape[0]))
    considere_weight = model_weights['considere_weight']

    weights = [tensile_weight, bulge_weight, considere_weight]
    # return model_out_params
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
            # st.warning(f"Could not fit {model_name} with {fit_methods[method_idx]}")
            if method_idx < len(fit_methods) - 1:
                method_idx += 1
            else:
                raise e
    model_out_params = get_lmfit_params_dict(out.params)

    return model_out_params


def _get_model_objective_error(df_tensile, df_bulge, model, model_grad, m_params, model_weights, eps_range):
    """
    Calculates the total error and sub-errors (tensile, bulge, Considère).
    """
    eps_pl_02, eps_pl_ag = eps_range

    # Compile tensile fitting data
    np_tensile = df_tensile[['file_name', 'eps_pl', 'sig']].to_numpy()
    
    # Compile bulge fitting data
    np_bulge = df_bulge[['file_name', 'eps_sc', 'sig_sc']].to_numpy()

    # Extract model weights
    tensile_weight = model_weights['tensile_weight']
    bulge_weight = model_weights['bulge_weight']
    considere_weight = model_weights['considere_weight']

    # Calculate sub-errors
    m_res = _obj_ls_considere_local_fit(
        m_params, model, model_grad, eps_pl_ag, [tensile_weight, bulge_weight, considere_weight], df_tensile, df_bulge
    )
    tensile_error = m_res[0]
    bulge_error = m_res[1]
    considere_error = m_res[2]

    # Calculate total weighted error
    weights = [tensile_weight, bulge_weight, considere_weight]
    total_error = np.sum([weights[0] * tensile_error, weights[1] * bulge_error, weights[2] * considere_error]) / np.sum(weights)

    # Return total and sub-errors as a dictionary
    return {
        "total_error": total_error,
        "tensile_error": (weights[0] * tensile_error)/ np.sum(weights),
        "bulge_error": (weights[1] * bulge_error)/ np.sum(weights),
        "considere_error": (weights[2] * considere_error) / np.sum(weights)
    }

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

def _get_rolling_window_lr_slope(x_series, y_series, window_side):

    # Emulate excel behaviour. window_side is the number of points on each side
    # From the point that is being investigated
    window_size = int(2 * window_side + 1)

    x_windows = [*x_series.rolling(window_size, center=True, min_periods=window_size)]
    y_windows = [*y_series.rolling(window_size, center=True, min_periods=window_size)]

    # Trim to only full-size windows
    x_windows = x_windows[window_size//2:-window_size//2]
    y_windows = y_windows[window_size//2:-window_size//2]

    sm_data = []
    sm_index = []
    for x_win, y_win in zip(x_windows, y_windows):
        x_data = x_win.values
        y_data = y_win.values

        p = np.polynomial.Polynomial.fit(x_data, y_data, 1)
        p_coef = p.convert().coef

        # Add the slope to results
        sm_data.append(p_coef[-1])

        # Add the current index to list
        sm_index.append(x_win.index[window_side])

    series_data = pd.Series(data=sm_data, index=sm_index)

    return series_data

def add_measurements_nvalues(df_tensile_plot, df_bulge_plot, smoothing_windows):

    df_tensile_local = df_tensile_plot.copy()
    df_bulge_local = df_bulge_plot.copy()

    diff_window_side_grad_tensile = smoothing_windows['diff_window_side_grad_tensile']
    diff_window_side_grad_bulge = smoothing_windows["diff_window_side_grad_bulge"]
    diff_window_side_n_tensile = smoothing_windows["diff_window_side_n_tensile"]
    diff_window_side_n_bulge = smoothing_windows["diff_window_side_n_bulge"]

    # Compute n-value stuff for the measurements
    for spl in df_tensile_local['file_name'].unique():
        idx_spl = (df_tensile_local['file_name'] == spl)

        eps = df_tensile_local.loc[idx_spl, 'eps_pl']
        sig = df_tensile_local.loc[idx_spl, 'sig']
        n_value = (sig.diff()/eps.diff()) * (eps/sig)
        df_tensile_local.loc[idx_spl, 'n_value'] = n_value

        # Rolling window smoothed stress/strain gradient
        dsig_deps_smooth = _get_rolling_window_lr_slope(eps, sig, diff_window_side_grad_tensile)
        df_tensile_local.loc[idx_spl, 'grad_smoothed'] = dsig_deps_smooth

        # Rolling window smoothed n-values
        dsig_deps_smooth = _get_rolling_window_lr_slope(eps, sig, diff_window_side_n_tensile)
        n_value_smoothed = dsig_deps_smooth * (eps/sig)
        df_tensile_local.loc[idx_spl, 'n_value_smoothed'] = n_value_smoothed

    for spl in df_bulge_local['file_name'].unique():
        idx_spl = (df_bulge_local['file_name'] == spl)

        eps = df_bulge_local.loc[idx_spl, 'eps_sc']
        sig = df_bulge_local.loc[idx_spl, 'sig_sc']
        n_value = (sig.diff()/eps.diff()) * (eps/sig)
        df_bulge_local.loc[idx_spl, 'n_value'] = n_value

        # Rolling window smoothed stress/strain gradient
        dsig_deps_smooth = _get_rolling_window_lr_slope(eps, sig, diff_window_side_grad_bulge)
        df_bulge_local.loc[idx_spl, 'grad_smoothed'] = dsig_deps_smooth

        # Rolling window smoothed
        dsig_deps_smooth = _get_rolling_window_lr_slope(eps, sig, diff_window_side_n_bulge)
        n_value_smoothed = dsig_deps_smooth * (eps/sig)
        df_bulge_local.loc[idx_spl, 'n_value_smoothed'] = n_value_smoothed

    return df_tensile_local, df_bulge_local

def compile_nvalues_df(df_results, avg_mech):

    n_vals_regex = r"n(\d+)_(\d+)"
    n_cols =  df_results.columns[df_results.columns.str.match(n_vals_regex, na=False)]
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

def get_model_and_measures_plot_data(dict_model, smoothing_windows, model_name):

    model = getattr(models, model_name)
    model_grad = elementwise_grad(model)

    df_tensile = dict_model['df_tensile']
    # df_tensile = df_tens[df_tens['file_name'].str.contains("_0")]
    df_bulge = dict_model['df_bulge']
    df_results = dict_model['df_results']
    df_model_params = dict_model['df_model_params']
    m_params_current = df_model_params.loc['current fit', :].to_dict()
    m_params_new = df_model_params.loc['new local fit', :].to_dict()
    m_err_current = dict_model['m_err_current']
    m_err_new = dict_model['m_err_new']

    # Get the fitting/plotting eps range
    avg_mech = df_results[['E', 'Rp02', 'Rm', 'Ag', 'Agt']].mean().to_dict()
    eps_range = get_tensile_eps_range(**avg_mech)
    eps_pl_02, eps_pl_ag = eps_range
    # Get tensile/bulge indexes for data which is in the fitting range (eps_range)
    tensile_eps_plot_idx = (df_tensile['eps_pl'] >= eps_pl_02) & (df_tensile['eps_pl'] <= eps_pl_ag)
    bulge_eps_plot_idx = (df_bulge['eps_sc'] >= eps_pl_02)

    df_tensile_plot = df_tensile.loc[tensile_eps_plot_idx, ['file_name', 'eps_pl', 'sig']]
    df_bulge_plot = df_bulge.loc[bulge_eps_plot_idx, ['file_name', 'eps_sc', 'sig_sc']]

    # Compute x_range for the model as the union of tensile and bulge sample ranges
    x_range_tensile = df_tensile_plot['eps_pl'].describe()[['min', 'max']].values
    x_range_bulge = df_bulge_plot['eps_sc'].describe()[['min', 'max']].values
    x_range = [min(x_range_tensile[0], x_range_bulge[0]), max(x_range_tensile[1], x_range_bulge[1])]
    x_model = np.linspace(*x_range, num=200)

    df_model_current = get_model_and_grad_plot_data(x_model, model_name, m_params_current)
    df_model_new = get_model_and_grad_plot_data(x_model, model_name, m_params_new)

    df_models = pd.DataFrame(
        {
            'x_model': x_model,
            'm_current': df_model_current['mdata'],
            'm_grad_current': df_model_current['m_grad_data'],
            'n_value_current': df_model_current['n_value'],
            'm_new': df_model_new['mdata'],
            'm_grad_new': df_model_new['m_grad_data'],
            'n_value_new': df_model_new['n_value'],
        }
    )
    # Add n-value plot data for tensile/bulge measurements
    df_tensile_plot, df_bulge_plot = add_measurements_nvalues(df_tensile_plot, df_bulge_plot, smoothing_windows)

    # Get coords of Rp02 and Rm points
    (eps_pl_02, sig_02), (eps_pl_ag, sig_ag) = get_rp_rm_plot_points(**avg_mech)

    # Transform n-value measurements
    df_nvalues = compile_nvalues_df(df_results, avg_mech)

    # Combine all df's in one dictionary
    dict_data = {
        # Fitting data
        'df_tensile_plot': df_tensile_plot,
        'df_bulge_plot': df_bulge_plot,
        'df_results': df_results,
        # Fitted models info
        'df_models': df_models,
        'df_model_params': df_model_params,
        'm_err_current': m_err_current,
        'm_err_new': m_err_new,
        'eps_sig_pl_02': (eps_pl_02, sig_02),
        'eps_sig_pl_ag': (eps_pl_ag, sig_ag),
        'df_nvalues': df_nvalues,

    }

    return dict_data

def calculate_local_fit(adjusted_params):
    try:
        project_id = adjusted_params.project_id
        selected_datasheet = adjusted_params.datasheet
        selected_nominal_age = adjusted_params.nominal_age
        file_name ='datasheet_local_fit_results.json'
        output_directory = os.path.join(EXPORT_PATH, str(project_id), str(selected_datasheet), str(selected_nominal_age))
        json_file_path = os.path.join(output_directory, file_name)
        m_err_current = None 
        initial_fit_errors = None
        new_fit_errors = None
        if os.path.exists(json_file_path): 
            json_data = read_json(project_id,selected_datasheet,selected_nominal_age,file_name)
            dict_data = json.loads(json_data) 
            m_err_current = dict_data['m_err_current']
            initial_fit_errors = dict_data['initial_fit_errors']
        if os.path.exists(json_file_path) and not adjusted_params.params['recompute']:
            return dict_data
        else: 
            model_name = 'hocket_sherby_swift'
            list_excluded_tensile = adjusted_params.params["excluded_tensile"]
            list_excluded_bulge = adjusted_params.params["excluded_bulge"]
            model_params = adjusted_params.params["model_params"]
            gradients= adjusted_params.params["gradients"]
            model_weights_param =  adjusted_params.params["model_weights"]
            for param in model_params.values():
                if "param_value" in param:
                    del param["param_value"]
            df_model_params_new = df = pd.DataFrame(model_params)
            com_df_data = read_csv(project_id, selected_datasheet, selected_nominal_age , 'tensile_combined_results_list.csv')
            com_df_yield_data = read_csv(project_id, selected_datasheet, selected_nominal_age , 'pdf_tensile_combined_results_list.csv')
            data_str_keys = read_json(project_id, selected_datasheet, selected_nominal_age , 'model_dict_params.json')
            dict_params_to_insert = {eval(key): value for key, value in data_str_keys.items()}

            df_bul_data = read_csv(project_id, selected_datasheet, selected_nominal_age , 'bulge_plot_data.csv')
            df_ten_data = read_csv(project_id, selected_datasheet, selected_nominal_age , 'tensile_plot_data.csv')
            mech_data_params = read_json(project_id, selected_datasheet, selected_nominal_age , 'mech_data_params.json')
            ts_tests = read_pkl(project_id, selected_datasheet, selected_nominal_age , 'ts_tests_data.pkl')
            bg_tests = read_pkl(project_id, selected_datasheet, selected_nominal_age , 'ts_bulge_data.pkl')
            flc_raw = read_pkl(project_id, selected_datasheet, selected_nominal_age , 'flc_raw_data.pkl')
            flc_fit = read_pkl(project_id, selected_datasheet, selected_nominal_age , 'flc_fit_data.pkl')
            # selected_columns = ['nominal_age', 'load_direction', 'Rp02', 'Rm', 'Ag', 'A80', 'n4_6', 'n2_20', 'r8_12']
            df_ten_data.rename(columns={
                    'xdata':'e',
                    'ydata':'s',
                },inplace=True)
            excluded_tensile_idx = df_ten_data['file_name'].isin(list_excluded_tensile) | ~df_ten_data['file_name'].str.contains("_0")
            df_tensile_included = df_ten_data[~excluded_tensile_idx]
            
            df_ten_results = com_df_data
            df_ten_results['filename_only'] = df_ten_results['file_name'].apply(lambda x: Path(x).name)
            excluded_results_idx = df_ten_results['filename_only'].isin(list_excluded_tensile) 
            df_results_included = df_ten_results[~excluded_results_idx]
            
            if list_excluded_tensile:
                com_df_yield_data = com_df_yield_data[~com_df_yield_data['file_name'].str.contains('|'.join(list_excluded_tensile), regex=True)]
            
            df_bulge = df_bul_data
            df_bulge.rename(columns={
                    'xdata':'eps_1',
                    'ydata':'sig_1',
                },inplace=True)
            excluded_bulge_idx = df_bul_data['file_name'].isin(list_excluded_bulge)
            df_bulge_included = df_bul_data[~excluded_bulge_idx]
            tensile_samples = df_tensile_included['file_name'].unique()
            df_tensile_computed = df_tensile_included.copy()
           
            df_results = df_results_included
                
            avg_mech = df_results[['E', 'Rp02', 'Rm', 'Ag', 'Agt']].mean().to_dict()
            eps_range = get_tensile_eps_range(**avg_mech)

            params_dict= dict_params_to_insert[(selected_datasheet, selected_nominal_age, model_name)]


            eps_sc=[]
            sig_sc=[]
            all_eps_sc=[]
            all_sig_sc=[]
            all_eps_sc_err =[]
            all_sig_sc_err =[]
            file_names_err = []
            file_names = []
            tensile_file_names = []
            all_eps_pl =[]
            all_sig =[]
            scale_factor =[]
            all_df_scale_factor=[]
            eps_min, eps_max = eps_range
            avg_mech_2 = (avg_mech['E'], avg_mech['Rp02'], avg_mech['Rm'], avg_mech['Ag'], avg_mech['Agt'])

            k_mean, scale_factor_bulge = calculate_k_mean(selected_nominal_age, bg_tests, avg_mech_2,list_excluded_bulge)
            E, Rp02, Rm, Ag, Agt = avg_mech_2
            for test in bg_tests:
                if test.nominal_age == selected_nominal_age and test.file_name not in list_excluded_bulge:
                    eps_sc_l,sig_sc_l, file_name = get_bulge_fitting_data(test,eps_min,k_mean)
                    all_eps_sc.append(eps_sc_l)
                    all_sig_sc.append(sig_sc_l)
                    file_names.extend([test.file_name] * len(eps_sc_l))

                    eps_sc_l_err,sig_sc_l_err, file_name_err = get_bulge_fitting_data(test,eps_max,k_mean)
                    all_eps_sc_err.append(eps_sc_l_err)
                    all_sig_sc_err.append(sig_sc_l_err)
                    file_names_err.extend([test.file_name] * len(eps_sc_l_err))
                    k = get_scale_factor(test,E, Rp02, Rm, Ag, Agt)
                    if not np.isnan(k):
                        scale_factor.append(k)

            eps_sc = np.concatenate(all_eps_sc)
            sig_sc = np.concatenate(all_sig_sc)
            eps_sc_err = np.concatenate(all_eps_sc_err)
            sig_sc_err = np.concatenate(all_sig_sc_err)
            data_bulge = list(zip(eps_sc, sig_sc))
            data_bulge_3 = list(zip(file_names_err,eps_sc_err, sig_sc_err))
            df_bulge = pd.DataFrame(data_bulge_3, columns=['file_name','eps_sc', 'sig_sc'])

            for test in ts_tests:
                
                filename = test.file_name.name
                if test.nominal_age == selected_nominal_age and test.file_name.name not in list_excluded_tensile and "_0" in filename:
                    eps_pl, sig, file_name = get_tensile_fitting_data(test,eps_min,eps_max)
                    all_eps_pl.append(eps_pl)
                    all_sig.append(sig)
                    tensile_file_names.extend([test.file_name.name] * len(eps_pl))

            eps_pl_list = np.concatenate(all_eps_pl)
            sig_list = np.concatenate(all_sig)
            data_tensile = list(zip(eps_pl_list, sig_list))
            data_tensile_3 = list(zip(tensile_file_names, eps_pl_list, sig_list))
            df_tensile = pd.DataFrame(data_tensile_3, columns=['file_name','eps_pl', 'sig'])
            
            if scale_factor:
                average_scale_factor = 1 / (sum(scale_factor) / len(scale_factor))
            else:
                average_scale_factor = 0  
            df_scale_factor = pd.DataFrame([{'nominal_age':selected_nominal_age, '1/AVG(scale_factor)':average_scale_factor}])
            df_scale_factor.set_index('nominal_age', inplace=True)
            all_df_scale_factor.append(df_scale_factor)
            df_scale_factor = pd.concat(all_df_scale_factor)
            df_yield = get_yield_surface_data(com_df_yield_data,df_scale_factor)

            json_result = {
                f"{col[0]} {col[1]}".strip(): df_yield[col].values[0]
                for col in df_yield.columns
            }
            json_result["aging days"] = str(df_yield.index[0])

            df_yield = json_result 

            df_model_params = get_model_parameters(dict_params_to_insert,int(selected_datasheet), int(selected_nominal_age))
            for key, param_dict in params_dict.items():
                param_dict['param_variable'] = int(param_dict['param_variable'])
                    
            df_params= pd.DataFrame(params_dict)         
            
            model = getattr(models, model_name)
            model_grad = elementwise_grad(model)
            model_weights = {
                    'tensile_weight': model_weights_param['tensile_weight'],
                    'bulge_weight': model_weights_param['bulge_weight'],
                    'considere_weight': model_weights_param['considere_weight'],
                    'scaled_residue': bool(model_weights_param['scaled_residue']),
                }
            
            new_local_fit_params = _fit_model_to_data(model_name, model_weights, df_model_params_new, data_tensile, data_bulge, eps_range)
            
            eps_pl_02, eps_pl_ag = eps_range
            tensile_eps_idx = (df_tensile['eps_pl'] > eps_pl_02) & (df_tensile['eps_pl'] < eps_pl_ag)
            np_tensile = df_tensile.loc[tensile_eps_idx, ['eps_pl', 'sig']].to_numpy()
            bulge_eps_idx = (df_bulge['eps_sc'] > eps_pl_ag)
            
            m_params_new = new_local_fit_params
            m_params_current = pd.DataFrame(df_model_params)
            m_params_current = m_params_current.to_dict(orient='records')[0]
            
            

            if not m_err_current:
                m_err_current_data = _get_model_objective_error(df_tensile, df_bulge, model, model_grad, m_params_current, model_weights, eps_range)
                m_err_current = m_err_current_data["total_error"]  # Extract total error
                
            # Check if `initial_fit_errors` is None
            if initial_fit_errors is None:
                print("***** Computing initial_fit_errors *****")
                m_err_current_data = _get_model_objective_error(df_tensile, df_bulge, model, model_grad, m_params_current, model_weights, eps_range)
                m_err_current = m_err_current_data["total_error"]  # Extract total error

                # Store sub-errors in `initial_fit_errors`
                initial_fit_errors = {
                    "tensile_error": m_err_current_data["tensile_error"],
                    "bulge_error": m_err_current_data["bulge_error"],
                    "considere_error": m_err_current_data["considere_error"],
                }

            m_err_new_data = _get_model_objective_error(df_tensile, df_bulge, model, model_grad, m_params_new, model_weights, eps_range)
            m_err_new = m_err_new_data["total_error"]  # Extract total error
              
            new_fit_errors = {  # Store sub-errors
                "tensile_error": m_err_new_data["tensile_error"],
                "bulge_error": m_err_new_data["bulge_error"],
                "considere_error": m_err_new_data["considere_error"]
            }

            df_model_params = pd.DataFrame(
                [
                    m_params_current,
                    m_params_new
                ],
                index=[
                    'current fit',
                    'new local fit'
                ]
            )

            # Add errors to dict_data
            dict_model_data = {
                'df_tensile': df_tensile,
                'df_bulge': df_bulge,
                'df_results': df_results,
                'df_model_params': df_model_params,
                'm_err_current': m_err_current,
                'm_err_new': m_err_new,
                'initial_fit_errors': initial_fit_errors,
                'new_fit_errors': new_fit_errors,
            }

            dict_model = dict_model_data

            sw_t_grad = gradients['tensile_grad']
            sw_b_grad = gradients['bulge_grad']
            sw_t_n = gradients['tensile_n_grad']
            sw_b_n = gradients['bulge_n_grad']
            smoothing_windows = {}
            # Update smoothing_windows dictionary with the new values
            smoothing_windows['diff_window_side_grad_tensile'] = sw_t_grad
            smoothing_windows['diff_window_side_grad_bulge'] = sw_b_grad
            smoothing_windows["diff_window_side_n_tensile"] = sw_t_n
            smoothing_windows["diff_window_side_n_bulge"] = sw_b_n

            dict_data = get_model_and_measures_plot_data(dict_model, smoothing_windows, model_name)

            dict_data['df_tensile_plot'] = json.loads(dict_data['df_tensile_plot'].to_json(orient='records'))
            dict_data['df_bulge_plot'] = json.loads(dict_data['df_bulge_plot'].to_json(orient='records'))
            dict_data['df_results'] = json.loads(dict_data['df_results'].to_json(orient='records'))
            dict_data['df_models'] = json.loads(dict_data['df_models'].to_json(orient='records'))
            dict_data['df_model_params'] = json.loads(dict_data['df_model_params'].to_json(orient='index'))

            # Convert NumPy float64 to Python float
            dict_data['m_err_current'] = float(dict_data['m_err_current'])
            dict_data['m_err_new'] = float(dict_data['m_err_new'])

            # Convert tuples to lists
            dict_data['eps_sig_pl_02'] = list(dict_data['eps_sig_pl_02'])
            dict_data['eps_sig_pl_ag'] = list(dict_data['eps_sig_pl_ag'])

            # Convert DataFrame df_nvalues to JSON
            dict_data['df_nvalues'] = json.loads(dict_data['df_nvalues'].to_json(orient='index'))
            json_data = json.dumps(dict_data)

            df_tensile_plot_w = pd.DataFrame(dict_data['df_tensile_plot'])
            df_bulge_plot_w = pd.DataFrame(dict_data['df_bulge_plot'])
            local_fit_tensile_plot_data_path = create_csv(project_id,df_tensile_plot_w,selected_datasheet,selected_nominal_age, 'local_fit_tensile_plot_data.csv')
            local_fit_bulge_plot_data_path = create_csv(project_id,df_bulge_plot_w,selected_datasheet, selected_nominal_age,'local_fit_bulge_plot_data.csv')
            
            dict_data['df_tensile_plot_path']  = local_fit_tensile_plot_data_path
            dict_data['df_bulge_plot_path']  = local_fit_bulge_plot_data_path
            dict_data['df_tensile_plot']={}
            dict_data['df_bulge_plot']={}
            dict_data['df_yield'] =  df_yield

            # update sub-errors in dict_data
            dict_data.update({
            'initial_fit_errors': initial_fit_errors,
            'new_fit_errors': new_fit_errors
            })
            
            json_data = json.dumps(dict_data, indent=4)
            new_mech_data_params = {'avg_mech':avg_mech, 'eps_range':eps_range}
            mech_data_params_path = create_json(project_id,new_mech_data_params,selected_datasheet, selected_nominal_age,'new_mech_data_params.json')
           
            params_data = json.dumps(adjusted_params.params, indent=4)
            datasheet_local_fit_results = create_json(project_id,json_data,selected_datasheet, selected_nominal_age,'datasheet_local_fit_results.json')
            datasheet_local_fit_params = create_json(project_id,params_data,selected_datasheet, selected_nominal_age,'datasheet_local_fit_params.json')
            
            return dict_data
    
    except Exception as e:
        raise Exception(f"Datasheet compute fit failed: {str(e)}")