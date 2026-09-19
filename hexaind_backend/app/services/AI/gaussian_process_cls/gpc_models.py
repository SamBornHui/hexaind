# -*- coding: utf-8 -*-
"""
Created on Wed May  8 13:33:26 2024

@author: marsh
"""
import torch
import gpytorch
from gpytorch.models import ExactGP
from gpytorch.models import ApproximateGP
from gpytorch.variational import CholeskyVariationalDistribution
from gpytorch.variational import UnwhitenedVariationalStrategy

class DirichletGPModel(ExactGP):
    def __init__(self, train_x, train_y, likelihood, covar_module, mean_module):
        super(DirichletGPModel, self).__init__(train_x, train_y, likelihood)
        self.mean_module = mean_module
        self.covar_module = covar_module

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)
    
class VariationalGPModel(ApproximateGP):
    def __init__(self, train_x, train_y, num_latents, num_inducing, covar_module, mean_module):
        
        num_tasks = train_y.shape[1]
        input_dims = train_x.shape[1]
        choel_mean_init = torch.std(train_y,0).mean()
        
        inducing_points = torch.randn(num_latents, num_inducing, input_dims)
        
        variational_distribution = gpytorch.variational.CholeskyVariationalDistribution(
            inducing_points.size(-2), batch_shape=torch.Size([num_latents]), mean_init_std = choel_mean_init,
        )

        variational_strategy = gpytorch.variational.LMCVariationalStrategy(
            gpytorch.variational.VariationalStrategy(
                self, inducing_points, variational_distribution, learn_inducing_locations=True
            ),
            num_tasks=num_tasks,
            num_latents=num_latents,
            latent_dim=-1,
        )

        super().__init__(variational_strategy)

        self.mean_module = mean_module
        self.covar_module=covar_module

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)
    