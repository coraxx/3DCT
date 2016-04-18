#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Get z axis position of spherical markers from 3D image stacks (tiff z-stack)
import beadPos.py and call z = beadPos.getz(x,y,img,n=None,optimize=False) to get z position
at the given x and y pixel coordinate or call x,y,z = beadPos.getz(x,y,img,n=None,optimize=True)
to get an optimized bead position (optimization of x, y and z)

# @Title			: beadPos
# @Project			: 3DCTv2
# @Description		: Get bead z axis position from 3D image stacks (tiff z-stack)
# @Author			: Jan Arnold
# @Email			: jan.arnold (at) coraxx.net
# @Copyright		: Copyright (C) 2016  Jan Arnold
# @License			: GPLv3 (see LICENSE file)
# @Credits			: endolith https://gist.github.com/endolith/255291 for parabolic fitting function
# 					  2D Gaussian fit from http://scipy.github.io/old-wiki/pages/Cookbook/FittingData
# @Maintainer		: Jan Arnold
# @Date				: 2015/12
# @Version			: 3DCT 2.0.0 module rev. 2
# @Status			: stable
# @Usage			: import beadPos.py and call z = beadPos.getz(x,y,img,n=None,optimize=False) to get z position
# 					  at the given x and y pixel coordinate or call x,y,z = beadPos.getz(x,y,img,n=None,optimize=True)
# 					  to get an optimized bead position (optimization of x, y and z)
# @Notes			: stable, but problems with low SNR <- needs revisiting
# @Python_version	: 2.7.11
"""
# ======================================================================================================================

import time
import math
import numpy as np
from scipy.optimize import curve_fit, leastsq
import matplotlib.pyplot as plt
import tifffile as tf
import parabolic

try:
	import clrmsg
	import TDCT_debug
except:
	pass

repeat = 0
debug = TDCT_debug.debug

def getzPoly(x,y,img,n=None,optimize=False):
	"""x and y are coordinates
	img is the path to the z-stack tiff file or a numpy.ndarray from tifffile.py imread function
	n is the number of points around the max value that are used in the polyfit
	leave n to use the maximum amount of points
	If optimize is set to True, the algorithm will try to optimize the x,y,z position
	!! if optimize is True, 3 values are returned: x,y,z"""

	if not isinstance(img, str) and not isinstance(img, np.ndarray):
		if clrmsg and debug is True: print clrmsg.ERROR
		raise TypeError('I can only handle an image path as string or an image volume as numpy.ndarray imported from tifffile.py')
	elif isinstance(img, str):
		img = tf.imread(img)

	data_z = img[:,y,x]

	if n is None:
		n = getn(data_z)

	data_z_xp_poly, data_z_yp_poly = parabolic.parabolic_polyfit(data_z, np.argmax(data_z), n)

	if math.isnan(data_z_xp_poly):
		if clrmsg and debug is True: print clrmsg.ERROR
		print TypeError('Failed: Probably due to low SNR')
		if optimize is True:
			return x,y,'failed'
		else:
			return 'failed'

	if debug is True:
		f, ax = plt.subplots()
		ax.plot(range(0,len(data_z)), data_z, color='blue')
		ax.plot(data_z_xp_poly, data_z_yp_poly, 'o', color='black')
		ax.set_title("mid: "+str(data_z_xp_poly))

		plt.draw()
		plt.pause(1)
		plt.close()

	if optimize is True:
		x_opt_vals, y_opt_vals, z_opt_vals = optimize_z(x,y,data_z_xp_poly,img,n=None)
		return x_opt_vals[-1], y_opt_vals[-1], z_opt_vals[-1]
	else:
		return data_z_xp_poly


def getzGauss(x,y,img,parent=None,optimize=False,threshold=None,threshVal=0.6,cutout=15):
	"""x and y are coordinates
	img is the path to the z-stack tiff file or a numpy.ndarray from tifffile.py imread function
	optimize == True kicks off the 2D Gaussian fit and this function will return x,y,z
	threshold == True filters the image where it cuts off at max - min * threshVal (threshVal between 0.1 and 1)
	cutout specifies the FOV for the 2D Gaussian fit"""

	if not isinstance(img, str) and not isinstance(img, np.ndarray):
		if clrmsg and debug is True: print clrmsg.ERROR
		raise TypeError('I can only handle an image path as string or an image volume as numpy.ndarray imported from tifffile.py')
	elif isinstance(img, str):
		img = tf.imread(img)

	data_z = img[:,y,x]
	data = np.array([np.arange(len(data_z)), data_z])
	poptZ, pcov = gaussfit(data,parent)

	if optimize is False:
		return poptZ[1]
	else:
		repeats = 5
		if clrmsg and debug is True: print clrmsg.DEBUG + '2D Gaussian xy optimization running %.f at z = %.f' % (repeats,round(poptZ[1]))
		for repeat in range(repeats):
			data = np.copy(img[
						round(poptZ[1]),
						y-cutout:y+cutout,
						x-cutout:x+cutout])
			if threshold is not None:
				threshold = data < data.max()-(data.max()-data.min())*threshVal
				data[threshold] = 0
			poptXY = fitgaussian(data,parent)
			if poptXY is None:
				return x, y, poptZ[1]
			(height, xopt, yopt, width_x, width_y) = poptXY
			## x and y are switched when applying the offset
			x = x-cutout+yopt
			y = y-cutout+xopt
			data_z = img[:,y,x]
			data = np.array([np.arange(len(data_z)), data_z])
			poptZ, pcov = gaussfit(data,parent,hold=True)
			parent.refreshUI()
			time.sleep(0.01)
		return x, y, poptZ[1]


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
			if clrmsg and debug is True: print clrmsg.ERROR
			print IndexError("Optimization failed, possibly due to low signal or low SNR. "+str(e))
			return [x],[y],['failed']
		n = getn(data_z)
		z_opt, data_z_yp_poly = parabolic.parabolic_polyfit(data_z, np.argmax(data_z), n)
		x_opt_vals.append(x_opt)
		y_opt_vals.append(y_opt)
		z_opt_vals.append(z_opt)

	return x_opt_vals, y_opt_vals, z_opt_vals


def getn(data):
	"""this function is used to determine the maximum amount of data points for the polyfit function
	data is a numpy array of values"""

	if len(data)-np.argmax(data) <= np.argmax(data):
		n = 2*(len(data)-np.argmax(data))-1
	else:
		n = 2*np.argmax(data)
	return n


def optimize_xy(x,y,z,image,nx=None,ny=None):
	"""x and y are coordinates, z is the layer in the z-stack tiff file
	image can be either the path to the z-stack tiff file or the np.array data of itself
	n is the number of points around the max value that are used in the polyfit
	leave n to use the maximum amount of points"""
	get_nx, get_ny = False, False
	if type(image) == str:
		img = tf.imread(image)
	elif type(image) == np.ndarray:
		img = image
	## amount of data points around coordinate
	samplewidth = 10
	data_x = img[z,y,x-samplewidth:x+samplewidth]
	data_y = img[z,y-samplewidth:y+samplewidth,x]

	if debug is True: f, axarr = plt.subplots(2, sharex=True)

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
		if debug is True:
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
		if debug is True:
			axarr[0].plot(range(0,len(data_x)), data_x, color=c)
			axarr[0].plot(data_x_xp_poly, data_x_yp_poly, 'o', color=c)

	if debug is True: axarr[0].set_title("mid-mean: "+str(xmaxvals.mean()))

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
		if debug is True:
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
		if debug is True:
			axarr[1].plot(range(0,len(data_y)), data_y, color=c)
			axarr[1].plot(data_y_xp_poly, data_y_yp_poly, 'o', color=c)

	if debug is True: axarr[1].set_title("mid-mean: "+str(ymaxvals.mean()))

	if debug is True:
		plt.draw()
		plt.pause(0.5)
		plt.close()
	## calculate offset into coordinates
	x_opt = x+xmaxvals.mean()-samplewidth
	y_opt = y+ymaxvals.mean()-samplewidth

	return x_opt, y_opt


## Gaussian 1D fit
def gauss(x, *p):
	# A "magnitude"
	# mu "offset on x axis"
	# sigma "width"
	A, mu, sigma = p
	return A*np.exp(-(x-mu)**2/(2.*sigma**2))


def gaussfit(data,parent=None,hold=False):
	## Fitting gaussian to data
	data[1] = data[1]-data[1].min()
	p0 = [data[1].max(), data[1].argmax(), 1]
	popt, pcov = curve_fit(gauss, data[0], data[1], p0=p0)

	if parent is not None:
		## Draw graphs in GUI
		x = []
		y = []
		for i in np.arange(len(data[0])):
			x.append(i)
			y.append(gauss(i,*popt))
		if hold is False:
			parent.widget_matplotlib.setupScatterCanvas(width=4,height=4,dpi=52,toolbar=False)
		parent.widget_matplotlib.xyPlot(data[0], data[1], label='z data',clear=True)
		parent.widget_matplotlib.xyPlot(x, y, label='gaussian fit',clear=False)

	## DEBUG
	if clrmsg and debug is True:
		from scipy.stats import ks_2samp
		## Get std from the diagonal of the covariance matrix
		std_height, std_mean, std_sigma = np.sqrt(np.diag(pcov))
		print clrmsg.DEBUG + '='*15, 'GAUSS FIT', '='*25
		print clrmsg.DEBUG + 'Amplitude		:', popt[0]
		print clrmsg.DEBUG + 'Location		:', popt[1]
		## http://mathworld.wolfram.com/GaussianFunction.html -> sigma * 2 * sqrt(2 * ln(2))
		print clrmsg.DEBUG + 'FWHM			:', popt[2] * 2 * math.sqrt(2 * math.log(2,math.e))
		print clrmsg.DEBUG + 'Std. Amplitude	:', std_height
		print clrmsg.DEBUG + 'Std. Location	:', std_mean
		print clrmsg.DEBUG + 'Std. FWHM		:', std_sigma * 2 * math.sqrt(2 * math.log(2,math.e))
		print clrmsg.DEBUG + 'Mean dy		:', np.absolute(y-data[1]).mean()
		print clrmsg.DEBUG + str(ks_2samp(y, data[1]))
	return popt, pcov


def test1Dgauss(data=None):
	if not data:
		data = np.random.normal(loc=5., size=10000)
	hist, bin_edges = np.histogram(data, density=True)
	bin_centres = (bin_edges[:-1] + bin_edges[1:])/2
	data = np.array([bin_centres, hist])
	# data = np.array([[0,1,2,3,4,5,6,7,8,9],[10,12,11,15,25,18,13,9,11,10]])
	popt, pcov = gaussfit(data)

	x = []
	y = []
	for i in np.arange(len(data[0])):
		x.append(i)
		y.append(gauss(i,*popt))
	plt.clf()
	plt.plot(data[0], data[1], label='Test data')
	plt.plot(x, y, label='Gaussian fit')

	new_bin_centers = np.linspace(bin_centres[0], bin_centres[-1], 200)
	new_hist_fit = gauss(new_bin_centers, *popt)
	plt.plot(new_bin_centers, new_hist_fit,label='Interpolated')

	plt.legend()
	plt.show()
	if clrmsg and debug is True:
		from scipy.stats import ks_2samp
		print clrmsg.DEBUG + ('Mean dy : %.6f' % np.absolute(y-data[1]).mean())
		print clrmsg.DEBUG + str(ks_2samp(y, data[1]))


## Gaussian 2D fit from http://scipy.github.io/old-wiki/pages/Cookbook/FittingData
def gaussian(height, center_x, center_y, width_x, width_y):
	"""Returns a Gaussian function with the given parameters"""
	width_x = float(width_x)
	width_y = float(width_y)
	return lambda x,y: height*np.exp(
				-(((center_x-x)/width_x)**2+((center_y-y)/width_y)**2)/2)


def moments(data):
	"""Returns (height, x, y, width_x, width_y)
	the Gaussian parameters of a 2D distribution by calculating its
	moments"""
	total = data.sum()
	X, Y = np.indices(data.shape)
	x = (X*data).sum()/total
	y = (Y*data).sum()/total
	col = data[:, int(y)]
	width_x = np.sqrt(abs((np.arange(col.size)-y)**2*col).sum()/col.sum())
	row = data[int(x), :]
	width_y = np.sqrt(abs((np.arange(row.size)-x)**2*row).sum()/row.sum())
	height = data.max()
	return height, x, y, width_x, width_y


def fitgaussian(data,parent=None):
	"""Returns (height, x, y, width_x, width_y)
	the Gaussian parameters of a 2D distribution found by a fit"""

	def errorfunction(p):
		return np.ravel(gaussian(*p)(*np.indices(data.shape)) - data)

	params = moments(data)
	p, success = leastsq(errorfunction, params)
	if np.isnan(p).any():
		parent.widget_matplotlib.matshowPlot(
			mat=data,contour=np.ones(data.shape),labelContour="XY optimization failed\n" +
			"Try reducing the\nmarker size (equates to\nFOV for gaussian fit)")
		return None
	if parent is not None:
		## Draw graphs in GUI
		fit = gaussian(*p)
		contour = fit(*np.indices(data.shape))
		(height, x, y, width_x, width_y) = p
		labelContour = (
						"      x : %.1f\n"
						"      y : %.1f\n"
						"width_x : %.1f\n"
						"width_y : %.1f") % (x, y, width_x, width_y)
		parent.widget_matplotlib.matshowPlot(mat=data,contour=contour,labelContour=labelContour)
	return p


# def test2Dgauss(data=None):
# 	from pylab import *
# 	if data is None:
# 		# Create the Gaussian data
# 		Xin, Yin = mgrid[0:201, 0:201]
# 		data = gaussian(3, 100, 100, 20, 40)(Xin, Yin) + np.random.random(Xin.shape)

# 	# data = data-data.min()
# 	print data.min(), data.max()
# 	threshold = data < data.max()-(data.max()-data.min())*0.6
# 	data[threshold] = 0

# 	matshow(data, cmap=cm.gist_earth_r)

# 	params = fitgaussian(data)
# 	fit = gaussian(*params)

# 	contour(fit(*indices(data.shape)), cmap=cm.copper)
# 	ax = gca()
# 	(height, x, y, width_x, width_y) = params

# 	text(0.85, 0.05, """
# 	x : %.1f
# 	y : %.1f
# 	width_x : %.1f
# 	width_y : %.1f""" % (x, y, width_x, width_y),
# 						fontsize=12, horizontalalignment='right',
# 						verticalalignment='bottom', transform=ax.transAxes)

# 	show()

# img = tf.imread('/Users/jan/Desktop/dot2.tif')
# print img.shape
# test2Dgauss(img)
