"""Public module containing the objective functions for the LS optimizations.

This module contains the definitions of the objective functions used in
the optimization of the model parameters.
"""

import numpy as np
import pandas as pd
from lmfit import Parameters
from typing import Callable, Tuple

from app.services.apps.datasheet_gen.dsgen_controller.utils.model_fitting import get_lmfit_params_dict

###########################
#   Objective Functions   #
###########################


def obj_ls(
        params: Parameters,
        xdata: 'np.ndarray[float]',
        ydata: 'np.ndarray[float]',
        model: Callable
        ) -> 'np.ndarray[float]':
    """Objective function computing the residues for the given model.

    Args:
        params (lmfit.Parameters): lmfit parameters to be optimized
        xdata (np.ndarray[float]): x-axis data used to fit model parameters
        ydata (np.ndarray[float]): y-axis data used to fit model parameters
        model (Callable): the model to be fitted

    Returns:
        np.ndarray[float]: array of residues given xdata, ydata and model
    """
    m_params = get_lmfit_params_dict(params)

    res = ydata - model(xdata, **m_params)
    print(res)
    return res


def _obj_ls_considere(
        m_params: dict,
        model: Callable,
        model_grad: Callable,
        eps_pl_ag: float,
        weights: Tuple[float, float, float],
        np_tensile: 'np.ndarray[float]',
        np_bulge: 'np.ndarray[float]',
        ) -> 'np.ndarray[float]':
    """Objective computing the LS squares residues and Considere Criterion error.

    Args:
        params (dict): dictionary of parameters to be optimized
        xdata (np.ndarray[float]): x-axis data used to fit model parameters
        ydata (np.ndarray[float]): y-axis data used to fit model parameters
        model (Callable): the model to be fitted
        model_grad (Callable): callable representing the gradient of the model (eg. autograd function)
        eps_pl_ag (float): Intersection point for the Considere Criterion
        weights (Tuple[float, float]): weights of least squares residues and considere crit. error

    Returns:
        np.ndarray[float]: array of the residues and considere crit. error for given parameters
    """

    xdata_tensile = np_tensile[:, 0]
    ydata_tensile = np_tensile[:, 1]
    tensile_res = ydata_tensile - model(xdata_tensile, **m_params)

    xdata_bulge = np_bulge[:, 0]
    ydata_bulge = np_bulge[:, 1]
    bulge_res = ydata_bulge - model(xdata_bulge, **m_params)

    considere_res = model(eps_pl_ag, **m_params) - model_grad(eps_pl_ag, **m_params)
    considere_res = np.array([considere_res])

    res = np.concatenate((
        weights[0] * tensile_res,
        weights[1] * bulge_res,
        weights[2] * considere_res,
    ))
    
    return res


def _obj_ls_considere_local_fit(
        m_params: dict,
        model: Callable,
        model_grad: Callable,
        eps_pl_ag: float,
        weights: Tuple[float, float, float],
        df_tensile: pd.DataFrame,
        df_bulge: pd.DataFrame,
        ) -> 'np.ndarray[float]':
    """Objective computing the LS squares residues and Considere Criterion error.

    Args:
        params (dict): dictionary of parameters to be optimized
        xdata (np.ndarray[float]): x-axis data used to fit model parameters
        ydata (np.ndarray[float]): y-axis data used to fit model parameters
        model (Callable): the model to be fitted
        model_grad (Callable): callable representing the gradient of the model (eg. autograd function)
        eps_pl_ag (float): Intersection point for the Considere Criterion
        weights (Tuple[float, float]): weights of least squares residues and considere crit. error

    Returns:
        np.ndarray[float]: array of the residues and considere crit. error for given parameters
    """
    mode = 'prod'
    
    t_res = []
    for f in df_tensile['file_name'].unique():
        test_data = df_tensile[df_tensile['file_name']==f]
        xdata_tensile = test_data['eps_pl'].values
        ydata_tensile = test_data['sig'].values
        
        if mode == 'dev':
            y_data_model = test_data['sig_pred'].values #dev
        elif mode == 'prod':
            y_data_model = model(xdata_tensile, **m_params) #prod
            
        y_res2 = (ydata_tensile-y_data_model)**2
        y_res2 = np.sum(y_res2)
        y_res2 = y_res2/len(y_data_model)    
        t_res.append(y_res2) #array of sum of squares for individual tests normalized by number of data points

    tensile_res = np.array([np.sum(t_res)])  
    
    
    b_res = []
    for f in df_bulge['file_name'].unique():
        test_data = df_bulge[df_bulge['file_name']==f]
        xdata_bulge = test_data['eps_sc'].values
        ydata_bulge = test_data['sig_sc'].values
        if mode == 'dev':
            y_data_model = test_data['sig_sc_pred'].values #dev
        elif mode == 'prod':
            y_data_model = model(xdata_bulge, **m_params) #prod
        y_res2 = (ydata_bulge-y_data_model)**2
        y_res2 = np.sum(y_res2)
        y_res2 = y_res2/len(y_data_model)    
        b_res.append(y_res2) 

    bulge_res =  np.array([np.sum(b_res)]) 
    considere_res = model(eps_pl_ag, **m_params) - model_grad(eps_pl_ag, **m_params)
    considere_res = np.array([considere_res])
    considere_res= np.square(considere_res)

    res = np.concatenate((
        tensile_res,
        bulge_res,
        considere_res,
    ))
    return res


def obj_ls_considere(
        params: Parameters,
        model: Callable,
        model_grad: Callable,
        eps_pl_ag: float,
        weights: Tuple[float, float, float],
        # df_tensile: pd.DataFrame,
        # df_bulge: pd.DataFrame,
        np_tensile: 'np.ndarray[float]',
        np_bulge: 'np.ndarray[float]',
        ) -> 'np.ndarray[float]':
    """Objective computing the LS squares residues and Considere Criterion error.

    Args:
        params (lmfit.Parameters): lmfit parameters to be optimized
        xdata (np.ndarray[float]): x-axis data used to fit model parameters
        ydata (np.ndarray[float]): y-axis data used to fit model parameters
        model (Callable): the model to be fitted
        model_grad (Callable): callable representing the gradient of the model (eg. autograd function)
        eps_pl_ag (float): Intersection point for the Considere Criterion
        weights (Tuple[float, float]): weights of least squares residues and considere crit. error

    Returns:
        np.ndarray[float]: array of the residues and considere crit. error for given parameters
    """
    # Unpack fitting parameters
    m_params = get_lmfit_params_dict(params)

    res = _obj_ls_considere(m_params, model, model_grad, eps_pl_ag, weights, np_tensile, np_bulge)

    return res

