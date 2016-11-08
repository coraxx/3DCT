#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""


# @Title			: conftest
# @Project			: 3DCTv2
# @Description		: conftest for pytest
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
# @Python_version	: 2.7.11
"""
# ======================================================================================================================
import pytest
from PyQt4 import QtGui
import sys
import os
import numpy as np
from scipy.ndimage.filters import gaussian_filter
import tifffile as tf

execdir = os.path.dirname(os.path.realpath(__file__))
maindir_ = execdir
sys.path.append(maindir_)

app = QtGui.QApplication(sys.argv)


@pytest.fixture(scope='session')
def maindir():
	print maindir_
	return maindir_


@pytest.fixture(scope='session')
def image_RGB(tmpdir_factory):
	img = np.random.randint(256, size=(941, 1024, 3))
	fn = tmpdir_factory.mktemp('data').join('img_RGB.tif')
	tf.imsave(str(fn), img.astype('uint8'), metadata={"PhysicalSizeX": "123", "FocusStepSize": "456"})
	return fn


@pytest.fixture(scope='session')
def image_Grey(tmpdir_factory):
	img = np.random.randint(256, size=(941, 1024))
	fn = tmpdir_factory.mktemp('data').join('img_grey.tif')
	tf.imsave(str(fn), img.astype('uint8'), metadata={"PhysicalSizeZ": "0.123", "FIBimage": "PixelWidth=4.56e-006\r\n"})
	return fn


@pytest.fixture(scope='module')
def testVolume(size=[100, 100, 100]):
	vol = np.zeros(size, dtype='uint8')
	vol = insertSphere(vol, [40,20,70], 10, blur=False)
	return vol


def insertSphere(volIn, pos, radius, blur=False):
	try:
		if pos[0] < radius or pos[0] > volIn.shape[0] - radius:
			raise Exception("Sphere's x position too close to volume boundaries! Returning original volume...")
		if pos[1] < radius or pos[1] > volIn.shape[1] - radius:
			raise Exception("Sphere's y position too close to volume boundaries! Returning original volume...")
		if pos[2] < radius or pos[2] > volIn.shape[2] - radius:
			raise Exception("Sphere's z position too close to volume boundaries! Returning original volume...")
	except Exception as e:
		print "ERROR:", e
		return volIn

	## diameter
	r = radius
	d = r * 2 + 1
	z,y,x = np.ogrid[-r:d-r, -r:d-r, -r:d-r]
	mask = x*x + y*y + z*z <= r*r
	sphere = np.zeros((d, d, d),dtype='uint8')
	sphere[mask] = 255
	if blur is True:
		sphere = gaussian_filter(sphere, sigma=1).astype('uint8')
	volIn[pos[0]-r:pos[0]-r+d, pos[1]-r:pos[1]-r+d, pos[2]-r:pos[2]-r+d] += sphere

	return volIn
