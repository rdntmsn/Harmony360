"""Harmony360 canonical runtime constants.

Historical approximations are preserved explicitly for lineage rather than
silently treated as current physical constants.
"""

import math

PHI = (1 + math.sqrt(5.0)) / 2.0
PI = math.pi

# 2022 CODATA recommended fine-structure constant.
ALPHA = 7.2973525643e-3

# Historical Harmony360 approximation retained for reproducibility/lineage.
ALPHA_LEGACY = 1.0 / 137.0

PLANCK_LENGTH = 1.616255e-35
HBAR = 1.054571817e-34
C = 299_792_458.0
