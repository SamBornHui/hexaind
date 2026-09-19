from typing import Tuple

import numpy as np


# Get parameter dictionary from lmfit.Parameters object
def get_lmfit_params_dict(params):

    dict_params = {}

    for key, value in params.items():
        dict_params[key] = value.value

    return dict_params


def get_tensile_eps_range(E, Rp02, Rm, Ag, Agt) -> Tuple[float, float]:

    e_02 = 0.2/100

    # True values
    sig_02 = Rp02 * (1 + e_02 + Rp02/E)
    eps_pl_02 = np.log(1 + e_02 + Rp02/E) - sig_02/E

    sig_ag = Rm * (1 + Ag + Rm/E)
    eps_pl_ag = np.log(1 + Ag + Rm/E) - sig_ag/E

    # eps_agt = np.log(1 + Agt)

    return eps_pl_02, eps_pl_ag


def get_rp_rm_plot_points(E, Rp02, Rm, Ag, Agt) -> Tuple[float, float]:

    e_02 = 0.2/100

    # True values
    sig_02 = Rp02 * (1 + e_02 + Rp02/E)
    eps_pl_02 = np.log(1 + e_02 + Rp02/E) - sig_02/E

    sig_ag = Rm * (1 + Ag + Rm/E)
    eps_pl_ag = np.log(1 + Ag + Rm/E) - sig_ag/E

    # eps_agt = np.log(1 + Agt)

    return (eps_pl_02, sig_02), (eps_pl_ag, sig_ag)
