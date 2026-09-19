"""Module containing the dataclasses for all the mechanical tests.

This module contains the definition of the dataclasses used in the flows when
compiling and passing around the experimental data for the mechanical tests.

"""

from dataclasses import dataclass, field

from typing import List

import numpy as np
import datetime

#####################
#   Tensile Tests   #
#####################


@dataclass
class TensileMetadata:
    """Dataclass containing the metadata of a Tensile Test.

    The fields are based on the data available from the Zwick exports.
    """
    test_procedure: str
    datasheet: int
    test_lab: str
    lab_ref: str
    test_date: datetime.datetime
    operator: str
    age: int
    pretreatment: str
    sample_geometry: str

    sample_name: str = field(default_factory=None)
    load_direction: float = field(default_factory=None)


@dataclass
class TensileGeometry:
    """Dataclass for the initial geometry of a Tensile Sample.

    This class contains the fields for the initial length, width, thickness
    of the Tensile Sample (assumed to have A90 shape).
    """
    L0: float       # Initial length
    a0: float       # Initial width
    b0: float       # Initial thickness


@dataclass
class TensileResults:
    """Dataclass containing the results of a Tensile Test.

    This dataclass is used both to keep track of the Zwick results
    and the manually recomputed results, in which case different fields
    will be populated.

    As a convention, the units of all the variables are SI units
    (eg. the Elastic Modulus `E` is represented in Pa)

    The first fields, lacking default_factory values are mandatory, while the other
    fields are optional.
    """
    Rp02: float
    Rm: float = field(default=np.nan)
    Ag: float = field(default=np.nan)
    A80: float = field(default=np.nan)

    E: float = field(default=np.nan)      # Elastic modulus
    E_c: float = field(default=np.nan)    # Elastic modulus intercept

    nu: float = field(default=np.nan)     # Poisson ratio
    nu_c: float = field(default=np.nan)    # Poisson ratio intercept

    r4_6: float = field(default=np.nan)
    r8_12: float = field(default=np.nan)
    r2_20: float = field(default=np.nan)
    r10_15: float = field(default=np.nan)
    n4_6: float = field(default=np.nan)
    n10_15: float = field(default=np.nan)
    n10_20: float = field(default=np.nan)
    n2_20: float = field(default=np.nan)


    @property
    def Agt(self) -> float:
        return self.Ag + self.Rm/self.E


@dataclass
class TensileResult:
    """Dataclass containing the results of a Tensile Test.

    This dataclass is used both to keep track of the Zwick results
    and the manually recomputed results, in which case different fields
    will be populated.

    As a convention, the units of all the variables are SI units
    (eg. the Elastic Modulus `E` is represented in Pa)

    The first fields, lacking default_factory values are mandatory, while the other
    fields are optional.
    """
    Rp02: float
    Rm: float = field(default_factory=np.nan)
    Ag: float = field(default_factory=np.nan)
    A80: float = field(default_factory=np.nan)

    E: float = field(default_factory=np.nan)      # Elastic modulus
    E_c: float = field(default_factory=np.nan)    # Elastic modulus intercept

    nu: float = field(default_factory=np.nan)     # Poisson ratio
    nu_c: float = field(default_factory=np.nan)    # Poisson ratio intercept

    r4_6: float = field(default_factory=np.nan)
    r8_12: float = field(default_factory=np.nan)
    r2_20: float = field(default_factory=np.nan)
    r10_15: float = field(default_factory=np.nan)
    n4_6: float = field(default_factory=np.nan)
    n10_15: float = field(default_factory=np.nan)
    n10_20: float = field(default_factory=np.nan)
    n2_20: float = field(default_factory=np.nan)

    @property
    def Agt(self) -> float:
        return self.Ag + self.Rm/self.E


@dataclass
class TensileTest:
    pass

@dataclass
class ZwickTestSheet:
    pass

@dataclass
class TensileData:
    """Dataclass containing the raw experimental measurements and stress/strains.

    This class contains the raw experimental measurements in the mandatory fields
    and the computed stress/strain values in the optional fields.
    """
    time: np.ndarray                                     # Time since start of experiment [s]
    delta_l: np.ndarray                                  # Change in length from the initial sample size [mm]
    delta_b: np.ndarray                                  # Change in thickness from the initial sample size [mm]
    load: np.ndarray                                     # Load on the sample [N]

    s: np.ndarray = field( default=None)            # Engineering stress
    e: np.ndarray = field( default=None)            # Engineering strain
    e_lat: np.ndarray = field( default=None)        # Lateral engineering strain
    e_toe: np.ndarray = field( default=None)        # Toe compensated engineering strain
    e_lat_toe: np.ndarray = field( default=None)    # Toe compensated engineering lateral strain
    eps: np.ndarray = field( default=None)          # True strain (computed using e_toe)
    sig: np.ndarray = field( default=None)          # True stress
    eps_pl: np.ndarray = field( default=None)       # True plastic strain
    eps_lat: np.ndarray = field( default=None)      # True lateral strain
    eps_lat_pl: np.ndarray = field( default=None) 
    # s: np.ndarray = field(default=np.empty(0))            # Engineering stress
    # e: np.ndarray = field(default=np.empty(0))            # Engineering strain
    # e_lat: np.ndarray = field(default=np.empty(0))        # Lateral engineering strain
    # e_toe: np.ndarray = field(default=np.empty(0))        # Toe compensated engineering strain
    # e_lat_toe: np.ndarray = field(default=np.empty(0))    # Toe compensated engineering lateral strain
    # eps: np.ndarray = field(default=np.empty(0))          # True strain (computed using e_toe)
    # sig: np.ndarray = field(default=np.empty(0))          # True stress
    # eps_pl: np.ndarray = field(default=np.empty(0))       # True plastic strain
    # eps_lat: np.ndarray = field(default=np.empty(0))      # True lateral strain
    # eps_lat_pl: np.ndarray = field(default=np.empty(0))   # True plastic lateral strain

    # time: np.ndarray                                     # Time since start of experiment [s]
    # delta_l: np.ndarray                                  # Change in length from the initial sample size [mm]
    # delta_b: np.ndarray                                  # Change in thickness from the initial sample size [mm]
    # load: np.ndarray                                     # Load on the sample [N]

    # s: np.ndarray            # Engineering stress
    # e: np.ndarray            # Engineering strain
    # e_lat: np.ndarray         # Lateral engineering strain
    # e_toe: np.ndarray        # Toe compensated engineering strain
    # e_lat_toe: np.ndarray    # Toe compensated engineering lateral strain
    # eps: np.ndarray          # True strain (computed using e_toe)
    # sig: np.ndarray          # True stress
    # eps_pl: np.ndarray       # True plastic strain
    # eps_lat: np.ndarray      # True lateral strain
    # eps_lat_pl: np.ndarray   # True plastic lateral strain

@dataclass
class TensileSample:
    """Dataclass combining all the other dataclasses related to the Tensile Test.

    This dataclass combines all the other dataclasses related to the Tensile Test.
    This class is used to pass around data in the tensile etl workflow, in order to keep track
    of the individual tensile tests.
    """
    datasheet: int
    nominal_age: int
    file_name: str
    sha256_hash: str

    metadata: TensileMetadata
    initial_geometry: TensileGeometry
    original_results: TensileResults
    recomputed_results: TensileResults
    data: TensileData

#####################
#    Bulge Tests    #
#####################


@dataclass
class BulgeMetadata:
    """Dataclass containing the metadata for the Bulge Test.

    This dataclass is based on the data available in the ASCII export of the Bulge Tests.
    All the fields are considered mandatory since they are all present in the Aramis exports.
    """
    test_date: datetime.datetime
    material: str
    initial_thickness: float                    # Initial thickness [mm]
    grid_spacing: float                         # Estimated grid spacing [mm]

    d_die: float
    r_1: float
    r_2: float

    type_geom: str                              # Type of geometry for shape fit
    type_pole: str                              # Type of pole's strain evaluation
    type_selection: str                         # Type of selection

    el_str_comp: str                            # Elastic strain compensation
    E: float                                    # Young's Modulus
    nu: float                                   # Poisson's Ratio

    ben_str_comp: str                           # Bending strain compensation
    rad_comp: str                               # Radius compensation

    str_rate_comp: str                          # Strain rate compensation
    C: float
    p: float
    fit_width: float

    extend_uniaxial_curve: str                  # Extend uniaxial yield curve
    ts_test_yield_curve_file: str               # Tensile test yield curve file
    true_strain_col: str                        # True strain column
    true_stress_col: str                        # True stress column
    biaxial_stress_ratio: float                 # Bi-axial stress ratio

    columns: List[str]
    header_rows: int


@dataclass
class BulgeData:
    """Dataclass containing the raw experimental measurements and stress/strains.

    This class contains the raw experimental measurements in the mandatory fields
    and the computed scaled stress/strain values in the optional fields.
    """
    exp_time: np.ndarray
    radius: np.ndarray
    pressure: np.ndarray

    eps_1: np.ndarray
    sig_1: np.ndarray

    eps_sc: np.ndarray = field(default=None)
    sig_sc: np.ndarray = field(default=None)


@dataclass
class BulgeSample:
    """Dataclass combining all the other dataclasses related to the Bulge Test.

    This dataclass combines all the other dataclasses related to the Bulge Test.
    This class is used to pass around data in the bulge etl workflow, in order to keep track
    of the individual bulge tests.
    """
    datasheet: int
    nominal_age: int
    file_name: str
    sha256_hash: str

    metadata: BulgeMetadata
    data: BulgeData
    scaling_factor: float = field(default=None)
