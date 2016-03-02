#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Title			: bead_pos
# @Project			: 3DCTv2
# @Description		: Get bead z axis position from 3D image stacks (tiff z-stack)
# @Author			: Jan Arnold
# @Email			: jan.arnold (at) coraxx.net
# @Credits			: endolith https://gist.github.com/endolith/255291 for parabolic fitting function
# @Maintainer		: Jan Arnold
# @Date				: 2015/12
# @Version			: 0.2
# @Status			: stable
# @Usage			: import bead_pos.py and call z = bead_pos.getz(x,y,img,n=None,optimize=False) to get z position
# 					  at the given x and y pixel coordinate or call x,y,z = bead_pos.getz(x,y,img,n=None,optimize=True)
# 					  to get an optimized bead position (optimization of x, y and z)
# @Notes			: stable, but problems with low SNR <- needs revisiting
# @Python_version	: 2.7.10
# @Last Modified	: 2016/03/02
# ============================================================================

import math
import numpy as np
import matplotlib.pyplot as plt
import tifffile as tf
import parabolic

try:
	import clrmsg
except:
	pass


def getz(x,y,img,n=None,optimize=False):
	## x and y are coordinates
	## img is the path to the z-stack tiff file or a numpy.ndarray from tifffile.py imread function
	## n is the number of points around the max value that are used in the polyfit
	## leave n to use the maximum amount of points
	## If optimize is set ti True, the algorythm will try to optimize the x,y,z position
	## !! if optimize is True, 3 values are returned: x,y,z

	if not isinstance(img, str) and not isinstance(img, np.ndarray):
		if clrmsg: print clrmsg.ERROR
		raise TypeError('I can only handle an image path as string or an image volume as numpy.ndarray imported from tifffile.py')
	elif isinstance(img, str):
		img = tf.imread(img)

	data_z = img[:,y,x]

	if n is None:
		n = getn(data_z)

	data_z_xp_poly, data_z_yp_poly = parabolic.parabolic_polyfit(data_z, np.argmax(data_z), n)

	if math.isnan(data_z_xp_poly):
		if clrmsg: print clrmsg.ERROR
		print TypeError('Failed: Probably due to low SNR')
		if optimize is True:
			return x,y,'failed'
		else:
			return 'failed'

	f, ax = plt.subplots()
	ax.plot(range(0,len(data_z)), data_z, color='blue')
	ax.plot(data_z_xp_poly, data_z_yp_poly, 'o', color='black')
	ax.set_title("mid: "+str(data_z_xp_poly))

	plt.draw()
	plt.pause(0.5)
	plt.close()

	if optimize is True:
		x_opt_vals, y_opt_vals, z_opt_vals = optimize_z(x,y,data_z_xp_poly,img,n=None)
		return x_opt_vals[-1], y_opt_vals[-1], z_opt_vals[-1]
	else:
		return data_z_xp_poly


def optimize_z(x,y,z,image,n=None):
	if type(image) == str:
		img = tf.imread(image)
	elif type(image) == np.ndarray:
		img = image

	data_z = img[:,y,x]

	if n is None:
		n = getn(data_z)

	x_opt_vals, y_opt_vals, z_opt_vals = [], [], []

	x_opt,y_opt,z_opt = x,y,z
	for i in range(5):
		try:
			print x_opt,y_opt,z_opt
			x_opt,y_opt,z_opt = int(round(x_opt)),int(round(y_opt)),int(round(z_opt))
			x_opt, y_opt = optimize_xy(x_opt,y_opt,z_opt,img,nx=None,ny=None)
			data_z = img[:,round(y_opt),round(x_opt)]
		except Exception as e:
			if clrmsg: print clrmsg.ERROR
			print IndexError("Optimization failed, possibly due to low signal or low SNR. "+str(e))
			return [x],[y],['failed']
		n = getn(data_z)
		z_opt, data_z_yp_poly = parabolic.parabolic_polyfit(data_z, np.argmax(data_z), n)
		x_opt_vals.append(x_opt)
		y_opt_vals.append(y_opt)
		z_opt_vals.append(z_opt)

	return x_opt_vals, y_opt_vals, z_opt_vals


def getn(data):
	## this funktion is used to determine the maximum amount of data points for the polyfit function
	## data is a numpy array of values

	if len(data)-np.argmax(data) <= np.argmax(data):
		n = 2*(len(data)-np.argmax(data))-1
	else:
		n = 2*np.argmax(data)
	return n


def optimize_xy(x,y,z,image,nx=None,ny=None):
	## x and y are coordinates, z is the layer in the z-stack tiff file
	## image can be either the path to the z-stack tiff file or the np.array data of itself
	## n is the number of points around the max value that are used in the polyfit
	## leave n to use the maximum amount of points

	get_nx, get_ny = False, False
	if type(image) == str:
		img = tf.imread(image)
	elif type(image) == np.ndarray:
		img = image
	## amount of datapoints around coordinate
	samplewidth = 10
	data_x = img[z,y,x-samplewidth:x+samplewidth]
	data_y = img[z,y-samplewidth:y+samplewidth,x]

	f, axarr = plt.subplots(2, sharex=True)

	if nx is None:
		get_nx = True
	if ny is None:
		get_ny = True

	## optimize x
	xmaxvals = np.array([], dtype=np.int32)
	for offset in range(10):
		data_x = img[z,y-offset,x-samplewidth:x+samplewidth]
		if data_x.max() < data_x.mean()*1.1:
			# print "breaking at ",offset
			# print data_x.max(), data_x.mean(), data_x.mean()*1.1
			break
		if get_nx is True:
			nx = getn(data_x)
		data_x_xp_poly, data_x_yp_poly = parabolic.parabolic_polyfit(data_x, np.argmax(data_x), nx)
		xmaxvals = np.append(xmaxvals,[data_x_xp_poly])
		c = np.random.rand(3,1)
		axarr[0].plot(range(0,len(data_x)), data_x, color=c)
		axarr[0].plot(data_x_xp_poly, data_x_yp_poly, 'o', color=c)
	for offset in range(10):
		data_x = img[z,y+offset,x-samplewidth:x+samplewidth]
		if data_x.max() < data_x.mean()*1.1:
			# print "breaking at ",offset
			# print data_x.max(), data_x.mean(), data_x.mean()*1.1
			break
		if get_nx is True:
			nx = getn(data_x)
		data_x_xp_poly, data_x_yp_poly = parabolic.parabolic_polyfit(data_x, np.argmax(data_x), nx)
		xmaxvals = np.append(xmaxvals,[data_x_xp_poly])
		c = np.random.rand(3,1)
		axarr[0].plot(range(0,len(data_x)), data_x, color=c)
		axarr[0].plot(data_x_xp_poly, data_x_yp_poly, 'o', color=c)

	axarr[0].set_title("mid-mean: "+str(xmaxvals.mean()))

	## optimize y
	ymaxvals = np.array([], dtype=np.int32)
	for offset in range(10):
		data_y = img[z,y-samplewidth:y+samplewidth,x-offset]
		if data_y.max() < data_y.mean()*1.1:
			# print "breaking at ",offset
			# print data_y.max(), data_y.mean(), data_y.mean()*1.1
			break
		if get_ny is True:
			ny = getn(data_y)
		data_y_xp_poly, data_y_yp_poly = parabolic.parabolic_polyfit(data_y, np.argmax(data_y), ny)
		ymaxvals = np.append(ymaxvals,[data_y_xp_poly])
		c = np.random.rand(3,1)
		axarr[1].plot(range(0,len(data_y)), data_y, color=c)
		axarr[1].plot(data_y_xp_poly, data_y_yp_poly, 'o', color=c)

	for offset in range(10):
		data_y = img[z,y-samplewidth:y+samplewidth,x+offset]
		if data_y.max() < data_y.mean()*1.1:
			# print "breaking at ",offset
			# print data_y.max(), data_y.mean(), data_y.mean()*1.1
			break
		if get_ny is True:
			ny = getn(data_y)
		data_y_xp_poly, data_y_yp_poly = parabolic.parabolic_polyfit(data_y, np.argmax(data_y), ny)
		ymaxvals = np.append(ymaxvals,[data_y_xp_poly])
		c = np.random.rand(3,1)
		axarr[1].plot(range(0,len(data_y)), data_y, color=c)
		axarr[1].plot(data_y_xp_poly, data_y_yp_poly, 'o', color=c)

	axarr[1].set_title("mid-mean: "+str(ymaxvals.mean()))

	plt.draw()
	plt.pause(0.5)
	plt.close()
	## caculate offset into coordinates
	x_opt = x+xmaxvals.mean()-samplewidth
	y_opt = y+ymaxvals.mean()-samplewidth

	return x_opt, y_opt
