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
# @Version			: 3DCT 2.2.0b module rev. 2
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
						"This was mainly build to process image stacks recorded with the FEI CorrSight Light Microscope. "
						"Image stacks are saved as single images for every slice and channel. "
						"With this tool you can join and/or reslice the single tiff files to one big tiff stack file per channel.\n\n"
						"- Select or drag in the folder containing the 'Tile_001-001-000_0-000.tif' images.\n\n"
						"- If the 'Cube voxels' checkbox is NOT ticked, the single tiff files will only be "
						"joined to one big file per channel. They will be saved in the same folder as the single "
						"tiff files with the name of the folder.\n\n"
						"- If the checkbox is ticked, you need to specify the input in output focus step size. "
						"By clicking the ''get pixel size' button you can extract both the focus step size (input size) "
						"and the pixel size information from the tiff exif/meta data. The pixel size is used as the new "
						"focus step size (output size). The resliced stack will be saved at the same location as the single "
						"tif files with the name of the folder and a '_resliced' suffix.\n\n"
						"    - Optionally you can also save a untouched\n      version (same as not ticking the\n      checkbox) "
						"while generating the resliced\n      version by ticking the 'save raw stack\n      copy' checkbox."
						))

	def Normalize(self):
		QtGui.QMessageBox.information(
					self.parent,"Help: Normalize", (
						"Select a tiff file (single image or stack) and run to normalize the image."
						))

	def FileList(self):
		QtGui.QMessageBox.information(
					self.parent,"Help: File list", (
						"Files in the working directory are listed here for quick correlation access. "
						"Select a valid tiff file and assign it to one of the two slots for correlation via the "
						"'Select for correlation' buttons at the bottom.\n\n"
						"To refresh the file list hit the refresh button at the bottom right (little circular arrow)."
						))

	def Mip(self):
		QtGui.QMessageBox.information(
					self.parent,"Help: Maximum Intensity Projection", (
						"Select a tiff image stack and run to create a maximum intensity projection (MIP).\n\n"
						"Check the 'normalize' box if you also want a subsequent normalization."
						))

	def Correlation(self):
		QtGui.QMessageBox.information(
					self.parent,"Help: Correlation", (
						"For 3D to 2D correlation select a tiff image stack (3D) and a single tiff image (2D) from the working "
						"directory file list or drag valid tiff files onto the address bar.\n\nSelect tiff image stack files for "
						"3D to 3D correlation or single tiff images for 2D to 2D correlation.\n\nHit 'Open Correlation Tool' to start "
						"the correlation module."
						))
