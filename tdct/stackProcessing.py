#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Can be used as standalone application, i.e. run python -u stackProcessing.py
or import stackProcessing.py and use main function like:
	stackProcessing.main(imgpath, original_steppsize, interpolated_stepsize, interpolationmethod)

e.g: stackProcessing("image_stack.tif", 300, 161.25, 'linear') => fast (~25x faster)
or: stackProcessing("image_stack.tif", 300, 161.25, 'spline') => slow

where 300 is the focus step size the image stack was acquired with and 161.25 the step size
of the interpolated stack.

The spline method also returns a graph representing the interpolation in z of one x,y pixel in the
middle for comparison between the original data and the linear as well as the spline interpolation.

kwargs:
	saveorigstack (boolean):
				If an image sequence is used, in the form of "Tile_001-001-001_1-000.tif"
				(FEI MAPS/LA tif sequence naming scheme), this program will save a single
				tiff stack file of the original images by default (True).

	nointerpolation (boolean):
				If set True (default is False) and saveorigstack is also True, no interpolation
				is done, only the packing of an image sequence to one single image stack file.

	showgraph (boolean):
				If set True (default False) and nointerpolation is False a graph is returned
				representing the interpolation in z of one x,y pixel in the middle of input stack
				for comparison between the original data and the linear as well as the spline interpolation.

# @Title			: stackProcessing
# @Project			: 3DCTv2
# @Description		: Process image stack files (.tif)
# @Author			: Jan Arnold
# @Email			: jan.arnold (at) coraxx.net
# @Copyright		: Copyright (C) 2016  Jan Arnold
# @License			: GPLv3 (see LICENSE file)
# @Credits			:
# @Maintainer		: Jan Arnold
# @Date				: 2016/01
# @Version			: 3DCT 2.3.0 module rev. 8
# @Status			: stable
# @Usage			: Can be used as standalone application, i.e. run python -u stackProcessing.py
# 					: or import stackProcessing.py and use main function like:
# 					: stackProcessing.main(imgpath, original_steppsize, interpolated_stepsize, interpolationmethod)
# 					:
# 					: e.g: stackProcessing("image_stack.tif", 300, 161.25, 'linear') => fast (~25x faster)
# 					: or: stackProcessing("image_stack.tif", 300, 161.25, 'spline') => slow
# 					:
# 					: where 300 is the focus step size the image stack was acquired with and 161.25 the step size
# 					: of the interpolated stack.
# 					:
# 					: The spline method also returns a graph representing the interpolation in z of one x,y pixel in the
# 					: middle for comparison between the original data and the linear as well as the spline interpolation.
# 					:
# 					: ##Options##
# 					: saveorigstack:	boolean	If an image sequence is used, in the form of "Tile_001-001-001_1-000.tif"
# 					: 							(FEI MAPS/LA tif sequence naming scheme), this program will save a
# 					: 							single tiff stack file of the original images by default (True).
# 					: nointerpolation:	boolean	If set True (default is False) and saveorigstack is also True, no
# 					: 							interpolation is done, only the packing of an image sequence to one
# 					: 							single image stack file.
# 					: showgraph:		boolean	If set True (default False) and nointerpolation is False a graph is
# 					: 							returned representing the interpolation in z of one x,y pixel in the
# 					: 							middle of input stack for comparison between the original data and the
# 					: 							linear as well as the spline interpolation.
# @Notes			:
# @Python_version	: 2.7.11
"""
# ======================================================================================================================

import sys
import os
import re
import fnmatch
import time
import numpy as np
from scipy import interpolate
import matplotlib
try:
	matplotlib.use('tkAgg')
except:
	pass
import matplotlib.pyplot as plt
## Adding execution directory to include possible scripts in the same folder (e.g. tifffile.py)
if getattr(sys, 'frozen', False):
	# programm runs in a bundle (pyinstaller)
	execdir = sys._MEIPASS
else:
	execdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(execdir)
try:
	import tifffile as tf
	from PyQt4 import QtGui
	import clrmsg
	import TDCT_debug
except:
	sys.exit("Please install tifffile, e.g.: pip install tifffile")

debug = TDCT_debug.debug


def main(img_path, ss_in, ss_out, qtprocessbar=None, interpolationmethod='linear', saveorigstack=True, showgraph=False, customSaveDir=None):
	"""Main function handling the file type and parsing of filenames/directories"""

	## Raise "error" when program has nothing to do due to all arguments set to none/false
	if interpolationmethod == 'none' and saveorigstack is False and showgraph is False:
		print clrmsg.WARNING, "At least let me do something! Setting everything to False... very funny -.-"
		return
	## For single image stack files
	if os.path.isfile(img_path) is True:
		if debug is True: print clrmsg.DEBUG, "Loading image: ", img_path
		if qtprocessbar:
			qtprocessbar.setValue(20)
			QtGui.QApplication.processEvents()
		img = tf.imread(img_path)
		if len(img.shape) < 3:
			print clrmsg.ERROR, "ERROR: This seems to be a 2D image with the shape {0}. Please select a stack image file.".format(img.shape)
			return
		if debug is True: print clrmsg.DEBUG, "		...done."
		## Get pixel size
		if qtprocessbar:
			qtprocessbar.setValue(40)
			QtGui.QApplication.processEvents()
		try:
			pixelsize = pxSize(img_path)
			if pixelsize is not None:
				px_info = True
				if debug is True: print clrmsg.DEBUG, 'Adding pixel size information:', pixelsize
			else:
				px_info = False
		except Exception as e:
			print clrmsg.ERROR, 'Error while adding pixel size information:', e, '... skipping'
			px_info = False
		## Start Processing
		if debug is True: print clrmsg.DEBUG, px_info
		if qtprocessbar:
			qtprocessbar.setValue(60)
			QtGui.QApplication.processEvents()
		if customSaveDir:
			file_out_int = os.path.join(customSaveDir, os.path.splitext(os.path.split(img_path)[1])[0]+"_resliced.tif")
		else:
			file_out_int = os.path.join(img_path, os.path.splitext(img_path)[0]+"_resliced.tif")  # revisit
		if debug is True: print clrmsg.DEBUG, "Interpolating..."
		img_int = interpol(img, ss_in, ss_out, interpolationmethod, showgraph)
		if qtprocessbar:
			qtprocessbar.setValue(80)
			QtGui.QApplication.processEvents()
		if type(img_int) == str:
			if debug is True: print clrmsg.DEBUG, img_int
			return
		if img_int is not None:
			if debug is True: print clrmsg.DEBUG, "Saving interpolated stack as: ", file_out_int
			if px_info is True:
				tf.imsave(file_out_int, img_int, metadata={'PixelSize': str(pixelsize),'FocusStepSize': str(ss_out/1000)})
			else:
				tf.imsave(file_out_int, img_int)
			if debug is True: print clrmsg.DEBUG, "		...done."
		if qtprocessbar:
			qtprocessbar.setValue(100)
			QtGui.QApplication.processEvents()
	## For image sequence (only FEI MAPS/LA image sequences at the moment)
	elif os.path.isdir(img_path):
		if qtprocessbar:
			qtprocessbar.setValue(5)
			QtGui.QApplication.processEvents()
		## bugfix for linux: os.listdir returns unsorted file list
		files = sorted(os.listdir(img_path))
		if debug is True: print clrmsg.DEBUG, "Checking directory: ", img_path
		channels = []
		## Setting trigger for FEI MAPS/LA filename scheme (only one that can be handled at the moment)
		match = False
		## Getting number of channels
		for filename in files:
			if fnmatch.fnmatch(filename, 'Tile_*.tif'):
				match = True
				channels.append(filename[17])  # 'Tile_001-001-001_1-000.tif' 17th character is the amount of channels
		if match is False:
			print clrmsg.ERROR,(
				"ERROR: I only know FEI MAPS image sequences looking like e.g. 'Tile_001-001-001_1-000.tif'. " +
				"I did not find images matching this naming scheme")
			return
		## Channel numbers in filename i zero-based, so add 1 for total number
		channels = int(max(channels))+1
		## Get pixel size
		if qtprocessbar:
			qtprocessbar.setValue(10)
			QtGui.QApplication.processEvents()
		try:
			for filename in files:
				if fnmatch.fnmatch(filename, 'Tile_*.tif'):
					pixelsize = pxSize(os.path.join(img_path,filename))
					pixelsizeZ = pxSize(os.path.join(img_path,filename),z=True)
					break
			if pixelsize is not None:
				px_info = True
				if debug is True: print clrmsg.DEBUG, 'Adding pixel size information:', pixelsize
			else:
				px_info = False
		except Exception as e:
			print clrmsg.ERROR, 'Error while adding pixel size information:', e, '... skipping'
			px_info = False
		## Start Processing
		if qtprocessbar:
			qtprocessbar.setValue(20)
			QtGui.QApplication.processEvents()
		if debug is True: print clrmsg.DEBUG, px_info
		for i in range(channels):
			if qtprocessbar:
				qtprocessbar.setValue(qtprocessbar.value()+int(20/channels))
				QtGui.QApplication.processEvents()
			if debug is True: print clrmsg.DEBUG, "Processing channel {0} of {1}".format(i+1, channels)
			filelist = []
			## Gather filenames from same channel
			for filename in files:
				if fnmatch.fnmatch(filename, 'Tile_*{0}-000.tif'.format(i)):
					filelist.append(os.path.join(img_path,filename))
			## Default pattern is not compatible with OME header from FEI MAPS/Live Acquisition Software
			img = tf.imread(filelist, pattern='')
			if qtprocessbar:
				qtprocessbar.setValue(qtprocessbar.value()+int(20/channels))
				QtGui.QApplication.processEvents()
			## Generate file output name
			if customSaveDir:
				file_out_int = os.path.join(customSaveDir, os.path.basename(os.path.normpath(img_path))+"_"+str(i)+"_resliced.tif")
			else:
				file_out_int = os.path.join(img_path, os.path.basename(os.path.normpath(img_path))+"_"+str(i)+"_resliced.tif")
			## Possibility to save the image sequence files as one single stack file for easier handling and better overview
			if saveorigstack is True:
				if customSaveDir:
					file_out_orig = os.path.join(customSaveDir, os.path.basename(os.path.normpath(img_path))+"_"+str(i)+".tif")
				else:
					file_out_orig = os.path.join(img_path, os.path.basename(os.path.normpath(img_path))+"_"+str(i)+".tif")
				if debug is True: print clrmsg.DEBUG, "Saving original image stack as single stack file: {0} |shape: {1}".format(file_out_orig,img.shape)
				if px_info is True:
					tf.imsave(file_out_orig, img, metadata={'PixelSize': str(pixelsize),'FocusStepSize': str(pixelsizeZ)})
				else:
					tf.imsave(file_out_orig, img)
				if debug is True: print clrmsg.DEBUG, "		...done."
				if qtprocessbar:
					qtprocessbar.setValue(qtprocessbar.value()+int(20/channels))
					QtGui.QApplication.processEvents()
			## In case only the original image sequence is saved as a single stack file the interpolation is skipped
			if interpolationmethod == 'none' and showgraph is False:
				pass
			else:
				if debug is True: print clrmsg.DEBUG, "Interpolating..."
				img_int = interpol(img, ss_in, ss_out, interpolationmethod, showgraph)
				## Error handling from 'interpol' function
				if type(img_int) == str:
					print clrmsg.ERROR, img_int
					return
				elif img_int is not None:
					if debug is True: print clrmsg.DEBUG, "Saving interpolated stack as: ", file_out_int
					if px_info is True:
						tf.imsave(file_out_int, img_int, metadata={'PixelSize': str(pixelsize),'FocusStepSize': str(ss_out/1000)})
					else:
						tf.imsave(file_out_int, img_int)
					if debug is True: print clrmsg.DEBUG, "		...done."
				if qtprocessbar:
					qtprocessbar.setValue(qtprocessbar.value()+int(20/channels))
					QtGui.QApplication.processEvents()
		if qtprocessbar:
			qtprocessbar.setValue(100)
			QtGui.QApplication.processEvents()
	else:
		print clrmsg.ERROR, 'ERROR: Path is neither a valid file nor a valid directory!'


def pxSize(img_path,z=False):
	"""Extract pixel size from meta/exif data. Tailored for image headers from FEI dual beam electron microscopes
	and CorrSight light microscope"""
	with tf.TiffFile(img_path) as tif:
		for page in tif:
			for tag in page.tags.values():
				if isinstance(tag.value, str):
					for keyword in ['PhysicalSizeX','PixelWidth','PixelSize'] if not z else ['PhysicalSizeZ','FocusStepSize']:
						tagposs = [m.start() for m in re.finditer(keyword, tag.value)]
						for tagpos in tagposs:
							if keyword == 'PhysicalSizeX' or keyword == 'PhysicalSizeZ':
								for piece in tag.value[tagpos:tagpos+30].split('"'):
									try:
										pixelsize = float(piece)
										return pixelsize
									except:
										pass
							elif keyword == 'PixelWidth':
								for piece in tag.value[tagpos:tagpos+30].split('='):
									try:
										try:
											pixelsize = float(piece.strip().split('\r\n')[0])
										except:
											pixelsize = float(piece.strip().split(r'\r\n')[0])
										return pixelsize
									except:
										pass
							elif keyword == 'PixelSize' or 'FocusStepSize':
								for piece in tag.value[tagpos:tagpos+30].split('"'):
									try:
										pixelsize = float(piece)
										return pixelsize
									except:
										pass


def interpol(img, ss_in, ss_out, interpolationmethod, showgraph):
	"""Main function for interpolating image stacks via polyfit"""
	## Depending on tiff format the file can have different shapes; e.g. z,y,x or c,z,y,x
	if len(img.shape) == 4 and img.shape[0] == 1:
		img = np.squeeze(img, axis=0)
	elif len(img.shape) == 4 and img.shape[0] > 1:
		return "ERROR: I'm sorry, I cannot handle multichannel files: "+str(img.shape)

	if len(img.shape) == 3:
		## Number of slices in original stack
		sl_in = img.shape[0]
		## Number of slices in interpolated stack
		# Discarding last data point. e.g. 56 in i.e.
		# 55 steps * (309 nm original spacing / 161.25 nm new spacing) = 105.39 -> int() = 105 + 1 = 106
		sl_out = int((sl_in-1)*(ss_in/ss_out)) + 1
		## Interpolate image stack shape
		img_int_shape = (sl_out, img.shape[1], img.shape[2])
	else:
		return "ERROR: I only know tiff stack image formats in z,y,x or c,z,y,x with one channel"

	if showgraph is True:
		if __name__ == '__main__':
			showgraph_(img, ss_in, ss_out, sl_in, sl_out, block=False)
		else:
			showgraph_(img, ss_in, ss_out, sl_in, sl_out, block=True)
	if interpolationmethod == 'none':
		return None
	elif interpolationmethod == 'linear':
		if debug is True: print clrmsg.DEBUG, "Nr. of slices (in/out): ", sl_in, sl_out
		return linear(img, img_int_shape, ss_in, ss_out, sl_in, sl_out)
	elif interpolationmethod == 'spline':
		if debug is True: print clrmsg.DEBUG, "Nr. of slices (in/out): ", sl_in, sl_out
		return spline(img, img_int_shape, ss_in, ss_out, sl_in, sl_out)
	else:
		return "Please specify the interpolation method ('linear', 'spline', 'none')."


def showgraph_(img, ss_in, ss_out, sl_in, sl_out, block=True):
	"""Show graph for polyfit function to visualize fitting process"""
	## Known x values in interpolated stack size.
	zx = np.arange(0,sl_out,(ss_in/ss_out))
	zy = img[:,int(img.shape[1]/2),int(img.shape[2]/2)]
	if ss_in/ss_out < 1.0:
		zx_mod = []
		for i in range(img.shape[0]):
			zx_mod.append(zx[i])
		zx = zx_mod
	## Linear interpolation
	lin = interpolate.interp1d(zx, zy, kind='linear')
	## Spline interpolation
	spl = interpolate.InterpolatedUnivariateSpline(zx, zy)

	zxnew = np.arange(0, (sl_in-1)*ss_in/ss_out, 1)  # First slice of original and interpolated are both 0. n-1 to discard last slice
	zynew_lin = lin(zxnew)
	zynew_spl = spl(zxnew)
	## Plotting data. blue = original, red = interpolated with interp1d, green = spline interpolation
	plt.plot(zx, zy, 'bo-', label='original')
	plt.plot(zxnew, zynew_lin, 'rx-', label='linear')
	plt.plot(zxnew, zynew_spl, 'g*-', label='spline')
	plt.legend(loc='upper left')
	if block is True:
		print clrmsg.INFO, "######## \nPAUSED: Please close graph in order to continue with the program \n########"
	plt.show(block)


def spline(img, img_int_shape, ss_in, ss_out, sl_in, sl_out):
	"""
	Spline interpolation

	# possible depricated due to changes in code -> marked for futur code changes
	ss_in : step size input stack
	ss_out : step size output stack
	sl_in : slices input stack
	sl_out : slices output stack
	"""
	## Known x values in interpolated stack size.
	zx = np.arange(0,sl_out,ss_in/ss_out)
	zxnew = np.arange(0, (sl_in-1)*ss_in/ss_out, 1)  # First slice of original and interpolated are both 0. n-1 to discard last slice
	if ss_in/ss_out < 1.0:
		zx_mod = []
		for i in range(img.shape[0]):
			zx_mod.append(zx[i])
		zx = zx_mod

	## Create new numpy array for the interpolated image stack
	img_int = np.zeros(img_int_shape,img.dtype)
	if debug is True: print clrmsg.DEBUG, "Interpolated stack shape: ", img_int.shape

	r_sl_out = range(sl_out)

	ping = time.time()
	for px in range(img.shape[-1]):
		for py in range(img.shape[-2]):
			spl = interpolate.InterpolatedUnivariateSpline(zx, img[:,py,px])
			np.put(img_int[:,py,px], r_sl_out, spl(zxnew))
		sys.stdout.write("\r%d%%" % int(px*100/img.shape[-1]))
		sys.stdout.flush()
	pong = time.time()
	if debug is True: print clrmsg.DEBUG, "This interpolation took {0} seconds".format(pong - ping)
	return img_int


def linear(img, img_int_shape, ss_in, ss_out, sl_in, sl_out):
	"""Linear interpolation"""
	##  Determine interpolated slice positions
	sl_int = np.arange(0,sl_in-1,ss_out/ss_in)  # sl_in-1 because last slice is discarded (no extrapolation)

	## Create new numpy array for the interpolated image stack
	img_int = np.zeros(img_int_shape,img.dtype)
	if debug is True: print clrmsg.DEBUG, "Interpolated stack shape: ", img_int.shape

	## Calculate distances from every interpolated image to its next original image
	sl_counter = 0
	ping = time.time()
	for i in sl_int:
		int_i = int(i)
		lower = i-int_i
		upper = 1-(lower)
		img_int[sl_counter,:,:] = img[int_i,:,:]*upper + img[int_i+1,:,:]*lower
		sl_counter += 1
	pong = time.time()
	if debug is True: print clrmsg.DEBUG, "This interpolation took {0} seconds".format(pong - ping)
	return img_int


def norm_img(img,copy=False,qtprocessbar=None):
	"""Normalizing image

	Supported data types are (u)int8, (u)int16, float32 and float64.
	Supported image types are 2D, 3D and/or multichannel images in the form of:

	[y,x]
	[y,x,c]
	[z,y,x]
	[z,c,y,x]
	[c,z,y,x]
	"""
	if copy is True:
		img = np.copy(img)
	else:
		# quick bug fix for immutable numpy array read-only error
		img = np.copy(img)
	dtype = str(img.dtype)
	if dtype == "uint16" or dtype == "int16": typesize = 65535
	elif dtype == "uint8" or dtype == "int8": typesize = 255
	elif dtype == "float32" or dtype == "float64": typesize = 1
	else: print clrmsg.ERROR, "Sorry, I don't know this file type yet: ", dtype
	if debug is True: print clrmsg.DEBUG, "Shape/type:", img.shape, dtype
	## 2D image
	if img.ndim == 2:
		if debug is True: print clrmsg.DEBUG, "2D image"
		img *= typesize/img.max()
	## 3D or multichannel image
	elif img.ndim == 3:
		## tiffimage reads z,y,x for stacks but y,x,c if it is multichannel image (or z,c,y,x if it is a multicolor image stack)
		if img.shape[-1] > 4:
			if debug is True: print clrmsg.DEBUG, "Image stack"
			if qtprocessbar:
				maximum = int(int(img.shape[0])*1.25)
				qtprocessbar.setMaximum(maximum)
				qtprocessbar.setValue(maximum*0.1)
				QtGui.QApplication.processEvents()
			for i in range(int(img.shape[0])):
				img[i,:,:] *= typesize/img[i,:,:].max()
				if qtprocessbar:
					qtprocessbar.setValue(qtprocessbar.value()+1)
					QtGui.QApplication.processEvents()
		else:
			if debug is True: print clrmsg.DEBUG, "Multichannel image"
			if qtprocessbar:
				maximum = int(int(img.shape[2])*1.25)
				qtprocessbar.setMaximum(maximum)
				qtprocessbar.setValue(maximum*0.1)
				QtGui.QApplication.processEvents()
			for i in range(int(img.shape[2])):
				img[:,:,i] *= typesize/img[:,:,i].max()
				if qtprocessbar:
					qtprocessbar.setValue(qtprocessbar.value()+1)
					QtGui.QApplication.processEvents()
	## 3D and multichannel image
	elif len(img.shape) == 4:
		if debug is True: print clrmsg.DEBUG, "3D and multichannel image"
		if qtprocessbar:
			maximum = int((int(img.shape[0])+int(img.shape[1]))*1.25)
			qtprocessbar.setMaximum(maximum)
			qtprocessbar.setValue(maximum*0.1)
			QtGui.QApplication.processEvents()
		for i in range(int(img.shape[0])):
			for ii in range(int(img.shape[1])):
				img[i,ii,:,:] *= typesize/img[i,ii,:,:].max()
				if qtprocessbar:
					qtprocessbar.setValue(qtprocessbar.value()+1)
					QtGui.QApplication.processEvents()
	return img


def normalize(path,qtprocessbar=None, customSaveDir=None):
	if debug is True: print clrmsg.DEBUG, "Normalizing:", path
	img = tf.imread(path)
	if qtprocessbar:
		qtprocessbar.setValue(10)
		QtGui.QApplication.processEvents()
	img = norm_img(img,qtprocessbar=qtprocessbar)
	fpath,fname = os.path.split(path)
	fname_norm = os.path.join(fpath,"norm_"+fname)
	if customSaveDir:
		fname_norm = os.path.join(customSaveDir, "norm_"+fname)
	else:
		fname_norm = os.path.join(fpath, "norm_"+fname)
	if debug is True: print clrmsg.DEBUG, "Saving..."
	if len(img.shape) == 4:
		tf.imsave(fname_norm, img, imagej=True)
	else:
		tf.imsave(fname_norm, img)
	if debug is True: print clrmsg.DEBUG, "		...done"
	if debug is True: print clrmsg.DEBUG, "Finished normalizing."


def mip(path,qtprocessbar=None, customSaveDir=None, normalize=False):
	if debug is True: print clrmsg.DEBUG, "Creating normalized Maximum Intensity Projection (MIP):", path
	img = tf.imread(path)
	if qtprocessbar:
		qtprocessbar.setValue(10)
		QtGui.QApplication.processEvents()
	fpath,fname = os.path.split(path)
	if customSaveDir:
		fname_mip = os.path.join(customSaveDir, "MIP_"+fname)
		fname_mip_norm = os.path.join(customSaveDir, "MIP_norm_"+fname)
	else:
		fname_mip = os.path.join(fpath, "MIP_"+fname)
		fname_mip_norm = os.path.join(fpath, "MIP_norm_"+fname)
	if len(img.shape) == 4:
		img = np.amax(img, axis=1)
		if normalize:
			if debug is True: print clrmsg.DEBUG, "Normalizing..."
			img = norm_img(img)
		if debug is True: print clrmsg.DEBUG, "Saving..."
		tf.imsave(fname_mip_norm if normalize else fname_mip, img, imagej=True)
		if debug is True: print clrmsg.DEBUG, "		...done"
	elif len(img.shape) == 3:
		img = np.amax(img, axis=0)
		if normalize:
			if debug is True: print clrmsg.DEBUG, "Normalizing..."
			img = norm_img(img)
		if debug is True: print clrmsg.DEBUG, "Saving..."
		tf.imsave(fname_mip_norm if normalize else fname_mip, img)
		if debug is True: print clrmsg.DEBUG, "		...done"
	else: print clrmsg.ERROR, "I'm sorry, I don't know this image shape: {0}".format(img.shape)


if __name__ == '__main__':
	import Tkinter
	import tkFileDialog
	import ttk
	import tkSimpleDialog
	import tkMessageBox

	## Initial UI setup
	root = Tkinter.Tk()
	root.title("Image Stack Tool")
	T = Tkinter.Text(root, height=10, width=100)
	T.grid(row=0,column=0,columnspan=2)
	T.insert(Tkinter.END, """IMAGE STACK TOOL - 0.1 - by Jan Arnold

	This application can interpolate/normalize image stacks and/or merge an image sequence
	to one single image stack file (for FEI MAPS generated single image stacks) as well as
	create Maximum Intensity Projections (MIP)

	Supported are .tif files in (u)int8, (u)int16, float32 and float64.

	All files are returned as tiff stack files.""")
	ft = ttk.Frame()
	ft.grid(row=1,column=0,columnspan=2)
	pb_hd = ttk.Progressbar(ft, orient='horizontal', mode='indeterminate', length=700)
	pb_hd.grid(row=2,columnspan=2)
	pb_hd.start(10)

	## Set up variables
	choices = ['linear', 'spline']
	int_method = Tkinter.StringVar(root)
	int_method.set('linear')
	showgraph = Tkinter.IntVar()

	## Button function for getting file names to interpolate single stack file(s)
	def getfiles():
		files = tkFileDialog.askopenfilenames(parent=root,title='Choose image stack files')
		if not files: return
		filenames = []
		for fname in files:
			filenames.append(os.path.split(fname)[1])
		if len(files) > 10:
			filenames = filenames[0:10]
			filenames.append("...")
		ss_in = tkSimpleDialog.askfloat(
			parent=root, title='Enter ORIGINAL focus step size',
			prompt='Enter ORIGINAL focus step size for:\n'+'\n'.join('{}'.format(k) for k in filenames))
		if not ss_in: return
		pixelsize = pxSize(files[0])
		if pixelsize is None: pixelsize = 0
		ss_out = tkSimpleDialog.askfloat(
			parent=root, title='Enter INTERPOLATED focus step size',
			prompt='Enter INTERPOLATED focus step size for:\n'+'\n'.join('{}'.format(k) for k in filenames), initialvalue=pixelsize*1000)
		if not ss_out: return
		print "Selected files: {0}\n".format(files), "\n", "Focus step size in: {0} | out: {1}\n".format(ss_in,ss_out),\
			"Interpolation method: {0}\n".format(int_method.get())
		for filename in files:
			main(filename,ss_in, ss_out, saveorigstack=False, interpolationmethod=int_method.get(), showgraph=bool(showgraph.get()))
		print "Finished interpolation."
		print "="*40

	## Button function for getting directory name to interpolate image sequence
	def getdirint():
		directory = tkFileDialog.askdirectory(parent=root,title='Choose directory with image sequence stack files')
		if not directory: return
		ss_in = tkSimpleDialog.askfloat(
			parent=root, title='Enter ORIGINAL focus step size',
			prompt='Enter ORIGINAL focus step size for:\n{0}'.format(os.path.split(directory)[1]))
		if not ss_in: return
		try:
			pixelsize = pxSize(os.path.join(directory,'Tile_001-001-000_0-000.tif'))
			if pixelsize is None: pixelsize = 0
		except:
			pixelsize = 0
			pass
		ss_out = tkSimpleDialog.askfloat(
			parent=root, title='Enter INTERPOLATED focus step size',
			prompt='Enter INTERPOLATED focus step size for:\n{0}'.format(os.path.split(directory)[1]), initialvalue=pixelsize*1000)
		if not ss_out: return
		saveorigstack = tkMessageBox.askyesno("Save single stack file option", "Do you also want to save single stack file with original focus step size?")
		print "directory: {0}\n".format(directory), "Focus step size in: {0} | out: {1}\n".format(ss_in,ss_out),\
			"Also save single stack file for original spacing?: {0}\n".format(saveorigstack), "Interpolation method: {0}\n".format(int_method.get())
		main(directory,ss_in, ss_out, saveorigstack=saveorigstack, interpolationmethod=int_method.get(), showgraph=bool(showgraph.get()))
		print "Finished interpolation."
		print "="*40

	## Button function for just converting image stack sequences to single stack files
	def getdircon():
		directory = tkFileDialog.askdirectory(parent=root,title='Choose directory with image sequence stack files')
		if not directory: return
		print directory
		main(directory, 0, 0, saveorigstack=True, interpolationmethod='none')
		print "Finished converting image stack sequences to single stack file(s)."
		print "="*40

	## Normalize Image
	def normalize():
		files = tkFileDialog.askopenfilenames(parent=root,title='Choose image(stack) file(s)')
		if not files: return
		for filename in files:
			if filename.endswith('.tif'):
				print "Normalizing:", filename
				img = tf.imread(filename)
				img = norm_img(img)
				fpath,fname = os.path.split(filename)
				fname_norm = os.path.join(fpath,"norm_"+fname)
				if len(img.shape) == 4:
					tf.imsave(fname_norm, img, imagej=True)
				else:
					tf.imsave(fname_norm, img)
				print "		...done"
		print "Finished normalizing."
		print "="*40

	def mip():
		files = tkFileDialog.askopenfilenames(parent=root,title='Choose image(stack) files')
		if not files: return
		for filename in files:
			if filename.endswith('.tif'):
				print "Creating normalized Maximum Intensity Projection (MIP):", filename
				img = tf.imread(filename)
				fpath,fname = os.path.split(filename)
				fname_norm = os.path.join(fpath,"MIP_"+fname)
				if len(img.shape) == 4:
					img_MIP = np.zeros((img.shape[0],img.shape[2],img.shape[3]), dtype=img.dtype)
					for i in range(0,img.shape[0]):
						for ii in range(0,img.shape[2]):
							for iii in range(0,img.shape[3]):
								img_MIP[i,ii,iii] = img[i,:,ii,iii].max()
					img_MIP = norm_img(img_MIP)
					tf.imsave(fname_norm, img_MIP, imagej=True)
				elif len(img.shape) == 3:
					img_MIP = np.zeros((img.shape[1],img.shape[2]), dtype=img.dtype)
					for i in range(0,img.shape[1]):
						for ii in range(0,img.shape[2]):
							img_MIP[i,ii] = img[:,i,ii].max()
					img_MIP = norm_img(img_MIP)
					tf.imsave(fname_norm, img_MIP)
				else: print "I'm sorry, I don't know this image shape: {0}".format(img.shape)
				print "		...done"
		print "Maximum Intensity Projection finished."
		print "="*40

	## Set up UI elements
	w = Tkinter.Label(root, text="Interpolation method (linear=fast, spline=slow):")
	w.grid(row=3,column=0,sticky=Tkinter.W)
	w = Tkinter.OptionMenu(root, int_method, *choices)
	w.grid(row=4,column=0,sticky=Tkinter.W)
	### Buttons
	B1 = Tkinter.Button(root, text="Interpolate single stack file(s)...", command=getfiles)
	B1.config(width=50)
	B1.grid(row=5,column=0,columnspan=2)
	B2 = Tkinter.Button(root, text="Interpolate image sequence...", command=getdirint)
	B2.config(width=50)
	B2.grid(row=6,column=0,columnspan=2)
	B3 = Tkinter.Button(root, text="Just convert image stack sequence to single stack files...", command=getdircon)
	B3.config(width=50)
	B3.grid(row=7,column=0,columnspan=2)
	B4 = Tkinter.Button(root, text="Normalize image(stack) files...", command=normalize)
	B4.config(width=50)
	B4.grid(row=8,column=0,columnspan=2)
	B5 = Tkinter.Button(root, text="Create normalized MIP of image stack files...", command=mip)
	B5.config(width=50)
	B5.grid(row=9,column=0,columnspan=2)
	### Check-boxes
	c = Tkinter.Checkbutton(root, text="Show graph comparing interpolation methods", variable=showgraph)
	c.grid(row=4,column=0,sticky=Tkinter.W,padx=100)

	## Run Tkinter main loop
	root.mainloop()
