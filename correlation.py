#!/usr/bin/env python
#title				: correlation.py
#description		: Establishes EM - LM correlation and correlates spots between EM and LM
#author				: Vladan Lucic (Max Planck Institute for Biochemistry)
#email				: 
#credits			: 
#maintainer			: Vladan Lucic
#date				: 2015/10
#version			: 0.1
#status				: developement
#usage				: import correlation.py and call main(markers_3d,markers_2d,spots_3d,rotation_center,results_file)
#					: "markers_3d", "markers_2d" and "spots_3d" are numpy arrays. Those contain 3D coordinates
#					: (arbitrary 3rd dimension for the 2D array). Marke rcoordinates are for the correlation and spot
#					: coordinates are points on which the correlation is applied to.
#notes				: Edited and adapted by Jan Arnold (Max Planck Institute for Biochemistry)
#python_version		: 2.7.10 
#=================================================================================

import sys
import math
import os
import numpy as np
import scipy as sp

import pyto
import pyto.scripts.common as common
from pyto.geometry.rigid_3d import Rigid3D

########## Functions #############################################################
##################################################################################

def write_results(
		transf, res_file_name, spots_3d, spots_2d, 
		markers_3d, transformed_3d, markers_2d,rotation_center,modified_translation):
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
		"#   - rotation (Euler phi, psi, theta): [%6.3f, %6.3f, %6.3f]" \
			% (eulers[0], eulers[2], eulers[1]),
		"#   - scale = %6.3f" % transf.s_scalar,
		"#   - translation for rotationaround [0,0,0] = [%6.3f, %6.3f, %6.3f]" \
			 % (transf.d[0], transf.d[1], transf.d[2]),
		"#   - translation for rotationaround [%5.2f, %5.2f, %5.2f] = [%6.3f, %6.3f, %6.3f]" \
			 % (rotation_center[0], rotation_center[1], rotation_center[2],
			 	modified_translation[0], modified_translation[1], modified_translation[2]),
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
		"#	Initial (3D) markers		Transformed initial"
		 + "		Final (2D) markers	Transformed-Final"])
	out_vars = [markers_3d[0,:], markers_3d[1,:], markers_3d[2,:], 
				transformed_3d[0,:], transformed_3d[1,:], transformed_3d[2,:],
				markers_2d[0,:], markers_2d[1,:], transformed_3d[0,:]-markers_2d[0,:], transformed_3d[1,:]-markers_2d[1,:]]
	out_format = '	%7.2f	%7.2f	%7.2f		%7.2f	%7.2f	%7.2f		%7.2f	%7.2f		%7.2f	%7.2f'
	ids = range(markers_3d.shape[1])
	res_tab_markers = pyto.io.util.arrayFormat(
		arrays=out_vars, format=out_format, indices=ids, prependIndex=False)
	table.extend(res_tab_markers)

	# prepare data lines
	if spots_3d.shape[0] != 0:
		table.extend([
			"#",
			"#",
			"# Correlation of 3D spots (POIs) to 2D",
			"#",
			"#	Spots (3D)			Correlated spots"])
		out_vars = [spots_3d[0,:], spots_3d[1,:], spots_3d[2,:], 
					spots_2d[0,:], spots_2d[1,:], spots_2d[2,:]]
		out_format = '	%6.0f	%6.0f	%6.0f		%7.2f	%7.2f	%7.2f'
		ids = range(spots_3d.shape[1])
		res_tab_spots = pyto.io.util.arrayFormat(
			arrays=out_vars, format=out_format, indices=ids, prependIndex=False)
		table.extend(res_tab_spots)

	# write data table
	for line in table:
		res_file.write(line + os.linesep)


########## Main ##################################################################
##################################################################################

def main(markers_3d,markers_2d,spots_3d,rotation_center,results_file):

	random_rotations = True
	rotation_init = 'gl2'
	restrict_rotations = 0.1
	scale = None
	random_scale = True
	scale_init = 'gl2'
	ninit = 10

	# read fluo markers 
	mark_3d = markers_3d[range(markers_3d.shape[0])].transpose()

	# read ib markers
	mark_2d = markers_2d[range(markers_2d.shape[0])][:,:2].transpose()

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

	# fluo spots
	spots_3d = spots_3d[range(spots_3d.shape[0])].transpose()

	# correlate spots
	if spots_3d.shape[0] != 0:
		spots_2d = transf.transform(x=spots_3d)
	else:
		spots_2d = None

	# transform markers
	transf_3d = transf.transform(x=mark_3d)

	# calculate translation if rotation center is not at (0,0,0)
	modified_translation = transf.recalculate_translation(
		rotation_center=rotation_center)
	#print 'modified_translation: ', modified_translation

	# write transformation params and correlation
	write_results(
		transf=transf, res_file_name=results_file, 
		spots_3d=spots_3d, spots_2d=spots_2d,
		markers_3d=mark_3d, transformed_3d=transf_3d, markers_2d=mark_2d,
		rotation_center=rotation_center, modified_translation=modified_translation)
	cm_3D_markers = mark_3d.mean(axis=-1).tolist()
	
	# delta calc,real
	delta2D = transf_3d[:2,:] - mark_2d
	return [transf, transf_3d, spots_2d, delta2D, cm_3D_markers, modified_translation]


