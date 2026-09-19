import pandas as pd
from pathlib import Path
from typing import Dict
import inspect


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

@ignore_extra_kwargs  
def PostProcess(rescale_output_file: Path=None) -> Dict:
    evaluated_data = pd.read_csv(rescale_output_file)
    trial_data = dict()
    for i in range(len(output_variables)):
        if output_variables_aliases:
            trial_data.update({output_variables[i]: tuple((evaluated_data[output_variables_aliases[output_variables[i]]][0], None))})
        else:
            trial_data.update({output_variables[i]: tuple((evaluated_data[output_variables[i]][0], None))})
    
    ### multiple maxThinning from rescale output by -1 
    try:
        rev_thinning = trial_data['max_thinning'][0]*-1
        trial_data['max_thinning'] = (rev_thinning, None)
    except: 
        print('Variable max_thinning not found in output.')
    
    return trial_data