import pandas as pd
from pathlib import Path
from typing import Dict
import inspect


output_variables_aliases = {'buckle_pressure':'buckle_pressure', 'Weight':'Mass'}
output_variables = ['buckle_pressure', 'Weight']
performance_file_col = ['metric', 'value']


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
def PostProcess(rescale_output_file: Path=None, trial_folder: Path=None) -> Dict:
    with open(rescale_output_file, 'r') as file:
        data=file.readlines()
        #read in file, split list by empty space
        split_data=[line.strip().split(' ') for line in data] 
        #give data to dataframe
        df=pd.DataFrame(split_data)
        #drop all empty spaces
        df=df.mask(df == '')
        #keep only numeric values and reindex
        df=df[pd.to_numeric(df[0], errors='coerce').notnull()].dropna(axis=1).reset_index(drop=True)
        #reset column index
        df=df = df.T.reset_index(drop=True).T
        #convert numbers to float
        df=df.astype(float)
        #get max pressure
        max_index=df[3].idxmax()
        buckle=(df.iloc[max_index, 0], df.iloc[max_index, 3])
    
    Perfom_file = trial_folder / 'Performance.txt'
    with open(Perfom_file, 'r+') as fout:
        if not 'buckle_time' in fout.read():
            fout.write('buckle_time, %.4f\n' %(buckle[0]))
            fout.write('buckle_pressure, %.4f\n' %(buckle[1]*10000*14.5038))


    df = pd.read_csv(Perfom_file, sep=",", header=None)
    df.columns = performance_file_col
    # format outputs for MOBO
    next_observation_evaluation = {}

    for var in output_variables:
        if output_variables_aliases:
            evaluation = df[df['metric'] == output_variables_aliases[var]].iloc[0]['value']
        else:
            evaluation = df[df['metric']==var].iloc[0]['value']
        next_observation_evaluation[var] = (evaluation, None)

    return next_observation_evaluation
