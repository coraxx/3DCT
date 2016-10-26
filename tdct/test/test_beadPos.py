#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""


# @Title			: test_beadPos
# @Project			: 3DCTv2
# @Description		: pytest test
# @Author			: Jan Arnold
# @Email			: jan.arnold (at) coraxx.net
# @Copyright		: Copyright (C) 2016  Jan Arnold
# @License			: GPLv3 (see LICENSE file)
# @Credits			:
# @Maintainer		: Jan Arnold
# @Date				: 2016/09
# @Version			: 3DCT 2.2.2b module rev. 2
# @Status			: stable
# @Usage			: pytest
# @Notes			:
# @Python_version	: 2.7.12
"""
# ======================================================================================================================
from tdct import beadPos
import numpy as np


def test_getzPoly(testVolume):
	retVal = beadPos.getzPoly(70,20,testVolume,n=None,optimize=False)
	# assert int(retVal) == 37
	# assert retVal == 37.148076923076893
	assert abs(retVal-37.148076923076893) < 0.0001
	## Not testing "optimized" parameter since it is still broken


def test_getzGauss(testVolume):
	retVal = beadPos.getzGauss(70,20,testVolume,parent=None,optimize=False,threshold=None,threshVal=0.6,cutout=15)
	assert abs(retVal-40.00000000073846) < 0.0001
	retVal = beadPos.getzGauss(70,20,testVolume,parent=None,optimize=True,threshold=None,threshVal=0.6,cutout=15)
	valExp = (70.05369545524978, 20.05369545976798, 40.00000000073846)
	for i in range(3):
		assert abs(retVal[i]-valExp[i]) < 0.0001


def test_1Dgauss():
	data = np.random.normal(loc=5., size=10000)
	hist, bin_edges = np.histogram(data, density=True)
	bin_centres = (bin_edges[:-1] + bin_edges[1:])/2
	data = np.array([bin_centres, hist])
	popt, pcov = beadPos.gaussfit(data)
	assert round(popt[1]) == 5


def test_2Dgauss():
	# Create Gaussian test data
	Xin, Yin = np.mgrid[0:201, 0:201]
	data = beadPos.gaussian(3, 100, 100, 20, 40)(Xin, Yin) + np.ones(Xin.shape)

	threshold = data < data.max()-(data.max()-data.min())*0.6
	data[threshold] = 0

	params = beadPos.fitgaussian(data)

	assert (round(params[1]), round(params[2])) == (100, 100)
