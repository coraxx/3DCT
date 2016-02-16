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

class GraphicsSceneHandler(QtGui.QGraphicsScene):
	def __init__(self, parent=None):
		QtGui.QGraphicsScene.__init__(self,parent)
		self.parent = parent
		self.parent.setDragMode(QtGui.QGraphicsView.NoDrag)
		## set standard pen color red
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
		# print self.selectedItems()

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
			# self.item1 = QtGui.QGraphicsEllipseItem(event.scenePos().x(), event.scenePos().y(), 20, 20)
			# self.item1.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
			# self.item1.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
			# self.addItem(self.item1)
		elif event.button() == QtCore.Qt.MiddleButton:
			if isinstance(self.itemAt(event.scenePos()), QtGui.QGraphicsEllipseItem):
				self.removeItem(self.itemAt(event.scenePos()))
		# elif event.button() == QtCore.Qt.MiddleButton and self.selectedItems():
		# 	for item in self.selectedItems(): self.removeItem(item)
		# print QtGui.QApplication.focusWidget()
		# print dir(QtGui.QApplication)

	# def mouseDoubleClickEvent(self, event):
	# 	pass#self.parent.setDragMode(QtGui.QGraphicsView.RubberBandDrag)

	def mouseReleaseEvent(self, event):
		self.parent.setDragMode(QtGui.QGraphicsView.NoDrag)

	def keyPressEvent(self, event):
		if event.key() == QtCore.Qt.Key_Delete:
			for item in self.selectedItems(): self.removeItem(item)


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
		self.initImageLeft()
		self.initImageRight()

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

		QtCore.QObject.connect(app, QtCore.SIGNAL("focusChanged(QWidget *, QWidget *)"), self.changedFocusSlot)

	def changedFocusSlot(self, old, now):
		print "focus changed to:", QtGui.QApplication.focusWidget().objectName()

	def resizeUI(self):
		if self.size >= 400:
			self.resize(self.size*2.25, self.size*1.125)
		else:
			self.resize(self.size*(2.25+400/self.size*0.2), self.size*(1.125+400/self.size*0.1))
		self.spinBox_size.setValue(self.size)

	def initImageLeft(self):
		if self.left != None:
			## Changed GraphicsSceneLeft(self) to GraphicsSceneHandler(self.graphicsView_left) to reuse class for both scenes
			self.sceneLeft = GraphicsSceneHandler(self.graphicsView_left)

			self.pixmap1 = QtGui.QPixmap(self.left)
			## save original image size
			self.pm1_orig_x, self.pm1_orig_y = self.pixmap1.width(), self.pixmap1.height()
			## scale image
			#self.pixmap1 = self.pixmap1.scaled(self.size, self.size, QtCore.Qt.KeepAspectRatio)
			## save scaled image size
			self.pm1_scaled_x, self.pm1_scaled_y = self.pixmap1.width(), self.pixmap1.height()

			self.pixmap_item1 = QtGui.QGraphicsPixmapItem(self.pixmap1, None, self.sceneLeft)
			## clicking stuff / scrolling in the image
			# self.pixmap_item1.mousePressEvent = self.pixelSelect1
			# self.pixmap_item1.keyPressEvent = self.pixelSelect1
			# self.pixmap_item1.wheelEvent = self.wheelEventLeft

			## connect scenes to gui elements
			self.graphicsView_left.setScene(self.sceneLeft)

			self.scaling_factor1 = float(max([self.pm1_scaled_x, self.pm1_scaled_y]))/max([self.pm1_orig_x, self.pm1_orig_y])
			self.scaling_factor_glob1 = float(self.size)/max(self.pm1_orig_x, self.pm1_orig_y)
			## reset scaling (needed for reinizialization)
			self.graphicsView_left.resetMatrix()
			## scaling scene, not image
			self.graphicsView_left.scale(self.scaling_factor_glob1,self.scaling_factor_glob1)

			# print self.graphicsView_left.DragMode()
			# self.graphicsView_left.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
			# print self.graphicsView_left.DragMode()

			# print "|1| orig:           ", self.pm1_orig_x, self.pm1_orig_y, "   scaled: ", self.pm1_scaled_x, self.pm1_scaled_y
			# print "    Scaling Factor: ", self.scaling_factor1

	def initImageRight(self):
		if self.right != None:
			self.sceneRight = GraphicsSceneHandler(self.graphicsView_right)
			## set pen color yellow
			self.sceneRight.pen = QtGui.QPen(QtCore.Qt.yellow)

			self.pixmap2 = QtGui.QPixmap(self.right)
			## save original image size
			self.pm2_orig_x, self.pm2_orig_y = self.pixmap2.width(), self.pixmap2.height()
			## scale image
			#self.pixmap2 = self.pixmap2.scaled(self.size, self.size, QtCore.Qt.KeepAspectRatio)
			## save scaled image size
			self.pm2_scaled_x, self.pm2_scaled_y = self.pixmap2.width(), self.pixmap2.height()

			self.pixmap_item2 = QtGui.QGraphicsPixmapItem(self.pixmap2, None, self.sceneRight)
			## clicking stuff / scrolling in the image
			# self.pixmap_item2.mousePressEvent = self.pixelSelect2
			# self.pixmap_item2.wheelEvent = self.wheelEventRight

			## connect scenes to gui elements
			self.graphicsView_right.setScene(self.sceneRight)

			self.scaling_factor2 = float(max([self.pm2_scaled_x, self.pm2_scaled_y]))/max([self.pm2_orig_x, self.pm2_orig_y])
			self.scaling_factor_glob2 = float(self.size)/max(self.pm2_orig_x, self.pm2_orig_y)
			## reset scaling (needed for reinizialization)
			self.graphicsView_right.resetMatrix()
			## scaling scene, not image
			self.graphicsView_right.scale(self.scaling_factor_glob2,self.scaling_factor_glob2)

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
		modifiers = QtGui.QApplication.keyboardModifiers()
		print event.key()
		if modifiers == QtCore.Qt.ShiftModifier:
		    print('Shift+Click')
		elif modifiers == QtCore.Qt.ControlModifier:
		    print('Control+Click')
		elif modifiers == (QtCore.Qt.ControlModifier |
		                   QtCore.Qt.ShiftModifier):
		    print('Control+Shift+Click')
		else:
		    print('Click')

		pen = QtGui.QPen(QtCore.Qt.red)
		self.sceneLeft.addEllipse(event.pos().x()-10, event.pos().y()-10, 20, 20, pen)
		print event.pos()

	## just for test purposes - draw circle on mouseclick
	def pixelSelect2(self, event):
		pen = QtGui.QPen(QtCore.Qt.yellow)
		self.sceneRight.addEllipse(event.pos().x()-10, event.pos().y()-10, 20, 20, pen)
		print event.pos()

	def addCircle1(self, x, y):
		pen = QtGui.QPen(QtCore.Qt.red)
		circsize = 36*self.scaling_factor1
		self.sceneLeft.addEllipse(	self.scaling_factor1*x-circsize*0.5,
								self.scaling_factor1*y-circsize*0.5,
								circsize, circsize, pen)
		# print "-"*10
		# print self.scaling_factor1*x, self.scaling_factor1*y

	def addCircle2(self, x, y):
		pen = QtGui.QPen(QtCore.Qt.yellow)
		circsize = 36*self.scaling_factor1
		self.sceneRight.addEllipse(	self.scaling_factor2*x-circsize*0.5,
								self.scaling_factor2*y-circsize*0.5,
								circsize, circsize, pen)
		# print "-"*10
		# print self.scaling_factor1*x, self.scaling_factor1*y

	def increaseWS(self):
		if self.size <= max([self.pm1_orig_x, self.pm1_orig_y, self.pm2_orig_x, self.pm2_orig_y])-50:
			self.size += 50
			self.resizeUI()
			self.initImageLeft()
			self.initImageRight()
			if self.size >= max([self.pm1_orig_x, self.pm1_orig_y, self.pm2_orig_x, self.pm2_orig_y])-50:
				self.toolButton_increaseWS.setEnabled(False)
		self.toolButton_decreaseWS.setEnabled(True)

	def decreaseWS(self):
		if self.size > 250:
			self.size -= 50
			self.resizeUI()
			self.initImageLeft()
			self.initImageRight()
			if self.size <= 250:
				self.toolButton_decreaseWS.setEnabled(False)
		self.toolButton_increaseWS.setEnabled(True)

	def setSize(self, percent):
		self.size = self.spinBox_size.value()
		self.resizeUI()
		self.initImageLeft()
		self.initImageRight()

	def wheelEventLeft(self, event):
		# Scaling
		if event.delta() > 0:
			scalingFactor = 1.15
		else:
			scalingFactor = 1 / 1.15
		self.graphicsView_left.scale(scalingFactor, scalingFactor)

		# Center on mouse pos
		self.graphicsView_left.centerOn(event.pos().x(), event.pos().y())

	def wheelEventRight(self, event):
		# Scaling
		if event.delta() > 0:
			scalingFactor = 1.15
		else:
			scalingFactor = 1 / 1.15
		self.graphicsView_right.scale(scalingFactor, scalingFactor)

		# Center on mouse pos
		self.graphicsView_right.centerOn(event.pos().x(), event.pos().y())

if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	size = 400
	## mac
	left = '/Users/jan/Desktop/pyPhoOvTest/IB_030.tif'
	right = '/Volumes/Silver/Dropbox/Dokumente/Code/test_stuff/px_test.tif'
	## win
	# left = r'E:\Dropbox\Dokumente\Code\test_stuff\IB_030.tif'
	# right = r'E:\Dropbox\Dokumente\Code\test_stuff\px_test.tif'
	widget = MainWidget(size=size, left=left, right=right)
	widget.show()
	sys.exit(app.exec_())