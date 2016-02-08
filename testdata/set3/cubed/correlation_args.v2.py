#!/usr/bin/python

#

import pdb

import argparse
import sys
import math

import os
import numpy as np
import scipy as sp

import pyto
import pyto.scripts.common as common
from pyto.geometry.rigid_3d import Rigid3D

# Parsing arguments

parser = argparse.ArgumentParser(description="""Establishes a correlation based on the 3D rigid body transformation 
(rotation, scale and translation) when marker positions are specified as 3D coordinates in the initial system and 2D coordinates (z component is missing) in the final system.

Typically the initial (3D) system is a light micrroscopy (confocal) image 
and the final (2D) is a ion beam image.""")

parser.add_argument('--f3D', metavar='coord_3D', help='Path to 3D marker coordinates file (confocal volume)', required=True)
parser.add_argument('--r3D', metavar='rows_3D', nargs='*', type=int, help='Rows in 3D file used for correlation. For using all rows, do not specify this parameter.')

parser.add_argument('--f2D', metavar='coord_2D', help='Path to 2D marker coordinates file (FIB)', required=True)
parser.add_argument('--r2D', metavar='rows_2D', nargs='*', type=int, help='Rows in 2D file used for correlation. For using all rows, do not specify this parameter.')

parser.add_argument('--feat', metavar='coord_feature', nargs='*', type=int, default=[], help='Rows in 3D file with feature coordinates.')
parser.add_argument('--rot', metavar='rot_center', nargs='*', type=int, default=[672, 672, 672], help='tom_rot rotation center to calculate correct translation.')
parser.add_argument('--resultspath', metavar='results_path', default=["./"], help='Path to where the reults should be saved to.')

args = parser.parse_args()

print("=")*25, ;print("Arguments"),;print("=")*25
#print(vars(args))
print(args.f3D)
print(args.f2D)
print(args.r3D)
print(args.r2D)
print(args.feat)
print("=")*61
##################################################################
#
# Parameters
#
#################################################################

##################################################################
#
# Markers
#

# initial (3D) markers file name 
markers_3d_file = args.f3D

# rows where 3D markers are; rows numbered from 0, top (info) row skipped
#marker_3d_rows = [3, 7, 10, 11, 12, 17, 20, 21]
if args.r3D == None:
	marker_3d_rows = []
	with open(markers_3d_file,"r") as f:
		for i in range(0, sum(1 for line in f)-1):
			marker_3d_rows.append(i)
else:
	marker_3d_rows = args.r3D

# final (2D) markers file name
markers_2d_file = args.f2D

# rows where 2D markers are, rows numbered from 0, top (info) row skipped
#marker_2d_rows = [6, 8, 9, 13, 14, 16, 18, 19]
if args.r2D == None:
	marker_2d_rows = []
	with open(markers_2d_file,"r") as f:
		for i in range(0, sum(1 for line in f)-1):
			marker_2d_rows.append(i)
else:
	marker_2d_rows = args.r2D

# pdb.set_trace()
##################################################################
#
# Spots to be correlated
#

# spots (3D) file name
spots_3d_file = markers_3d_file

# rows where spots are, rows numbered from 0, top (info) row skipped
spot_3d_rows = args.feat

##################################################################
#
# Results
#

# results file name
# results_file = 'correlation.dat'
results_file = ''.join([args.resultspath, '_correlation.txt'])

##################################################################
#
# Initial conditions and optimization
#

# do multiple optimization runs with different initial rotation (True / False)
random_rotations = True

# initial rotation specified by Euler angles:
#   phi, theta, psi, extrinsic, 'X' or 'ZXZ' mode in degrees
# uncomment one of the following
#rotation_init = None            # use default rotation
#rotation_init = [23, 45, 67]   # specified rotation angles
rotation_init = 'gl2'            # use 2d affine to get initial rotation

# restrict random initial rotations to a neighborhood of the initial rotation
# used if rotation_init is is specified by angles or it is '2d'
# should be < 0.5, value 0.1 roughly corresponds to 15 deg
restrict_rotations = 0.1   

# optimze of fix fluorescence to ib magnification 
# uncomment one of the following
scale = None    # optimize 
#scale = 150.   # fixed scale, no optimization

# do multiple optimization runs with different initial scale (True / False)
random_scale = True

# initial value for fluorescence to ib magnification, used only if scale=None
#scale_init = 1.               # specified value
scale_init = 'gl2'            # use 2d transform to get init scale

# number of optimization runs, each run has different initial values;
# first run has initial conditions specified by rotation_init and scale_init
# (uncomment one of the following)
#ninit = 1    # one run only (two runs if rotation_init is '2d') 
ninit = 10    # multiple runs, random_rotations or random_scale should be True

##################################################################
#
# File format related
#

# comment symbol
comments=None

# number of top rows to skip
skiprows=1

# filed delimiter
delimiter='\t'

# x, y and z coordinate columns, in this order
usecols=[1, 2, 3]

# alternative (more flexible) form to specify columns
# not implemented yet
dtype = {
    'names' : ('id', 'label', 'density', 'x', 'y', 'z'), 
    'formats' : ('i', 'a40', 'f', 'f', 'f', 'i')}
fmt = ('%4i', '%s', '%9.3f', '%7.1f', '%7.1f', '%7.1f')


#####################################################################
#
# Functions
#
#####################################################################

# ToDo pick rows by order or by index

# print transformation params
def write_results(
        transf, res_file_name, spots_3d, spots_2d, 
        markers_3d, transformed_3d, markers_2d):
    """
    """

    # open results file
    res_file = open(res_file_name, 'w')
    
    # header top
    header = common.make_top_header()

    # extract eulers in degrees
    eulers = transf.extract_euler(r=transf.q, mode='x', ret='one') 
    eulers = eulers * 180 / np.pi

    # correlation parameters
    header.extend([
        "#",
        "# Transformation parameters",
        "#",
        "#   - rotation (Euler phi, theta psi): [%6.3f, %6.3f, %6.3f]" \
            % (eulers[0], eulers[1], eulers[2]),
        "#   - scale = %6.3f" % transf.s_scalar,
        "#   - translation = [%6.3f, %6.3f, %6.3f]" \
             % (transf.d[0], transf.d[1], transf.d[2]),
        "#   - rms error (in 2d pixels) = %6.2f" % transf.rmsError
        ])

    # check success
    if transf.optimizeResult['success']:
        header.extend([
            "#   - optimization successful"])
    else:
        header.extend([
            "#",
            "# ERROR: Optimization failed (status %d)" \
                % transf.optimizeResult['status'],
            "#   Repeat run with changed initial values and / or "
            + "increased ninit"])

    # write header
    for line in header:
        res_file.write(line + os.linesep)

    # prepare marker lines
    table = ([
        "#",
        "#",
        "# Transformation of initial (3D) markers",
        "#",
        "#  Initial (3D) markers      Transformed initial"
         + "     Final (2D) markers "])
    out_vars = [markers_3d[0,:], markers_3d[1,:], markers_3d[2,:], 
                transformed_3d[0,:], transformed_3d[1,:], transformed_3d[2,:],
                markers_2d[0,:], markers_2d[1,:]]
    out_format = '  %6.0f %6.0f %6.0f     %7.2f %7.2f %7.2f     %7.2f %7.2f  '
    ids = range(markers_3d.shape[1])
    res_tab_markers = pyto.io.util.arrayFormat(
        arrays=out_vars, format=out_format, indices=ids, prependIndex=False)
    table.extend(res_tab_markers)

    # prepare data lines
    table.extend([
        "#",
        "#",
        "# Correlation of 3D spots to 2D",
        "#",
        "#       Spots (3D)             Correlated spots"])
    out_vars = [spots_3d[0,:], spots_3d[1,:], spots_3d[2,:], 
                spots_2d[0,:], spots_2d[1,:], spots_2d[2,:]]
    out_format = '  %6.0f %6.0f %6.0f     %7.2f %7.2f %7.2f '
    ids = range(spots_3d.shape[1])
    res_tab_spots = pyto.io.util.arrayFormat(
        arrays=out_vars, format=out_format, indices=ids, prependIndex=False)
    table.extend(res_tab_spots)

    # write data table
    for line in table:
        res_file.write(line + os.linesep)


#####################################################################
#
# Main
#
#####################################################################


def main():

    # read fluo markers 
    mark_3d_all = np.loadtxt(
        markers_3d_file, delimiter=delimiter, 
        comments=comments, skiprows=skiprows, usecols=usecols)
    mark_3d = mark_3d_all[marker_3d_rows].transpose()

    # alternative 
    #mark_3d = np.loadtxt(
    #    markers_3d_file, delimiter=delimiter, comments=comments, 
    #    skiprows=skiprows, usecols=usecols, dtype=dtype)
    
    # read ib markers 
    mark_2d_whole = np.loadtxt(
        markers_2d_file, delimiter=delimiter, 
        comments=comments, skiprows=skiprows, usecols=usecols)
    mark_2d = mark_2d_whole[marker_2d_rows][:,:2].transpose()

    # convert Eulers in degrees to Caley-Klein params
    if (rotation_init is not None) and (rotation_init != 'gl2'):
        rotation_init_rad = rotation_init * np.pi / 180
        einit = Rigid3D.euler_to_ck(angles=rotation_init_rad, mode='x')
    else:
        einit = rotation_init

    # establish correlation
    transf = pyto.geometry.Rigid3D.find_32(
        x=mark_3d, y=mark_2d, scale=scale, 
        randome=random_rotations, einit=einit, einit_dist=restrict_rotations, 
        randoms=random_scale, sinit=scale_init, ninit=ninit)

    # read fluo spots 
    spots_3d = np.loadtxt(
        spots_3d_file, delimiter=delimiter, 
        comments=comments, skiprows=skiprows, usecols=usecols)
    spots_3d = spots_3d[spot_3d_rows].transpose()

    # correlate spots
    spots_2d = transf.transform(x=spots_3d)

    # transform markers
    transf_3d = transf.transform(x=mark_3d)

    # calculate translation if rotation center is not at (0,0,0)
    rotation_center = args.rot
    # rotation_center = [770, 770, 770]
    # rotation_center = [770, 626.5, 53.5]
    # rotation_center = [770, 626.5, 53.5]
    modified_translation = transf.recalculate_translation(
        rotation_center=rotation_center)
    #print 'modified_translation: ', modified_translation

    # write transformation params and correlation
    write_results(
        transf=transf, res_file_name=results_file, 
        spots_3d=spots_3d, spots_2d=spots_2d,
        markers_3d=mark_3d, transformed_3d=transf_3d, markers_2d=mark_2d)
    cm_3D_markers = mark_3d.mean(axis=-1).tolist()
#    pdb.set_trace()
    return [transf, spots_3d, spots_2d, cm_3D_markers,modified_translation]

# run if standalone
if __name__ == '__main__':
    output = main()
    transf = output[0]
    spots_3d = output[1]
    calc_spots_2d = output[2]
    cm_3D_markers = output[3]
    modified_translation = output[4]
#    pdb.set_trace()
    with open(markers_2d_file,"r") as f:
    	i=0
    	real_spots2d = []
    	for line in f:
			if i == int(args.feat[0])+1:
				for word in line.split():
					real_spots2d.append(word)
			i = i+1
    with open(".cache.dat","w") as f:
# 		f.write(str(output.rmsError))
		f.write("%f	%f	%f	%f	%f	%f	%f	%f	%f	%f	%f	%f	%f	%s" % (float(transf.rmsError), \
		float(calc_spots_2d[0,:]), float(calc_spots_2d[1,:]), \
		float(real_spots2d[1]), float(real_spots2d[2]), \
		float(calc_spots_2d[0,:])-float(real_spots2d[1]), float(calc_spots_2d[1,:])-float(real_spots2d[2]), \
		float(spots_3d[0,:]), float(spots_3d[1,:]), float(spots_3d[2,:]), \
		cm_3D_markers[0], cm_3D_markers[1], \
		math.sqrt(math.pow(abs(float(real_spots2d[1])-cm_3D_markers[0]),2)+math.pow(abs(float(real_spots2d[2])-cm_3D_markers[1]),2)), \
		str(modified_translation) \
		))

#pdb.set_trace()
