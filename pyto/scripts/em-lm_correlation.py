#!/usr/bin/env python
"""
Light microscopy - electron microscopy correlation

This script may be placed anywhere in the directory tree.

$Id: em-lm_correlation.py 25 2007-12-29 20:14:24Z vladan $
Author: Vladan Lucic 
"""
__version__ = "$Revision: 25 $"

import numpy
import pyto

# marker coordinates in EM
marker_em = [[100, 200],
             [100, 240],
             [150, 240],
             [150, 200]]

# marker coordinates in grid frame
merker_grid = [[2,5],
               [3,5],
               [3,4],
               [2,4]]

# find EM-grid transformation
grid2em = pyto.geometry.Transformation.findGM(x=marker_grid, y=marker_em)

# print error

# marker coordinates on a LM image
marker_lm = [[100, 200],
             [120, 200],
             [120, 220],
             [100, 220]]

# find LM to EM transformation
lm2em = pyto.geometry.Transformation.gindGM(x=marker_lm, y=marker_em)

# print error

# interesting LM positions
lm_spots = [[105, 210],
            [110, 215]]

# find EM coordinates of LM spots
em_correlated = lm2em.transform(lm_spots)
# print

# interesting EM positions
em_spots = [[100, 220],
            [130,240]]

# find LM coordinates of EM spots
lm_correlated = lm2em.inverse().transform(em_spots)
# print
