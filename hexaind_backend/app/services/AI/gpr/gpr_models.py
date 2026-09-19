import gpytorch
import torch

class SingletaskGPModel(gpytorch.models.ExactGP):
    def __init__(self, train_x, train_y, likelihood, covar_module, mean_module):
        
        super(SingletaskGPModel, self).__init__(train_x, train_y, likelihood)
        self.mean_module = mean_module
        self.covar_module=covar_module
        
    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)

class MultitaskGPModel(gpytorch.models.ExactGP):
    def __init__(self, train_x, train_y, likelihood, num_latents, covar_module, mean_module):
        
        super(MultitaskGPModel, self).__init__(train_x, train_y, likelihood)

        self.mean_module = gpytorch.means.MultitaskMean(
            mean_module, num_tasks=train_y.shape[1]
        )
        
        latent_kernels = [covar_module for _ in range(num_latents)]
        self.covar_module = gpytorch.kernels.LCMKernel(
            latent_kernels, num_tasks=train_y.shape[1], rank=1) #positive integers (1 to # tasks) 

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gpytorch.distributions.MultitaskMultivariateNormal(mean_x, covar_x)

class SingletaskGPModelLarge(gpytorch.models.ApproximateGP):
    def __init__(self, train_x, train_y, num_inducing, covar_module, mean_module):

        input_dims = train_x.shape[1]
        inducing_points = torch.randn(num_inducing, input_dims)

        variational_distribution = gpytorch.variational.CholeskyVariationalDistribution(inducing_points.size(0))
        variational_strategy = gpytorch.variational.VariationalStrategy(self, inducing_points, variational_distribution, learn_inducing_locations=True)
        super(SingletaskGPModelLarge, self).__init__(variational_strategy)
        self.mean_module = mean_module
        self.covar_module = covar_module

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)

class MultitaskGPModelLarge(gpytorch.models.ApproximateGP):
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