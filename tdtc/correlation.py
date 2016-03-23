#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Establishes 2D to 3D correlation and correlates spots (Point of Interests) between e.g. EM and LM

The procedure is organized as follows:

	1) Find transformation between LM and EM overview systems using specified
	markers. LM markers are typically specified as (coordinates of) features on a
	LM image, and overview markers (as coordinates) of the same features on a low
	mag EM image (so that the whole gid square fits on this image, such as 220x).

	This transformation is an affine transformation in 2D, that is it is composed
	of a Gl (general linear) transformation and a translation. The Gl
	transformation can be decomposed into rotation, scaling along two principal
	axes, parity (flipping one axis) and shear. The LM - overview transformation
	can be calculated in two ways:

		(a) Direct: Markers lm_markers and overview_markers need to correspond to
		the same spots, the transformation is calculated directly

		(b) Separate gl and translation:  Markers lm_markers_gl and
		overview_markers_gl have to outline the same shape in the same orientation
		but they need not don't need to be the same spots, that is they can have a
		fixed displacement. For example, holes on a quantifoil can be used for this
		purpose. These parameters are used to find the Gl transformation. In the
		next step, parameters lm_markers_d and overview_markers_d are used to
		calculate only the translation.

	2)  Find transformation between EM overview and EM search systems using
	(overview and search) markers (here caled details). The transformation is
	also affine, but it can be restricted so that instead of the full Gl
	transformation only orthogonal transformation is used (rotation, one scaling
	and parity). The EM overview system has to have the same mag as the one used
	for the LM - overview transformation, while the search system can be chosen
	in a different way:

		(a) Collage: A collage of medium mag EM images (image size around 10 um) is
		used as a search system and the same overview image as the one used for
		the LM - overview transformation. The markers (details) are simply
		identified (as coordinates) of features found in these images
		(overview_detail and search_detail). Parameter overview2search_mode has to
		be set to 'move search'. This is conceptually the simplest method, but
		assembling the EM image collage might take some time or not be feasible.

		(b) Stage, move search: The same overview image as the one used for
		the LM - overview transformation is used for the overview system, but the
		stage movement system is used for the search system. Specifically, for each
		detail (markers for this transformation) found on the overview image, the
		EM stage needs to be moved so that the same feature is seen in the center
		of the EM image made at a medium mag (image size typically up to 10 um).
		The stage coordinates are used as search details. Parameter
		overview2search_mode has to be set to 'move search'. The difficulty here is
		to find enough features that are seen in the overview image but can be
		easily navigated to in search (cracks in ice are often used).

		(c) Stage, move overview: First one feature needs to be identified on the
		overview image used for the LM - overview transformation. The coordinates
		of that feature are used as one marker (search_detail) and the EM stage
		coordinates for that image is the corresponding search marker
		(search_detail). This particular stage position has also to be specified
		as search_main parameter. The other markers are obtained by moving the
		stage around (typically 10 - 20 um) and making overview at these positions.
		Coordinates of the feature at overview images, and the corresponding
		stage coordinates are used as overview and stage markers. Naturally, the
		feature has to be present in all overview images. Parameter
		overview2search_mode has to be set to 'move overview'. This is perhaps the
		easiest method to use, but conceptually the most difficult.

	3) Calculates transformation between LM and search systems as a composition of
	the LM - overview and overview - search transforms

	4) Correlates spots specified in one system to the other systems. Coordinates
	of spots correlated to search system are interpreted according to the method
	used to establish the overview - search transformation (see point 2)

		(a) Collage: Spots in search system are simply the coordinates in the
		collage used for the overview - search transformation.

		(b) Stage, move search: Correlated spots are stage coordinates where
		spots are located in the center of search images (medium mag).

		(c) Stage, move overview: Correlated spots are stage coordinates. An search
		image made at this stage position (low mag) contains the spot at the
		coordinate specified by parameter overview_center.

# @Title			: correlation
# @Project			: 3DCTv2
# @Description		: Establishes EM - LM correlation and correlates spots between EM and LM
# @Author			: Vladan Lucic (Max Planck Institute for Biochemistry)
# @Email			:
# @Credits			:
# @Maintainer		: Vladan Lucic, Jan Arnold
# @Date				: 2015/10
# @Version			: 3DCT 2.0.0 module rev. 3
# @Status			: stable
# @Usage			: import correlation.py and call main(markers_3d,markers_2d,spots_3d,rotation_center,results_file)
# 					: "markers_3d", "markers_2d" and "spots_3d" are numpy arrays. Those contain 3D coordinates
# 					: (arbitrary 3rd dimension for the 2D array). Marker coordinates are for the correlation and spot
# 					: coordinates are points on which the correlation is applied to.
# @Notes			: Edited and adapted by Jan Arnold (Max Planck Institute for Biochemistry)
# @Python_version	: 2.7.10
"""
# ======================================================================================================================

import os
import numpy as np

import pyto
import pyto.common as common
import pyto.util
from pyto.rigid_3d import Rigid3D

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
		"#   - rotation (Euler phi, psi, theta): [%6.3f, %6.3f, %6.3f]"
		% (eulers[0], eulers[2], eulers[1]),
		"#   - scale = %6.3f" % transf.s_scalar,
		"#   - translation for rotationaround [0,0,0] = [%6.3f, %6.3f, %6.3f]"
		% (transf.d[0], transf.d[1], transf.d[2]),
		"#   - translation for rotationaround [%5.2f, %5.2f, %5.2f] = [%6.3f, %6.3f, %6.3f]"
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
			"# ERROR: Optimization failed (status %d)"
			% transf.optimizeResult['status'],
			"#   Repeat run with changed initial values and / or " +
			"increased ninit"])

	# write header
	for line in header:
		res_file.write(line + os.linesep)

	# prepare marker lines
	table = ([
		"#",
		"#",
		"# Transformation of initial (3D) markers",
		"#",
		"#	Initial (3D) markers		Transformed initial" +
		"		Final (2D) markers	Transformed-Final"])
	out_vars = [
				markers_3d[0,:], markers_3d[1,:], markers_3d[2,:],
				transformed_3d[0,:], transformed_3d[1,:], transformed_3d[2,:],
				markers_2d[0,:], markers_2d[1,:], transformed_3d[0,:]-markers_2d[0,:], transformed_3d[1,:]-markers_2d[1,:]
				]
	out_format = '	%7.2f	%7.2f	%7.2f		%7.2f	%7.2f	%7.2f		%7.2f	%7.2f		%7.2f	%7.2f'
	ids = range(markers_3d.shape[1])
	res_tab_markers = pyto.util.arrayFormat(
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
		out_vars = [
					spots_3d[0,:], spots_3d[1,:], spots_3d[2,:],
					spots_2d[0,:], spots_2d[1,:], spots_2d[2,:]
					]
		out_format = '	%6.0f	%6.0f	%6.0f		%7.2f	%7.2f	%7.2f'
		ids = range(spots_3d.shape[1])
		res_tab_spots = pyto.util.arrayFormat(
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
	transf = Rigid3D.find_32(
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
	# print 'modified_translation: ', modified_translation

	# write transformation params and correlation
	if results_file != '':
		write_results(
			transf=transf, res_file_name=results_file,
			spots_3d=spots_3d, spots_2d=spots_2d,
			markers_3d=mark_3d, transformed_3d=transf_3d, markers_2d=mark_2d,
			rotation_center=rotation_center, modified_translation=modified_translation)
	cm_3D_markers = mark_3d.mean(axis=-1).tolist()

	# delta calc,real
	delta2D = transf_3d[:2,:] - mark_2d
	return [transf, transf_3d, spots_2d, delta2D, cm_3D_markers, modified_translation]
