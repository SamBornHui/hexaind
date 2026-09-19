# -*- coding: utf-8 -*-
"""
Created on Thu May  9 13:08:46 2024

@author: marsh
"""

from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import RandomOverSampler, ADASYN, SMOTE, SVMSMOTE, BorderlineSMOTE
from imblearn.under_sampling import RandomUnderSampler, NearMiss, AllKNN, EditedNearestNeighbours, RepeatedEditedNearestNeighbours, CondensedNearestNeighbour, OneSidedSelection
from imblearn.combine import SMOTEENN, SMOTETomek

def resample(X,y,sampler_type):
    if sampler_type=='none':
        X_res=X
        y_res=y
        return X_res, y_res
    elif sampler_type=='randomos':
        sampler = RandomOverSampler(random_state=0)
    elif sampler_type=='adasyn':
        sampler = ADASYN(random_state=0)
    elif sampler_type=='smote':
        sampler = SMOTE(random_state=0)
    elif sampler_type=='svmsmote':
        sampler = SVMSMOTE(random_state=0)
    elif sampler_type=='borderlinesmote':
        sampler = BorderlineSMOTE(random_state=0)
    elif sampler_type=='randomus':
        sampler = RandomUnderSampler(random_state=0)
    elif sampler_type=='nearmiss1':
        sampler = NearMiss(version=1)
    elif sampler_type=='nearmiss2':
        sampler = NearMiss(version=2)
    elif sampler_type=='nearmiss3':
        sampler = NearMiss(version=3)
    elif sampler_type=='allknn':
        sampler = AllKNN(allow_minority=True)
    elif sampler_type=='ENN':
        sampler = EditedNearestNeighbours()
    elif sampler_type=='RENN':
        sampler = RepeatedEditedNearestNeighbours()
    elif sampler_type=='CNN':
        sampler = CondensedNearestNeighbour(random_state=0)
    elif sampler_type=='OSS':
        sampler = OneSidedSelection(random_state=0)
    elif sampler_type=='smoteenn':
        sampler = SMOTEENN(random_state=0)
    elif sampler_type=='smotetomek':
        sampler = SMOTETomek(random_state=0)
    
    X_res, y_res = sampler.fit_resample(X, y)
    
    return X_res,y_res

def standardize_inputs(X):
    '''

    Parameters
    ----------
    X : TYPE
        DESCRIPTION.
    y : TYPE
        DESCRIPTION.

    Returns
    -------
    x_scaler : TYPE
        DESCRIPTION.
    y_scaler : TYPE
        DESCRIPTION.
    train_x : TYPE
        DESCRIPTION.
    train_y : TYPE
        DESCRIPTION.

    '''
    
    #Standardize inputs and outputs
    x_scaler=StandardScaler()
    train_x=x_scaler.fit_transform(X)
    
    return x_scaler, train_x