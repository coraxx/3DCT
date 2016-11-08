#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""


# @Title			: test_TDCT_main
# @Project			: 3DCTv2
# @Description		: pytest test
# @Author			: Jan Arnold
# @Email			: jan.arnold (at) coraxx.net
# @Copyright		: Copyright (C) 2016  Jan Arnold
# @License			: GPLv3 (see LICENSE file)
# @Credits			:
# @Maintainer		: Jan Arnold
# @Date				: 2016/04
# @Version			: 3DCT 2.2.2 module rev. 3
# @Status			: stable
# @Usage			: pytest
# @Notes			:
# @Python_version	: 2.7.11
"""
# ======================================================================================================================
import pytest
import os

try:
	import TDCT_main
	TDCT_error = ""
except Exception as e:
	TDCT_error = e


def test_TDCT_mainImport():
	if 'TDCT_main' not in globals():
		pytest.fail("TDCT_main import: {0}".format(TDCT_error))


@pytest.mark.skipif(TDCT_error != "", reason="TDCT_main import failed: {0}".format(TDCT_error))
def test_TDCT_mainInit():
	window = TDCT_main.APP()
	assert window


@pytest.mark.skipif(TDCT_error != "", reason="TDCT_main import failed: {0}".format(TDCT_error))
def test_splashScreen(maindir):
	print maindir
	gif = os.path.join(maindir,'icons','SplashScreen.gif')
	assert os.path.isfile(gif) is True
	movie = TDCT_main.QtGui.QMovie(gif)
	splash = TDCT_main.MovieSplashScreen(movie)
	assert splash


@pytest.mark.skipif(TDCT_error != "", reason="TDCT_main import failed: {0}".format(TDCT_error))
def test_guiFile(maindir):
	print maindir
	qtCreatorFile_main = os.path.join(maindir, "TDCT_main.ui")
	assert os.path.isfile(qtCreatorFile_main) is True
	Ui_MainWindow, QtBaseClass = TDCT_main.uic.loadUiType(qtCreatorFile_main)
	assert Ui_MainWindow
	assert QtBaseClass
