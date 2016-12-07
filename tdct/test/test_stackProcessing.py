#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""


# @Title			: test_stackProcessing
# @Project			: 3DCTv2
# @Description		: pytest test
# @Author			: Jan Arnold
# @Email			: jan.arnold (at) coraxx.net
# @Copyright		: Copyright (C) 2016  Jan Arnold
# @License			: GPLv3 (see LICENSE file)
# @Credits			:
# @Maintainer		: Jan Arnold
# @Date				: 2016/09
# @Version			: 3DCT 2.2.2 module rev. 1
# @Status			: stable
# @Usage			: pytest
# @Notes			:
# @Python_version	: 2.7.12
"""
# ======================================================================================================================
from tdct import stackProcessing
import numpy as np

stackProcessing.debug = False


def test_norm_img():
	compArray = np.array([[127, 127, 127],[254, 254, 254]], dtype='uint8')
	retArray = stackProcessing.norm_img(np.array([[1,1,1],[2,2,2]],dtype='uint8'))
	assert np.testing.assert_array_equal(retArray, compArray) is None


def test_pxSize(image_RGB, image_Grey):
	pixelSize = stackProcessing.pxSize(str(image_RGB),z=False)
	assert pixelSize == 123.
	pixelSize = stackProcessing.pxSize(str(image_Grey),z=False)
	assert pixelSize == 4.56e-006
	pixelSize = stackProcessing.pxSize(str(image_RGB),z=True)
	assert pixelSize == 456.
	pixelSize = stackProcessing.pxSize(str(image_Grey),z=True)
	assert pixelSize == 0.123


def test_interpolation():
	calcArray = np.ones([4,5,5],dtype='uint8')
	calcArray[1] += 50
	calcArray[2] += 100
	calcArray[3] += 150
	compArray = np.array([
		[[0, 0, 0, 0, 0],
			[0, 0, 0, 0, 0],
			[0, 0, 0, 0, 0],
			[0, 0, 0, 0, 0],
			[0, 0, 0, 0, 0]],
		[[17, 17, 17, 17, 17],
			[17, 17, 17, 17, 17],
			[17, 17, 17, 17, 17],
			[17, 17, 17, 17, 17],
			[17, 17, 17, 17, 17]],
		[[34, 34, 34, 34, 34],
			[34, 34, 34, 34, 34],
			[34, 34, 34, 34, 34],
			[34, 34, 34, 34, 34],
			[34, 34, 34, 34, 34]],
		[[51, 51, 51, 51, 51],
			[51, 51, 51, 51, 51],
			[51, 51, 51, 51, 51],
			[51, 51, 51, 51, 51],
			[51, 51, 51, 51, 51]],
		[[67, 67, 67, 67, 67],
			[67, 67, 67, 67, 67],
			[67, 67, 67, 67, 67],
			[67, 67, 67, 67, 67],
			[67, 67, 67, 67, 67]],
		[[84, 84, 84, 84, 84],
			[84, 84, 84, 84, 84],
			[84, 84, 84, 84, 84],
			[84, 84, 84, 84, 84],
			[84, 84, 84, 84, 84]],
		[[101, 101, 101, 101, 101],
			[101, 101, 101, 101, 101],
			[101, 101, 101, 101, 101],
			[101, 101, 101, 101, 101],
			[101, 101, 101, 101, 101]],
		[[117, 117, 117, 117, 117],
			[117, 117, 117, 117, 117],
			[117, 117, 117, 117, 117],
			[117, 117, 117, 117, 117],
			[117, 117, 117, 117, 117]],
		[[134, 134, 134, 134, 134],
			[134, 134, 134, 134, 134],
			[134, 134, 134, 134, 134],
			[134, 134, 134, 134, 134],
			[134, 134, 134, 134, 134]],
		[[0, 0, 0, 0, 0],
			[0, 0, 0, 0, 0],
			[0, 0, 0, 0, 0],
			[0, 0, 0, 0, 0],
			[0, 0, 0, 0, 0]]], dtype="uint8")
	retArray = stackProcessing.interpol(calcArray, 300., 100., "spline", showgraph=False)
	assert np.testing.assert_array_equal(retArray, compArray) is None
	compArray[0] += 1
	retArray = stackProcessing.interpol(calcArray, 300., 100., "linear", showgraph=False)
	assert np.testing.assert_array_equal(retArray, compArray) is None
