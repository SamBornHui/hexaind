import torch
import gpytorch
import numpy as np

#for v0-3

class MultitaskGPModel(gpytorch.models.ExactGP):
    def __init__(self, train_x, train_y, likelihood, latent, tasks):
        super(MultitaskGPModel, self).__init__(train_x, train_y, likelihood)
        self.mean_module = gpytorch.means.MultitaskMean(
            gpytorch.means.ConstantMean(), num_tasks=tasks
        )

        latent_kernels = []
        for i in range(5):
            latent_kernels.append(gpytorch.kernels.RBFKernel(ard_num_dims=train_x.shape[1]))
        
        self.covar_module = gpytorch.kernels.LCMKernel(
            latent_kernels, num_tasks=tasks, rank=latent
        )
        
    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gpytorch.distributions.MultitaskMultivariateNormal(mean_x, covar_x)

def normScaling(inputs,device):
    inputs_t = torch.from_numpy(inputs).double().to(device)
    m = inputs_t.mean(0, keepdim=True).to(device)
    s = inputs_t.std(0, unbiased=False, keepdim=True).to(device)
    inputs_t -= m
    inputs_t /= s 
    inputs_t = inputs_t.to(device)
    
    return inputs_t, m, s

def unitScaling(inputs,device):
    inputs = torch.from_numpy(inputs).double().to(device)
    inputs_min = inputs.min(0)[0]
    inputs_max = inputs.max(0)[0]
    inputs = 2 * (inputs - inputs_min)/(inputs_max - inputs_min) - 1
    
    return inputs, inputs_min, inputs_max

def unitScalingMod(inputs, cmin, cmax, device):
    # cmin, cmax - user provided min/max constraints
    mins = np.asarray(cmin, dtype=np.float64)
    maxs = np.asarray(cmax, dtype=np.float64)

    inputs = torch.from_numpy(inputs).double().to(device)
    inputs_min = torch.from_numpy(mins).double().to(device)
    inputs_max = torch.from_numpy(maxs).double().to(device)
    inputs = 2 * (inputs - inputs_min)/(inputs_max - inputs_min) - 1
    
    return inputs, inputs_min, inputs_max

def kldiv(p2,p1):
    err = False
    try:
        #with gpytorch.settings.cholesky_max_tries(10), gpytorch.settings.cholesky_jitter(1e-2):
        term1 = (p2._covar.log_det() - p1._covar.log_det())
        term2 = torch.trace(torch.matmul(p2.precision_matrix,p1.covariance_matrix))
        term3 = torch.matmul(torch.matmul((p2.mean-p1.mean).flatten(),p2.precision_matrix),(p2.mean-p1.mean).flatten())
        kldiv = 0.5*(term1 + term2 + term3 - p1.covariance_matrix.shape[0])
    except Exception:
        print('Unable to calculate KL-divergence')
        err = True
        kldiv = 0
        pass
    
    return kldiv, err

def entropy(p):
    err = False
    try:
        entrop = 0.5*(p._covar.log_det() + p.covariance_matrix.shape[0]*(1 + np.log(2*np.pi)))
    except Exception:
        print('Unable to calculate entropy')
        err = True
        pass
    return entrop, err


def rechypers(model,likelihood,n_latent_gp):
    '''records hyperparameter values from trained MOGP in dict'''
    hypers = {
        'likelihood.task_noises': likelihood.task_noises,
        'likelihood.noise': likelihood.noise
        }
        
    for i in range(n_latent_gp):
        hypers['mean_module.base_means.'+str(i)+'.constant'] = model.mean_module.base_means[i].constant
        hypers['covar_module.covar_module_list.'+str(i)+'.task_covar_module.covar_factor'] = model.covar_module.covar_module_list[i].task_covar_module.covar_factor
        hypers['covar_module.covar_module_list.'+str(i)+'.task_covar_module.var'] = model.covar_module.covar_module_list[i].task_covar_module.var
        hypers['covar_module.covar_module_list.'+str(i)+'.data_covar_module.lengthscale'] = model.covar_module.covar_module_list[i].data_covar_module.lengthscale
    
    return hypers
