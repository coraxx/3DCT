#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""


# @Title			: test_TDCT_correlation
# @Project			: 3DCTv2
# @Description		: pytest test
# @Author			: Jan Arnold
# @Email			: jan.arnold (at) coraxx.net
# @Copyright		: Copyright (C) 2016  Jan Arnold
# @License			: GPLv3 (see LICENSE file)
# @Credits			:
# @Maintainer		: Jan Arnold
# @Date				: 2016/04
# @Version			: 3DCT 2.3.0 module rev. 3
# @Status			: stable
# @Usage			: pytest
# @Notes			:
# @Python_version	: 2.7.11
"""
# ======================================================================================================================#
import pytest
import os
import tifffile as tf

try:
	import TDCT_correlation
	TDCT_error = ""
	TDCT_correlation.debug = False
except Exception as e:
	TDCT_error = e


def test_imgShapeRGB(image_RGB):
	img = tf.imread(str(image_RGB))
	assert img.shape == (941, 1024, 3)


def test_imgShapeGrey(image_Grey):
	img = tf.imread(str(image_Grey))
	assert img.shape == (941, 1024)


@pytest.fixture(scope='module')
def tdct_CorrelationInstance_setup(request, image_RGB):
	def tdct_CorrelationInstance_teardown():
		print('\ndone using TDCT_correlation instance')
	request.addfinalizer(tdct_CorrelationInstance_teardown)

	print('\nsetting up TDCT_correlation instance')
	left = str(image_RGB)
	right = str(image_RGB)
	main = TDCT_correlation.Main(leftImage=left,rightImage=right)
	return main


def test_TDCT_correlationImport():
	if 'TDCT_correlation' not in globals():
		pytest.fail("TDCT_correlation import: {0}".format(TDCT_error))


# @pytest.mark.skipif(TDCT_error != "", reason="TDCT_correlation import failed: {0}".format(TDCT_error))
# def test_TDCT_correlationInit():
# 	window = TDCT_correlation.MainWidget()
# 	assert window


@pytest.mark.skipif(TDCT_error != "", reason="TDCT_correlation import failed: {0}".format(TDCT_error))
def test_guiFile(maindir):
	qtCreatorFile_main = os.path.join(maindir, "TDCT_correlation.ui")
	assert os.path.isfile(qtCreatorFile_main) is True
	Ui_MainWindow, QtBaseClass = TDCT_correlation.uic.loadUiType(qtCreatorFile_main)
	assert Ui_MainWindow
	assert QtBaseClass


@pytest.mark.skipif(TDCT_error != "", reason="TDCT_correlation import failed: {0}".format(TDCT_error))
def test_model2np(tdct_CorrelationInstance_setup):
	# print dir(tdct_CorrelationInstance_setup.window)
	compArray = TDCT_correlation.np.array([
		[0., 0., 0.],
		[50., 25., 5.],
		[100., 50., 10.],
		[150., 75., 15.],
		[200., 100., 20.]])
	for i in range(5):
		items = [
			TDCT_correlation.QtGui.QStandardItem(str(50*i)),
			TDCT_correlation.QtGui.QStandardItem(str(25*i)),
			TDCT_correlation.QtGui.QStandardItem(str(5*i))]
		tdct_CorrelationInstance_setup.window.modelRight.appendRow(items)
	retArray = tdct_CorrelationInstance_setup.window.model2np(tdct_CorrelationInstance_setup.window.modelRight,[0,5])
	# assert TDCT_correlation.np.array_equal(retArray, compArray)
	assert TDCT_correlation.np.testing.assert_array_equal(retArray, compArray) is None


@pytest.mark.skipif(TDCT_error != "", reason="TDCT_correlation import failed: {0}".format(TDCT_error))
def test_anglectrl(tdct_CorrelationInstance_setup):
	testArray = {-1:359,0:0,1:1,359:359,360:0,361:1}
	for k,v in testArray.iteritems():
		print "Testing angle {0:03}, expecting {1:03} ... ".format(k, v),
		angle = tdct_CorrelationInstance_setup.window.anglectrl(angle=k)
		assert angle == v
		print "OK"


@pytest.mark.skipif(TDCT_error != "", reason="TDCT_correlation import failed: {0}".format(TDCT_error))
def test_pxSize(tdct_CorrelationInstance_setup, image_RGB, image_Grey):
	pixelSize = tdct_CorrelationInstance_setup.window.pxSize(str(image_RGB),z=False)
	assert pixelSize == 123.
	pixelSize = tdct_CorrelationInstance_setup.window.pxSize(str(image_Grey),z=False)
	assert pixelSize == 4.56e-006*1e006
	pixelSize = tdct_CorrelationInstance_setup.window.pxSize(str(image_RGB),z=True)
	assert pixelSize == 456.
	pixelSize = tdct_CorrelationInstance_setup.window.pxSize(str(image_Grey),z=True)
	assert pixelSize == 123.


@pytest.mark.skipif(TDCT_error != "", reason="TDCT_correlation import failed: {0}".format(TDCT_error))
def test_norm_img(tdct_CorrelationInstance_setup):
	compArray = TDCT_correlation.np.array([[127, 127, 127],[254, 254, 254]], dtype='uint8')
	retArray = tdct_CorrelationInstance_setup.window.norm_img(TDCT_correlation.np.array([[1,1,1],[2,2,2]],dtype='uint8'))
	assert TDCT_correlation.np.testing.assert_array_equal(retArray, compArray) is None


@pytest.mark.skipif(TDCT_error != "", reason="TDCT_correlation import failed: {0}".format(TDCT_error))
def test_blendImages(tdct_CorrelationInstance_setup):
	## Blending images
	img1 = TDCT_correlation.np.array([[1,1],[2,2]],dtype='uint8')
	img2 = TDCT_correlation.np.array([[3,4],[4,4]],dtype='uint8')

	## Blending using "screen"
	compArray = TDCT_correlation.np.array([[3,4],[5,5]], dtype='uint8')
	retArray = tdct_CorrelationInstance_setup.window.blendImages([img1,img2], blendmode='screen')
	assert TDCT_correlation.np.testing.assert_array_equal(retArray, compArray) is None

	## Blending using "minimum"
	compArray = TDCT_correlation.np.array([[1,1],[2,2]], dtype='uint8')
	retArray = tdct_CorrelationInstance_setup.window.blendImages([img1,img2], blendmode='minimum')
	assert TDCT_correlation.np.testing.assert_array_equal(retArray, compArray) is None

	## Passing no images should return a "white image" i.e. array with all pixels = 255
	compArray = TDCT_correlation.np.zeros([10,10], dtype='uint8')-1
	retArray = tdct_CorrelationInstance_setup.window.blendImages([], blendmode='screen')
	assert TDCT_correlation.np.testing.assert_array_equal(retArray, compArray) is None
	retArray = tdct_CorrelationInstance_setup.window.blendImages([], blendmode='minimum')
	assert TDCT_correlation.np.testing.assert_array_equal(retArray, compArray) is None


# @pytest.fixture(scope='module')
# def resource_a_setup(request):
# 	print('\nresources_a_setup()')
# 	def resource_a_teardown():
# 		print('\nresources_a_teardown()')
# 	request.addfinalizer(resource_a_teardown)

# def test_1_that_needs_resource_a(resource_a_setup):
# 	print('test_1_that_needs_resource_a()')

# def test_2_that_does_not():
# 	print('\ntest_2_that_does_not()')

# def test_3_that_does(resource_a_setup):
# 	print('\ntest_3_that_does()')

##########################################

# def resource_a_setup():
# 	print('resources_a_setup()')

# def resource_a_teardown():
# 	print('resources_a_teardown()')

# class TestClass:
# 	@classmethod
# 	def setup_class(cls):
# 		print ('\nsetup_class()')
# 		resource_a_setup()

# 	@classmethod
# 	def teardown_class(cls):
# 		print ('\nteardown_class()')
# 		resource_a_teardown()

# 	def test_1_that_needs_resource_a(self):
# 		print('\ntest_1_that_needs_resource_a()')

# def test_2_that_does_not():
# 	print('\ntest_2_that_does_not()')
