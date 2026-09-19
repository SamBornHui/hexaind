# -*- coding: utf-8 -*-
"""
Created on Wed Oct 2 10:59:19 2024

@author: leclerc
"""

__all__ = ['CategoricalTransformer', 'PolynomialTransformer', 'custom_scikit_train_test_split']
#            'categorical_encoding', 'drop_nan_zero_rows',
#            , 'custom_dask_train_test_split']

import numpy as np
import pandas as pd
import logging
import sys
# import dask.array as da
# from dask_ml.model_selection import train_test_split as dask_train_test_split

from sklearn.model_selection import train_test_split
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import PolynomialFeatures
logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

'''
CategoricalTransformer allows categorical variables in a dataset to be encoded in two ways:
1. One-hot encoding ('ohe'): Each category becomes a new column with binary values (0 or 1).
2. Mean encoding ('me'): Each category is replaced by the mean of the target variable y for that category.
'''
class CategoricalTransformer(BaseEstimator, TransformerMixin):

    # Initializing the categorical transformation
    def __init__(self, cat_encoding = 'One_hot'):

        # Writing the type of transformer
        self.cat_encoding = cat_encoding

    # Fitting categorical transformer
    def fit(self, X, y = None):

        # Extracting categorical variables
        if isinstance(X, pd.DataFrame):
            logger.info(f"Dtype of pandas dataframe {str(X.dtypes)}")
            logger.info(f"Encoding type: {str(self.cat_encoding)}")
            # Check if any column has 'string[pyarrow]' dtype
            # Check if any column has 'string[pyarrow]' dtype
            if any(X.dtypes== 'string[pyarrow]'):
                cat_var_names = X.select_dtypes(['object', 'category', 'string']).columns.to_list()
            else:
                cat_var_names = X.select_dtypes(['object', 'category']).columns.to_list()
            logger.info(f"cat_var_names {str(cat_var_names)}")

        # Fitting categorical transformer
        if cat_var_names.__len__() > 0:

            self.cat_var_names = cat_var_names

            # One-hot encoding case
            if self.cat_encoding == 'One_hot':

                # Getting the one hot encoding of categorical variables
                X_ohe = pd.get_dummies(X, self.cat_var_names)
                self.cat_encoding_info = X_ohe.columns

            # Mean-encoding case
            elif hasattr(self, 'cat_encoding') and self.cat_encoding == 'Mean':

                if y is None:
                    raise ValueError('Mean encoding requires a pandas series as the same length of X.')

                unique_categ_labels = {} # Dictionary to store unique entries in categorical variables
                X_me = X.copy().assign(**{y.name: y.values}) # Combining input and out
                for categ in self.cat_var_names:

                    # Mean encoding the variable
                    mean_encoded_subject = X_me.groupby(categ)[y.name].mean().to_dict()

                    # Unique entries in categorical variables
                    unique_categ_labels[categ] = mean_encoded_subject

                # Writing the unique categorical labels to class
                self.cat_encoding_info = unique_categ_labels

        return self
    
    # Transforming future datasets  based on the fit transformer
    def transform(self, X_t):
        logger.info("In transform")

        if hasattr(self, 'cat_var_names') and self.cat_var_names:
            # One-hot encoding case
            if self.cat_encoding == 'One_hot':

                X_t = pd.get_dummies(X_t, self.cat_var_names)
                missing_cols = set(self.cat_encoding_info) - set(X_t.columns)
                for i in missing_cols:
                    X_t[i] = 0
                X_t = X_t[self.cat_encoding_info]
                return X_t

            # Mean-encoding case
            elif self.cat_encoding == 'Mean':

                # Casting the mean encoded subjects to test set
                X_tc = X_t.copy()
                for i in self.cat_encoding_info:
                    X_tc.loc[:, i] = X_t.loc[:, i].map(self.cat_encoding_info[i])

                return X_tc

        # Return the same input in case there is no categorical feature
        else:
            return X_t

    # Fit-transform
    def fit_transform(self,X,y):

        # Combined fit and transformation
        return self.fit(X, y).transform(X)
    

    
'''
PolynomialTransformer generates polynomial features for each input feature, but with custom degree control. You can specify different degrees for each feature, unlike the standard PolynomialFeatures from scikit-learn, which applies a uniform degree to all features
PD:  either be a single integer (applied to all features) or a list/array specifying different degrees for each feature.
'''
class PolynomialTransformer(BaseEstimator, TransformerMixin):

    # Initialization of PolynomialTransformer class
    def __init__(self, PD):

        # Writing PD to polynomial transformer class
        self.PD = PD
        logger.info(f"PD_value {str(self.PD)}")

        # Preparing the polynomial features class
        self.poly = PolynomialFeatures(np.max(PD), include_bias = False)

    # Fitting categorical transformer
    def fit(self, X):

        # Setting up polynomial degrees
        if isinstance(self.PD, (int, np.int64)):
            # If an integer is entered for PD, it is replicated to accommodate all variables
            self.PD = [self.PD] * X.shape[1]
        
        logger.info(f"PD values{str(self.PD)}")
        if self.PD.__len__() < X.shape[1]:
            raise ValueError('PD variable must either be an integer or a list/numpy array with'\
                             ' the same number of arrays as the number of variables in input.')

        # Raise error for negative values
        if any(n < 0 for n in self.PD):
            raise ValueError('Negative values for polynomials are not allowed.')

        # Maximum degree for polynomials
        self.poly.fit(np.zeros((1, X.shape[1])))

        # Removing the monomials with variables that have larger powers than
        # assigned in power array
        self.valid_poly_indices = (self.poly.powers_ <= np.tile(self.PD,(self.poly.powers_.shape[0],1))).all(1)
        self.PowerMatrix = self.poly.powers_[self.valid_poly_indices]

        return self

    # Transforming future datasets  based on the fit transformer
    def transform(self, X_t):

        X_t = self.poly.transform(X_t)
        return X_t[:, self.valid_poly_indices]

    # Fit-transform
    def fit_transform(self, X):

        # Combined fit and transformation
        return self.fit(X).transform(X)
    
    

   
    
    
    
    
# def custom_scikit_train_test_split(x, y, 
#                             test_size=0.2, 
#                             split_type="Random", 
#                             random_state=None):
    
#     """
#     This function is useful for splitting the data either randomly or sequentially for pandas or sklearn objects
#     and it will aslo return the indices of the train and test data poitns
#     """

#     logger.info(x)
    
#     # decide random or sequential
#     shuffle = True if split_type == "Random" else False
 
#     if shuffle: # random split
#         X_train, X_test, y_train, y_test, train_indices, test_indices = train_test_split(x, y,
#                                                                                          np.arange(x.shape[0]),  
#                                                                                          test_size=test_size,
#                                                                                          shuffle=True,
#                                                                                          random_state=random_state)
#     else: # sequential split
#         X_train, X_test, y_train, y_test, train_indices, test_indices = train_test_split(x, y,
#                                                                                          np.arange(x.shape[0]), 
#                                                                                          test_size=test_size,
#                                                                                          shuffle=False,
#                                                                                          random_state=None)
#     return X_train, X_test, y_train, y_test, train_indices, test_indices
    