#!/usr/bin/env python
#title				: image_navigation.py
#description		: Creating a MiniMap with zoom selection. Cropped area is
#					  displayed in main window
#author				: Jan Arnold
#email				: jan.arnold (at) coraxx.net
#credits			: 
#maintainer			: Max-Planck-Instute of Biochemistry
#					  Department of Molecular Structural Biology
#date				: 2015/08
#version			: 0.1
#status				: developement
#usage				: python minimap.py
#notes				: 
#python_version		: 2.7.10 
#=================================================================================

import pdb
import cv2
import time
import numpy as np
import tifffile as tf

#img = "/Users/jan/Desktop/pyPhoOvTest/IB_030.tif"
img = "testdata/px_test.tif"
#img = "F:/jan_temp/px_test.tif"
#img = cv2.imread("/Users/jan/Desktop/pyPhoOvTest/pxtest.tif")

class MINIMAP():
	def __init__(self,img_path,normalize=False,parent=None):
		if parent:
			self.parent = parent
		Image = cv2.imread(img_path,-1)
		print len(Image.shape)
		if len(Image.shape) == 2:
			Image = Image*(255.0/Image.max())
			Image = Image.astype(np.uint8)
			Image = cv2.cvtColor(Image,cv2.COLOR_GRAY2RGB)
		print len(Image.shape)
		self.origimgsize = (Image.shape[0],Image.shape[1])
		if normalize == True:
			self.image = self.norm_img(Image,True)
			self.orig_img_adj = np.copy(self.image)
		else:
			self.image = np.copy(Image)
			self.orig_img_adj = np.copy(self.image)
		self.zoomfactor = 1
		self.image_ratio = float(Image.shape[0])/Image.shape[1]
		self.mmresize_factor = 256.0/Image.shape[0]
		self.main_window_width, self.main_window_height = 768, 768
		#self.main_window_height = int(round(self.main_window_width*self.image_ratio))
		self.main_window_size = (self.main_window_width,self.main_window_height)
		self.image_minimap = cv2.resize(Image, (0,0), fx=self.mmresize_factor, fy=self.mmresize_factor)
		self.tmp_mm_img = np.copy(self.image_minimap)
		self.mouse_x = int(self.image_minimap.shape[1]*0.5)
		self.mouse_y = int(self.image_minimap.shape[0]*0.5)
		self.drawRectangle(self.mouse_x,self.mouse_y)
		print self.mouse_x , self.mouse_y
		self.rectangle_draw = False
		self.point_draw = False
		self.click_tic = 0
		#self.poicount = 0 # porbably needless/unused 
		self.exit = False
		print "...initilized "
		print self.image.shape

	def closeWindows(self):
		self.exit = True

	## normalize image for e.g. 12 bit camara information in 16 bit tiff files
	def norm_img(self,img,copy=False):
		if copy == True:
			img = np.copy(img)
		dtype = str(img.dtype)
		if dtype == "uint16" or dtype == "int16":
			typesize = 65535
		elif dtype == "uint8" or dtype == "int8":
			typesize = 255
		else:
			print "Sorry, I don't know this file type yet: " + dtype
		img *= int(typesize/img.max())
		return img

	## executed on change of zoom slider (in cv2 window)
	def zoomTrackbar(self,*args):
		self.zoomfactor = 1-float(cv2.getTrackbarPos("Zoom:", "Mini Map"))*0.01
		self.drawRectangle(self.mouse_x,self.mouse_y)

	## function for drawing rectangle in Mini Map
	def drawRectangle(self,x,y):
		self.tmp_mm_img = np.copy(self.image_minimap)
		# print min([self.image_minimap.shape[0],self.image_minimap.shape[1]])
		self.x_s = int(round(x-min([self.image_minimap.shape[0],self.image_minimap.shape[1]])*self.zoomfactor*0.5))
		self.y_s = int(round(y-min([self.image_minimap.shape[0],self.image_minimap.shape[1]])*self.zoomfactor*0.5))
		self.x_e = int(round(x+min([self.image_minimap.shape[0],self.image_minimap.shape[1]])*self.zoomfactor*0.5))-1
		self.y_e = int(round(y+min([self.image_minimap.shape[0],self.image_minimap.shape[1]])*self.zoomfactor*0.5))-1
		# x borders
		#pdb.set_trace()
		if self.x_s < 0:
			self.x_s = 0
			self.x_e = int(round(min([self.image_minimap.shape[0],self.image_minimap.shape[1]])*self.zoomfactor))-1
		if self.x_e > self.image_minimap.shape[1]:
			self.x_s = int(round(self.image_minimap.shape[1]-min([self.image_minimap.shape[0],self.image_minimap.shape[1]])*self.zoomfactor))
			self.x_e = self.image_minimap.shape[1]-1
		# y borders
		if self.y_s < 0:
			self.y_s = 0
			self.y_e = int(round(min([self.image_minimap.shape[0],self.image_minimap.shape[1]])*self.zoomfactor))-1
		if self.y_e > self.image_minimap.shape[0]:
			self.y_s = int(round(self.image_minimap.shape[0]-min([self.image_minimap.shape[0],self.image_minimap.shape[1]])*self.zoomfactor))
			self.y_e = self.image_minimap.shape[0]-1
		cv2.rectangle(self.tmp_mm_img, (self.x_s,self.y_s), (self.x_e,self.y_e), (0,0,255))
		x1,x2 = int(round(self.x_s/self.mmresize_factor)),int(np.ceil((self.x_e+1)/self.mmresize_factor))
		y1,y2 = int(round(self.y_s/self.mmresize_factor)),int(np.ceil((self.y_e+1)/self.mmresize_factor))
		# since there has to be a round up in the previous step due to crooked scaling, max has to be limited
		x2 = self.image.shape[1] if x2 > self.image.shape[1] else x2
		y2 = self.image.shape[0] if y2 > self.image.shape[0] else y2
		self.displayImage(x1,x2,y1,y2)
		# print x1,y1,x2,y2

	## get mouse actions on Mini Map window with appropriate actions
	def miniMapOnMouse(self,event,x,y,flags,param):
		if event == cv2.EVENT_LBUTTONDOWN:
			self.mouse_x,self.mouse_y = x,y
			self.drawRectangle(x,y)

		elif event == cv2.EVENT_RBUTTONDOWN:
			self.rectangle_draw = True
			self.ix,self.iy = x,y

		elif event == cv2.EVENT_MOUSEMOVE:
			if self.rectangle_draw == True:
				self.tmp_mm_img = np.copy(self.image_minimap)
				cv2.rectangle(self.tmp_mm_img,(self.ix,self.iy),(x,y),(255,0,0))

		elif event == cv2.EVENT_RBUTTONUP:
			self.rectangle_draw = False
			if x != self.ix:
				# when dx smaller than dy -> adjust x
				if abs(x-self.ix) <= abs(y-self.iy):
					if x-self.ix > 0:
						x = (int(round(self.ix+float(abs(y-self.iy)))))
						x1,x2 = self.ix,x
						if x > self.image_minimap.shape[1]:
							self.ix = self.ix-(x-self.image_minimap.shape[1])
							x = self.image_minimap.shape[1]-1
							x2 = x+1
						self.mouse_x = x-(x-self.ix)/2
					else:
						x = (int(round(self.ix-float(abs(y-self.iy)))))
						x1,x2 = x,self.ix
						if x < 0:
							self.ix = self.ix-x
							x = 0
							x1 = x
						self.mouse_x = x+(self.ix-x)/2
					if y-self.iy > 0:
						self.mouse_y = y-(y-self.iy)/2
						y1,y2 = self.iy,y
					else:
						self.mouse_y = y+(self.iy-y)/2
						y1,y2 = y,self.iy
				# when dx greater than dy -> adjust y
				elif abs(x-self.ix) >= abs(y-self.iy):
					if x-self.ix > 0:
						self.mouse_x = x-(x-self.ix)/2
						x1,x2 = self.ix,x
					else:
						self.mouse_x = x+(self.ix-x)/2
						x1,x2 = x,self.ix
					if y-self.iy > 0:
						y = (int(round(self.iy+float(abs(x-self.ix)))))
						y1,y2 = self.iy,y
						if y > self.image_minimap.shape[0]:
							self.iy = self.iy-(y-self.image_minimap.shape[0])
							y = self.image_minimap.shape[0]-1
							y2 = y+1
						self.mouse_y = y-(y-self.iy)/2
					else:
						y = (int(round(self.iy-float(abs(x-self.ix)))))
						y1,y2 = y,self.iy
						if y < 0:
							self.iy = self.iy-y
							y = 0
							y1 = y
						self.mouse_y = y+(self.iy-y)/2
				self.tmp_mm_img = np.copy(self.image_minimap)
				cv2.rectangle(self.tmp_mm_img,(self.ix,self.iy),(x,y),(0,0,255))
				x1,x2 = int(round(x1/self.mmresize_factor)),int(round((x2)/self.mmresize_factor))
				y1,y2 = int(round(y1/self.mmresize_factor)),int(round((y2)/self.mmresize_factor))
				self.displayImage(x1,x2,y1,y2)
				self.zoomfactor = int(round(100-99*float(abs(x-self.ix))/min([self.image_minimap.shape[0],self.image_minimap.shape[1]])))
				cv2.setTrackbarPos("Zoom:", "Mini Map", self.zoomfactor)

	## get mouse actions on Mini Map window with appropriate actions
	def mainImageOnMouse (self,event,x,y,flags,param):
		if event == cv2.EVENT_LBUTTONDOWN:
			self.click_tic = time.time()
			self.point_draw = True
			self.tmp_orig_img = np.copy(self.tmp_orig_img_crop)
			cv2.circle(self.tmp_orig_img, (x,y), 3, (0,255,555), -1)
			cv2.circle(self.tmp_orig_img, (x,y), 10, (0,0,555), 1)
			self.px,self.py = x,y

		elif event == cv2.EVENT_MOUSEMOVE:
			elapsed = time.time() - self.click_tic
			if self.point_draw == True and elapsed > 0.2:
				self.tmp_orig_img = np.copy(self.tmp_orig_img_crop)
				cv2.circle(self.tmp_orig_img, (x,y), 3, (0,255,555), -1)
				self.px,self.py = x,y

		elif event == cv2.EVENT_LBUTTONUP:
			self.point_draw = False
			cv2.circle(self.tmp_orig_img, (self.px,self.py), 10, (0,0,555), 1)

		if event == cv2.EVENT_RBUTTONDOWN:
			try:
				self.point = (self.px,self.py)
			except:
				print "Please set a marker first"
				return

			# calculate scale to original image
			sfactor_CropToOrig = float((self.cc[1]-self.cc[0]))/(self.main_window_width)
			self.px_backscale = self.cc[0]+sfactor_CropToOrig*self.point[0]
			self.py_backscale = self.cc[2]+sfactor_CropToOrig*self.point[1]
			# print "======"
			# print "point in window:			" + str(self.point)
			# print "px backscale:				" + str(self.px_backscale)
			# print "py backscale:				" + str(self.py_backscale)
			# print "crop coords in orig image:		" + str(self.cc)
			# print "sfactor:				" + str(sfactor_CropToOrig)
			# print "-------------------"
			if hasattr(self,'parent'):
				self.parent.addPoint(self.px_backscale,self.py_backscale)

	def mainImageDrawPoint(self,x,y,add=False):
		if add:
			sfactor_CropToOrig = float((self.cc[1]-self.cc[0]))/(self.main_window_width)
			xbs = (x-self.cc[0])/sfactor_CropToOrig
			ybs = (y-self.cc[2])/sfactor_CropToOrig
			cv2.circle(self.tmp_orig_img, (int(round(xbs)),int(round(ybs))), 3, (0,255,0), -1)
		else:
			sfactor_CropToOrig = float((self.cc[1]-self.cc[0]))/(self.main_window_width)
			self.tmp_orig_img = np.copy(self.tmp_orig_img_crop)
			xbs = (x-self.cc[0])/sfactor_CropToOrig
			ybs = (y-self.cc[2])/sfactor_CropToOrig
			cv2.circle(self.tmp_orig_img, (int(round(xbs)),int(round(ybs))), 3, (0,255,0), -1)
			#cv2.circle(self.tmp_orig_img, (x,y), 10, (0,0,555), 1)

	## Adjust Brightness and Contrast when sliders (cv2 Trackbar) are moved
	def adjustBrightCont(self,*args):
		self.brightness = float(cv2.getTrackbarPos("Brightness:", "Mini Map")-100)
		self.contrast = float(cv2.getTrackbarPos("Contrast:", "Mini Map"))*0.1
		self.orig_img_adj = np.copy(self.image)
		self.orig_img_adj = cv2.add(self.orig_img_adj,np.array([self.brightness]))
		self.orig_img_adj = cv2.multiply(self.orig_img_adj,np.array([self.contrast]))
		self.displayImage(self.cc[0],self.cc[1],self.cc[2],self.cc[3])

	## Display image in main image window
	def displayImage(self,x1,x2,y1,y2):
		self.tmp_orig_img = np.copy(self.orig_img_adj)
		self.tmp_orig_img = self.tmp_orig_img[y1:y2, x1:x2] # x2,y2 = number of pixels to cut starting from x1,y1
		self.tmp_orig_img = cv2.resize(self.tmp_orig_img,self.main_window_size)
		self.tmp_orig_img_crop = np.copy(self.tmp_orig_img)
		# access current crop by self.displayImage(self.cc[0],self.cc[1],self.cc[2],self.cc[3])
		self.cc = (x1,x2,y1,y2)

	def scroll(self,key):
		dx = 0
		dy = 0
		px = int(round(10*self.zoomfactor))
		if px == 0:
			px = 1
		# up
		if key in (63232,2490368) and self.cc[2] > 0:
			self.mouse_x,self.mouse_y = self.mouse_x,self.mouse_y-px
			self.drawRectangle(self.mouse_x,self.mouse_y)
			dy = px
		# down
		elif key in (63233,2261440,2621440) and self.cc[3] < self.origimgsize[0]:
			self.mouse_x,self.mouse_y = self.mouse_x,self.mouse_y+px
			self.drawRectangle(self.mouse_x,self.mouse_y)
			dy = -px
		# left
		elif key in (63234,2424832) and self.cc[0] > 0:
			self.mouse_x,self.mouse_y = self.mouse_x-px,self.mouse_y
			self.drawRectangle(self.mouse_x,self.mouse_y)
			dx = px
		# right
		elif key in (63235,2555904) and self.cc[1] < self.origimgsize[1]-px:
			self.mouse_x,self.mouse_y = self.mouse_x+px,self.mouse_y
			self.drawRectangle(self.mouse_x,self.mouse_y)
			dx = -px
		# try:
		# 	x = self.px+dx
		# 	y = self.py+dy
		# 	self.tmp_orig_img = np.copy(self.tmp_orig_img_crop)
		# 	cv2.circle(self.tmp_orig_img, (x,y), 3, (0,255,555), -1)
		# 	cv2.circle(self.tmp_orig_img, (x,y), 10, (0,0,555), 1)
		# 	self.px,self.py = x,y
		# except:
		# 	pass

	def movePoint(self,key):
		try:
			x,y = self.px,self.py
		except:
			print "Please set a marker first"
			return
		if key == 52 and x > 0:
			x -= 1
		if key == 54 and x < self.main_window_width:
			x += 1
		if key == 56 and y > 0:
			y -= 1
		if key == 50 and y < self.main_window_height:
			y += 1
		self.tmp_orig_img = np.copy(self.tmp_orig_img_crop)
		cv2.circle(self.tmp_orig_img, (x,y), 3, (0,255,555), -1)
		cv2.circle(self.tmp_orig_img, (x,y), 10, (0,0,555), 1)
		self.px,self.py = x,y

	def zoomKey(self,key):
		if key == 43 and self.zoomfactor > 0.05:
			self.zoomfactor -= 0.05
		if key == 45 and self.zoomfactor < 1.0:
			self.zoomfactor += 0.05
		self.drawRectangle(self.mouse_x,self.mouse_y)
		self.zoomfactor = int(round(100-100*self.zoomfactor))
		cv2.setTrackbarPos("Zoom:", "Mini Map", self.zoomfactor)


	## Main function running the cv2 windows
	def main(self):
		cv2.namedWindow("Mini Map")
		cv2.namedWindow("Image")
		cv2.resizeWindow("Image",self.main_window_width,self.main_window_height)
		cv2.moveWindow("Mini Map", 10, 60)
		cv2.moveWindow("Image", 400, 30)
		cv2.setMouseCallback("Mini Map",self.miniMapOnMouse)
		cv2.setMouseCallback("Image",self.mainImageOnMouse)
		cv2.createTrackbar("Zoom:", "Mini Map", 0, 99, self.zoomTrackbar)
		cv2.createTrackbar("Brightness:", "Mini Map", 100, 200, self.adjustBrightCont)
		cv2.createTrackbar("Contrast:", "Mini Map", 10, 99, self.adjustBrightCont)
		while True:
			self.zoomfactor = 1-float(cv2.getTrackbarPos("Zoom:", "Mini Map"))*0.01
			cv2.imshow("Mini Map", self.tmp_mm_img)
			cv2.imshow("Image", self.tmp_orig_img)
			key = cv2.waitKey(15)
			# if key != -1:
			# 	print key
			if key == 27 or key == 113:
				try:
					self.parent.close()
				except:
					break
			# down arrow on windows (american keyboard only?!) is 2621440
			if key in (63232,63233,63234,63235,2261440,2621440,2424832,2490368,2555904):
				self.scroll(key)
			if key in (50,52,54,56):
				self.movePoint(key)
			if key in (43,45):
				self.zoomKey(key)
			if self.exit == True:
				break
		cv2.destroyAllWindows()
		return None

## Run this when script is invoked as standalone
if __name__ == '__main__':
	minimap = MINIMAP(img,normalize=True)
	minimap.main()