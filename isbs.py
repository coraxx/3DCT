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

execdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(execdir)

qtCreatorFile_main =  os.path.join(execdir, "TDCT_isbs.ui")
Ui_WidgetWindow, QtBaseClass = uic.loadUiType(qtCreatorFile_main)

class MainWidget(QtGui.QWidget, Ui_WidgetWindow):
	def __init__(self, parent=None, size=400, left=None, right=None):
		QtGui.QWidget.__init__(self, parent)
		Ui_WidgetWindow.__init__(self)
		self.setupUi(self)

		## Initialize parameters
		self.rotangle_left = 0
		self.rotangle_right = 0

		## store parameters for resizing
		self.parent = parent
		self.size = size
		self.left = left
		self.right = right

		self.pm1_orig_x, self.pm1_orig_y, self.pm2_orig_x, self.pm2_orig_y = 0,0,0,0
		self.resizeUI()
		self.initImage1()
		self.initImage2()

		# spinBoxes
		self.spinBox_size.setMaximum(max([self.pm1_orig_x, self.pm1_orig_y, self.pm2_orig_x, self.pm2_orig_y]))
		self.spinBox_size.valueChanged.connect(self.setSize)
		self.spinBox_size.setKeyboardTracking(False)

		self.spinBox_rot_left.valueChanged.connect(lambda: self.rotateImage(side='left'))
		self.spinBox_rot_right.valueChanged.connect(lambda: self.rotateImage(side='right'))

		##buttons
		self.toolButton_increaseWS.clicked.connect(self.increaseWS)
		self.toolButton_decreaseWS.clicked.connect(self.decreaseWS)
		self.toolButton_rotcw_left.clicked.connect(lambda: self.rotateImage45(direction='cw',side='left'))
		self.toolButton_rotccw_left.clicked.connect(lambda: self.rotateImage45(direction='ccw',side='left'))
		self.toolButton_rotcw_right.clicked.connect(lambda: self.rotateImage45(direction='cw',side='right'))
		self.toolButton_rotccw_right.clicked.connect(lambda: self.rotateImage45(direction='ccw',side='right'))

	def resizeUI(self):
		if self.size >= 400:
			self.resize(self.size*2.25, self.size*1.125)
		else:
			self.resize(self.size*(2.25+400/self.size*0.2), self.size*(1.125+400/self.size*0.1))
		self.spinBox_size.setValue(self.size)

	def initImage1(self):
		if self.left != None:
			self.scene1 = QtGui.QGraphicsScene()

			self.pixmap1 = QtGui.QPixmap(self.left)
			## save original image size
			self.pm1_orig_x, self.pm1_orig_y = self.pixmap1.width(), self.pixmap1.height()
			## scale image
			self.pixmap1 = self.pixmap1.scaled(self.size, self.size, QtCore.Qt.KeepAspectRatio)
			## save scaled image size
			self.pm1_scaled_x, self.pm1_scaled_y = self.pixmap1.width(), self.pixmap1.height()

			self.pixmap_item1 = QtGui.QGraphicsPixmapItem(self.pixmap1, None, self.scene1)
			## clicking stuff in the image
			#self.pixmap_item1.mousePressEvent = self.pixelSelect1

			## connect scenes to gui elements
			self.graphicsView_left.setScene(self.scene1)

			self.scaling_factor1 = float(max([self.pm1_scaled_x, self.pm1_scaled_y]))/max([self.pm1_orig_x, self.pm1_orig_y])

			# print "|1| orig:           ", self.pm1_orig_x, self.pm1_orig_y, "   scaled: ", self.pm1_scaled_x, self.pm1_scaled_y
			# print "    Scaling Factor: ", self.scaling_factor1

	def initImage2(self):
		if self.right != None:
			self.scene2 = QtGui.QGraphicsScene()

			self.pixmap2 = QtGui.QPixmap(self.right)
			## save original image size
			self.pm2_orig_x, self.pm2_orig_y = self.pixmap2.width(), self.pixmap2.height()
			## scale image
			self.pixmap2 = self.pixmap2.scaled(self.size, self.size, QtCore.Qt.KeepAspectRatio)
			## save scaled image size
			self.pm2_scaled_x, self.pm2_scaled_y = self.pixmap2.width(), self.pixmap2.height()

			self.pixmap_item2 = QtGui.QGraphicsPixmapItem(self.pixmap2, None, self.scene2)
			## clicking stuff in the image
			#self.pixmap_item2.mousePressEvent = self.pixelSelect2

			## connect scenes to gui elements
			self.graphicsView_right.setScene(self.scene2)

			self.scaling_factor2 = float(max([self.pm2_scaled_x, self.pm2_scaled_y]))/max([self.pm2_orig_x, self.pm2_orig_y])

			# print "|2| orig:           ", self.pm2_orig_x, self.pm2_orig_y, "   scaled: ", self.pm2_scaled_x, self.pm2_scaled_y
			# print "    Scaling Factor: ", self.scaling_factor2

	def rotateImage(self,side=None):
		if side == None:
			print "Please specify side, e.g. rotateImage(side='left')"
		elif side == 'left':
			if int(self.spinBox_rot_left.value()) == 360:
				self.spinBox_rot_left.setValue(0)
			elif int(self.spinBox_rot_left.value()) == -1:
				self.spinBox_rot_left.setValue(359)
			self.graphicsView_left.rotate(int(self.spinBox_rot_left.value())-self.rotangle_left)
			self.rotangle_left = int(self.spinBox_rot_left.value())
		elif side == 'right':
			if int(self.spinBox_rot_right.value()) == 360:
				self.spinBox_rot_right.setValue(0)
			elif int(self.spinBox_rot_right.value()) == -1:
				self.spinBox_rot_right.setValue(359)
			self.graphicsView_right.rotate(int(self.spinBox_rot_right.value())-self.rotangle_right)
			self.rotangle_right = int(self.spinBox_rot_right.value())

	def rotateImage45(self,direction=None,side=None):
		if direction == None or side == None:
			print "Please specify side and angle, e.g. rotateImage45(direction='cw',side='left')"
		# rotate 45 degree clockwise
		elif direction == 'cw':
			if side == 'left':
				self.rotangle_left = self.rotangle_left+45
				self.graphicsView_left.rotate(45)
				self.rotangle_left = self.anglectrl(angle=self.rotangle_left)
				self.spinBox_rot_left.setValue(self.rotangle_left)
			elif side == 'right':
				self.rotangle_right = self.rotangle_right+45
				self.graphicsView_right.rotate(45)
				self.rotangle_right = self.anglectrl(angle=self.rotangle_right)
				self.spinBox_rot_right.setValue(self.rotangle_right)
		# rotate 45 degree anticlockwise
		elif direction == 'ccw':
			if side == 'left':
				self.rotangle_left = self.rotangle_left-45
				self.graphicsView_left.rotate(-45)
				self.rotangle_left = self.anglectrl(angle=self.rotangle_left)
				self.spinBox_rot_left.setValue(self.rotangle_left)
			elif side == 'right':
				self.rotangle_right = self.rotangle_right-45
				self.graphicsView_right.rotate(-45)
				self.rotangle_right = self.anglectrl(angle=self.rotangle_right)
				self.spinBox_rot_right.setValue(self.rotangle_right)

	def anglectrl(self,angle=None):
		if angle == None:
			print "Please specify side, e.g. anglectrl(angle=self.rotangle_left)"
		elif angle >= 360:
			angle = angle-360
		elif angle < 0:
			angle = angle+360
		return angle

	## just for test purposes - draw circle on mouseclick
	def pixelSelect1(self, event):
		pen = QtGui.QPen(QtCore.Qt.red)
		self.scene1.addEllipse(event.pos().x()-10, event.pos().y()-10, 20, 20, pen)
		print event.pos()

	## just for test purposes - draw circle on mouseclick
	def pixelSelect2(self, event):
		pen = QtGui.QPen(QtCore.Qt.yellow)
		self.scene2.addEllipse(event.pos().x()-10, event.pos().y()-10, 20, 20, pen)
		print event.pos()

	def addCircle1(self, x, y):
		pen = QtGui.QPen(QtCore.Qt.red)
		circsize = 36*self.scaling_factor1
		self.scene1.addEllipse(	self.scaling_factor1*x-circsize*0.5,
								self.scaling_factor1*y-circsize*0.5,
								circsize, circsize, pen)
		# print "-"*10
		# print self.scaling_factor1*x, self.scaling_factor1*y

	def addCircle2(self, x, y):
		pen = QtGui.QPen(QtCore.Qt.yellow)
		circsize = 36*self.scaling_factor1
		self.scene2.addEllipse(	self.scaling_factor2*x-circsize*0.5,
								self.scaling_factor2*y-circsize*0.5,
								circsize, circsize, pen)
		# print "-"*10
		# print self.scaling_factor1*x, self.scaling_factor1*y

	def increaseWS(self):
		if self.size <= max([self.pm1_orig_x, self.pm1_orig_y, self.pm2_orig_x, self.pm2_orig_y])-50:
			self.size += 50
			self.resizeUI()
			self.initImage1()
			self.initImage2()
			if self.size >= max([self.pm1_orig_x, self.pm1_orig_y, self.pm2_orig_x, self.pm2_orig_y])-50:
				self.toolButton_increaseWS.setEnabled(False)
		self.toolButton_decreaseWS.setEnabled(True)

	def decreaseWS(self):
		if self.size > 250:
			self.size -= 50
			self.resizeUI()
			self.initImage1()
			self.initImage2()
			if self.size <= 250:
				self.toolButton_decreaseWS.setEnabled(False)
		self.toolButton_increaseWS.setEnabled(True)

	def setSize(self, percent):
		self.size = self.spinBox_size.value()
		self.resizeUI()
		self.initImage1()
		self.initImage2()

if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	size = 400
	left = '/Users/jan/Desktop/pyPhoOvTest/IB_030.tif'
	right = '/Volumes/Silver/Dropbox/Dokumente/Code/px_test.tif'
	widget = MainWidget(size=size, left=left, right=right)
	widget.show()
	sys.exit(app.exec_())