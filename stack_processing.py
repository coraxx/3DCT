#!/usr/bin/env python
#title				: stack_processing.py
#description		: Process image stack files (.tif)
#author				: Jan Arnold
#email				: jan.arnold (at) coraxx.net
#credits			: 
#maintainer			: Jan Arnold
#date				: 2016/01
#version			: 0.1
#status				: developement
#usage				: Can be used as standalone application, i.e. run python -u stack_processing.py
#					: or import stack_processing.py and use main function like:
#					: stack_processing.main(imgpath, original_steppsize, interpolated_stepsize, interpolationmethod)
#					: 
#					: e.g: stack_processing("image_stack.tif", 300, 161.25, 'linear') => fast (~25x faster)
#					: or: stack_processing("image_stack.tif", 300, 161.25, 'spline') => slow
#					: 
#					: where 300 is the focus step size the image stack was acquired with and 161.25 the step size
#					: of the interpolated stack.
#					: 
#					: The spline method also returns a graph representing the interpolation in z of one x,y pixel in the
#					: middle for comparison between the original data and the linear as well as the spline interpolation.
#					: 
#					: ##Options##
#					: saveorigstack:	boolean	If an image sequence is used, in the form of "Tile_001-001-001_1-000.tif"
#					: 							(FEI MAPS/LA tif sequence naming scheme), this programm will save a single
#					: 							tiff stack file of the original images by default (True).
#					: nointerpolation:	boolean	If set True (default is False) and saveorigstack is also True, no interpoaltion
#					: 							is done, only the packing of an image sequence to one single image stack file.
#					: showgraph:		boolean	If set True (default False) and nointerpolation is False a graph is returned
#					: 							representing the interpolation in z of one x,y pixel in the middle of input stack
#					: 							for comparison between the original data and the linear as well as the spline interpolation.
#					: 							
#					: 							
#					: 
#notes				: 
#python_version		: 2.7.10 
#=================================================================================

import sys
import os
import fnmatch
import time
import numpy as np
from scipy import interpolate
import matplotlib
matplotlib.use('tkAgg')
import matplotlib.pyplot as plt
## Adding execution directory to include possible scripts in the same folder (e.g. tifffile.py)
execdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(execdir)
try:
	import tifffile as tf
except:
	sys.exit("Please install tifffile, e.g.: pip install tifffile")

## Main function handling the file type and parsing of filenames/directories
def main(img_path, ss_in, ss_out, interpolationmethod='linear', saveorigstack=True, showgraph=False):
	## Raise "error" when prgramm has nothing to do due to all arguments set to none/false
	if interpolationmethod == 'none' and saveorigstack == False and showgraph == False:
		print "At least let me do somthing! Setting everything to False... very funny -.-"
		return
	## For single image stack files
	if os.path.isfile(img_path) == True:
		print "Loading image: ", img_path
		img = tf.imread(img_path)
		if len(img.shape) < 3:
			print "ERROR: This seems to be a 2D image with the shape {0}. Please select a stack image file.".format(img.shape)
			return
		print "		...done."
		file_out_int = os.path.join(img_path, os.path.splitext(img_path)[0]+"_resliced.tif")
		print "Interpolating..."
		img_int = interpol(img, ss_in, ss_out, interpolationmethod, showgraph)
		if type(img_int) == str:
			print img_int
			return
		if img_int != None:
			print "Saving interpolated stack as: ", file_out_int
			tf.imsave(file_out_int, img_int)
			print "		...done."
	## For image sequence (only FEI MAPS/LA image sequences at the moment)
	elif os.path.isfile(img_path) == False:
		files = os.listdir(img_path)
		print "Checking directory: ", img_path
		channels = []
		## Setting trigger for FEI MAPS/LA filename scheme (only one that can be handled at the moment)
		match = False
		## Getting number of channels
		for filename in files:
			if fnmatch.fnmatch(filename, 'Tile_*.tif'):
				match = True
				channels.append(filename[17]) # 'Tile_001-001-001_1-000.tif' 17th character is the amount of channels
		if match == False:
			print("ERROR: I only know FEI MAPS image sequences looking like e.g. 'Tile_001-001-001_1-000.tif'. " +
				"I did not find images matching thise naming scheme")
			return
		## Channel numbers in filename i zero-based, so add 1 for total number
		channels = int(max(channels))+1
		for i in range(channels):
			print "Processing channel {0} of {1}".format(i+1, channels)
			filelist = []
			## Gather filenames from same channel
			for filename in files:
				if fnmatch.fnmatch(filename, 'Tile_001-001-*{0}-000.tif'.format(i)):
					filelist.append(os.path.join(img_path,filename))
			## Default pattern is not compatible with OME header from FEI MAPS/Live Acquisition Software
			img = tf.imread(filelist, pattern='')
			## Generate file output name
			file_out_int = os.path.join(img_path, os.path.basename(os.path.normpath(img_path))+"_"+str(i)+"_resliced.tif")
			## Possibility to save the image sequence files as one single stack file for easier handling and better overview
			if saveorigstack == True:
				file_out_orig = os.path.join(img_path, os.path.basename(os.path.normpath(img_path))+"_"+str(i)+".tif")
				print "Saving original image stack as single stack file: {0} |shape: {1}".format(file_out_orig,img.shape)
				tf.imsave(file_out_orig, img)
				print "		...done."
			## In case only the original image sequence is saved as a single stack file the interpolation is skiped
			if interpolationmethod == 'none' and showgraph == False:
				pass
			else:
				print "Interpolating..."
				img_int = interpol(img, ss_in, ss_out, interpolationmethod, showgraph)
				## Error handling from 'interpol' function
				if type(img_int) == str:
					print img_int
					return
				elif img_int != None:
					print "Saving interpolated stack as: ", file_out_int
					tf.imsave(file_out_int, img_int)
					print "		...done."

def interpol(img, ss_in, ss_out, interpolationmethod, showgraph):
	## Depending on tiff format the file can have a different shapes; e.g. z,y,x or c,z,y,x
	if len(img.shape) == 4 and img.shape[0] == 1:
		img = np.squeeze(img, axis=0)
	else:
		return "ERROR: I'm sorry, I cannot handle multichannel files!"

	if len(img.shape) == 3:
		## Number of slices in original stack
		sl_in = img.shape[0]
		## Number of slices in interpolated stack
		sl_out = int((sl_in-1)*(ss_in/ss_out))+1	# discarding last data point. e.g. 56 in i.e. 
													# 55 steps * (309nm original spacing/161.25nm new spacing) = 105.39 -> int()=105 + 1 = 106
		## Interpolatet image stack shape
		img_int_shape = (sl_out, img.shape[1], img.shape[2])
	else:
		return "ERROR: I only know tiff stack image formats in z,y,x or c,z,y,x with one channel"

	if showgraph == True:
		if __name__ == '__main__':
			showgraph_(img, ss_in, ss_out, sl_in, sl_out, block=False)
		else:
			showgraph_(img, ss_in, ss_out, sl_in, sl_out, block=True)
	if interpolationmethod == 'none':
		return None
	elif interpolationmethod == 'linear':
		print "Nr. of slices (in/out): ", sl_in, sl_out
		return linear(img, img_int_shape, ss_in, ss_out, sl_in, sl_out)
	elif interpolationmethod == 'spline':
		print "Nr. of slices (in/out): ", sl_in, sl_out
		return spline(img, img_int_shape, ss_in, ss_out, sl_in, sl_out)
	else:
		return "Please specify the interpolation method ('linear', 'spline', 'none')."

def showgraph_(img, ss_in, ss_out, sl_in, sl_out, block=True):
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

	zxnew = np.arange(0, (sl_in-1)*ss_in/ss_out, 1) # First slice of original and interpolated are both 0. n-1 to discard last slize
	zynew_lin = lin(zxnew)
	zynew_spl = spl(zxnew)
	## Ploting data. blue = original, red = interpolated with interp1d, green = spline interpolation
	plt.plot(zx, zy, 'bo-', label='original')
	plt.plot(zxnew, zynew_lin, 'rx-', label='linear')
	plt.plot(zxnew, zynew_spl, 'g*-', label='spline')
	plt.legend(loc='upper left')
	if block == True:
		print "######## \nPAUSED: Please close graph in order to continue with the programm \n########"
	plt.show(block)

def spline(img, img_int_shape, ss_in, ss_out, sl_in, sl_out):
	## Known x values in interpolated stack size.
	zx = np.arange(0,sl_out,(ss_in/ss_out))
	zxnew = np.arange(0, (sl_in-1)*ss_in/ss_out, 1) # First slice of original and interpolated are both 0. n-1 to discard last slize
	if ss_in/ss_out < 1.0:
		zx_mod = []
		for i in range(img.shape[0]):
			zx_mod.append(zx[i])
		zx = zx_mod

	## Create new numpy array for the interpolated image stack
	img_int = np.zeros(img_int_shape,img.dtype)
	print "Interpolated stack shape: ", img_int.shape

	## Data for percentage display
	numofpx = img.shape[-1]*img.shape[-2]

	r_sl_out = range(sl_out)

	ping = time.time()
	for px in range(img.shape[-1]):
		for py in range(img.shape[-2]):
			spl = interpolate.InterpolatedUnivariateSpline(zx, img[:,py,px])
			np.put(img_int[:,py,px], r_sl_out, spl(zxnew))
		sys.stdout.write("\r%d%%" % int(px*100/img.shape[-1]))
		sys.stdout.flush()
	pong = time.time()
	print "This interpolation took {0} seconds".format(pong - ping)
	return img_int


def linear(img, img_int_shape, ss_in, ss_out, sl_in, sl_out):
	##  Determine interpolatet slice positions
	sl_int = np.arange(0,sl_in-1,ss_out/ss_in) # sl_in-1 because last slice is discarded (no extrapolation)

	## Create new numpy array for the interpolated image stack
	img_int = np.zeros(img_int_shape,img.dtype)
	print "Interpolated stack shape: ", img_int.shape

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
	print "This interpolation took {0} seconds".format(pong - ping)
	return img_int

def norm_img(img,copy=False):
	if copy == True: img = np.copy(img)
	dtype = str(img.dtype)
	if dtype == "uint16" or dtype == "int16": typesize = 65535
	elif dtype == "uint8" or dtype == "int8": typesize = 255
	elif dtype == "float32" or dtype == "float64": typesize = 1
	else: print "Sorry, I don't know this file type yet: ", dtype
	## 2D image
	if len(img.shape) == 2: img *= typesize/img.max()
	## 3D or multichannel image
	elif len(img.shape) == 3:
		for i in range(int(img.shape[0])):
			img[i,:,:] *= typesize/img[i,:,:].max()
	## 3D and multichannel image
	elif len(img.shape) == 4:
		for i in range(int(img.shape[0])):
			for ii in range(int(img.shape[1])):
				img[i,ii,:,:] *= typesize/img[i,ii,:,:].max()
	return img


if __name__ == '__main__':
	import Tkinter,tkFileDialog,ttk,tkSimpleDialog,tkMessageBox

	## Initial UI setup
	root = Tkinter.Tk()
	root.title("Image Stack Tool")
	T = Tkinter.Text(root, height=10, width=100)
	T.grid(row=0,column=0,columnspan=2)
	T.insert(Tkinter.END,
	"""IMAGE STACK TOOL - 0.1 - by Jan Arnold

	This application can interpolate/nomalize image stacks and/or merge an image sequence
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
		ss_in = tkSimpleDialog.askfloat(parent=root, title='Enter ORIGINAL focus step size', prompt='Enter ORIGINAL focus step size for:\n'+'\n'.join('{}'.format(k) for k in filenames))
		if not ss_in: return
		ss_out = tkSimpleDialog.askfloat(parent=root, title='Enter INTERPOLATED focus step size', prompt='Enter INTERPOLATED focus step size for:\n'+'\n'.join('{}'.format(k) for k in filenames))
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
		ss_in = tkSimpleDialog.askfloat(parent=root, title='Enter ORIGINAL focus step size', prompt='Enter ORIGINAL focus step size for:\n{0}'.format(os.path.split(directory)[1]))
		if not ss_in: return
		ss_out = tkSimpleDialog.askfloat(parent=root, title='Enter INTERPOLATED focus step size', prompt='Enter INTERPOLATED focus step size for:\n{0}'.format(os.path.split(directory)[1]))
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
	B1 = Tkinter.Button(root, text = "Interpolate single stack file(s)...", command = getfiles)
	B1.config(width = 50)
	B1.grid(row=5,column=0,columnspan=2)
	B2 = Tkinter.Button(root, text = "Interpolate image sequence...", command = getdirint)
	B2.config(width = 50)
	B2.grid(row=6,column=0,columnspan=2)
	B3 = Tkinter.Button(root, text = "Just convert image stack sequence to single stack files...", command = getdircon)
	B3.config(width = 50)
	B3.grid(row=7,column=0,columnspan=2)
	B4 = Tkinter.Button(root, text = "Normalize image(stack) files...", command = normalize)
	B4.config(width = 50)
	B4.grid(row=8,column=0,columnspan=2)
	B5 = Tkinter.Button(root, text = "Create normalized MIP of image stack files...", command = mip)
	B5.config(width = 50)
	B5.grid(row=9,column=0,columnspan=2)
	### Checkboxes
	c = Tkinter.Checkbutton(root, text="Show graph comparing interpolation methods", variable=showgraph)
	c.grid(row=4,column=0,sticky=Tkinter.W,padx=100)

	## Run Tkinter main loop
	root.mainloop()



