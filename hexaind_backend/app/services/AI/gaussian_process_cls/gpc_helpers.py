import numpy as np
import torch
import gpytorch
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import RandomOverSampler, ADASYN, SMOTE, SVMSMOTE, BorderlineSMOTE
from imblearn.under_sampling import RandomUnderSampler, NearMiss, AllKNN, EditedNearestNeighbours, RepeatedEditedNearestNeighbours, CondensedNearestNeighbour, OneSidedSelection
from imblearn.combine import SMOTEENN, SMOTETomek

from .gpc_models import DirichletGPModel,VariationalGPModel


def resample(X,y,sampler_type):
    if sampler_type=='none':
        X_res=X
        y_res=y
        return X_res, y_res
    elif sampler_type=='randomos':
        sampler = RandomOverSampler(random_state=0)
    elif sampler_type=='adasyn':
        sampler = ADASYN(random_state=0)
    elif sampler_type=='smote':   ######over sampling
        sampler = SMOTE(random_state=0)
    elif sampler_type=='svmsmote':
        sampler = SVMSMOTE(random_state=0)
    elif sampler_type=='borderlinesmote':
        sampler = BorderlineSMOTE(random_state=0)
    elif sampler_type=='randomus': ### under sampling
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
    X=x_scaler.fit_transform(X)

    train_x=torch.from_numpy(X).float()
    
    return x_scaler, train_x

def construct_kernel(train_x, train_y, max_train, kernel_selected, num_classes, num_mixtures=None, spectral_selected=False):
    '''
    Parameters
    ----------
    train_x : input data matrix
    train_y : output data matrix
    max_train : threshold for switching from exact GP posterior to a sparse approximation
    num_latents : Number of latent GPs for Linear Model of Coregionalization.

    Returns
    -------
    covar_module : covariance module for gpytorch through selected kernels
    likelihood : Gaussian likelihood for multi or single output GP

    '''
    
    # spectral_kernel=gpytorch.kernels.SpectralMixtureKernel(ard_num_dims=train_x.shape[1],num_mixtures=num_mixtures,batch_shape=torch.Size((num_classes,)))
    # rbf_kernel=gpytorch.kernels.RBFKernel(batch_shape=torch.Size((num_classes,)))
    # ard_rbf_kernel=gpytorch.kernels.RBFKernel(ard_num_dims=train_x.shape[1],batch_shape=torch.Size((num_classes,)))
    # matern_kernel=gpytorch.kernels.MaternKernel(nu=2.5,batch_shape=torch.Size((num_classes,)))
    # ard_matern_kernel=gpytorch.kernels.MaternKernel(nu=2.5,ard_num_dims=train_x.shape[1],batch_shape=torch.Size((num_classes,)))
    # linear_kernel=gpytorch.kernels.LinearKernel(batch_shape=torch.Size((num_classes,)))
    
    if train_x.shape[0]<=max_train:
        spectral_kernel=gpytorch.kernels.SpectralMixtureKernel(ard_num_dims=train_x.shape[1],num_mixtures=num_mixtures,batch_shape=torch.Size((num_classes,)))
        rbf_kernel=gpytorch.kernels.RBFKernel(batch_shape=torch.Size((num_classes,)))
        ard_rbf_kernel=gpytorch.kernels.RBFKernel(ard_num_dims=train_x.shape[1],batch_shape=torch.Size((num_classes,)))
        matern_kernel=gpytorch.kernels.MaternKernel(nu=2.5,batch_shape=torch.Size((num_classes,)))
        ard_matern_kernel=gpytorch.kernels.MaternKernel(nu=2.5,ard_num_dims=train_x.shape[1],batch_shape=torch.Size((num_classes,)))
        linear_kernel=gpytorch.kernels.LinearKernel(batch_shape=torch.Size((num_classes,)))
    else:
        spectral_kernel=gpytorch.kernels.SpectralMixtureKernel(ard_num_dims=train_x.shape[1],num_mixtures=num_mixtures)
        rbf_kernel=gpytorch.kernels.RBFKernel()
        ard_rbf_kernel=gpytorch.kernels.RBFKernel(ard_num_dims=train_x.shape[1])
        matern_kernel=gpytorch.kernels.MaternKernel(nu=2.5)
        ard_matern_kernel=gpytorch.kernels.MaternKernel(nu=2.5,ard_num_dims=train_x.shape[1])
        linear_kernel=gpytorch.kernels.LinearKernel()
    
    kernels_list=[]
    
    kernel_options=[rbf_kernel,ard_rbf_kernel,matern_kernel,ard_matern_kernel,linear_kernel]
    
    #if spectral mixture kernel is selected, use only that. Otherwise, use the combination of RBF/Matern/Linear specified
    #by the user
    if spectral_selected:
        print('Kernel: Spectral-Mixture')
        covar_module=spectral_kernel
        covar_module.initialize_from_data(train_x, train_y)
    else:
        for i in range(len(kernel_selected)):
            if kernel_selected[i]==True:
                kernels_list.append(kernel_options[i])
                if len(kernels_list)==1:
                    covar_module=gpytorch.kernels.ScaleKernel(kernel_options[i])
                else:
                    covar_module+=gpytorch.kernels.ScaleKernel(kernel_options[i])
        #covar_module=gpytorch.kernels.ScaleKernel(covar_module)
        
    return covar_module

def construct_likelihood(train_y,max_train):
    '''
    Parameters
    ----------
    train_y : output data matrix

    Returns
    -------
    likelihood : gpytorch Gaussian likelihood for multi or single output GP

    '''
    if len(train_y)>max_train:
        likelihood = gpytorch.likelihoods.MultitaskGaussianLikelihood(num_tasks=train_y.shape[1])
    else:
        likelihood = gpytorch.likelihoods.DirichletClassificationLikelihood(train_y, learn_additional_noise=True)
        
    return likelihood

def construct_mean_function(train_x, train_y, mean, num_classes, max_train, num_latents=None):
    '''
    Selects the mean function for the GP based on user-selection
    
    Parameters
    ----------
    train_x : input data matrix
    train_y : output data matrix
    num_latents : Number of latent GPs for Linear Model of Coregionalization.

    Returns
    -------
    mean_module : user-selected gpytorch mean function

    '''
    
    if train_x.shape[0]>max_train:
        if mean=='zero':
            mean_module=gpytorch.means.ZeroMean()
        elif mean=='constant':
            mean_module=gpytorch.means.ConstantMean()
        elif mean=='linear':
            mean_module=gpytorch.means.LinearMean(input_size=train_x.shape[1])
    else:
        if mean=='zero':
            mean_module=gpytorch.means.ZeroMean(batch_shape=torch.Size((num_classes,)))
        elif mean=='constant':
            mean_module=gpytorch.means.ConstantMean(batch_shape=torch.Size((num_classes,)))
        elif mean=='linear':
            mean_module=gpytorch.means.LinearMean(input_size=train_x.shape[1],batch_shape=torch.Size((num_classes,)))
            
    return mean_module


def construct_model(train_x, train_y, covar_module, mean_module, likelihood, max_train, num_latents=None, num_inducing=None):
    #Choose model based on numpber of output features and number of training points
    if train_x.shape[0]>max_train:
        model = VariationalGPModel(train_x, train_y, num_latents, num_inducing, covar_module, mean_module)
        print('Model: Variational MultitaskGP')
    else:
        model = DirichletGPModel(train_x, likelihood.transformed_targets, likelihood, covar_module, mean_module)
        print('Model: Exact SingletaskGP')
            
    return model
