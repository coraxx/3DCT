#!/usr/bin/env python
#title				: isbs.py
#description		: Display two images side by side in PyQt4 widget. Widget design fom ui file.
#author				: Jan Arnold
#email				: jan.arnold (at) coraxx.net
#credits			: 
#maintainer			: Jan Arnold
#date				: 2015/09
#version			: 0.1
#status				: developement
#usage				: python isbs.py path_to_img1 path_to_img2 display_size_in_px
#					: e.g: python isbs.py img1.tif img2.tif 600
#notes				: 
#python_version		: 2.7.10 
#=================================================================================
import sys
import os
from PyQt4 import QtCore, QtGui, uic
import numpy as np
import cv2
import tifffile as tf
## Colored stdout
import clrmsg

execdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(execdir)

qtCreatorFile_main =  os.path.join(execdir, "TDCT_correlation.ui")
Ui_WidgetWindow, QtBaseClass = uic.loadUiType(qtCreatorFile_main)

class GraphicsSceneHandler(QtGui.QGraphicsScene):
	def __init__(self, parent=None):
		QtGui.QGraphicsScene.__init__(self,parent)
		self.parent = parent
		self.parent.setDragMode(QtGui.QGraphicsView.NoDrag)
		## set standard pen color
		self.pen = QtGui.QPen(QtCore.Qt.red)
		self.lastScreenPos = QtCore.QPoint(0, 0)
		self.lastScenePos = 0

	def wheelEvent(self, event):
		## Scaling
		if event.delta() > 0:
			scalingFactor = 1.15
		else:
			scalingFactor = 1 / 1.15
		self.parent.scale(scalingFactor, scalingFactor)
		## Center on mouse pos only if mouse moved mor then 25px
		if (event.screenPos()-self.lastScreenPos).manhattanLength() > 25:
			self.parent.centerOn(event.scenePos().x(), event.scenePos().y())
			self.lastScenePos = event.scenePos()
		else:
			self.parent.centerOn(self.lastScenePos.x(), self.lastScenePos.y())
		## Save pos for precise scrolling, i.e. centering view only when mouse moved
		self.lastScreenPos = event.screenPos()

	def mousePressEvent(self, event):
		modifiers = QtGui.QApplication.keyboardModifiers()
		if event.button() == QtCore.Qt.LeftButton and modifiers != QtCore.Qt.ControlModifier:
			self.parent.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
		elif event.button() == QtCore.Qt.LeftButton and modifiers == QtCore.Qt.ControlModifier:
			self.parent.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
		elif event.button() == QtCore.Qt.RightButton:
			lol = self.addEllipse(event.scenePos().x()-10, event.scenePos().y()-10, 20, 20, self.pen)
			lol.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
			lol.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
		elif event.button() == QtCore.Qt.MiddleButton:
			if isinstance(self.itemAt(event.scenePos()), QtGui.QGraphicsEllipseItem):
				self.removeItem(self.itemAt(event.scenePos()))

	def mouseReleaseEvent(self, event):
		self.parent.setDragMode(QtGui.QGraphicsView.NoDrag)

	def keyPressEvent(self, event):
		if event.key() == QtCore.Qt.Key_Delete:
			for item in self.selectedItems(): self.removeItem(item)


class MainWidget(QtGui.QWidget, Ui_WidgetWindow):
	def __init__(self, parent=None, left=None, right=None):
		QtGui.QWidget.__init__(self, parent)
		Ui_WidgetWindow.__init__(self)
		self.setupUi(self)
		self.debug = True

		## store parameters for resizing
		self.parent = parent
		self.size = 500
		self.left = left
		self.right = right

		## Initialize parameters
		self.rotangle_left = 0
		self.rotangle_right = 0
		## Initialize Images
		self.initImageLeft()
		self.initImageRight()

		# SpinBoxes
		self.spinBox_rot.valueChanged.connect(self.rotateImage)

		## Buttons
		self.toolButton_rotcw.clicked.connect( lambda: self.rotateImage45(direction='cw' ))
		self.toolButton_rotccw.clicked.connect(lambda: self.rotateImage45(direction='ccw'))
		self.pushButton_test.clicked.connect(self.test)

		## Sliders
		self.horizontalSlider_brightness.valueChanged.connect(self.adjustBrightCont)
		self.horizontalSlider_contrast.valueChanged.connect(self.adjustBrightCont)
		## Capture focus change events
		QtCore.QObject.connect(app, QtCore.SIGNAL("focusChanged(QWidget *, QWidget *)"), self.changedFocusSlot)

	def test(self):
		## Remove image (item)
		self.sceneRight.removeItem(self.pixmap_item_right)
		## Load replacement
		self.pixmap_right = QtGui.QPixmap('/Volumes/Silver/Dropbox/Dokumente/Code/test_stuff/px_test_red.tif')
		self.pixmap_item_right = QtGui.QGraphicsPixmapItem(self.pixmap_right, None, self.sceneRight)
		## Put exchanged image into background
		QtGui.QGraphicsItem.stackBefore(self.pixmap_item_right, self.sceneRight.items()[-1])

	def changedFocusSlot(self, former, current):
		if self.debug == True: print clrmsg.DEBUG + "focus changed from/to:", former, current
		if current:
			self.currentFocusedWidgetName = current.objectName()
			self.currentFocusedWidget = current
		if former:
			self.formerFocusedWidgetName = former.objectName()
			self.formerFocusedWidget = former

		## Feed saved rotation angle value from selected image to spinbox
		if self.currentFocusedWidgetName == 'graphicsView_left':
			self.spinBox_rot.setValue(self.rotangle_left)
		elif self.currentFocusedWidgetName == 'graphicsView_right':
			self.spinBox_rot.setValue(self.rotangle_right)

		## Lable showing selected image
		if self.currentFocusedWidgetName == 'spinBox_rot':
			pass
		else:
			if self.currentFocusedWidgetName != 'graphicsView_left' and self.currentFocusedWidgetName != 'graphicsView_right':
				self.label_selimg.setStyleSheet("color: rgb(255, 190, 0);")
				self.label_selimg.setText('none')
			elif self.currentFocusedWidgetName == 'graphicsView_left':
				self.label_selimg.setStyleSheet("color: rgb(0, 225, 90);")
				self.label_selimg.setText('left')
			elif self.currentFocusedWidgetName == 'graphicsView_right':
				self.label_selimg.setStyleSheet("color: rgb(0, 190, 255);")
				self.label_selimg.setText('right')

	def initImageLeft(self):
		if self.left != None:
			## Changed GraphicsSceneLeft(self) to GraphicsSceneHandler(self.graphicsView_left) to reuse class for both scenes
			self.sceneLeft = GraphicsSceneHandler(self.graphicsView_left)
			## Load image and assign to scene
			self.img_left = self.imread(self.left)
			#self.pixmap_left = QtGui.QPixmap(self.left)
			self.pixmap_left = self.cv2Qimage(self.img_left)
			self.pixmap_item_left = QtGui.QGraphicsPixmapItem(self.pixmap_left, None, self.sceneLeft)
			## connect scenes to gui elements
			self.graphicsView_left.setScene(self.sceneLeft)
			## reset scaling (needed for reinizialization)
			self.graphicsView_left.resetMatrix()
			## scaling scene, not image
			scaling_factor = float(self.size)/max(self.pixmap_left.width(), self.pixmap_left.height())
			self.graphicsView_left.scale(scaling_factor,scaling_factor)

	def initImageRight(self):
		if self.right != None:
			self.sceneRight = GraphicsSceneHandler(self.graphicsView_right)
			## set pen color yellow
			self.sceneRight.pen = QtGui.QPen(QtCore.Qt.yellow)
			## Load image and assign to scene
			self.img_right = self.imread(self.right)
			#self.pixmap_right = QtGui.QPixmap(self.right)
			self.pixmap_right = self.cv2Qimage(self.img_right)
			self.pixmap_item_right = QtGui.QGraphicsPixmapItem(self.pixmap_right, None, self.sceneRight)
			## connect scenes to gui elements
			self.graphicsView_right.setScene(self.sceneRight)
			## reset scaling (needed for reinizialization)
			self.graphicsView_right.resetMatrix()
			## scaling scene, not image
			scaling_factor = float(self.size)/max(self.pixmap_right.width(), self.pixmap_right.height())
			self.graphicsView_right.scale(scaling_factor,scaling_factor)

	def rotateImage(self):
		if self.currentFocusedWidgetName == 'spinBox_rot':
			if self.formerFocusedWidgetName != 'graphicsView_left' and self.formerFocusedWidgetName != 'graphicsView_right':
				print clrmsg.ERROR + "Please click on the image you want to rotate."
			elif self.formerFocusedWidgetName == 'graphicsView_left':
				if int(self.spinBox_rot.value()) == 360:
					self.spinBox_rot.setValue(0)
				elif int(self.spinBox_rot.value()) == -1:
					self.spinBox_rot.setValue(359)
				self.graphicsView_left.rotate(int(self.spinBox_rot.value())-self.rotangle_left)
				self.rotangle_left = int(self.spinBox_rot.value())
			elif self.formerFocusedWidgetName == 'graphicsView_right':
				if int(self.spinBox_rot.value()) == 360:
					self.spinBox_rot.setValue(0)
				elif int(self.spinBox_rot.value()) == -1:
					self.spinBox_rot.setValue(359)
				self.graphicsView_right.rotate(int(self.spinBox_rot.value())-self.rotangle_right)
				self.rotangle_right = int(self.spinBox_rot.value())

	def rotateImage45(self,direction=None):
		if self.currentFocusedWidgetName == 'spinBox_rot':
			cfwn = self.formerFocusedWidgetName
		else:
			cfwn = self.currentFocusedWidgetName
		if cfwn != 'graphicsView_left' and cfwn != 'graphicsView_right':
			print clrmsg.ERROR + "Please click on the image you want to rotate."
		elif direction == None:
			print clrmsg.ERROR + "Please specify direction ('cw' or 'ccw')."
		# rotate 45 degree clockwise
		elif direction == 'cw':
			if cfwn == 'graphicsView_left':
				self.rotangle_left = self.rotangle_left+45
				self.graphicsView_left.rotate(45)
				self.rotangle_left = self.anglectrl(angle=self.rotangle_left)
				self.spinBox_rot.setValue(self.rotangle_left)
			elif cfwn == 'graphicsView_right':
				self.rotangle_right = self.rotangle_right+45
				self.graphicsView_right.rotate(45)
				self.rotangle_right = self.anglectrl(angle=self.rotangle_right)
				self.spinBox_rot.setValue(self.rotangle_right)
		# rotate 45 degree anticlockwise
		elif direction == 'ccw':
			if cfwn == 'graphicsView_left':
				self.rotangle_left = self.rotangle_left-45
				self.graphicsView_left.rotate(-45)
				self.rotangle_left = self.anglectrl(angle=self.rotangle_left)
				self.spinBox_rot.setValue(self.rotangle_left)
			elif cfwn == 'graphicsView_right':
				self.rotangle_right = self.rotangle_right-45
				self.graphicsView_right.rotate(-45)
				self.rotangle_right = self.anglectrl(angle=self.rotangle_right)
				self.spinBox_rot.setValue(self.rotangle_right)

	def anglectrl(self,angle=None):
		if angle == None:
			print clrmsg.ERROR + "Please specify side, e.g. anglectrl(angle=self.rotangle_left)"
		elif angle >= 360:
			angle = angle-360
		elif angle < 0:
			angle = angle+360
		return angle

	### Image processing functions
	## Read image
	def imread(self,path,normalize=True):
		if self.debug == True: print clrmsg.DEBUG + "##### imread ..."
		img = tf.imread(path)
		if self.debug == True: print clrmsg.DEBUG + "Image shape/dtype:", img.shape, img.dtype
		## Displaying issues with uint16 images -> convert to uint8
		if img.dtype == 'uint16':
			img = img*(255.0/img.max())
			img = img.astype(dtype='uint8')
			if self.debug == True: print clrmsg.DEBUG + "Image dtype converted to:", img.shape, img.dtype
		if img.ndim == 4:
			return self.mip(img)
		## this can only handle rgb. For more channels set "3" to whatever max number of channels should be handled
		elif img.ndim == 3 and any([True for dim in img.shape if dim <= 3]) or img.ndim == 2:
			if self.debug == True: print clrmsg.DEBUG + "Loading regular 2D image... multicolor/normalize:", [True for x in [img.ndim] if img.ndim == 3],'/',[normalize]
			if normalize == True:
				return self.norm_img(img)
			else:
				return img
		elif img.ndim == 3:
			if self.debug == True: print clrmsg.DEBUG + "Calculating MIP..."
			return self.mip(img)

	## Convert opencv image (numpy array in BGR) to RGB QImage and return pixmap. Only takes 2D images
	def cv2Qimage(self,img):
		if self.debug == True: print clrmsg.DEBUG + "##### cv2Qimage ..."
		## Format 2D greyscale to RGB for QImage
		if img.ndim == 2:
			img = cv2.cvtColor(img,cv2.COLOR_GRAY2RGB)
		if img.shape[0] <= 3:
			if self.debug == True: print clrmsg.DEBUG + "Swaping image axes from c,y,x to y,x,c."
			img = img.swapaxes(0,2).swapaxes(0,1)
		if self.debug == True: print clrmsg.DEBUG + "Image shape:", img.shape
		image = QtGui.QImage(img.tobytes(), img.shape[1], img.shape[0], QtGui.QImage.Format_RGB888)#.rgbSwapped()
		return QtGui.QPixmap.fromImage(image)
		#return QtGui.QPixmap('/Users/jan/Desktop/160202/LM-SEM.tif')

	## Adjust Brightness and Contrast by sliders
	def adjustBrightCont(self):
		if self.debug == True: print clrmsg.DEBUG + "##### adjustBrightCont ..."

		if self.currentFocusedWidgetName == 'horizontalSlider_brightness' or self.currentFocusedWidgetName == 'horizontalSlider_contrast':
			if self.formerFocusedWidgetName != 'graphicsView_left' and self.formerFocusedWidgetName != 'graphicsView_right':
				print clrmsg.ERROR + "Please click on the image you want to rotate."
			elif self.formerFocusedWidgetName == 'graphicsView_left':
				self.brightness_left = float(self.horizontalSlider_brightness.value()-100)
				self.contrast_left = float(self.horizontalSlider_contrast.value())*0.1
			elif self.formerFocusedWidgetName == 'graphicsView_right':
				self.brightness_right = float(self.horizontalSlider_brightness.value()-100)
				self.contrast_right = float(self.horizontalSlider_contrast.value())*0.1


		self.brightness = float(self.horizontalSlider_brightness.value()-100)
		self.contrast = float(self.horizontalSlider_contrast.value())*0.1
		self.orig_img_adj = np.copy(self.image)
		self.orig_img_adj = cv2.add(self.orig_img_adj,np.array([self.brightness]))
		self.orig_img_adj = cv2.multiply(self.orig_img_adj,np.array([self.contrast]))
		self.displayImage(self.cc[0],self.cc[1],self.cc[2],self.cc[3])

		## Remove image (item)
		self.sceneRight.removeItem(self.pixmap_item_right)
		## Load replacement
		self.pixmap_right = QtGui.QPixmap('/Volumes/Silver/Dropbox/Dokumente/Code/test_stuff/px_test_red.tif')
		self.pixmap_item_right = QtGui.QGraphicsPixmapItem(self.pixmap_right, None, self.sceneRight)
		## Put exchanged image into background
		QtGui.QGraphicsItem.stackBefore(self.pixmap_item_right, self.sceneRight.items()[-1])

	## Normalize Image
	def norm_img(self,img,copy=False):
		if self.debug == True: print clrmsg.DEBUG + "##### norm_img ..."
		if copy == True:
			img = np.copy(img)
		dtype = str(img.dtype)
		if dtype == "uint16" or dtype == "int16":
			typesize = 65535
		elif dtype == "uint8" or dtype == "int8":
			typesize = 255
		elif dtype == "float32" or dtype == "float64":
			typesize = 1
		else:
			print clrmsg.ERROR + "Sorry, I don't know this file type yet: ", dtype
		## 2D image
		if img.ndim == 2: img *= typesize/img.max()
		## 3D or multichannel image
		elif img.ndim == 3:
			## tiffimage reads z,y,x for stacks but y,x,c if it is multichannel image (or z,c,y,x if it is a multicolor image stack)
			if img.shape[-1] > 3:
				for i in range(int(img.shape[0])):
					img[i,:,:] *= typesize/img[i,:,:].max()
			else:
				for i in range(int(img.shape[2])):
					img[:,:,i] *= typesize/img[:,:,i].max()
		## 3D and multichannel image ###DELETE?!####
		# elif img.ndim == 4:
		# 	for i in range(int(img.shape[0])):
		# 		for ii in range(int(img.shape[1])):
		# 			img[i,ii,:,:] *= typesize/img[i,ii,:,:].max()
		return img

	## Create Maximum Intensity Projection (MIP)
	def mip(self,img):
		if self.debug == True: print clrmsg.DEBUG + "##### mip ..."
		if len(img.shape) == 4:
			img_MIP = np.zeros((img.shape[0],img.shape[2],img.shape[3]), dtype=img.dtype)
			for i in range(0,img.shape[0]):
				for ii in range(0,img.shape[2]):
					for iii in range(0,img.shape[3]):
						img_MIP[i,ii,iii] = img[i,:,ii,iii].max()
			if self.debug == True: print clrmsg.DEBUG + "Image shape original/MIP:", img.shape, img_MIP.shape
			img_MIP = self.norm_img(img_MIP)
			if self.debug == True: print clrmsg.DEBUG + "Image shape normalized MIP:", img_MIP.shape
			return img_MIP
		elif len(img.shape) == 3:
			img_MIP = np.zeros((img.shape[1],img.shape[2]), dtype=img.dtype)
			for i in range(0,img.shape[1]):
				for ii in range(0,img.shape[2]):
					img_MIP[i,ii] = img[:,i,ii].max()
			if self.debug == True: print clrmsg.DEBUG + "Image shape original/MIP:", img.shape, img_MIP.shape
			img_MIP = self.norm_img(img_MIP)
			if self.debug == True: print clrmsg.DEBUG + "Image shape normalized MIP:", img_MIP.shape
			return img_MIP
		else:
			print clrmsg.ERROR + "I'm sorry, I don't know this image shape: {0}".format(img.shape)

if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	## mac
	left = '/Volumes/Silver/Dropbox/Dokumente/Code/test_stuff/IB_030.tif'
	#left = '/Volumes/Silver/Dropbox/Dokumente/Code/test_stuff/IB_030_bw.tif'
	#left = '/Users/jan/Desktop/160202/LM-SEM.tif'
	#left = '/Volumes/Silver/output/MAX_input-0.tif'
	#left = '/Users/jan/Desktop/rofllol.tif'
	#left = '/Volumes/Silver/output/input-0.tif'
	#left = '/Volumes/Silver/output/Composite.tif'
	#left = '/Users/jan/Desktop/LM-SEM.tif'
	right = '/Volumes/Silver/Dropbox/Dokumente/Code/test_stuff/px_test.tif'
	## win
	# left = r'E:\Dropbox\Dokumente\Code\test_stuff\IB_030.tif'
	# right = r'E:\Dropbox\Dokumente\Code\test_stuff\px_test.tif'
	widget = MainWidget(left=left, right=right)
	widget.show()
	sys.exit(app.exec_())