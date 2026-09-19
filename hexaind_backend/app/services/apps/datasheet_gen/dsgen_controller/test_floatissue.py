
from dataclasses import dataclass, field

from typing import List

import numpy as np
import datetime

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
    E: float = field(default_factory=np.nan)
    Rp02: float = field(default_factory=np.nan)
    Rm: float = field(default_factory=np.nan)
    Ag: float = field(default_factory=np.nan)
    A80: float = field(default_factory=np.nan)



dict_result = {'E': 68.61434719261176, 'Rp02': 119.91451577422876, 'Rm': 241.61644853215, 'Ag': 22.48011461571508, 'A80': 27.064179248961302, 'r4_6': 0.6841514042269405, 'r8_12': 0.683442129101711, 'r2_20': 0.6931230143598014, 'r10_15': 0.686096110884461, 'n4_6': 0.2977861377069765, 'n10_15': 0.2695490568485791, 'n10_20': 0.2558814122707837, 'n2_20': 0.2831241188011867}
# tdict = TensileResults(**dict_result)
# print(tdict)