from pathlib import Path
from decouple import config

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from shapely.geometry import LineString

# TODO: Implement this in some global configuration file
IMPORT_PATH = './Data import/datasheet_import/'
# IMPORT_PATH = Path(config('IMPORT_PATH'))


###############################
#    Mechanical Properties    #
###############################
def compute_elastic_modulus(e, s, s_min, s_max):

    assert e.size == s.size

    idx_lin = np.asarray((s > s_min) & (s < s_max))

    # Fit the Elastic Modulus for e and s in the desired range

    E, E_c = np.polyfit(
        e[idx_lin],
        s[idx_lin],
        1,
    )

    return E, E_c


def compute_poisson_ratio(e_lat, s, E, s_min, s_max):

    assert e_lat.size == s.size

    idx_lin = np.asarray((s > s_min) & (s < s_max))

    # Fit the Elastic Modulus for e and s in the desired range

    m_fit, n_fit = np.polyfit(
        s[idx_lin],
        e_lat[idx_lin],
        1,
    )

    nu = m_fit * E

    return nu, n_fit


def compute_Rp02(e, s, E):

    # 0.2% Plastic deformation line
    e_02 = 0.2/100
    pt1 = (e_02, 0)  # Intersection with the x-axis at 0.2% plastic deformation
    pt2 = (e.max(), E * (e.max() - e_02))

    line_el = LineString([pt1, pt2])  # Line of elastic return
    line_es = LineString([(x, y) for x, y in zip(e, s)])  # Engineering stress/strain curve

    intersection = line_es.intersection(line_el)  # Intersection of engineering stress/strain curve with elastic return
    pts_intersection = np.array(intersection.xy)

    if pts_intersection.shape == (2, 1):
        Rp02 = float(pts_intersection[1, 0])
    elif pts_intersection.shape[1] > 1:
        raise ArithmeticError("0.2% plastic deformation line has multiple intersection with the engineering stress/strain curve")
    else:
        raise ArithmeticError("0.2% plastic deformation line does not intersect the engineering stress/strain curve")

    return Rp02


def compute_Agt_Rm(e, s):

    # # The naive way: look for max
    # idx_max = np.argmax(s)

    # Agt = e[idx_max]
    # Rm = s[idx_max]

    # The better way: first filter the signal to remove false peaks
    ehat = savgol_filter(e, 69, 3)
    shat = savgol_filter(s, 69, 3)

    idx_max = np.argmax(shat)

    Agt = ehat[idx_max]
    Rm = shat[idx_max]

    return Agt, Rm


def compute_Ag(E, Agt, Rm):

    Ag = Agt - Rm/E

    return Ag


def compute_bulge_scaling_factor(E, Rm, Ag, sig_1, eps_1):

    df_bulge_comp = pd.DataFrame(
        {
            'sig_1': sig_1,
            'eps_1': eps_1,
        }
    )
    sig_ag = Rm * (1 + Ag + Rm/E)
    eps_pl_ag = np.log(1 + Ag + Rm/E) - sig_ag/E

    # Compute the sig*eps error
    np_err = np.array(df_bulge_comp['sig_1'] * df_bulge_comp['eps_1'] - sig_ag * eps_pl_ag)
    df_bulge_comp.loc[:, 'sig_eps_err'] = np_err

    # Find the rising edge(s) of the error
    np_rising = np.where((np.sign(np_err[:-1]) == -1) & (np.sign(np_err[1:]) == 1), 1, np.nan)
    # Insert a np.nan in the begining
    np_rising = np.insert(np_rising, 0, np.nan)
    df_bulge_comp.loc[:, 'k_rising'] = np_rising

    # Interpolate sig_eps_err intersection point
    np_err_intpl = (0 - np_err[:-1]) / (np_err[1:] - np_err[:-1])

    # df_bulge_comp.loc[:, 'err_intpl'] = np.where(np_rising == 1, np.insert(np_err_intpl, 0, 0), np.nan)
    df_bulge_comp.loc[:, 'err_intpl'] = np.insert(np_err_intpl, 0, 0)

    # Interpolated value of sig_1 at err_k = 0
    np_sig1 = df_bulge_comp['sig_1'].values
    np_sig_intpl = np.array(np_sig1[:-1] + np_err_intpl * (np_sig1[1:] - np_sig1[:-1]))
    np_sig_intpl = np.insert(np_sig_intpl, 0, np.nan)

    # Interpolated value of eps_1 at err_k = 0
    np_eps1 = df_bulge_comp['eps_1'].values
    np_eps_intpl = np.array(np_eps1[:-1] + np_err_intpl * (np_eps1[1:] - np_eps1[:-1]))
    np_eps_intpl = np.insert(np_eps_intpl, 0, np.nan)

    df_bulge_comp.loc[:, 'eps_ref'] = np_rising * np_eps_intpl
    df_bulge_comp.loc[:, 'sig_ref'] = np_rising * np_sig_intpl

    df_bulge_comp.loc[:, 'k'] = sig_ag/df_bulge_comp['sig_ref']

    k = df_bulge_comp['k'].mean()

    return k


def compute_df_tensile_values(df_data_sample, df_results):

    df_tensile_computed = df_data_sample.copy()

    E = df_results['E'].values
    E_c = df_results['E_c'].values

    # Toe compensation
    e = df_tensile_computed['e']
    e_toe = e + E_c/E
    df_tensile_computed.loc[:, 'e_toe'] = e_toe

    # Compute true stress/strain
    eps = np.log(1 + e_toe)
    df_tensile_computed.loc[:, 'eps'] = eps

    s = df_tensile_computed['s']
    sig = s * (1 + e_toe)
    df_tensile_computed.loc[:, 'sig'] = sig

    # plastic strain
    eps_pl = eps - sig/E
    df_tensile_computed.loc[:, 'eps_pl'] = eps_pl

    return df_tensile_computed
