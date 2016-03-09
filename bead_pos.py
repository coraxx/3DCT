#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Title			: bead_pos
# @Project			: 3DCTv2
# @Description		: Get bead z axis position from 3D image stacks (tiff z-stack)
# @Author			: Jan Arnold
# @Email			: jan.arnold (at) coraxx.net
# @Credits			: endolith https://gist.github.com/endolith/255291 for parabolic fitting function
# 					  2D Gaussian fit from http://scipy.github.io/old-wiki/pages/Cookbook/FittingData
# @Maintainer		: Jan Arnold
# @Date				: 2015/12
# @Version			: 0.2
# @Status			: stable
# @Usage			: import bead_pos.py and call z = bead_pos.getz(x,y,img,n=None,optimize=False) to get z position
# 					  at the given x and y pixel coordinate or call x,y,z = bead_pos.getz(x,y,img,n=None,optimize=True)
# 					  to get an optimized bead position (optimization of x, y and z)
# @Notes			: stable, but problems with low SNR <- needs revisiting
# @Python_version	: 2.7.10
# @Last Modified	: 2016/03/09
# ============================================================================

import math
import numpy as np
from scipy.optimize import curve_fit, leastsq
import matplotlib.pyplot as plt
import tifffile as tf
import parabolic

try:
	import clrmsg
except:
	pass


def getzPoly(x,y,img,n=None,optimize=False):
	debug = True
	## x and y are coordinates
	## img is the path to the z-stack tiff file or a numpy.ndarray from tifffile.py imread function
	## n is the number of points around the max value that are used in the polyfit
	## leave n to use the maximum amount of points
	## If optimize is set ti True, the algorythm will try to optimize the x,y,z position
	## !! if optimize is True, 3 values are returned: x,y,z

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


def getzGauss(x,y,img,parent=None,optimize=False):
	debug = True
	## x and y are coordinates
	## img is the path to the z-stack tiff file or a numpy.ndarray from tifffile.py imread function
	## n is the number of points around the max value that are used in the polyfit
	## leave n to use the maximum amount of points
	## If optimize is set ti True, the algorythm will try to optimize the x,y,z position
	## !! if optimize is True, 3 values are returned: x,y,z

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
		print 'gauss optimized'
		return x, y, poptZ[1]
		'''
		pseude code:
		get image slize poptZ[1] and cut out x-radius, y-radius, x+radius, y+radius
		fitgauss2D over cutout
		maybe loop over it to optimize position further?!
		try to to gauss2D fit on cutout in every plane and plot center to see drift
		'''
		poptXY = fitgaussian(data)
		(height, xopt, yopt, width_x, width_y) = poptXY
		return xopt, yopt, poptZ[1]


def optimize_z(x,y,z,image,n=None):
	debug = True
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
	## this funktion is used to determine the maximum amount of data points for the polyfit function
	## data is a numpy array of values

	if len(data)-np.argmax(data) <= np.argmax(data):
		n = 2*(len(data)-np.argmax(data))-1
	else:
		n = 2*np.argmax(data)
	return n


def optimize_xy(x,y,z,image,nx=None,ny=None):
	debug = True
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
	## caculate offset into coordinates
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


def gaussfit(data,parent=None):
	debug = True
	## Fitting gaussian to data
	data[1] = data[1]-data[1].min()
	p0 = [data[1].max(), data[1].argmax(), 1]
	popt, pcov = curve_fit(gauss, data[0], data[1], p0=p0)

	## Draw graphs in GUI
	x = []
	y = []
	for i in np.arange(len(data[0])):
		x.append(i)
		y.append(gauss(i,*popt))
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
		print clrmsg.DEBUG + 'STD Amplitude	:', std_height
		print clrmsg.DEBUG + 'STD Location	:', std_mean
		print clrmsg.DEBUG + 'STD FWHM		:', std_sigma * 2 * math.sqrt(2 * math.log(2,math.e))
		print clrmsg.DEBUG + 'Mean dy		:', np.absolute(y-data[1]).mean()
		print clrmsg.DEBUG + str(ks_2samp(y, data[1]))
	return popt, pcov


def test1Dgauss(data=None):
	debug = True
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
	"""Returns a gaussian function with the given parameters"""
	width_x = float(width_x)
	width_y = float(width_y)
	return lambda x,y: height*np.exp(
				-(((center_x-x)/width_x)**2+((center_y-y)/width_y)**2)/2)


def moments(data):
	"""Returns (height, x, y, width_x, width_y)
	the gaussian parameters of a 2D distribution by calculating its
	moments """
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


def fitgaussian(data):
	"""Returns (height, x, y, width_x, width_y)
	the gaussian parameters of a 2D distribution found by a fit"""
	params = moments(data)
	errorfunction = lambda p: np.ravel(gaussian(*p)(*np.indices(data.shape)) - data)
	p, success = leastsq(errorfunction, params)
	return p


def test2Dgauss(data=None):
	from pylab import *
	if data is None:
		# Create the gaussian data
		Xin, Yin = mgrid[0:201, 0:201]
		data = gaussian(3, 100, 100, 20, 40)(Xin, Yin) + np.random.random(Xin.shape)

	# data = data-data.min()
	print data.min(), data.max()
	low_values_indices = data < data.max()-(data.max()-data.min())*0.6  # Where values are low
	data[low_values_indices] = 0

	matshow(data, cmap=cm.gist_earth_r)

	params = fitgaussian(data)
	fit = gaussian(*params)

	contour(fit(*indices(data.shape)), cmap=cm.copper)
	ax = gca()
	(height, x, y, width_x, width_y) = params

	text(0.95, 0.05, """
	x : %.1f
	y : %.1f
	width_x : %.1f
	width_y : %.1f""" % (x, y, width_x, width_y),
						fontsize=16, horizontalalignment='right',
						verticalalignment='bottom', transform=ax.transAxes)

	show()

img = tf.imread('/Users/jan/Desktop/dot2.tif')
print img.shape
test2Dgauss(img)