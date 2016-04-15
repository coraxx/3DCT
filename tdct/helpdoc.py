#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This contains Qt dialogs for quick help buttons


# @Title			: helpdoc
# @Project			: 3DCTv2
# @Description		: Contains Qt dialogs for quick help buttons
# @Author			: Jan Arnold
# @Email			: jan.arnold (at) coraxx.net
# @Copyright		: Copyright (C) 2016  Jan Arnold
# @License			: GPLv3 (see LICENSE file)
# @Credits			:
# @Maintainer		: Jan Arnold
# @Date				: 2016/03/25
# @Version			: 3DCT 2.0.0 module rev. 1
# @Status			: stable
# @Usage			: import helpdoc.py and call functions
# @Notes			:
# @Python_version	: 2.7.11
"""
# ======================================================================================================================
from PyQt4 import QtGui


class help():
	def __init__(self,parent=None):
		self.parent = parent

	def WorkingDir(self):
		QtGui.QMessageBox.information(
					self.parent,"Help: Working directory", (
						"Results from the correlation are saved into this directory.\n\n"
						"Also its contents are listed further down for a quick "
						"correlation files selection.\n\n"
						"The selected path is checked for writing privileges.\n\n"
						"It is colored red if the path is not valid or read-only."
						))

	def ImageStack(self):
		QtGui.QMessageBox.information(
					self.parent,"Help: Image stack", (
						"Selected image stack file is resliced by linear interpolation.\n\n"
						"Both the original focus step size and the targeted focus step size "
						"(usually the pixel size to generate cubic voxels) must have the same "
						"unit of measurement.\n\n"
						"Optionally the image stack can be normalized by checking the check box"
						))

	def ImageSequence(self):
		QtGui.QMessageBox.information(
					self.parent,"Help: Image sequence", (
						""
						))

	def Normalize(self):
		QtGui.QMessageBox.information(
					self.parent,"Help: Normalize", (
						""
						))

	def FileList(self):
		QtGui.QMessageBox.information(
					self.parent,"Help: File list", (
						""
						))

	def Mip(self):
		QtGui.QMessageBox.information(
					self.parent,"Help: Maximum Intensity Projection", (
						""
						))

	def Correlation(self):
		QtGui.QMessageBox.information(
					self.parent,"Help: Correlation", (
						""
						))
