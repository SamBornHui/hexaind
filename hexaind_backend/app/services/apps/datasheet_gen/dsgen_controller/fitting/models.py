"""Public module containing the mathematical models used for Hardening Curve fitting.

This module contains the definition of the mathematical models used for fitting
the parameters of the Hardening Curves.

As a convention, the variable names are consistent with the variable names used in the
other parts of the project, such as the name of the `lmfit` parameters and the name of
the parameters used in the SQL local data storage.
"""
import autograd.numpy as np


def voce(
        eps_pl: 'np.ndarray[float]',
        sig_0: float,
        sig_inf: float,
        n: float
        ) -> 'np.ndarray[float]':
    """Voce hardening curve model.

    Args:
        eps_pl (np.ndarray[float]): Array of the plastic strains where the model should be interrogated.
        sig_0 (float): sig_0 model parameter
        sig_inf (float): sig_inf model parameter
        n (float): n model parameter

    Returns:
        np.ndarray[float]: Array of equivalent stress for the input plastic strains
    """
    return sig_inf - (sig_inf - sig_0)*np.exp(-n*eps_pl)


def swift(
        eps_pl: 'np.ndarray[float]',
        C: float,
        eps_0: float,
        m: float
        ) -> 'np.ndarray[float]':
    """Swift hardening curve model.

    Args:
        eps_pl (np.ndarray[float]): Array of the plastic strains where the model should be interrogated.
        C (float): C model parameter
        eps_0 (float): eps_0 model parameter
        m (float): m model parameter

    Returns:
        np.ndarray[float]: Array of equivalent stress for the input plastic strains
    """
    return C * np.power(eps_0 + eps_pl, m)


def hocket_sherby(
        eps_pl: 'np.ndarray[float]',
        sig_i: float,
        sig_sat: float,
        a: float,
        p: float
        ) -> 'np.ndarray[float]':
    """Hocket-Sherby hardening curve model.

    Args:
        eps_pl (np.ndarray[float]): Array of the plastic strains where the model should be interrogated.
        sig_i (float): sig_i model parameter
        sig_sat (float): sig_sat model parameter
        a (float): a model parameter
        c (float): c model parameter

    Returns:
        np.ndarray[float]: Array of equivalent stress for the input plastic strains
    """
    return sig_sat - (sig_sat - sig_i)*np.exp(-a*np.power(eps_pl, p))


def hocket_sherby_swift(
        eps_pl: 'np.ndarray[float]',
        sig_i: float,
        sig_sat: float,
        a: float,
        p: float,
        C: float,
        eps_0: float,
        m: float,
        alpha: float,
        ) -> 'np.ndarray[float]':
    """Hocket-Sherby-Swift hardening curve model.

    This model is a combination of the Hocket-Sherby and Swift hardening models. The weight of each model's
    contribution is determined by the `alpha` parameter, set by default to 0.75.

    Args:
        eps_pl (np.ndarray[float]): Array of the plastic strains where the model should be interrogated.
        sig_i (float): sig_i model parameter
        sig_sat (float): sig_sat model parameter
        a (float): a model parameter
        p (float): p model parameter
        C (float): C model parameter
        eps_0 (float): eps_0 model parameter
        m (float): m model parameter

    Returns:
        np.ndarray[float]: Array of equivalent stress for the input plastic strains
    """
    hss = alpha*hocket_sherby(eps_pl, sig_i, sig_sat, a, p) + \
        (1-alpha)*swift(eps_pl, C, eps_0, m)
    return hss
