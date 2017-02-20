#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""


# @Title			: test_parabolic
# @Project			: 3DCTv2
# @Description		: pytest test
# @Author			: Jan Arnold
# @Email			: jan.arnold (at) coraxx.net
# @Copyright		: Copyright (C) 2016  Jan Arnold
# @License			: GPLv3
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
from tdct import parabolic
from numpy import argmax


def test_parabolic():
	f = [2, 3, 1, 6, 4, 2, 3, 1]
	retVal = parabolic.parabolic(f, argmax(f))
	# assert parabolic.parabolic(f, argmax(f)) == (3.2142857142857144, 6.1607142857142856)
	assert abs(retVal[0] - 3.2142857142857144) < 0.0001
	assert abs(retVal[1] - 6.1607142857142856) < 0.0001


def test_parabolic_polyfit():
	f = [2, 3, 1, 6, 4, 2, 3, 1]
	retVal = parabolic.parabolic_polyfit(f, argmax(f), 2)
	# assert parabolic.parabolic_polyfit(f, argmax(f), 2) == (3.2142857142857295, 6.1607142857143131)
	assert abs(retVal[0] - 3.2142857142857295) < 0.0001
	assert abs(retVal[1] - 6.1607142857143131) < 0.0001
