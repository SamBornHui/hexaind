import pandas as pd
from pathlib import Path
from typing import Any, Dict
import math
import pickle
import numpy as np
import inspect

model_gen_name = None
model_gen_module = None
model_post_process = True
model_scaler_file = 'scaler.pkl'
model_file = 'gp_scaling.pkl'
output_variables = ['buckle_pressure', 'max_thinning']
output_variables_aliases = {'buckle_pressure':'Buckling Pressure', 'max_thinning':'Max Thinning Percent'}


def ignore_extra_kwargs(func):
    """Decorator to ignore extra arguments from a dictionary of arguments while function calling."""

    def wrapper(**kwargs):
        """Wrapper function to ignore extra arguments from a dictionary of arguments."""

        # Get the expected keyword arguments for the function.
        expected_kwargs = set(inspect.getfullargspec(func).args)

        # Ignore any extra keyword arguments.
        kwargs = {k: v for k, v in kwargs.items() if k in expected_kwargs}

        # Call the function with the remaining keyword arguments.
        return func(**kwargs)

    return wrapper

def condition_eval(assignments) -> int:
    pp_spacer_thickness = assignments['pp_spacer']
    # Upper Radius - SigOpt suggestion
    upper_radius = assignments['upper_radius']
    # Lower Radius - SigOpt suggestion
    lower_radius = assignments['lower_radius']
    # t value - SigOpt suggestion
    t_value = assignments['t_value']
    # Lower Radius Opening - SigOpt suggestion
    lr_opening = assignments['lr_opening']
    # Catcher Depth - SigOpt suggestion
    catcher_depth = assignments['catcher_depth']
    
    cx_u = 0.811939962095721
    cy_u = -0.173700000193601+pp_spacer_thickness-0.1625-upper_radius

    cx_l = lr_opening/2.0 - lower_radius
    cy_l = -0.173700000193601+pp_spacer_thickness-0.1625-upper_radius-t_value

    delta_x = cx_u - cx_l

    delta_y = t_value

    reldis = math.sqrt(delta_x*delta_x + delta_y*delta_y)

    delta_r = upper_radius - lower_radius
    phi_angle = math.atan2(-1.0*delta_x,delta_y)
    
    condeval = 1 #False-fail, fail_flag=1
    if abs(reldis) > abs(delta_r) :
        theta_angle = ((phi_angle - math.atan2(delta_r,math.sqrt(reldis*reldis - delta_r*delta_r)))*180.0/math.pi) % 360.0  
        straight_line_segment_length = (-0.173700000193601 + 0.226699999996061 + (catcher_depth-0.0829) - upper_radius - t_value)
        if theta_angle < 90.0 and theta_angle > 0.0 and straight_line_segment_length > 0.0 :
            condeval = 0 #True-pass fail_flag=0
           
    return condeval

def PreProcess(parameters_file: Path) -> Any:
    dff = pd.read_csv(parameters_file)
    suggestion = dff.to_dict('records')[0]
    fail_criter = condition_eval(suggestion)
    additional_files = []
    return fail_criter, additional_files


@ignore_extra_kwargs
def PostProcess(rescale_output_file: Path=None, parameters_file: Path=None, additional_files_dir: Path=None) -> Dict:
        
    evaluated_data = pd.read_csv(rescale_output_file)
    trial_data = dict()
    for i in range(len(output_variables)):
        if output_variables_aliases:
            trial_data.update({output_variables[i]: tuple((evaluated_data[output_variables_aliases[output_variables[i]]][0], None))})
        else:
            trial_data.update({output_variables[i]: tuple((evaluated_data[output_variables[i]][0], None))})
    
    # Multiply maxThinning from rescale output by -1 
    try:
        rev_thinning = trial_data['max_thinning'][0]*-1
        trial_data['max_thinning'] = (rev_thinning, None)
    except: 
        print('Variable max_thinning not found in output.')
    
    # If want to post-process results with a model
    if model_post_process:    
        # load model & scaler
        with open(additional_files_dir/model_file, 'rb') as file:
            gp_model = pickle.load(file)
        with open(additional_files_dir/model_scaler_file, 'rb') as file:
            input_scaler = pickle.load(file)
        
        # load input values
        suggestions_list = pd.read_csv(parameters_file)
        ips_pressure = suggestions_list['ips_pressure'][0]
        up_pressure = suggestions_list['up_pressure'][0]
        dcp_spacer = suggestions_list['dcp_spacer'][0]
        pp_spacer = suggestions_list['pp_spacer'][0]
            
        scaler_inputs = np.array([[dcp_spacer,pp_spacer,ips_pressure,up_pressure]])
        scaled_inputs = input_scaler.transform(scaler_inputs)
        mean_pred, std_pred = gp_model.predict(scaled_inputs, return_std=True)
        corr_factor = mean_pred[0]
        new_buckle_pressure = trial_data['buckle_pressure'][0]*corr_factor
        trial_data['buckle_pressure'] = (new_buckle_pressure, None)
    
    return trial_data
