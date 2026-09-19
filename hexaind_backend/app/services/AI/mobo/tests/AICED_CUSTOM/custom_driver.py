import pandas as pd
from pathlib import Path
from typing import Any, Dict
import math
import inspect


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
