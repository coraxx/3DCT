#!/usr/bin/env python
#title				: correlation-widget.py
#description		: Extracting 2D and 3D points for 2D to 3D correlation
#author				: Jan Arnold
#email				: jan.arnold (at) coraxx.net
#credits			: 
#maintainer			: Jan Arnold
#date				: 2015/09
#version			: 0.1
#status				: developement
#usage				: part of 3D Correlation Toolbox
#					: 
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

class QGraphicsSceneCustom(QtGui.QGraphicsScene):
	def __init__(self, parent=None,name=None,model=None):
		QtGui.QGraphicsScene.__init__(self,parent)
		self.parent = parent
		self.name = name
		self.model = model
		self.parent.setDragMode(QtGui.QGraphicsView.NoDrag)
		## set standard pen color
		self.pen = QtGui.QPen(QtCore.Qt.red)
		self.lastScreenPos = QtCore.QPoint(0, 0)
		self.lastScenePos = 0
		self.selectionmode = False
		self.pointidx = 1
		## Circle size
		self.cs = 10

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
			## Model does not to be refreshed every time while navigating
			return
		elif event.button() == QtCore.Qt.LeftButton and modifiers == QtCore.Qt.ControlModifier:
			self.parent.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
			self.selectionmode = True
			## Model does not to be refreshed every time while selecting
			return
		elif event.button() == QtCore.Qt.RightButton:
			## First add at 0,0 then move to get position from item.scenePos() or .x() and y.()
			circle = self.addEllipse(-self.cs/2, -self.cs/2, self.cs, self.cs, self.pen)
			circle.setPos(event.scenePos().x(), event.scenePos().y())
			circle.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
			circle.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
			## Reorder to have them in ascending order in the tableview
			QtGui.QGraphicsItem.stackBefore(circle, self.items()[-2])
			self.enumeratePoints()
			#self.addPointToModel(event.scenePos().x(), event.scenePos().y())
		elif event.button() == QtCore.Qt.MiddleButton:
			item = self.itemAt(event.scenePos())
			if isinstance(item, QtGui.QGraphicsEllipseItem):
				#print item.mapToScene(0, 0).x(),item.mapToScene(0, 0).y()
				# print item.x(),item.y()
				# item.setPos(100.0,100.0)
				# print item.x(),item.y()
				self.removeItem(item)
				self.enumeratePoints()
		self.itemsToModel()

	def mouseReleaseEvent(self, event):
		## Reinitialize mouseReleaseEvent handling from QtGui.QGraphicsScene for item drag and drop feature
		super(QGraphicsSceneCustom, self).mouseReleaseEvent(event)
		## Only update position when single item is drag and dropped
		if self.selectedItems() and self.selectionmode == False:
			#print 'New pos:', self.selectedItems()[0].x(), self.selectedItems()[0].y()
			self.clearSelection()
			self.itemsToModel()
		self.parent.setDragMode(QtGui.QGraphicsView.NoDrag)
		self.selectionmode = False

	def keyPressEvent(self, event):
		if event.key() == QtCore.Qt.Key_Delete:
			for item in self.selectedItems(): self.removeItem(item)
			self.itemsToModel()

	def enumeratePoints(self):
		## Remove numbering
		for item in self.items():
			if isinstance(item, QtGui.QGraphicsSimpleTextItem) or isinstance(item, QtGui.QGraphicsLineItem):
				self.removeItem(item)
		pointidx = 1
		for item in self.items():
			if isinstance(item, QtGui.QGraphicsEllipseItem):
				nr = self.addSimpleText(str(pointidx),QtGui.QFont("Helvetica", pointSize = self.cs))
				nr.setParentItem(item)
				nr.setPos(self.cs/2,self.cs/4)
				#nr.setPen(self.pen) # outline
				nr.setBrush(QtCore.Qt.cyan) # fill
				## Adding crosshair
				hline = self.addLine(-self.cs/2-2,0,self.cs/2+2,0)
				hline.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 128)))# r,g,b,alpha
				hline.setParentItem(item)
				vline = self.addLine(0,-self.cs/2-2,0,self.cs/2+2)
				vline.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 128)))# r,g,b,alpha
				vline.setParentItem(item)
				## Counter
				pointidx += 1

	def itemsToModel(self):
		self.model.removeRows(0,self.model.rowCount())
		for item in self.items():
			if isinstance(item, QtGui.QGraphicsEllipseItem):
				x_item = QtGui.QStandardItem(str(item.x()))
				y_item = QtGui.QStandardItem(str(item.y()))
				x_item.setFlags(x_item.flags() & ~QtCore.Qt.ItemIsDropEnabled)
				y_item.setFlags(y_item.flags() & ~QtCore.Qt.ItemIsDropEnabled)
				items = [x_item, y_item]
				self.model.appendRow(items)
				self.model.setHeaderData(0, QtCore.Qt.Horizontal,'x')
				self.model.setHeaderData(1, QtCore.Qt.Horizontal,'y')

	# def addPointToModel(self,x,y):
	# 	x_item = QtGui.QStandardItem(str(x))
	# 	y_item = QtGui.QStandardItem(str(y))
	# 	x_item.setFlags(x_item.flags() & ~QtCore.Qt.ItemIsDropEnabled)
	# 	y_item.setFlags(y_item.flags() & ~QtCore.Qt.ItemIsDropEnabled)
	# 	items = [x_item, y_item]
	# 	model = getattr(widget, "%s" % "model_"+self.name)
	# 	model.appendRow(items)
	# 	model.setHeaderData(0, QtCore.Qt.Horizontal,'x')
	# 	model.setHeaderData(1, QtCore.Qt.Horizontal,'y')

# class StandardItemModelHandler(QtGui.QStandardItemModel):
# 	def __init__(self, parent=None):
# 		QtGui.QStandardItemModel.__init__(self,parent)
# 		self.parent = parent

# 	def mousePressEvent(self, event):
# 		print 'click from', self.objectName()

class MainWidget(QtGui.QWidget, Ui_WidgetWindow):
	def __init__(self, parent=None, left=None, right=None):
		QtGui.QWidget.__init__(self, parent)
		Ui_WidgetWindow.__init__(self)
		self.setupUi(self)
		self.debug = True

		## Tableview and models
		print dir(self.tableView_left.model)
		self.model_left = QtGui.QStandardItemModel(self)
		print dir(self.model_left)
		self.tableView_left.setModel(self.model_left)
		self.model_right = QtGui.QStandardItemModel(self)
		self.tableView_right.setModel(self.model_right)

		self.tableView_left.setDragDropOverwriteMode(False)
		self.tableView_left.setDragEnabled(True)
		self.tableView_left.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
		self.tableView_right.setDragDropOverwriteMode(False)
		self.tableView_right.setDragEnabled(True)
		self.tableView_right.setDragDropMode(QtGui.QAbstractItemView.InternalMove)

		print dir(self.tableView_left.model)

		## store parameters for resizing
		self.parent = parent
		self.size = 500
		self.left = left
		self.right = right

		## Initialize parameters
		self.rotangle_left = 0
		self.rotangle_right = 0
		self.brightness_left = 0
		self.contrast_left = 10
		self.brightness_right = 0
		self.contrast_right = 10
		## Initialize Images
		self.initImageLeft()
		self.initImageRight()

		## connect item change signal to write changes in model back to QGraphicItems
		# self.model_left.itemChanged.connect(lambda: self.updateItems(self.model_left,self.sceneLeft))
		# self.model_right.itemChanged.connect(lambda: self.updateItems(self.model_right,self.sceneRight))

		self.model_left.itemChanged.connect(self.tableView_left.updateItems)
		self.model_right.itemChanged.connect(self.tableView_right.updateItems)

		# self.tableView_left.selectionModel().selectionChanged.connect(lambda: self.showSelectedItem(self.tableView_left,self.sceneLeft))
		# self.tableView_right.selectionModel().selectionChanged.connect(lambda: self.showSelectedItem(self.tableView_right,self.sceneRight))
		self.tableView_left.selectionModel().selectionChanged.connect(self.tableView_left.showSelectedItem)
		self.tableView_right.selectionModel().selectionChanged.connect(self.tableView_right.showSelectedItem)

		#self.tableView_left.doubleClicked.connect(lambda: self.deleteItem(self.tableView_right,self.model_right,self.sceneRight))
		#keyPressEvent(QtCore.Qt.Key_Delete)

		# SpinBoxes
		self.spinBox_rot.valueChanged.connect(self.rotateImage)

		## Buttons
		self.toolButton_rotcw.clicked.connect( lambda: self.rotateImage45(direction='cw' ))
		self.toolButton_rotccw.clicked.connect(lambda: self.rotateImage45(direction='ccw'))
		self.pushButton_test.clicked.connect(self.test)
		self.toolButton_brightness_reset.clicked.connect(lambda: self.horizontalSlider_brightness.setValue(0))
		self.toolButton_contrast_reset.clicked.connect(lambda: self.horizontalSlider_contrast.setValue(10))

		## Sliders
		self.horizontalSlider_brightness.valueChanged.connect(self.adjustBrightCont)
		self.horizontalSlider_contrast.valueChanged.connect(self.adjustBrightCont)
		## Capture focus change events
		QtCore.QObject.connect(app, QtCore.SIGNAL("focusChanged(QWidget *, QWidget *)"), self.changedFocusSlot)

		## Pass models and scenes to tableviewa
		self.tableView_left._model = self.model_left
		self.tableView_right._model = self.model_right
		self.tableView_left._scene = self.sceneLeft
		self.tableView_right._scene = self.sceneRight

	def keyPressEvent(self,event):
		if event.key() == QtCore.Qt.Key_Delete:
			if self.currentFocusedWidgetName == 'tableView_left':
				if self.debug == True: print clrmsg.DEBUG + "Deleting item(s) on the left side"
				# self.deleteItem(self.tableView_left,self.model_left,self.sceneLeft)
				self.tableView_left.deleteItem()
				# self.updateItems(self.model_left,self.sceneLeft)
				self.tableView_left.updateItems()
			elif self.currentFocusedWidgetName == 'tableView_right':
				if self.debug == True: print clrmsg.DEBUG + "Deleting item(s) on the right side"
				# self.deleteItem(self.tableView_right,self.model_right,self.sceneRight)
				self.tableView_right.deleteItem()
				# self.updateItems(self.model_right,self.sceneRight)
				self.tableView_right.updateItems()

	def test(self):
		print 'lol'

	def changedFocusSlot(self, former, current):
		if self.debug == True: print clrmsg.DEBUG + "focus changed from/to:", former, current
		if current:
			self.currentFocusedWidgetName = current.objectName()
			self.currentFocusedWidget = current
		if former:
			self.formerFocusedWidgetName = former.objectName()
			self.formerFocusedWidget = former

		## Feed saved rotation angle/brightness-contrast value from selected image to spinbox/slider
		 # Block emitting signals for correct setting of BOTH sliders. Otherwise the second one gets overwritten with wrong value
		self.horizontalSlider_brightness.blockSignals(True)
		self.horizontalSlider_contrast.blockSignals(True)
		if self.currentFocusedWidgetName == 'graphicsView_left':
			self.spinBox_rot.setValue(self.rotangle_left)
			self.horizontalSlider_brightness.setValue(self.brightness_left)
			self.horizontalSlider_contrast.setValue(self.contrast_left)
		elif self.currentFocusedWidgetName == 'graphicsView_right':
			self.spinBox_rot.setValue(self.rotangle_right)
			self.horizontalSlider_brightness.setValue(self.brightness_right)
			self.horizontalSlider_contrast.setValue(self.contrast_right)
		 # Unblock emitting signals.
		self.horizontalSlider_brightness.blockSignals(False)
		self.horizontalSlider_contrast.blockSignals(False)

		## Lable showing selected image
		if self.currentFocusedWidgetName == 'spinBox_rot':
			pass
		else:
			if self.currentFocusedWidgetName != 'graphicsView_left' and self.currentFocusedWidgetName != 'graphicsView_right':
				self.label_selimg.setStyleSheet("color: rgb(255, 190, 0);")
				self.label_selimg.setText('none')
				self.ctrlEnDisAble(False)
			elif self.currentFocusedWidgetName == 'graphicsView_left':
				self.label_selimg.setStyleSheet("color: rgb(0, 225, 90);")
				self.label_selimg.setText('left')
				self.ctrlEnDisAble(True)
			elif self.currentFocusedWidgetName == 'graphicsView_right':
				self.label_selimg.setStyleSheet("color: rgb(0, 190, 255);")
				self.label_selimg.setText('right')
				self.ctrlEnDisAble(True)

	## Funtion to dis-/enabling the buttons controlling rotation and contrast/brightness
	def ctrlEnDisAble(self,status):
		self.spinBox_rot.setEnabled(status)
		self.horizontalSlider_brightness.setEnabled(status)
		self.horizontalSlider_contrast.setEnabled(status)
		self.toolButton_rotcw.setEnabled(status)
		self.toolButton_rotccw.setEnabled(status)

												#################################################
												####### Image initialization and rotation #######
																	## START ##
	def initImageLeft(self):
		if self.left != None:
			## Changed GraphicsSceneLeft(self) to QGraphicsSceneCustom(self.graphicsView_left) to reuse class for both scenes
			self.sceneLeft = QGraphicsSceneCustom(self.graphicsView_left,name='left',model=self.model_left)
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
			self.sceneRight = QGraphicsSceneCustom(self.graphicsView_right,name='right',model=self.model_right)
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

																	## END ##
												####### Image initialization and rotation #######
												#################################################

												#################################################
												#######            Update items           #######
																	## START ##
	def updateItems(self,model,scene):
		row = 0
		for item in scene.items():
			if isinstance(item, QtGui.QGraphicsEllipseItem):
				item.setPos(float(model.data(model.index(row, 0)).toString()),float(model.data(model.index(row, 1)).toString()))
				row += 1

	def showSelectedItem(self,tableview,scene):
		indices = tableview.selectedIndexes()
		## Color all circles red and nly get ellipses, not text, to iterate through in green coloring process.
		activeitems = []
		for item in scene.items():
			if isinstance(item, QtGui.QGraphicsEllipseItem):
				item.setPen(scene.pen)
				activeitems.append(item)
		## Color selected items green
		if indices:
			## Filter selected rows
			rows = set(index.row() for index in indices)
			## Paint selected rows green
			for row in rows:
				activeitems[row].setPen(QtGui.QPen(QtCore.Qt.green))

	def deleteItem(self,tableview,model,scene):
		indices = tableview.selectedIndexes()
		## Only get ellipses, not text.
		activeitems = []
		for item in scene.items():
			if isinstance(item, QtGui.QGraphicsEllipseItem):
				activeitems.append(item)
		## Deleting selected
		if indices:
			## Filter selected rows
			rows = set(index.row() for index in indices)
			## Delete selected rows in scene.
			for row in rows:
				scene.removeItem(activeitems[row])
				scene.enumeratePoints()
			scene.itemsToModel()

																	## END ##
												#######            Update items           #######
												#################################################

												#################################################
												#######    Image processing functions     #######
																	## START ##
	## Read image
	def imread(self,path,normalize=True):
		if self.debug == True: print clrmsg.DEBUG + "===== imread"
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
			if self.debug == True: print clrmsg.DEBUG + "Calculating MI"
			return self.mip(img)

	## Convert opencv image (numpy array in BGR) to RGB QImage and return pixmap. Only takes 2D images
	def cv2Qimage(self,img):
		if self.debug == True: print clrmsg.DEBUG + "===== cv2Qimage"
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
		if self.debug == True: print clrmsg.DEBUG + "===== adjustBrightCont"
		if self.currentFocusedWidgetName == 'spinBox_rot':
			cfwn = self.formerFocusedWidgetName
		else:
			cfwn = self.currentFocusedWidgetName
		if cfwn != 'graphicsView_left' and cfwn != 'graphicsView_right':
			print clrmsg.ERROR + "Please click on the image you want to rotate."
		elif cfwn == 'graphicsView_left':
			self.brightness_left = self.horizontalSlider_brightness.value()
			self.contrast_left = self.horizontalSlider_contrast.value()
			#print self.brightness_left,self.contrast_left
			## Remove image (item)
			self.sceneLeft.removeItem(self.pixmap_item_left)
			## Load replacement
			img_adj = np.copy(self.img_left)
			## Load contrast value (Slider value between 0 and 100)
			contr = self.contrast_left*0.1
			## Adjusting contrast
			img_adj = np.where(img_adj*contr>=255,255,img_adj*contr)
			## Convert float64 back to uint8
			img_adj = img_adj.astype(dtype='uint8')
			## Adjust brightness
			if self.brightness_left > 0:
				img_adj = np.where(255-img_adj<=self.brightness_left,255,img_adj+self.brightness_left)
			else:
				img_adj = np.where(img_adj<=-self.brightness_left,0,img_adj+self.brightness_left)
				## Convert from int16 back to uint8
				img_adj = img_adj.astype(dtype='uint8')
			## Display image
			self.pixmap_left = self.cv2Qimage(img_adj)
			self.pixmap_item_left = QtGui.QGraphicsPixmapItem(self.pixmap_left, None, self.sceneLeft)
			## Put exchanged image into background
			QtGui.QGraphicsItem.stackBefore(self.pixmap_item_left, self.sceneLeft.items()[-1])
		elif cfwn == 'graphicsView_right':
			self.brightness_right = self.horizontalSlider_brightness.value()
			self.contrast_right = self.horizontalSlider_contrast.value()
			#print self.brightness_right,self.contrast_right
			## Remove image (item)
			self.sceneRight.removeItem(self.pixmap_item_right)
			## Load replacement
			img_adj = np.copy(self.img_right)
			## Load contrast value (Slider value between 0 and 100)
			contr = self.contrast_right*0.1
			## Adjusting contrast
			img_adj = np.where(img_adj*contr>=255,255,img_adj*contr)
			## Convert float64 back to uint8
			img_adj = img_adj.astype(dtype='uint8')
			## Adjust brightness
			if self.brightness_right > 0:
				img_adj = np.where(255-img_adj<=self.brightness_right,255,img_adj+self.brightness_right)
			else:
				img_adj = np.where(img_adj<=-self.brightness_right,0,img_adj+self.brightness_right)
				## Convert from int16 back to uint8
				img_adj = img_adj.astype(dtype='uint8')
			## Display image
			self.pixmap_right = self.cv2Qimage(img_adj)
			self.pixmap_item_right = QtGui.QGraphicsPixmapItem(self.pixmap_right, None, self.sceneRight)
			## Put exchanged image into background
			QtGui.QGraphicsItem.stackBefore(self.pixmap_item_right, self.sceneRight.items()[-1])

	## Normalize Image
	def norm_img(self,img,copy=False):
		if self.debug == True: print clrmsg.DEBUG + "===== norm_img"
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
		if self.debug == True: print clrmsg.DEBUG + "===== mip"
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

																	## END ##
												#######    Image processing functions    ########
												#################################################

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