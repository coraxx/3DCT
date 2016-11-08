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
import tifffile as tf

execdir = os.path.dirname(os.path.realpath(__file__))
maindir_ = execdir[:-5]
sys.path.append(maindir_)

app = QtGui.QApplication(sys.argv)


@pytest.fixture(scope='session')
def maindir():
	print maindir_
	return maindir_


@pytest.fixture(scope='session')
def image_RGB(tmpdir_factory):
	# img = tf.imread('/Users/jan/Desktop/correlation_test_dataset/IB_030.tif')
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
