#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extracting 2D and 3D points with subsequent 2D to 3D correlation.
This module can be run as a standalone python application, but is best paired
with the preceding data processing (cubing voxels, merge single image files
to one single stack file, ...).

# @Title			: TDCT_correlation
# @Project			: 3DCTv2
# @Description		: Extracting 2D and 3D points for 2D to 3D correlation
# @Author			: Jan Arnold
# @Email			: jan.arnold (at) coraxx.net
# @Copyright		: Copyright (C) 2016  Jan Arnold
# @License			: GPLv3 (see LICENSE file)
# @Credits			:
# @Maintainer		: Jan Arnold
# @Date				: 2016/01
# @Version			: 3DCT 2.2.2b module rev. 28
# @Status			: stable
# @Usage			: part of 3D Correlation Toolbox
# @Notes			:
# @Python_version	: 2.7.11
"""
# ======================================================================================================================


import sys
import os
import time
import re
import tempfile
from PyQt4 import QtCore, QtGui, uic
import numpy as np
import cv2
import tifffile as tf
import qimage2ndarray
## Colored stdout, custom Qt functions (mostly to handle events), CSV handler
## and correlation algorithm
from tdct import clrmsg, TDCT_debug, QtCustom, csvHandler, correlation

__version__ = 'v2.2.2b'

# add working directory temporarily to PYTHONPATH
if getattr(sys, 'frozen', False):
	# program runs in a bundle (pyinstaller)
	execdir = sys._MEIPASS
else:
	execdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(execdir)

qtCreatorFile_main = os.path.join(execdir, "TDCT_correlation.ui")
Ui_WidgetWindow, QtBaseClass = uic.loadUiType(qtCreatorFile_main)

debug = TDCT_debug.debug
# debug = True
if debug is True: print clrmsg.DEBUG + "Execdir =", execdir


class MainWidget(QtGui.QMainWindow, Ui_WidgetWindow):
	def __init__(self, parent=None, leftImage=None, rightImage=None,workingdir=None):
		if debug is True: print clrmsg.DEBUG + 'Debug messages enabled'
		QtGui.QWidget.__init__(self)
		Ui_WidgetWindow.__init__(self)
		self.setupUi(self)
		self.parent = parent
		self.counter = 0		# Just for testing (loop counter for test button)
		self.refreshUI = QtGui.QApplication.processEvents
		self.currentFocusedWidgetName = QtGui.QApplication.focusWidget()
		if workingdir is None:
			self.workingdir = execdir
		else:
			self.workingdir = workingdir
		self.lineEdit_workingDir.setText(self.workingdir)

		## Stylesheet colors:
		self.stylesheet_orange = "color: rgb(255, 120,   0);"
		self.stylesheet_green = "color:  rgb(  0, 200,   0);"
		self.stylesheet_blue = "color:   rgb(  0, 190, 255);"
		self.stylesheet_red = "color:    rgb(255,   0,   0);"
		## Marker and POI color
		self.markerColor = (0,255,0)
		self.poiColor = (0,0,255)

		## Tableview and models
		self.modelLleft = QtCustom.QStandardItemModelCustom(self)
		self.tableView_left.setModel(self.modelLleft)
		self.modelLleft.tableview = self.tableView_left

		self.modelRight = QtCustom.QStandardItemModelCustom(self)
		self.tableView_right.setModel(self.modelRight)
		self.modelRight.tableview = self.tableView_right

		self.modelResults = QtGui.QStandardItemModel(self)
		self.modelResultsProxy = QtCustom.NumberSortModel()
		self.modelResultsProxy.setSourceModel(self.modelResults)
		self.tableView_results.setModel(self.modelResultsProxy)

		## store parameters for resizing
		self.parent = parent
		self.size = 500
		self.leftImage = leftImage
		self.rightImage = rightImage

		## Initialize parameters
		## left
		self.selectedLayer_left = 1
		self.brightness_left_layer1 = 0
		self.brightness_left_layer2 = 0
		self.brightness_left_layer3 = 0
		self.contrast_left_layer1 = 10
		self.contrast_left_layer2 = 10
		self.contrast_left_layer3 = 10
		self.slice_left = 0
		self.mipCHKbox_left = True
		self.layer1CHKbox_left = True
		self.layer2CHKbox_left = False
		self.layer3CHKbox_left = False
		self.layer1Color_left = 0
		self.layer2Color_left = 0
		self.layer3Color_left = 0
		self.layer1CustomColor_left = [255,0,255]
		self.layer2CustomColor_left = [255,0,255]
		self.layer3CustomColor_left = [255,0,255]
		self.img_left_overlay = None
		# self.img_left_layer1 = None
		self.img_left_layer2 = None
		self.img_left_layer3 = None
		## right
		self.selectedLayer_right = 1
		self.brightness_right_layer1 = 0
		self.brightness_right_layer2 = 0
		self.brightness_right_layer3 = 0
		self.contrast_right_layer1 = 10
		self.contrast_right_layer2 = 10
		self.contrast_right_layer3 = 10
		self.slice_right = 0
		self.mipCHKbox_right = True
		self.layer1CHKbox_right = True
		self.layer2CHKbox_right = False
		self.layer3CHKbox_right = False
		self.layer1Color_right = 0
		self.layer2Color_right = 0
		self.layer3Color_right = 0
		self.layer1CustomColor_right = [255,0,255]
		self.layer2CustomColor_right = [255,0,255]
		self.layer3CustomColor_right = [255,0,255]
		self.img_right_overlay = None
		# self.img_right_layer1 = None
		self.img_right_layer2 = None
		self.img_right_layer3 = None
		## Initialize Images and connect image load buttons
		self.toolButton_loadLeftImage.clicked.connect(self.openImageLeft)
		self.toolButton_loadRightImage.clicked.connect(self.openImageRight)
		self.toolButton_resetLeftImage.clicked.connect(lambda: self.resetImageLeft(img=None))
		self.toolButton_resetRightImage.clicked.connect(lambda: self.resetImageRight(img=None))
		if leftImage is None or rightImage is None:
			return
		self.initImageLeft()
		self.initImageRight()

		## connect item change signal to write changes in model back to QGraphicItems as well as highlighting selected points
		self.modelLleft.itemChanged.connect(self.tableView_left.updateItems)
		self.modelRight.itemChanged.connect(self.tableView_right.updateItems)
		self.tableView_left.selectionModel().selectionChanged.connect(self.tableView_left.showSelectedItem)
		self.tableView_right.selectionModel().selectionChanged.connect(self.tableView_right.showSelectedItem)
		self.tableView_results.selectionModel().selectionChanged.connect(self.showSelectedResidual)
		self.tableView_results.doubleClicked.connect(lambda: self.showSelectedResidual(doubleclick=True))

		# SpinBoxes
		self.spinBox_rot.valueChanged.connect(self.rotateImage)
		self.spinBox_markerSize.valueChanged.connect(self.changeMarkerSize)
		self.spinBox_slice.valueChanged.connect(self.selectSlice)
		self.doubleSpinBox_scatterPlotFrameSize.valueChanged.connect(lambda: self.displayResults(
																frame=self.checkBox_scatterPlotFrame.isChecked(),
																framesize=self.doubleSpinBox_scatterPlotFrameSize.value()))

		## Checkboxes
		self.checkBox_scatterPlotFrame.stateChanged.connect(lambda: self.displayResults(
																frame=self.checkBox_scatterPlotFrame.isChecked(),
																framesize=self.doubleSpinBox_scatterPlotFrameSize.value()))
		self.checkBox_resultsAbsolute.stateChanged.connect(lambda: self.displayResults(
																frame=self.checkBox_scatterPlotFrame.isChecked(),
																framesize=self.doubleSpinBox_scatterPlotFrameSize.value()))
		self.checkBox_MIP.stateChanged.connect(self.selectSlice)
		self.checkBox_layer1.toggled.connect(lambda: self.layerCtrl('layer1'))
		self.checkBox_layer2.toggled.connect(lambda: self.layerCtrl('layer2'))
		self.checkBox_layer3.toggled.connect(lambda: self.layerCtrl('layer3'))

		## Comboboxes
		self.comboBox_channelColorLayer1.currentIndexChanged.connect(self.changeColorChannel)
		self.comboBox_channelColorLayer2.currentIndexChanged.connect(self.changeColorChannel)
		self.comboBox_channelColorLayer3.currentIndexChanged.connect(self.changeColorChannel)

		## Radiobuttons
		self.radioButton_layer1.clicked.connect(self.setSliders)
		self.radioButton_layer2.clicked.connect(self.setSliders)
		self.radioButton_layer3.clicked.connect(self.setSliders)

		## Buttons
		self.toolButton_rotcw.clicked.connect(lambda: self.rotateImage45(direction='cw'))
		self.toolButton_rotccw.clicked.connect(lambda: self.rotateImage45(direction='ccw'))
		self.toolButton_brightness_reset.clicked.connect(lambda: self.horizontalSlider_brightness.setValue(0))
		self.toolButton_contrast_reset.clicked.connect(lambda: self.horizontalSlider_contrast.setValue(10))
		self.toolButton_importPoints.clicked.connect(self.importPoints)
		self.toolButton_exportPoints.clicked.connect(self.exportPoints)
		self.toolButton_selectWorkingDir.clicked.connect(self.selectWorkingDir)
		self.toolButton_selectMarkerColor.clicked.connect(self.getMarkerColor)
		self.toolButton_selectPoiColor.clicked.connect(self.getPoiColor)
		self.toolButton_saveImage_left.clicked.connect(lambda: self.displayImage(side='left',save=True))
		self.toolButton_saveImage_right.clicked.connect(lambda: self.displayImage(side='right',save=True))
		self.toolButton_loadLayer2.clicked.connect(lambda: self.layerCtrl('layer2',load=True))
		self.toolButton_loadLayer3.clicked.connect(lambda: self.layerCtrl('layer3',load=True))
		self.commandLinkButton_correlate.clicked.connect(self.correlate)

		## Sliders
		self.horizontalSlider_brightness.valueChanged.connect(self.setBrightCont)
		self.horizontalSlider_contrast.valueChanged.connect(self.setBrightCont)
		## Capture focus change events
		QtCore.QObject.connect(QtGui.QApplication.instance(), QtCore.SIGNAL("focusChanged(QWidget *, QWidget *)"), self.changedFocusSlot)

		## Pass models and scenes to tableview for easy access
		self.tableView_left._model = self.modelLleft
		self.tableView_right._model = self.modelRight
		self.tableView_left._scene = self.sceneLeft
		self.tableView_right._scene = self.sceneRight

		self.tableView_results.setContextMenuPolicy(3)
		self.tableView_results.customContextMenuRequested.connect(self.cmTableViewResults)

		self.lineEdit_workingDir.textChanged.connect(self.updateWorkingDir)

		self.activateWindow()

	def keyPressEvent(self,event):
		"""Filter key press event
		Selected table rows can be deleted by pressing the "Del" key
		"""
		if event.key() == QtCore.Qt.Key_Delete:
			if self.currentFocusedWidgetName == 'tableView_left':
				if debug is True: print clrmsg.DEBUG + "Deleting item(s) on the left side"
				# self.deleteItem(self.tableView_left,self.modelLleft,self.sceneLeft)
				self.tableView_left.deleteItem()
				# self.updateItems(self.modelLleft,self.sceneLeft)
				self.tableView_left.updateItems()
			elif self.currentFocusedWidgetName == 'tableView_right':
				if debug is True: print clrmsg.DEBUG + "Deleting item(s) on the right side"
				# self.deleteItem(self.tableView_right,self.modelRight,self.sceneRight)
				self.tableView_right.deleteItem()
				# self.updateItems(self.modelRight,self.sceneRight)
				self.tableView_right.updateItems()

	def closeEvent(self, event):
		"""Warning when closing application to prevent unintentional quitting with reminder to save data"""
		quit_msg = "Are you sure you want to exit the\n3DCT Correlation?\n\nUnsaved data will be lost!"
		reply = QtGui.QMessageBox.question(self, 'Message', quit_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes:
			event.accept()
			if self.parent:
				self.parent.cleanUp()
				self.parent.exitstatus = 0
		else:
			event.ignore()
			if self.parent:
				self.parent.exitstatus = 1

	def selectWorkingDir(self):
		path = str(QtGui.QFileDialog.getExistingDirectory(self, "Select working directory", self.workingdir))
		self.activateWindow()
		if path:
			workingdir = self.checkWorkingDirPrivileges(path)
			if workingdir:
				self.workingdir = workingdir
			self.lineEdit_workingDir.setText(self.workingdir)

	def updateWorkingDir(self):
		if os.path.isdir(self.lineEdit_workingDir.text()):
			workingdir = self.checkWorkingDirPrivileges(str(self.lineEdit_workingDir.text()))
			if workingdir:
				self.workingdir = workingdir
			self.lineEdit_workingDir.setText(self.workingdir)
			print 'updated working dir to:', self.workingdir
		else:
			self.lineEdit_workingDir.setText(self.workingdir)
			print clrmsg.ERROR + "Dropped object is not a valid path. Returning to {0} as working directory.".format(self.workingdir)

	def checkWorkingDirPrivileges(self,path):
		try:
			testfile = tempfile.TemporaryFile(dir=path)
			testfile.close()
			return path
		except Exception:
			QtGui.QMessageBox.critical(
				self,"Warning",
				"I cannot write to this folder: {0}\nFalling back to {1} as the working directory".format(path, self.workingdir))
			return None

	def changedFocusSlot(self, former, current):
		if debug is True: print clrmsg.DEBUG + "focus changed from/to:", former.objectName() if former else former, \
				current.objectName() if current else current
		if current:
			self.currentFocusedWidgetName = current.objectName()
			self.currentFocusedWidget = current
		if former:
			self.formerFocusedWidgetName = former.objectName()
			self.formerFocusedWidget = former

		## Label showing selected image
		## WORKAROUND: check against empty string, because the popup from the comboboxes emit an empty focus object name string.
		if self.currentFocusedWidgetName in [
											'spinBox_rot','spinBox_markerSize','spinBox_slice','horizontalSlider_brightness','horizontalSlider_contrast',
											'doubleSpinBox_custom_rot_center_x','doubleSpinBox_custom_rot_center_y','doubleSpinBox_custom_rot_center_z',
											'checkBox_MIP','checkBox_layer1','checkBox_layer2','checkBox_layer3',
											'comboBox_channelColorLayer1','comboBox_channelColorLayer2','comboBox_channelColorLayer3',
											'radioButton_layer1','radioButton_layer2','radioButton_layer3','']:
			pass
		else:
			if self.currentFocusedWidgetName != 'graphicsView_left' and self.currentFocusedWidgetName != 'graphicsView_right':
				self.label_selimg.setStyleSheet(self.stylesheet_orange)
				self.label_selimg.setText('none')
				self.label_markerSizeNano.setText('')
				self.label_markerSizeNanoUnit.setText('')
				self.label_imgpxsize.setText('')
				self.label_imgpxsizeUnit.setText('')
				self.label_imagetype.setText('')
				self.ctrlEnDisAble(False)
			elif self.currentFocusedWidgetName == 'graphicsView_left':
				self.label_selimg.setStyleSheet(self.stylesheet_green)
				self.label_selimg.setText('left')
				self.label_imagetype.setStyleSheet(self.stylesheet_green)
				# self.label_imagetype.setText('(2D)' if '{0:b}'.format(self.sceneLeft.imagetype)[-1] == '1' else '(3D)')
				if '{0:b}'.format(self.sceneLeft.imagetype)[-1] == '1':
					self.label_imagetype.setText('(2D)')
					self.widget_sliceSelector.setVisible(False)
				else:
					self.label_imagetype.setText('(3D)')
					self.widget_sliceSelector.setVisible(True)
				self.ctrlEnDisAble(True)
				if self.mipCHKbox_left is False:
					self.spinBox_slice.setEnabled(True)
			elif self.currentFocusedWidgetName == 'graphicsView_right':
				self.label_selimg.setStyleSheet(self.stylesheet_blue)
				self.label_selimg.setText('right')
				self.label_imagetype.setStyleSheet(self.stylesheet_blue)
				# self.label_imagetype.setText('(2D)' if '{0:b}'.format(self.sceneRight.imagetype)[-1] == '1' else '(3D)')
				if '{0:b}'.format(self.sceneRight.imagetype)[-1] == '1':
					self.label_imagetype.setText('(2D)')
					self.widget_sliceSelector.setVisible(False)
				else:
					self.label_imagetype.setText('(3D)')
					self.widget_sliceSelector.setVisible(True)
				self.ctrlEnDisAble(True)
				if self.mipCHKbox_right is False:
					self.spinBox_slice.setEnabled(True)

		## Label showing selected table
		if self.currentFocusedWidgetName != 'tableView_left' and self.currentFocusedWidgetName != 'tableView_right':
			self.label_selectedTable.setStyleSheet(self.stylesheet_orange)
			self.label_selectedTable.setText('none')
			# self.ctrlEnDisAble(False)
		elif self.currentFocusedWidgetName == 'tableView_left':
			self.label_selectedTable.setStyleSheet(self.stylesheet_green)
			self.label_selectedTable.setText('left')
			self.ctrlEnDisAble(False)
		elif self.currentFocusedWidgetName == 'tableView_right':
			self.label_selectedTable.setStyleSheet(self.stylesheet_blue)
			self.label_selectedTable.setText('right')
			self.ctrlEnDisAble(False)

		## Feed saved rotation angle/brightness-contrast value from selected image to spinbox/slider
		# Block emitting signals for correct setting of BOTH sliders. Otherwise the second one gets overwritten with the old value
		self.horizontalSlider_brightness.blockSignals(True)
		self.horizontalSlider_contrast.blockSignals(True)
		self.spinBox_slice.blockSignals(True)
		self.checkBox_MIP.blockSignals(True)
		self.checkBox_layer1.blockSignals(True)
		self.checkBox_layer2.blockSignals(True)
		self.checkBox_layer3.blockSignals(True)
		self.comboBox_channelColorLayer1.blockSignals(True)
		self.comboBox_channelColorLayer2.blockSignals(True)
		self.comboBox_channelColorLayer3.blockSignals(True)

		if self.currentFocusedWidgetName == 'graphicsView_left':
			self.spinBox_rot.setValue(self.sceneLeft.rotangle)
			self.spinBox_markerSize.setValue(self.sceneLeft.markerSize)
			self.spinBox_slice.setValue(self.slice_left)
			self.checkBox_MIP.setChecked(self.mipCHKbox_left)
			self.checkBox_layer1.setChecked(self.layer1CHKbox_left)
			self.comboBox_channelColorLayer1.setEnabled(self.layer1CHKbox_left)
			self.comboBox_channelColorLayer1.setCurrentIndex(self.layer1Color_left)
			self.checkBox_layer2.setChecked(self.layer2CHKbox_left)
			self.comboBox_channelColorLayer2.setEnabled(self.layer2CHKbox_left)
			self.comboBox_channelColorLayer2.setCurrentIndex(self.layer2Color_left)
			self.checkBox_layer3.setChecked(self.layer3CHKbox_left)
			self.comboBox_channelColorLayer3.setEnabled(self.layer3CHKbox_left)
			self.comboBox_channelColorLayer3.setCurrentIndex(self.layer3Color_left)
			if self.selectedLayer_left == 1:
				self.radioButton_layer1.setChecked(True)
			elif self.selectedLayer_left == 2:
				self.radioButton_layer2.setChecked(True)
			elif self.selectedLayer_left == 3:
				self.radioButton_layer3.setChecked(True)
			self.radioButton_layer1.setEnabled(self.layer1CHKbox_left)
			self.radioButton_layer2.setEnabled(self.layer2CHKbox_left)
			self.radioButton_layer3.setEnabled(self.layer3CHKbox_left)
			if self.radioButton_layer1.isChecked():
				self.horizontalSlider_brightness.setValue(self.brightness_left_layer1)
				self.horizontalSlider_contrast.setValue(self.contrast_left_layer1)
			elif self.radioButton_layer2.isChecked():
				self.horizontalSlider_brightness.setValue(self.brightness_left_layer2)
				self.horizontalSlider_contrast.setValue(self.contrast_left_layer2)
			elif self.radioButton_layer3.isChecked():
				self.horizontalSlider_brightness.setValue(self.brightness_left_layer3)
				self.horizontalSlider_contrast.setValue(self.contrast_left_layer3)
			self.label_imgpxsize.setText(str(self.sceneLeft.pixelSize))  # + ' um') # breaks marker size adjustments check
			self.label_imgpxsizeUnit.setText('um') if self.sceneLeft.pixelSize else self.label_imgpxsizeUnit.setText('')
		elif self.currentFocusedWidgetName == 'graphicsView_right':
			self.spinBox_rot.setValue(self.sceneRight.rotangle)
			self.spinBox_markerSize.setValue(self.sceneRight.markerSize)
			self.spinBox_slice.setValue(self.slice_right)
			self.checkBox_MIP.setChecked(self.mipCHKbox_right)
			self.checkBox_layer1.setChecked(self.layer1CHKbox_right)
			self.comboBox_channelColorLayer1.setEnabled(self.layer1CHKbox_right)
			self.comboBox_channelColorLayer1.setCurrentIndex(self.layer1Color_right)
			self.checkBox_layer2.setChecked(self.layer2CHKbox_right)
			self.comboBox_channelColorLayer2.setEnabled(self.layer2CHKbox_right)
			self.comboBox_channelColorLayer2.setCurrentIndex(self.layer2Color_right)
			self.checkBox_layer3.setChecked(self.layer3CHKbox_right)
			self.comboBox_channelColorLayer3.setEnabled(self.layer3CHKbox_right)
			self.comboBox_channelColorLayer3.setCurrentIndex(self.layer3Color_right)
			if self.selectedLayer_right == 1:
				self.radioButton_layer1.setChecked(True)
			elif self.selectedLayer_right == 2:
				self.radioButton_layer2.setChecked(True)
			elif self.selectedLayer_right == 3:
				self.radioButton_layer3.setChecked(True)
			self.radioButton_layer1.setEnabled(self.layer1CHKbox_right)
			self.radioButton_layer2.setEnabled(self.layer2CHKbox_right)
			self.radioButton_layer3.setEnabled(self.layer3CHKbox_right)
			if self.radioButton_layer1.isChecked():
				self.horizontalSlider_brightness.setValue(self.brightness_right_layer1)
				self.horizontalSlider_contrast.setValue(self.contrast_right_layer1)
			if self.radioButton_layer2.isChecked():
				self.horizontalSlider_brightness.setValue(self.brightness_right_layer2)
				self.horizontalSlider_contrast.setValue(self.contrast_right_layer2)
			if self.radioButton_layer3.isChecked():
				self.horizontalSlider_brightness.setValue(self.brightness_right_layer3)
				self.horizontalSlider_contrast.setValue(self.contrast_right_layer3)
			self.label_imgpxsize.setText(str(self.sceneRight.pixelSize))  # + ' um') # breaks marker size adjustments check
			self.label_imgpxsizeUnit.setText('um') if self.sceneRight.pixelSize else self.label_imgpxsizeUnit.setText('')
		# Unblock emitting signals.
		self.horizontalSlider_brightness.blockSignals(False)
		self.horizontalSlider_contrast.blockSignals(False)
		self.spinBox_slice.blockSignals(False)
		self.checkBox_MIP.blockSignals(False)
		self.checkBox_layer1.blockSignals(False)
		self.checkBox_layer2.blockSignals(False)
		self.checkBox_layer3.blockSignals(False)
		self.comboBox_channelColorLayer1.blockSignals(False)
		self.comboBox_channelColorLayer2.blockSignals(False)
		self.comboBox_channelColorLayer3.blockSignals(False)
		# update marker size in nm
		self.changeMarkerSize()

	## Function to dis-/enabling the buttons controlling rotation and contrast/brightness
	def ctrlEnDisAble(self,status):
		self.spinBox_rot.setEnabled(status)
		self.spinBox_markerSize.setEnabled(status)
		self.spinBox_slice.setEnabled(False)
		self.checkBox_MIP.setEnabled(status)
		self.checkBox_layer1.setEnabled(status)
		self.checkBox_layer2.setEnabled(status)
		self.checkBox_layer3.setEnabled(status)
		self.comboBox_channelColorLayer1.setEnabled(False)
		self.comboBox_channelColorLayer2.setEnabled(False)
		self.comboBox_channelColorLayer3.setEnabled(False)
		self.radioButton_layer1.setEnabled(False)
		self.radioButton_layer2.setEnabled(False)
		self.radioButton_layer3.setEnabled(False)
		self.horizontalSlider_brightness.setEnabled(status)
		self.horizontalSlider_contrast.setEnabled(status)
		self.toolButton_brightness_reset.setEnabled(status)
		self.toolButton_contrast_reset.setEnabled(status)
		self.toolButton_rotcw.setEnabled(status)
		self.toolButton_rotccw.setEnabled(status)
		self.toolButton_importPoints.setEnabled(not status)
		self.toolButton_exportPoints.setEnabled(not status)
		self.toolButton_loadLayer2.setEnabled(status)
		self.toolButton_loadLayer3.setEnabled(status)

	def setSliders(self):
		self.horizontalSlider_brightness.blockSignals(True)
		self.horizontalSlider_contrast.blockSignals(True)
		if self.label_selimg.text() == 'left':
			if self.radioButton_layer1.isChecked():
				self.horizontalSlider_brightness.setValue(self.brightness_left_layer1)
				self.horizontalSlider_contrast.setValue(self.contrast_left_layer1)
				self.selectedLayer_left = 1
			elif self.radioButton_layer2.isChecked():
				self.horizontalSlider_brightness.setValue(self.brightness_left_layer2)
				self.horizontalSlider_contrast.setValue(self.contrast_left_layer2)
				self.selectedLayer_left = 2
			elif self.radioButton_layer3.isChecked():
				self.horizontalSlider_brightness.setValue(self.brightness_left_layer3)
				self.horizontalSlider_contrast.setValue(self.contrast_left_layer3)
				self.selectedLayer_left = 3
		if self.label_selimg.text() == 'right':
			if self.radioButton_layer1.isChecked():
				self.horizontalSlider_brightness.setValue(self.brightness_right_layer1)
				self.horizontalSlider_contrast.setValue(self.contrast_right_layer1)
				self.selectedLayer_right = 1
			if self.radioButton_layer2.isChecked():
				self.horizontalSlider_brightness.setValue(self.brightness_right_layer2)
				self.horizontalSlider_contrast.setValue(self.contrast_right_layer2)
				self.selectedLayer_right = 2
			if self.radioButton_layer3.isChecked():
				self.horizontalSlider_brightness.setValue(self.brightness_right_layer3)
				self.horizontalSlider_contrast.setValue(self.contrast_right_layer3)
				self.selectedLayer_right = 3
		self.horizontalSlider_brightness.blockSignals(False)
		self.horizontalSlider_contrast.blockSignals(False)

	def colorModels(self):
		rowsLeft = self.modelLleft.rowCount()
		rowsRight = self.modelRight.rowCount()
		alpha = 100
		for row in range(min([rowsLeft,rowsRight])):
			color_correlate = (50,220,175,alpha)
			if rowsLeft != 0:
				self.modelLleft.item(row, 0).setBackground(QtGui.QColor(*color_correlate))
				self.modelLleft.item(row, 1).setBackground(QtGui.QColor(*color_correlate))
				self.modelLleft.item(row, 2).setBackground(QtGui.QColor(*color_correlate))
			if rowsRight != 0:
				self.modelRight.item(row, 0).setBackground(QtGui.QColor(*color_correlate))
				self.modelRight.item(row, 1).setBackground(QtGui.QColor(*color_correlate))
				self.modelRight.item(row, 2).setBackground(QtGui.QColor(*color_correlate))
		if rowsLeft > rowsRight:
			if '{0:b}'.format(self.sceneLeft.imagetype)[-1] == '0' or '{0:b}'.format(
												self.sceneLeft.imagetype)[-1] == '{0:b}'.format(self.sceneRight.imagetype)[-1]:
				color_overflow = (105,220,0,alpha)  # green if entries are used as POIs
			else:
				color_overflow = (220,25,105,alpha)  # red(ish) color to indicate unbalanced amount of markers for correlation
			for row in range(rowsRight,rowsLeft):
				self.modelLleft.item(row, 0).setBackground(QtGui.QColor(*color_overflow))
				self.modelLleft.item(row, 1).setBackground(QtGui.QColor(*color_overflow))
				self.modelLleft.item(row, 2).setBackground(QtGui.QColor(*color_overflow))
		elif rowsLeft < rowsRight:
			if '{0:b}'.format(self.sceneRight.imagetype)[-1] == '0' or '{0:b}'.format(
												self.sceneLeft.imagetype)[-1] == '{0:b}'.format(self.sceneRight.imagetype)[-1]:
				color_overflow = (105,220,0,alpha)  # green if entries are used as POIs
			else:
				color_overflow = (220,25,105,alpha)  # red(ish) color to indicate unbalanced amount of markers for correlation
			for row in range(rowsLeft,rowsRight):
				self.modelRight.item(row, 0).setBackground(QtGui.QColor(*color_overflow))
				self.modelRight.item(row, 1).setBackground(QtGui.QColor(*color_overflow))
				self.modelRight.item(row, 2).setBackground(QtGui.QColor(*color_overflow))

	def getMarkerColor(self):
		color = QtGui.QColorDialog.getColor()
		self.activateWindow()
		if color.isValid():
			self.markerColor = (color.blue(), color.green(), color.red())
			self.label_markerColor.setStyleSheet("background-color: rgb{0};".format((color.red(), color.green(), color.blue())))

	def getPoiColor(self):
		color = QtGui.QColorDialog.getColor()
		self.activateWindow()
		if color.isValid():
			self.poiColor = (color.blue(), color.green(), color.red())
			self.label_poiColor.setStyleSheet("background-color: rgb{0};".format((color.red(), color.green(), color.blue())))

	def getCustomChannelColor(self):
		color = QtGui.QColorDialog.getColor()
		self.activateWindow()
		if color.isValid():
			return [color.red(), color.green(), color.blue()]

												###############################################
												###### Image initialization and rotation ######
												#################### START ####################
	def initImageLeft(self):
		if self.leftImage is not None:
			## Changed GraphicsSceneLeft(self) to QtCustom.QGraphicsSceneCustom(self.graphicsView_left) to reuse class for both scenes
			self.sceneLeft = QtCustom.QGraphicsSceneCustom(self.graphicsView_left,mainWidget=self,side='left',model=self.modelLleft)
			## set pen color yellow
			self.sceneLeft.pen = QtGui.QPen(QtCore.Qt.red)
			## Splash screen message
			try:
				splashscreen.splash.showMessage("Loading images... "+self.leftImage,color=QtCore.Qt.white)
			except Exception as e:
				print clrmsg.WARNING, e
				pass
			QtGui.QApplication.processEvents()
			## Get pixel size
			self.sceneLeft.pixelSize = self.pxSize(self.leftImage)
			self.sceneLeft.pixelSizeUnit = 'um'
			## Load image, assign it to scene and store image type information
			self.img_left_layer1,self.sceneLeft.imagetype,self.imgstack_left_layer1 = self.imread(self.leftImage)
			self.img_left_displayed_layer1 = np.copy(self.img_left_layer1)
			self.img_adj_left_layer1 = np.copy(self.img_left_layer1)
			## Set slice spinbox maximum
			if self.imgstack_left_layer1 is not None:
				self.spinBox_slice.setValue(0)
				self.slice_left = 0
				self.spinBox_slice.setMaximum(self.imgstack_left_layer1.shape[0]-1)
			## link image to QTableview for determining z
			self.tableView_left.img = self.imgstack_left_layer1
			## check if coloring z values in table is needed (correlation needs z=0 in 2D image, so no checking for valid z
			## with 2D images needed)
			if self.imgstack_left_layer1 is None:
				self.sceneLeft._z = False
			else:
				self.sceneLeft._z = True
				self.setCustomRotCenter(max(self.imgstack_left_layer1.shape))
			# self.pixmap_left = QtGui.QPixmap(self.leftImage)
			self.pixmap_left = self.cv2Qimage(self.img_left_displayed_layer1)
			self.pixmap_item_left = QtGui.QGraphicsPixmapItem(self.pixmap_left, None, self.sceneLeft)
			## connect scenes to GUI elements
			self.graphicsView_left.setScene(self.sceneLeft)
			## reset scaling (needed for reinitialization)
			self.graphicsView_left.resetMatrix()
			## scaling scene, not image
			scaling_factor = float(self.size)/max(self.pixmap_left.width(), self.pixmap_left.height())
			self.graphicsView_left.scale(scaling_factor,scaling_factor)

	def initImageRight(self):
		if self.rightImage is not None:
			self.sceneRight = QtCustom.QGraphicsSceneCustom(self.graphicsView_right,mainWidget=self,side='right',model=self.modelRight)
			## set pen color yellow
			self.sceneRight.pen = QtGui.QPen(QtCore.Qt.yellow)
			## Splash screen message
			try:
				splashscreen.splash.showMessage("Loading images... "+self.rightImage,color=QtCore.Qt.white)
			except Exception as e:
				print clrmsg.WARNING, e
				pass
			QtGui.QApplication.processEvents()
			## Get pixel size
			self.sceneRight.pixelSize = self.pxSize(self.rightImage)
			self.sceneRight.pixelSizeUnit = 'um'
			## Load image, assign it to scene and store image type information
			self.img_right_layer1,self.sceneRight.imagetype,self.imgstack_right_layer1 = self.imread(self.rightImage)
			self.img_right_displayed_layer1 = np.copy(self.img_right_layer1)
			self.img_adj_right_layer1 = np.copy(self.img_right_layer1)
			## Set slice spinbox maximum
			if self.imgstack_right_layer1 is not None:
				self.spinBox_slice.setValue(0)
				self.slice_left = 0
				self.spinBox_slice.setMaximum(self.imgstack_right_layer1.shape[0]-1)
			## link image to QTableview for determining z
			self.tableView_right.img = self.imgstack_right_layer1
			## check if coloring z values in table is needed (correlation needs z=0 in 2D image, so no checking for valid z
			## with 2D images needed)
			if self.imgstack_right_layer1 is None:
				self.sceneRight._z = False
			else:
				self.sceneRight._z = True
				self.setCustomRotCenter(max(self.imgstack_right_layer1.shape))
			# self.pixmap_right = QtGui.QPixmap(self.rightImage)
			self.pixmap_right = self.cv2Qimage(self.img_right_displayed_layer1)
			self.pixmap_item_right = QtGui.QGraphicsPixmapItem(self.pixmap_right, None, self.sceneRight)
			## connect scenes to GUI elements
			self.graphicsView_right.setScene(self.sceneRight)
			## reset scaling (needed for reinitialization)
			self.graphicsView_right.resetMatrix()
			## scaling scene, not image
			scaling_factor = float(self.size)/max(self.pixmap_right.width(), self.pixmap_right.height())
			self.graphicsView_right.scale(scaling_factor,scaling_factor)

	def openImageLeft(self):
		## *.png *.jpg *.bmp not yet supported
		path = str(QtGui.QFileDialog.getOpenFileName(
			None,"Select image file for correlation", self.workingdir,"Image Files (*.tif *.tiff);; All (*.*)"))
		self.activateWindow()
		if path != '':
			## Set focus to corresponding side to properly reset layer checkboxes
			self.graphicsView_left.setFocus()
			## reset brightness contrast
			self.brightness_left_layer1 = 0
			self.brightness_left_layer2 = 0
			self.brightness_left_layer3 = 0
			self.contrast_left_layer1 = 10
			self.contrast_left_layer2 = 10
			self.contrast_left_layer3 = 10
			self.radioButton_layer1.setChecked(True)
			self.horizontalSlider_brightness.setValue(0)
			self.horizontalSlider_contrast.setValue(10)
			## Reset Layers
			self.spinBox_slice.setValue(0)
			self.checkBox_MIP.setChecked(True)
			self.img_left_layer2,self.img_adj_left_layer2,self.sceneLeft.imagetype_layer2,self.imgstack_left_layer2 = None, None, None, None
			self.img_left_layer3,self.img_adj_left_layer3,self.sceneLeft.imagetype_layer3,self.imgstack_left_layer3 = None, None, None, None
			self.layer2CHKbox_left = False
			self.layer3CHKbox_left = False
			self.checkBox_layer2.setChecked(False)
			self.checkBox_layer3.setChecked(False)
			self.comboBox_channelColorLayer1.setCurrentIndex(0)
			self.comboBox_channelColorLayer2.setCurrentIndex(0)
			self.comboBox_channelColorLayer3.setCurrentIndex(0)
			## Load new image
			self.leftImage = path
			self.sceneLeft.clear()
			self.initImageLeft()
			self.tableView_left._scene = self.sceneLeft
			for i in range(self.tableView_left._model.rowCount()):
				self.sceneLeft.addCircle(0.0,0.0,0.0)
			self.tableView_left.updateItems()
			## Update controls (GUI)
			self.tableView_left.setFocus()
			self.graphicsView_left.setFocus()

	def openImageRight(self):
		## *.png *.jpg *.bmp not yet supported
		path = str(QtGui.QFileDialog.getOpenFileName(
			None,"Select image file for correlation", self.workingdir,"Image Files (*.tif *.tiff);; All (*.*)"))
		self.activateWindow()
		if path != '':
			## Set focus to corresponding side to properly reset layer checkboxes
			self.graphicsView_right.setFocus()
			## reset brightness contrast
			self.brightness_right_layer1 = 0
			self.brightness_right_layer2 = 0
			self.brightness_right_layer3 = 0
			self.contrast_right_layer1 = 10
			self.contrast_right_layer2 = 10
			self.contrast_right_layer3 = 10
			self.radioButton_layer1.setChecked(True)
			self.horizontalSlider_brightness.setValue(0)
			self.horizontalSlider_contrast.setValue(10)
			## Reset Layers
			self.spinBox_slice.setValue(0)
			self.checkBox_MIP.setChecked(True)
			self.img_right_layer2,self.img_adj_right_layer2,self.sceneRight.imagetype_layer2,self.imgstack_right_layer2 = None, None, None, None
			self.img_right_layer3,self.img_adj_right_layer3,self.sceneRight.imagetype_layer3,self.imgstack_right_layer3 = None, None, None, None
			self.layer2CHKbox_right = False
			self.layer3CHKbox_right = False
			self.checkBox_layer2.setChecked(False)
			self.checkBox_layer3.setChecked(False)
			self.comboBox_channelColorLayer1.setCurrentIndex(0)
			self.comboBox_channelColorLayer2.setCurrentIndex(0)
			self.comboBox_channelColorLayer3.setCurrentIndex(0)
			## Load new image
			self.rightImage = path
			self.sceneRight.clear()
			self.initImageRight()
			self.tableView_right._scene = self.sceneRight
			for i in range(self.tableView_right._model.rowCount()):
				self.sceneRight.addCircle(0.0,0.0,0.0)
			self.tableView_right.updateItems()
			## Update controls (GUI)
			self.tableView_right.setFocus()
			self.graphicsView_right.setFocus()

	def resetImageLeft(self,img=None):
		if img is None and self.mipCHKbox_left is False:
			img = self.imgstack_left_layer1[self.slice_left,:]
			## reset brightness contrast
			self.brightness_left_layer1 = 0
			self.contrast_left_layer1 = 10
			self.horizontalSlider_brightness.setValue(0)
			self.horizontalSlider_contrast.setValue(10)
		elif img is None:
			img = self.img_left_layer1
			## reset brightness contrast
			self.brightness_left_layer1 = 0
			self.contrast_left_layer1 = 10
			self.horizontalSlider_brightness.setValue(0)
			self.horizontalSlider_contrast.setValue(10)
		# print img.shape
		## Reset Overlay
		self.img_left_overlay = None
		## Load original
		self.img_left_displayed_layer1 = np.copy(img)
		self.img_adj_left_layer1 = np.copy(img)
		## Display image
		self.displayImage(side='left')
		self.sceneLeft.deleteArrows()
		# self.changeMarkerSize()

	def resetImageRight(self,img=None):
		if img is None and self.mipCHKbox_right is False:
			img = self.imgstack_right_layer1[self.slice_right,:]
			## reset brightness contrast
			self.brightness_right_layer1 = 0
			self.contrast_right_layer1 = 10
			self.horizontalSlider_brightness.setValue(0)
			self.horizontalSlider_contrast.setValue(10)
		elif img is None:
			img = self.img_right_layer1
			## reset brightness contrast
			self.brightness_right_layer1 = 0
			self.contrast_right_layer1 = 10
			self.horizontalSlider_brightness.setValue(0)
			self.horizontalSlider_contrast.setValue(10)
		# print img.shape
		## Reset Overlay
		self.img_right_overlay = None
		## Load original
		self.img_right_displayed_layer1 = np.copy(img)
		self.img_adj_right_layer1 = np.copy(img)
		## Display image
		self.displayImage(side='right')
		self.sceneRight.deleteArrows()
		# self.changeMarkerSize()

	def rotateImage(self):
		if self.label_selimg.text() == 'left':
			if int(self.spinBox_rot.value()) == 360:
				self.spinBox_rot.setValue(0)
			elif int(self.spinBox_rot.value()) == -1:
				self.spinBox_rot.setValue(359)
			self.graphicsView_left.rotate(int(self.spinBox_rot.value())-self.sceneLeft.rotangle)
			self.sceneLeft.rotangle = int(self.spinBox_rot.value())
			## Update graphics
			self.sceneLeft.enumeratePoints()
		elif self.label_selimg.text() == 'right':
			if int(self.spinBox_rot.value()) == 360:
				self.spinBox_rot.setValue(0)
			elif int(self.spinBox_rot.value()) == -1:
				self.spinBox_rot.setValue(359)
			self.graphicsView_right.rotate(int(self.spinBox_rot.value())-self.sceneRight.rotangle)
			self.sceneRight.rotangle = int(self.spinBox_rot.value())
			## Update graphics
			self.sceneRight.enumeratePoints()

	def rotateImage45(self,direction=None):
		if direction is None:
			print clrmsg.ERROR + "Please specify direction ('cw' or 'ccw')."
		# rotate 45 degree clockwise
		elif direction == 'cw':
			if self.label_selimg.text() == 'left':
				self.sceneLeft.rotangle += 45
				self.graphicsView_left.rotate(45)
				self.sceneLeft.rotangle = self.anglectrl(angle=self.sceneLeft.rotangle)
				self.spinBox_rot.setValue(self.sceneLeft.rotangle)
				## Update graphics
				self.sceneLeft.enumeratePoints()
			elif self.label_selimg.text() == 'right':
				self.sceneRight.rotangle += 45
				self.graphicsView_right.rotate(45)
				self.sceneRight.rotangle = self.anglectrl(angle=self.sceneRight.rotangle)
				self.spinBox_rot.setValue(self.sceneRight.rotangle)
				## Update graphics
				self.sceneRight.enumeratePoints()
		# rotate 45 degree anticlockwise
		elif direction == 'ccw':
			if self.label_selimg.text() == 'left':
				self.sceneLeft.rotangle -= 45
				self.graphicsView_left.rotate(-45)
				self.sceneLeft.rotangle = self.anglectrl(angle=self.sceneLeft.rotangle)
				self.spinBox_rot.setValue(self.sceneLeft.rotangle)
			elif self.label_selimg.text() == 'right':
				self.sceneRight.rotangle -= 45
				self.graphicsView_right.rotate(-45)
				self.sceneRight.rotangle = self.anglectrl(angle=self.sceneRight.rotangle)
				self.spinBox_rot.setValue(self.sceneRight.rotangle)

	def anglectrl(self,angle=None):
		if angle is None:
			print clrmsg.ERROR + "Please specify side, e.g. anglectrl(angle=self.sceneLeft.rotangle)"
		elif angle >= 360:
			angle -= 360
		elif angle < 0:
			angle += 360
		return angle

	def changeMarkerSize(self):
		if self.label_selimg.text() == 'left':
			self.sceneLeft.markerSize = int(self.spinBox_markerSize.value())
			## Update graphics
			self.sceneLeft.enumeratePoints()
			if self.sceneLeft.pixelSize:
				if debug is True: print clrmsg.DEBUG + "Doing stuff with image pixelSize (left image).", self.label_imgpxsize.text()
				try:
					self.label_markerSizeNano.setText(str(self.sceneLeft.markerSize*2*self.sceneLeft.pixelSize))
					self.label_markerSizeNanoUnit.setText(self.sceneLeft.pixelSizeUnit)
				except:
					if debug is True: print clrmsg.DEBUG + "Image pixel size is not a number:", self.label_imgpxsize.text()
					self.label_markerSizeNano.setText("NaN")
					self.label_markerSizeNanoUnit.setText('')
			else:
				self.label_markerSizeNano.setText('')
				self.label_markerSizeNanoUnit.setText('')
		elif self.label_selimg.text() == 'right':
			self.sceneRight.markerSize = int(self.spinBox_markerSize.value())
			## Update graphics
			self.sceneRight.enumeratePoints()
			if self.sceneRight.pixelSize:
				if debug is True: print clrmsg.DEBUG + "Doing stuff with image pixelSize (right image).", self.label_imgpxsize.text()
				try:
					self.label_markerSizeNano.setText(str(self.sceneRight.markerSize*2*self.sceneRight.pixelSize))
					self.label_markerSizeNanoUnit.setText(self.sceneRight.pixelSizeUnit)
				except:
					if debug is True: print clrmsg.DEBUG + "Image pixel size is not a number:", self.label_imgpxsize.text()
					self.label_markerSizeNano.setText("NaN")
					self.label_markerSizeNanoUnit.setText('')
			else:
				self.label_markerSizeNano.setText('')
				self.label_markerSizeNanoUnit.setText('')

	def setCustomRotCenter(self,maxdim):
		## The default value is set as the center of a cube with an edge length equal to the longest edge of the image volume
		halfmaxdim = 0.5 * maxdim
		self.doubleSpinBox_custom_rot_center_x.setValue(halfmaxdim)
		self.doubleSpinBox_custom_rot_center_y.setValue(halfmaxdim)
		self.doubleSpinBox_custom_rot_center_z.setValue(halfmaxdim)

												##################### END #####################
												###### Image initialization and rotation ######
												###############################################

												###############################################
												######    Image processing functions     ######
												#################### START ####################
	## Read image
	def imread(self,path,normalize=True):
		"""
		Returns a 2D numpy array (maximum intensity projection for stack image files), the kind of image as 5 bit
		encoded image property and the original stack file as a numpy array or 'None' if file is 2D image.

		return 5 bit encoded image property:
			1 = 2D
			2 = 3D (always normalized, +16)
			4 = gray scale
			8 = multicolor/multichannel
			16= normalized
		"""
		if debug is True: print clrmsg.DEBUG + "===== imread"
		img = tf.imread(path)
		if debug is True: print clrmsg.DEBUG + "Image shape/dtype:", img.shape, img.dtype
		## Displaying issues with uint16 images -> convert to uint8
		if img.dtype == 'uint16':
			img = img*(255.0/img.max())
			img = img.astype(dtype=np.uint8)
			if debug is True: print clrmsg.DEBUG + "Image dtype converted to:", img.shape, img.dtype
		if img.ndim == 4:
			if debug is True: print clrmsg.DEBUG + "Calculating multichannel MIP"
			## return MIP, code 2+8+16 and image stack
			return np.amax(img, axis=1), 26, img
		## this can only handle rgb. For more channels set "3" to whatever max number of channels should be handled
		elif img.ndim == 3 and any([True for dim in img.shape if dim <= 4]) or img.ndim == 2:
			if debug is True: print clrmsg.DEBUG + "Loading regular 2D image... multicolor/normalize:", \
				[True for x in [img.ndim] if img.ndim == 3],'/',[normalize]
			if normalize is True:
				## return normalized 2D image with code 1+4+16 for gray scale normalized 2D image and 1+8+16 for
				## multicolor normalized 2D image
				return self.norm_img(img), 25 if img.ndim == 3 else 21, None
			else:
				## return 2D image with code 1+4 for gray scale 2D image and 1+8 for multicolor 2D image
				return img, 9 if img.ndim == 3 else 5, None
		elif img.ndim == 3:
			if debug is True: print clrmsg.DEBUG + "Calculating MIP"
			## return MIP and code 2+4+1E6
			return np.amax(img, axis=0), 22, img

	def pxSize(self,img_path,z=False):
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
											pixelSize = float(piece)
											if debug is True: print clrmsg.DEBUG + "Pixel size from exif metakey:", keyword
											## Value is in um from CorrSight/LA tiff files
											if z:
												pixelSize = pixelSize*1000
											return pixelSize
										except Exception as e:
											if debug is True: print clrmsg.DEBUG + "Pixel size parser:", e
											pass
								elif keyword == 'PixelWidth':
									for piece in tag.value[tagpos:tagpos+30].split('='):
										try:
											pixelSize = float(piece.strip().split('\r\n')[0])
											if debug is True: print clrmsg.DEBUG + "Pixel size from exif metakey:", keyword
											## *1E6 because these values from SEM/FIB image is in m
											return pixelSize*1E6
										except Exception as e:
											if debug is True: print clrmsg.DEBUG + "Pixel size parser:", e
											pass
								elif keyword == 'PixelSize' or 'FocusStepSize':
									for piece in tag.value[tagpos:tagpos+30].split('"'):
										try:
											pixelSize = float(piece)
											if debug is True: print clrmsg.DEBUG + "Pixel size from exif metakey:", keyword
											## Value is in um from CorrSight/LA tiff files
											return pixelSize
										except Exception as e:
											if debug is True: print clrmsg.DEBUG + "Pixel size parser:", e
											pass

	## Convert opencv image (numpy array in BGR) to RGB QImage and return pixmap. Only takes 2D images
	def cv2Qimage(self,img,combobox=None):
		if debug is True: print clrmsg.DEBUG + "===== cv2Qimage"
		if img.shape[0] <= 4:
			if debug is True: print clrmsg.DEBUG + "Swapping image axes from c,y,x to y,x,c."
			img = img.swapaxes(0,2).swapaxes(0,1)
		if debug is True: print clrmsg.DEBUG + "Image shape:", img.shape

		return QtGui.QPixmap.fromImage(qimage2ndarray.array2qimage(img))

	def setBrightCont(self):
		if self.label_selimg.text() == 'left':
			if self.radioButton_layer1.isChecked():
				self.brightness_left_layer1 = self.horizontalSlider_brightness.value()
				self.contrast_left_layer1 = self.horizontalSlider_contrast.value()
				self.img_adj_left_layer1 = self.adjustBrightCont(
					self.img_left_displayed_layer1,self.img_adj_left_layer1,self.brightness_left_layer1,self.contrast_left_layer1)
			elif self.radioButton_layer2.isChecked():
				self.brightness_left_layer2 = self.horizontalSlider_brightness.value()
				self.contrast_left_layer2 = self.horizontalSlider_contrast.value()
				self.img_adj_left_layer2 = self.adjustBrightCont(
					self.img_left_displayed_layer2,self.img_adj_left_layer2,self.brightness_left_layer2,self.contrast_left_layer2)
			elif self.radioButton_layer3.isChecked():
				self.brightness_left_layer3 = self.horizontalSlider_brightness.value()
				self.contrast_left_layer3 = self.horizontalSlider_contrast.value()
				self.img_adj_left_layer3 = self.adjustBrightCont(
					self.img_left_displayed_layer3,self.img_adj_left_layer3,self.brightness_left_layer3,self.contrast_left_layer3)
		if self.label_selimg.text() == 'right':
			if self.radioButton_layer1.isChecked():
				self.brightness_right_layer1 = self.horizontalSlider_brightness.value()
				self.contrast_right_layer1 = self.horizontalSlider_contrast.value()
				self.img_adj_right_layer1 = self.adjustBrightCont(
					self.img_right_displayed_layer1,self.img_adj_right_layer1,self.brightness_right_layer1,self.contrast_right_layer1)
			elif self.radioButton_layer2.isChecked():
				self.brightness_right_layer2 = self.horizontalSlider_brightness.value()
				self.contrast_right_layer2 = self.horizontalSlider_contrast.value()
				self.img_adj_right_layer2 = self.adjustBrightCont(
					self.img_right_displayed_layer2,self.img_adj_right_layer2,self.brightness_right_layer2,self.contrast_right_layer2)
			elif self.radioButton_layer3.isChecked():
				self.brightness_right_layer3 = self.horizontalSlider_brightness.value()
				self.contrast_right_layer3 = self.horizontalSlider_contrast.value()
				self.img_adj_right_layer3 = self.adjustBrightCont(
					self.img_right_displayed_layer3,self.img_adj_right_layer3,self.brightness_right_layer3,self.contrast_right_layer3)
		## Display image
		self.displayImage()

	## Adjust Brightness and Contrast by sliders
	def adjustBrightCont(self,img_displayed,img_adjusted,brightness,contrast):
		if debug is True: ping = time.time()
		if debug is True: print clrmsg.DEBUG + "===== adjustBrightCont"
		## Load replacement
		img_adjusted = np.copy(img_displayed)
		## Load contrast value (Slider value between 0 and 100)
		contr = contrast*0.1
		## Adjusting contrast
		img_adjusted = np.where(img_adjusted*contr >= 255,255,img_adjusted*contr)
		## Convert float64 back to uint8
		img_adjusted = img_adjusted.astype(dtype=np.uint8)
		## Adjust brightness
		if brightness > 0:
			img_adjusted = np.where(255-img_adjusted <= brightness,255,img_adjusted+brightness)
		else:
			img_adjusted = np.where(img_adjusted <= -brightness,0,img_adjusted+brightness)
			## Convert from int16 back to uint8
			img_adjusted = img_adjusted.astype(dtype=np.uint8)
		if debug is True: pong = time.time()
		if debug is True: print clrmsg.DEBUG + 'adjusting brightness/contrast in s:', pong-ping
		return img_adjusted

	## Normalize Image
	def norm_img(self,img,copy=False):
		if debug is True: print clrmsg.DEBUG + "===== norm_img"
		if copy is True:
			img = np.copy(img)
		dtype = str(img.dtype)
		## Determine data type
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
			## tifffile reads z,y,x for stacks but y,x,c if it is multichannel image (or z,c,y,x if it is a multicolor image stack)
			if img.shape[-1] > 4:
				if debug is True: print clrmsg.DEBUG + "image stack"
				for i in range(int(img.shape[0])):
					img[i,:,:] *= typesize/img[i,:,:].max()
			else:
				if debug is True: print clrmsg.DEBUG + "multichannel image"
				for i in range(int(img.shape[2])):
					img[:,:,i] *= typesize/img[:,:,i].max()
		return img

	def selectSlice(self):
		if self.label_selimg.text() == 'left':
			self.mipCHKbox_left = self.checkBox_MIP.isChecked()
		elif self.label_selimg.text() == 'right':
			self.mipCHKbox_right = self.checkBox_MIP.isChecked()

		if self.checkBox_MIP.isChecked():
			if self.label_selimg.text() == 'left' and '{0:b}'.format(self.sceneLeft.imagetype)[-1] == '0':
				self.img_left_displayed_layer1 = self.img_left_layer1
				self.img_adj_left_layer1 = self.img_left_layer1
				self.img_left_displayed_layer2 = self.img_left_layer2
				self.img_adj_left_layer2 = self.img_left_layer2
				self.img_left_displayed_layer3 = self.img_left_layer3
				self.displayImage('left')
				if self.brightness_left_layer1 != 0 and self.contrast_left_layer1 != 10:
					self.setBrightCont()
				else:
					self.img_adj_left_layer3 = self.img_left_layer3
				# self.resetImageLeft(img=None)
			elif self.label_selimg.text() == 'right' and '{0:b}'.format(self.sceneRight.imagetype)[-1] == '0':
				self.img_right_displayed_layer1 = self.img_right_layer1
				self.img_adj_right_layer1 = self.img_right_layer1
				self.img_right_displayed_layer2 = self.img_right_layer2
				self.img_adj_right_layer2 = self.img_right_layer2
				self.img_right_displayed_layer3 = self.img_right_layer3
				self.img_adj_right_layer3 = self.img_right_layer3
				# self.resetImageRight(img=None)
				if self.brightness_right_layer1 != 0 or self.contrast_right_layer1 != 10:
					self.setBrightCont()
				else:
					self.displayImage('right')
		else:
			if self.label_selimg.text() == 'left' and '{0:b}'.format(self.sceneLeft.imagetype)[-1] == '0':
				self.slice_left = int(self.spinBox_slice.value())
				# img = self.imgstack_left_layer1[self.slice_left,:]
				self.img_left_displayed_layer1 = self.imgstack_left_layer1[self.slice_left,:]
				self.img_adj_left_layer1 = self.imgstack_left_layer1[self.slice_left,:]
				if self.img_left_layer2 is not None:
					self.img_left_displayed_layer2 = self.imgstack_left_layer2[self.slice_left,:]
					self.img_adj_left_layer2 = self.imgstack_left_layer2[self.slice_left,:]
				if self.img_left_layer3 is not None:
					self.img_left_displayed_layer3 = self.imgstack_left_layer3[self.slice_left,:]
					self.img_adj_left_layer3 = self.imgstack_left_layer3[self.slice_left,:]
				# self.resetImageLeft(img=img)
				if self.brightness_left_layer1 != 0 and self.contrast_left_layer1 != 10:
					self.setBrightCont()
				else:
					self.displayImage('left')
			elif self.label_selimg.text() == 'right' and '{0:b}'.format(self.sceneRight.imagetype)[-1] == '0':
				self.slice_right = int(self.spinBox_slice.value())
				# img = self.imgstack_right_layer1[self.slice_right,:]
				self.img_right_displayed_layer1 = self.imgstack_right_layer1[self.slice_right,:]
				self.img_adj_right_layer1 = self.imgstack_right_layer1[self.slice_right,:]
				if self.img_right_layer2 is not None:
					self.img_right_displayed_layer2 = self.imgstack_right_layer2[self.slice_right,:]
					self.img_adj_right_layer2 = self.imgstack_right_layer2[self.slice_right,:]
				if self.img_right_layer3 is not None:
					self.img_right_displayed_layer3 = self.imgstack_right_layer3[self.slice_right,:]
					self.img_adj_right_layer3 = self.imgstack_right_layer3[self.slice_right,:]
				# self.resetImageRight(img=img)
				if self.brightness_right_layer1 != 0 or self.contrast_right_layer1 != 10:
					self.setBrightCont()
				else:
					self.displayImage('right')
		# self.img_adj_left_layer1

	def changeColorChannel(self):
		if self.label_selimg.text() == 'left':
			if self.layer1Color_left != self.comboBox_channelColorLayer1.currentIndex():
				self.layer1Color_left = self.comboBox_channelColorLayer1.currentIndex()
				if self.layer1Color_left == 4:
					self.layer1CustomColor_left = self.getCustomChannelColor()
			if self.layer2Color_left != self.comboBox_channelColorLayer2.currentIndex():
				self.layer2Color_left = self.comboBox_channelColorLayer2.currentIndex()
				if self.layer2Color_left == 4:
					self.layer2CustomColor_left = self.getCustomChannelColor()
			if self.layer3Color_left != self.comboBox_channelColorLayer3.currentIndex():
				self.layer3Color_left = self.comboBox_channelColorLayer3.currentIndex()
				if self.layer3Color_left == 4:
					self.layer3CustomColor_left = self.getCustomChannelColor()
			self.displayImage(side='left')
		elif self.label_selimg.text() == 'right':
			if self.layer1Color_right != self.comboBox_channelColorLayer1.currentIndex():
				self.layer1Color_right = self.comboBox_channelColorLayer1.currentIndex()
				if self.layer1Color_right == 4:
					self.layer1CustomColor_right = self.getCustomChannelColor()
			if self.layer2Color_right != self.comboBox_channelColorLayer2.currentIndex():
				self.layer2Color_right = self.comboBox_channelColorLayer2.currentIndex()
				if self.layer2Color_right == 4:
					self.layer2CustomColor_right = self.getCustomChannelColor()
			if self.layer3Color_right != self.comboBox_channelColorLayer3.currentIndex():
				self.layer3Color_right = self.comboBox_channelColorLayer3.currentIndex()
				if self.layer3Color_right == 4:
					self.layer3CustomColor_right = self.getCustomChannelColor()
			self.displayImage(side='right')

	def colorizeImage(self,img,color=None):
		if debug is True: ping = time.time()
		if color is None and all(comboboxColor == 'none' for comboboxColor in [
																self.comboBox_channelColorLayer1.currentText(),
																self.comboBox_channelColorLayer2.currentText(),
																self.comboBox_channelColorLayer3.currentText()]):
			if debug is True: pong = time.time()
			if debug is True: print clrmsg.DEBUG + 'colorize image in s:', pong-ping
			return img
		elif color is None:
			color = [255,255,255]
		## rgb to gray scale if colored
		if img.ndim == 3:
			img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
		imgC = np.zeros([img.shape[0],img.shape[1],3], dtype=np.uint8)
		imgC[:,:,0] = img*(color[0]/255.0)
		imgC[:,:,1] = img*(color[1]/255.0)
		imgC[:,:,2] = img*(color[2]/255.0)
		if debug is True: pong = time.time()
		if debug is True: print clrmsg.DEBUG + 'colorize image in s:', pong-ping
		return imgC.astype(dtype=np.uint8)

	def colorCoder(self,code,side,layer):
		if code == 0:
			if side == 'left' and self.img_left_overlay is not None:
				return [255,255,255]
			elif side == 'right' and self.img_right_overlay is not None:
				return [255,255,255]
			else:
				return None
		elif code == 1:
			return [255,0,0]
		elif code == 2:
			return [0,255,0]
		elif code == 3:
			return [0,0,255]
		elif code == 4:
			if side == 'left':
				if layer == 1:
					return self.layer1CustomColor_left
				elif layer == 2:
					return self.layer2CustomColor_left
				elif layer == 3:
					return self.layer3CustomColor_left
			elif side == 'right':
				if layer == 1:
					return self.layer1CustomColor_right
				elif layer == 2:
					return self.layer2CustomColor_right
				elif layer == 3:
					return self.layer3CustomColor_right

	def displayImage(self,side=None,save=False,keepRGB=False):
		"""
		Display all active images. Set side to 'left' or 'right' for specific refresh, otherwise the active focused image side is used.
		"""
		if debug is True: ping = time.time()
		if side is None:
			side = self.label_selimg.text()
		if side == 'left':
			if self.layer1CHKbox_left is True:
				if keepRGB is True:
					image_list = [self.img_adj_left_layer1]
				else:
					image_list = [self.colorizeImage(self.img_adj_left_layer1,color=self.colorCoder(self.layer1Color_left,'left',1))]
			else:
				image_list = []
			if self.img_left_layer2 is not None and self.layer2CHKbox_left is True:
				image_list.append(self.colorizeImage(self.img_adj_left_layer2,color=self.colorCoder(self.layer2Color_left,'left',2)))
			if self.img_left_layer3 is not None and self.layer3CHKbox_left is True:
				image_list.append(self.colorizeImage(self.img_adj_left_layer3,color=self.colorCoder(self.layer3Color_left,'left',3)))
			if self.img_left_overlay is not None:
				image_list.append(self.img_left_overlay)
			img_blend = self.blendImages(image_list)
			## Display image
			## Remove image (item)
			self.sceneLeft.removeItem(self.pixmap_item_left)
			self.pixmap_left = self.cv2Qimage(img_blend)
			self.pixmap_item_left = QtGui.QGraphicsPixmapItem(self.pixmap_left, None, self.sceneLeft)
			## Put exchanged image into background
			QtGui.QGraphicsItem.stackBefore(self.pixmap_item_left, self.sceneLeft.items()[-1])
			## fix bug, where markers vanished behind image, by setting z value low enough
			self.pixmap_item_left.setZValue(-10)
		elif side == 'right':
			if self.layer1CHKbox_right is True:
				image_list = [self.colorizeImage(self.img_adj_right_layer1,color=self.colorCoder(self.layer1Color_right,'right',1))]
			else:
				image_list = []
			if self.img_right_layer2 is not None and self.layer2CHKbox_right is True:
				image_list.append(self.colorizeImage(self.img_adj_right_layer2,color=self.colorCoder(self.layer2Color_right,'right',2)))
			if self.img_right_layer3 is not None and self.layer3CHKbox_right is True:
				image_list.append(self.colorizeImage(self.img_adj_right_layer3,color=self.colorCoder(self.layer3Color_right,'right',3)))
			if self.img_right_overlay is not None:
				image_list.append(self.img_right_overlay)
			img_blend = self.blendImages(image_list)
			## Display image
			## Remove image (item)
			self.sceneRight.removeItem(self.pixmap_item_right)
			self.pixmap_right = self.cv2Qimage(img_blend)
			self.pixmap_item_right = QtGui.QGraphicsPixmapItem(self.pixmap_right, None, self.sceneRight)
			## Put exchanged image into background
			QtGui.QGraphicsItem.stackBefore(self.pixmap_item_right, self.sceneRight.items()[-1])
			## fix bug, where markers vanished behind image, by setting z value low enough
			self.pixmap_item_right.setZValue(-10)
		if save is True:
			timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
			cv2.imwrite(os.path.join(self.workingdir,timestamp+"_image.tif"), cv2.cvtColor(img_blend,cv2.COLOR_RGB2BGR))
		if debug is True: pong = time.time()
		if debug is True: print clrmsg.DEBUG + 'displaying image in s:', pong-ping

	def blendImages(self,images,blendmode='screen'):
		"""
		Blends multiple images (same numpy size and type) and returns a single image (numpy array). Images are passed in as a list argument.
		"""
		if debug is True: ping = time.time()
		if len(images) == 0:
			return np.zeros([10,10],dtype=np.uint8)-1
		if len(images) == 1:
			return images[0].astype(dtype=np.uint8)
		else:
			blend = []
			for i in range(len(images)):
				if i == 0:
					blend = images[i]
				else:
					if blendmode == 'screen':
						blend = blend + images[i] - (blend * images[i].astype(dtype=np.float32)/255.0)
					elif blendmode == 'minimum':
						blend = np.minimum(blend,images[i])
			if debug is True: pong = time.time()
			if debug is True: print clrmsg.DEBUG + 'blending images in s:', pong-ping
			return blend.astype(dtype=np.uint8)

	def layerCtrl(self,layer,load=False):
		"""
		Keeping tabs on which layers are active or not
		"""
		if layer == 'layer1':
			if self.label_selimg.text() == 'left':
				self.layer1CHKbox_left = self.checkBox_layer1.isChecked()
			else:
				self.layer1CHKbox_right = self.checkBox_layer1.isChecked()
		elif layer == 'layer2':
			if self.label_selimg.text() == 'left':
				self.layer2CHKbox_left = self.checkBox_layer2.isChecked()
				if self.img_left_layer2 is None and self.checkBox_layer2.isChecked() or load is True:
					path = str(QtGui.QFileDialog.getOpenFileName(
						None,"Select image file", self.workingdir,"Image Files (*.tif *.tiff);; All (*.*)"))
					self.activateWindow()
					if path == '':
						if load is True:
							return
						else:
							self.layer2CHKbox_left = False
							self.checkBox_layer2.setChecked(False)
							return
					# path = '/Users/jan/Desktop/correlation_test_dataset/single_tif_files/single_tif_files_1.tif'
					self.img_left_layer2,self.sceneLeft.imagetype_layer2,self.imgstack_left_layer2 = self.imread(path)
					self.img_adj_left_layer2 = np.copy(self.img_left_layer2)
					if self.sceneLeft.imagetype_layer2 != self.sceneLeft.imagetype:
						QtGui.QMessageBox.critical(
							self,"Warning", "This image file does not seem to be of the same kind as the first image!")
						self.img_left_layer2,self.sceneLeft.imagetype_layer2,self.imgstack_left_layer2 = None, None, None
						self.layer2CHKbox_left = False
						self.checkBox_layer2.setChecked(False)
					elif self.imgstack_left_layer1 is not None and self.imgstack_left_layer2.shape != self.imgstack_left_layer1.shape:
						QtGui.QMessageBox.critical(
							self,"Warning",
							"This image file does not have the same dimensions as the first image: \nNeeds to be {0}\nbut is{1}".format(
								self.imgstack_left_layer1.shape, self.imgstack_left_layer2.shape))
						self.img_left_layer2,self.sceneLeft.imagetype_layer2,self.imgstack_left_layer2 = None, None, None
						self.layer2CHKbox_left = False
						self.checkBox_layer2.setChecked(False)
					elif self.imgstack_left_layer1 is None and self.img_left_layer2.shape != self.img_left_layer1.shape:
						QtGui.QMessageBox.critical(
							self,"Warning",
							"This image file does not have the same dimensions as the first image: \nNeeds to be {0}\nbut is{1}".format(
								self.img_left_layer1.shape, self.img_left_layer2.shape))
						self.img_left_layer2,self.sceneLeft.imagetype_layer2,self.imgstack_left_layer2 = None, None, None
						self.layer2CHKbox_left = False
						self.checkBox_layer2.setChecked(False)
					else:
						if load is True:
							self.checkBox_layer2.blockSignals(True)
							self.layer2CHKbox_left = True
							self.checkBox_layer2.setChecked(True)
							self.comboBox_channelColorLayer2.setEnabled(True)
							self.radioButton_layer2.setEnabled(True)
							self.checkBox_layer2.blockSignals(False)
						self.img_left_displayed_layer2 = self.img_left_layer2
						self.selectSlice()
			else:
				self.layer2CHKbox_right = self.checkBox_layer2.isChecked()
				if self.img_right_layer2 is None and self.checkBox_layer2.isChecked() or load is True:
					path = str(QtGui.QFileDialog.getOpenFileName(
						None,"Select image file", self.workingdir,"Image Files (*.tif *.tiff);; All (*.*)"))
					self.activateWindow()
					if path == '':
						if load is True:
							return
						else:
							self.layer2CHKbox_right = False
							self.checkBox_layer2.setChecked(False)
							return
					# path = '/Users/jan/Desktop/correlation_test_dataset/single_tif_files/single_tif_files_1.tif'
					self.img_right_layer2,self.sceneRight.imagetype_layer2,self.imgstack_right_layer2 = self.imread(path)
					self.img_adj_right_layer2 = np.copy(self.img_right_layer2)
					if self.sceneRight.imagetype_layer2 != self.sceneRight.imagetype:
						QtGui.QMessageBox.critical(
							self,"Warning", "This image file does not seem to be of the same kind as the first image!")
						self.img_right_layer2,self.sceneRight.imagetype_layer2,self.imgstack_right_layer2 = None, None, None
						self.layer2CHKbox_right = False
						self.checkBox_layer2.setChecked(False)
					elif self.imgstack_right_layer1 is not None and self.imgstack_right_layer2.shape != self.imgstack_right_layer1.shape:
						QtGui.QMessageBox.critical(
							self,"Warning",
							"This image file does not have the same dimensions as the first image: \nNeeds to be {0}\nbut is{1}".format(
								self.imgstack_right_layer1.shape, self.imgstack_right_layer2.shape))
						self.img_right_layer2,self.sceneRight.imagetype_layer2,self.imgstack_right_layer2 = None, None, None
						self.layer2CHKbox_right = False
						self.checkBox_layer2.setChecked(False)
					elif self.imgstack_right_layer1 is None and self.img_right_layer2.shape != self.img_right_layer1.shape:
						QtGui.QMessageBox.critical(
							self,"Warning",
							"This image file does not have the same dimensions as the first image: \nNeeds to be {0}\nbut is{1}".format(
								self.img_right_layer1.shape, self.img_right_layer2.shape))
						self.img_right_layer2,self.sceneRight.imagetype_layer2,self.imgstack_right_layer2 = None, None, None
						self.layer2CHKbox_right = False
						self.checkBox_layer2.setChecked(False)
					else:
						if load is True:
							self.checkBox_layer2.blockSignals(True)
							self.layer2CHKbox_right = True
							self.checkBox_layer2.setChecked(True)
							self.comboBox_channelColorLayer2.setEnabled(True)
							self.radioButton_layer2.setEnabled(True)
							self.checkBox_layer2.blockSignals(False)
						self.img_right_displayed_layer2 = self.img_right_layer2
						self.selectSlice()
		elif layer == 'layer3':
			if self.label_selimg.text() == 'left':
				self.layer3CHKbox_left = self.checkBox_layer3.isChecked()
				if self.img_left_layer3 is None and self.checkBox_layer3.isChecked() or load is True:
					path = str(QtGui.QFileDialog.getOpenFileName(
						None,"Select image file", self.workingdir,"Image Files (*.tif *.tiff);; All (*.*)"))
					self.activateWindow()
					if path == '':
						if load is True:
							return
						else:
							self.layer3CHKbox_left = False
							self.checkBox_layer3.setChecked(False)
							return
					# path = '/Users/jan/Desktop/correlation_test_dataset/single_tif_files/single_tif_files_1.tif'
					self.img_left_layer3,self.sceneLeft.imagetype_layer3,self.imgstack_left_layer3 = self.imread(path)
					self.img_adj_left_layer3 = np.copy(self.img_left_layer3)
					if self.sceneLeft.imagetype_layer3 != self.sceneLeft.imagetype:
						QtGui.QMessageBox.critical(
							self,"Warning", "This image file does not seem to be of the same kind as the first image!")
						self.img_left_layer3,self.sceneLeft.imagetype_layer3,self.imgstack_left_layer3 = None, None, None
						self.layer3CHKbox_left = False
						self.checkBox_layer3.setChecked(False)
					elif self.imgstack_left_layer1 is not None and self.imgstack_left_layer3.shape != self.imgstack_left_layer1.shape:
						QtGui.QMessageBox.critical(
							self,"Warning",
							"This image file does not have the same dimensions as the first image: \nNeeds to be {0}\nbut is{1}".format(
								self.imgstack_left_layer1.shape, self.imgstack_left_layer3.shape))
						self.img_left_layer3,self.sceneLeft.imagetype_layer3,self.imgstack_left_layer3 = None, None, None
						self.layer3CHKbox_left = False
						self.checkBox_layer3.setChecked(False)
					elif self.imgstack_left_layer1 is None and self.img_left_layer3.shape != self.img_left_layer1.shape:
						QtGui.QMessageBox.critical(
							self,"Warning",
							"This image file does not have the same dimensions as the first image: \nNeeds to be {0}\nbut is{1}".format(
								self.img_left_layer1.shape, self.img_left_layer3.shape))
						self.img_left_layer3,self.sceneLeft.imagetype_layer3,self.imgstack_left_layer3 = None, None, None
						self.layer3CHKbox_left = False
						self.checkBox_layer3.setChecked(False)
					else:
						if load is True:
							self.checkBox_layer3.blockSignals(True)
							self.layer3CHKbox_left = True
							self.checkBox_layer3.setChecked(True)
							self.comboBox_channelColorLayer3.setEnabled(True)
							self.radioButton_layer3.setEnabled(True)
							self.checkBox_layer3.blockSignals(False)
						self.img_left_displayed_layer3 = self.img_left_layer3
						self.selectSlice()
			else:
				self.layer3CHKbox_right = self.checkBox_layer3.isChecked()
				if self.img_right_layer3 is None and self.checkBox_layer3.isChecked() or load is True:
					path = str(QtGui.QFileDialog.getOpenFileName(
						None,"Select image file", self.workingdir,"Image Files (*.tif *.tiff);; All (*.*)"))
					self.activateWindow()
					if path == '':
						if load is True:
							return
						else:
							self.layer3CHKbox_right = False
							self.checkBox_layer3.setChecked(False)
							return
					# path = '/Users/jan/Desktop/correlation_test_dataset/single_tif_files/single_tif_files_1.tif'
					self.img_right_layer3,self.sceneRight.imagetype_layer3,self.imgstack_right_layer3 = self.imread(path)
					self.img_adj_right_layer3 = np.copy(self.img_right_layer3)
					if self.sceneRight.imagetype_layer3 != self.sceneRight.imagetype:
						QtGui.QMessageBox.critical(
							self,"Warning", "This image file does not seem to be of the same kind as the first image!")
						self.img_right_layer3,self.sceneRight.imagetype_layer3,self.imgstack_right_layer3 = None, None, None
						self.layer3CHKbox_right = False
						self.checkBox_layer3.setChecked(False)
					elif self.imgstack_right_layer1 is not None and self.imgstack_right_layer3.shape != self.imgstack_right_layer1.shape:
						QtGui.QMessageBox.critical(
							self,"Warning",
							"This image file does not have the same dimensions as the first image: \nNeeds to be {0}\nbut is{1}".format(
								self.imgstack_right_layer1.shape, self.imgstack_right_layer3.shape))
						self.img_right_layer3,self.sceneRight.imagetype_layer3,self.imgstack_right_layer3 = None, None, None
						self.layer3CHKbox_right = False
						self.checkBox_layer3.setChecked(False)
					elif self.imgstack_right_layer1 is None and self.img_right_layer3.shape != self.img_right_layer1.shape:
						QtGui.QMessageBox.critical(
							self,"Warning",
							"This image file does not have the same dimensions as the first image: \nNeeds to be {0}\nbut is{1}".format(
								self.img_right_layer1.shape, self.img_right_layer3.shape))
						self.img_right_layer3,self.sceneRight.imagetype_layer3,self.imgstack_right_layer3 = None, None, None
						self.layer3CHKbox_right = False
						self.checkBox_layer3.setChecked(False)
					else:
						if load is True:
							self.checkBox_layer3.blockSignals(True)
							self.layer3CHKbox_right = True
							self.checkBox_layer3.setChecked(True)
							self.comboBox_channelColorLayer3.setEnabled(True)
							self.radioButton_layer3.setEnabled(True)
							self.checkBox_layer3.blockSignals(False)
						self.img_right_displayed_layer3 = self.img_right_layer3
						self.selectSlice()
		self.displayImage()

												##################### END #####################
												######    Image processing functions    #######
												###############################################

												###############################################
												######     CSV - Point import/export    #######
												#################### START ####################

	def autosave(self):
		csv_file_out = os.path.splitext(self.leftImage)[0] + '_coordinates.txt'
		csvHandler.model2csv(self.modelLleft,csv_file_out,delimiter="\t")
		csv_file_out = os.path.splitext(self.rightImage)[0] + '_coordinates.txt'
		csvHandler.model2csv(self.modelRight,csv_file_out,delimiter="\t")

	def exportPoints(self):
		## bugfix for KDE file dialog
		side = self.label_selectedTable.text()

		if side == 'left':
			model = self.modelLleft
		elif side == 'right':
			model = self.modelRight
		## Export Dialog. Needs check for extension or add default extension
		csv_file_out, filterdialog = QtGui.QFileDialog.getSaveFileNameAndFilter(
			self, 'Export file as',
			os.path.dirname(self.leftImage) if side == 'left' else os.path.dirname(self.rightImage),
			"Tabstop separated (*.csv *.txt);;Comma separated (*.csv *.txt)")
		self.activateWindow()
		if str(filterdialog).startswith('Comma') is True:
			csvHandler.model2csv(model,csv_file_out,delimiter=",")
		elif str(filterdialog).startswith('Tabstop') is True:
			csvHandler.model2csv(model,csv_file_out,delimiter="\t")

	def importPoints(self):
		## bugfix for KDE file dialog
		side = self.label_selectedTable.text()

		csv_file_in, filterdialog = QtGui.QFileDialog.getOpenFileNameAndFilter(
			self, 'Import file as',
			os.path.dirname(self.leftImage) if side == 'left' else os.path.dirname(self.rightImage),
			"Tabstop separated (*.csv *.txt);;Comma separated (*.csv *.txt)")
		self.activateWindow()
		if str(filterdialog).startswith('Comma') is True:
			itemlist = csvHandler.csv2list(csv_file_in,delimiter=",",parent=self,sniff=True)
		elif str(filterdialog).startswith('Tabstop') is True:
			itemlist = csvHandler.csv2list(csv_file_in,delimiter="\t",parent=self,sniff=True)
		if side == 'left':
			for item in itemlist: self.sceneLeft.addCircle(
				float(item[0]),
				float(item[1]),
				float(item[2]) if len(item) > 2 else 0)
			self.sceneLeft.itemsToModel()
			# csvHandler.csvAppend2model(csv_file_in,self.modelLleft,delimiter="\t",parent=self,sniff=True)
		elif side == 'right':
			for item in itemlist: self.sceneRight.addCircle(
				float(item[0]),
				float(item[1]),
				float(item[2]) if len(item) > 2 else 0)
			self.sceneRight.itemsToModel()
			# csvHandler.csvAppend2model(csv_file_in,self.modelRight,delimiter="\t",parent=self,sniff=True)

												##################### END #####################
												######     CSV - Point import/export    #######
												###############################################

												###############################################
												######            Correlation           #######
												#################### START ####################

	def model2np(self,model,rows):
		"""
		Convert Qt model to numpy array.
		Pass the model and the range of rows to convert. E.g. if the model has rows nr 1,2,3,4,5,6,7,8 
		model2np(model, [3,7]) would convert rows 4,5,6,7 of the model to a numpy array.
		"""
		listarray = []
		for rowNumber in range(*rows):
			fields = [
					model.data(model.index(rowNumber, columnNumber), QtCore.Qt.DisplayRole).toFloat()[0]
					for columnNumber in range(model.columnCount())]
			listarray.append(fields)
		return np.array(listarray).astype(np.float)

	def correlate(self):
		if '{0:b}'.format(self.sceneLeft.imagetype)[-1] == '1' and '{0:b}'.format(self.sceneRight.imagetype)[-1] == '0':
			model2D = self.modelLleft
			model3D = self.modelRight
			## Temporary img to draw results and save it
			img = np.copy(self.colorizeImage(self.img_adj_left_layer1,color=self.colorCoder(self.layer1Color_left,'left',1)))
			imgSide = 'left'
			## SEM/FIB imaging size is:	512x442, 1024x884, 2048x1768 or 4096x3536. Saved image file is
			#  SEM/FIB image + footer:	512x470, 1024x941, 2048x1883 or 4096x3767
			if img.shape[0] == 470:
				imgShape = [442,img.shape[1]]
			elif img.shape[0] == 941:
				imgShape = [884,img.shape[1]]
			elif img.shape[0] == 1883:
				imgShape = [1768,img.shape[1]]
			elif img.shape[0] == 3767:
				imgShape = [3536,img.shape[1]]
			else:
				imgShape = img.shape
			imageProps = [imgShape,self.sceneLeft.pixelSize,self.imgstack_right_layer1.shape]
			if img.ndim == 2:
				## Need RGB for colored markers
				img = cv2.cvtColor(img,cv2.COLOR_GRAY2BGR)
		elif '{0:b}'.format(self.sceneLeft.imagetype)[-1] == '0' and '{0:b}'.format(self.sceneRight.imagetype)[-1] == '1':
			model2D = self.modelRight
			model3D = self.modelLleft
			## Temporary img to draw results and save it
			img = np.copy(self.colorizeImage(self.img_adj_right_layer1,color=self.colorCoder(self.layer1Color_right,'right',1)))
			imgSide = 'right'
			## SEM/FIB imaging size is:	512x442, 1024x884, 2048x1768 or 4096x3536. Saved image file is
			#  SEM/FIB image + footer:	512x470, 1024x941, 2048x1883 or 4096x3767
			if img.shape[0] == 470:
				imgShape = [442,img.shape[1]]
			elif img.shape[0] == 941:
				imgShape = [884,img.shape[1]]
			elif img.shape[0] == 1883:
				imgShape = [1768,img.shape[1]]
			elif img.shape[0] == 3767:
				imgShape = [3536,img.shape[1]]
			else:
				imgShape = img.shape
			imageProps = [imgShape,self.sceneRight.pixelSize,self.imgstack_left_layer1.shape]
			if img.ndim == 2:
				## Need RGB for colored markers
				img = cv2.cvtColor(img,cv2.COLOR_GRAY2BGR)
		else:
			def corrMsgBox(self,msg):
				print 'message box'
				msgBox = QtGui.QMessageBox()
				msgBox.setIcon(QtGui.QMessageBox.Question)
				msgBox.setText(msg)
				l2rButton = msgBox.addButton("Left to Right", QtGui.QMessageBox.ActionRole)
				r2lButton = msgBox.addButton("Right to Left", QtGui.QMessageBox.ActionRole)
				abortButton = msgBox.addButton(QtGui.QMessageBox.Cancel)
				msgBox.exec_()
				if msgBox.clickedButton() == l2rButton:
					return "l2r"
				elif msgBox.clickedButton() == r2lButton:
					return "r2l"
				elif msgBox.clickedButton() == abortButton:
					return None

			if '{0:b}'.format(self.sceneLeft.imagetype)[-1] == '0' and '{0:b}'.format(self.sceneRight.imagetype)[-1] == '0':
				rowsLeft = self.modelLleft.rowCount()
				rowsRight = self.modelRight.rowCount()
				if rowsLeft > rowsRight:
					corrMsgBoxRetVal = 'l2r'
				elif rowsLeft < rowsRight:
					corrMsgBoxRetVal = 'r2l'
				else:
					corrMsgBoxRetVal = corrMsgBox(
						self,"It seems you want to do a 3D to 3D correlation. " +
						"Since both data sets contain the same amount of markers, please specify which side you want to correlate to:")
				if corrMsgBoxRetVal == 'l2r':
					model2D = self.modelRight
					model3D = self.modelLleft
					## Temporary img to draw results and save it
					img = np.copy(self.colorizeImage(self.img_adj_right_layer1,color=self.colorCoder(self.layer1Color_right,'right',1)))
					imgSide = 'right'
				elif corrMsgBoxRetVal == 'r2l':
					model2D = self.modelLleft
					model3D = self.modelRight
					## Temporary img to draw results and save it
					img = np.copy(self.colorizeImage(self.img_adj_left_layer1,color=self.colorCoder(self.layer1Color_left,'left',1)))
					imgSide = 'left'
				else:
					return
				if img.ndim == 2:
					## Need RGB for colored markers
					img = cv2.cvtColor(img,cv2.COLOR_GRAY2BGR)
				imageProps = None
				# QtGui.QMessageBox.critical(self, "Data Structure",'Both datasets contain only 3D information. I need one 3D and one 2D dataset')
				# raise ValueError('Both datasets contain only 3D information. I need one 3D and one 2D dataset')
			elif '{0:b}'.format(self.sceneLeft.imagetype)[-1] == '1' and '{0:b}'.format(self.sceneRight.imagetype)[-1] == '1':
				rowsLeft = self.modelLleft.rowCount()
				rowsRight = self.modelRight.rowCount()
				if rowsLeft > rowsRight:
					corrMsgBoxRetVal = 'l2r'
				elif rowsLeft < rowsRight:
					corrMsgBoxRetVal = 'r2l'
				else:
					corrMsgBoxRetVal = corrMsgBox(
							self,"It seems you want to do a 2D to 2D correlation. " +
							"Since both data sets contain the same amount of markers, please specify which side you want to correlate to:")
				if corrMsgBoxRetVal == 'l2r':
					model2D = self.modelRight
					model3D = self.modelLleft
					## Temporary img to draw results and save it
					img = np.copy(self.colorizeImage(self.img_adj_right_layer1,color=self.colorCoder(self.layer1Color_right,'right',1)))
					imgSide = 'right'
				elif corrMsgBoxRetVal == 'r2l':
					model2D = self.modelLleft
					model3D = self.modelRight
					## Temporary img to draw results and save it
					img = np.copy(self.colorizeImage(self.img_adj_left_layer1,color=self.colorCoder(self.layer1Color_left,'left',1)))
					imgSide = 'left'
				else:
					return
				if img.ndim == 2:
					## Need RGB for colored markers
					img = cv2.cvtColor(img,cv2.COLOR_GRAY2BGR)
				imageProps = None
				# QtGui.QMessageBox.critical(self, "Data Structure",'Both datasets contain only 2D information. I need one 3D and one 2D dataset')
				# raise ValueError('Both datasets contain only 2D information. I need one 3D and one 2D dataset')
			else:
				QtGui.QMessageBox.critical(self, "Data Structure",'Cannot determine if datasets are 2D or 3D')
				raise ValueError('Cannot determine if datasets are 2D or 3D')
		## variables for dataset validation. The amount of markers from the 2D and 3D model have to be in corresponding order.
		## All extra rows in the 3D model are used as POIs.
		nrRowsModel2D = model2D.rowCount()
		nrRowsModel3D = model3D.rowCount()
		# self.rotation_center = [self.doubleSpinBox_psi.value(),self.doubleSpinBox_phi.value(),self.doubleSpinBox_theta.value()]
		# self.rotation_center = [670, 670, 670]
		self.rotation_center = [
								self.doubleSpinBox_custom_rot_center_x.value(),
								self.doubleSpinBox_custom_rot_center_y.value(),
								self.doubleSpinBox_custom_rot_center_z.value()]

		if nrRowsModel2D >= 3:
			if nrRowsModel2D <= nrRowsModel3D:
				timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
				self.correlation_results = correlation.main(
														markers_3d=self.model2np(model3D,[0,nrRowsModel2D]),
														markers_2d=self.model2np(model2D,[0,nrRowsModel2D]),
														spots_3d=self.model2np(model3D,[nrRowsModel2D,nrRowsModel3D]),
														rotation_center=self.rotation_center,
														results_file=''.join([
															self.workingdir,'/',timestamp, '_correlation.txt'
															] if self.checkBox_writeReport.isChecked() else ''),
														imageProps=imageProps
														)
			else:
				QtGui.QMessageBox.critical(self, "Data Structure", "The two datasets do not contain the same amount of markers!")
				return
		else:
			QtGui.QMessageBox.critical(self, "Data Structure",'At least THREE markers are needed to do the correlation')
			return

		transf_3d = self.correlation_results[1]
		alpha = self.doubleSpinBox_markerAlpha.value()
		radius = self.spinBox_markerRadius.value()
		## convert RGB to BGR for cv2 handling
		img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
		img_orig = np.copy(img)
		img_overlay = np.zeros(img.shape,dtype=img.dtype)
		for i in range(transf_3d.shape[1]):
			cv2.circle(img, (int(round(transf_3d[0,i])), int(round(transf_3d[1,i]))), radius, self.markerColor, -1)
			cv2.circle(img_overlay, (int(round(transf_3d[0,i])), int(round(transf_3d[1,i]))), radius, self.markerColor, -1)
		img = cv2.addWeighted(img, alpha, img_orig, 1-alpha, 0.0)
		img_overlay = cv2.addWeighted(img_overlay, alpha, np.zeros(img.shape,dtype=img.dtype), 1-alpha, 0.0)
		if self.correlation_results[2] is not None:
			calc_spots_2d = self.correlation_results[2]
			# draw POI cv2.circle(img, (center x, center y), radius, [b,g,r], thickness(-1 for filled))
			for i in range(calc_spots_2d.shape[1]):
				cv2.circle(img, (int(round(calc_spots_2d[0,i])), int(round(calc_spots_2d[1,i]))), 1, self.poiColor, -1)
				cv2.circle(img_overlay, (int(round(calc_spots_2d[0,i])), int(round(calc_spots_2d[1,i]))), 1, self.poiColor, -1)
		if self.checkBox_writeReport.isChecked():
			cv2.imwrite(os.path.join(self.workingdir,timestamp+"_correlated.tif"), img)
		## back to RGB again for displaying in QT
		try:
			img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
			img_overlay = cv2.cvtColor(img_overlay,cv2.COLOR_BGR2RGB)
		except:
			pass
		## Display image
		if imgSide == 'left':
			## reset brightness contrast
			# self.brightness_left_layer1 = 0
			# self.contrast_left_layer1 = 10
			# self.horizontalSlider_brightness.setValue(0)
			# self.horizontalSlider_contrast.setValue(10)

			# self.img_left_displayed_layer1 = np.copy(img)
			# self.img_adj_left_layer1 = np.copy(img)
			self.img_left_overlay = np.copy(img_overlay)
			self.displayImage(side='left',keepRGB=False)
		else:
			## reset brightness contrast
			# self.brightness_right_layer1 = 0
			# self.contrast_right_layer1 = 10
			# self.horizontalSlider_brightness.setValue(0)
			# self.horizontalSlider_contrast.setValue(10)

			# self.img_right_displayed_layer1 = np.copy(img)
			# self.img_adj_right_layer1 = np.copy(img)
			self.img_right_overlay = np.copy(img_overlay)
			self.displayImage(side='right',keepRGB=False)

		# self.displayResults(frame=False,framesize=None)
		self.displayResults(frame=self.checkBox_scatterPlotFrame.isChecked(),framesize=self.doubleSpinBox_scatterPlotFrameSize.value())
		model2D.tableview._scene.deleteArrows()
		for i in range(nrRowsModel2D):
			model2D.tableview._scene.addArrow(self.model2np(
				model2D,[0,nrRowsModel2D])[i,:2],self.correlation_results[1][:2,i],arrowangle=45,color=QtCore.Qt.red)

	def displayResults(self,frame=False,framesize=None):
		"""Populates the result tab with the appropriate information from the correlation result

		This also includes a scatter plot of the clicked markers' deviation from their calculated coordinates.

		Optionally a "frame" (boolean) with the pixel size of "framesize" (int or float) can be drawn to validate
		graphically how large the deviation is. E.g. if the correlation deviation should ideally be lower than 300 um
		at a pixel size of 161 nm, a frame with the size of 1.863 could be drawn to validate if the deviation is inside
		this margin.

		The frame is drawn in x and y from -framesize/2 to framesize/2.
		"""
		if hasattr(self, "correlation_results"):
			## get data
			transf = self.correlation_results[0]
			# transf_3d = self.correlation_results[1]			## unused atm
			# calc_spots_2d = self.correlation_results[2]		## unused atm
			delta2D = self.correlation_results[3]
			delta2D_mean = np.absolute(delta2D).mean(axis=1)
			# cm_3D_markers = self.correlation_results[4]		## unused atm
			translation = (transf.d[0], transf.d[1], transf.d[2])
			translation_customRotation = self.correlation_results[5]
			eulers = transf.extract_euler(r=transf.q, mode='x', ret='one')
			eulers = eulers * 180 / np.pi
			scale = transf.s_scalar

			# ## display data
			self.label_phi.setText('{0:.3f}'.format(eulers[0]))
			self.label_phi.setStyleSheet(self.stylesheet_green)
			self.label_psi.setText('{0:.3f}'.format(eulers[2]))
			self.label_psi.setStyleSheet(self.stylesheet_green)
			self.label_theta.setText('{0:.3f}'.format(eulers[1]))
			self.label_theta.setStyleSheet(self.stylesheet_green)
			self.label_scale.setText('{0:.3f}'.format(scale))
			self.label_scale.setStyleSheet(self.stylesheet_green)
			self.label_translation.setText('x = {0:.3f} | y = {1:.3f}'.format(translation[0], translation[1]))
			self.label_translation.setStyleSheet(self.stylesheet_green)
			self.label_custom_rot_center.setText('[{0},{1},{2}]:'.format(
								int(self.doubleSpinBox_custom_rot_center_x.value()),
								int(self.doubleSpinBox_custom_rot_center_y.value()),
								int(self.doubleSpinBox_custom_rot_center_z.value())))
			self.label_translation_custom_rot.setText('x = {0:.3f} | y = {1:.3f}'.format(
				translation_customRotation[0], translation_customRotation[1]))
			self.label_translation_custom_rot.setStyleSheet(self.stylesheet_green)
			self.label_meandxdy.setText('{0:.5f} / {1:.5f}'.format(delta2D_mean[0], delta2D_mean[1]))
			if delta2D_mean[0] <= 1 and delta2D_mean[1] <= 1: self.label_meandxdy.setStyleSheet(self.stylesheet_green)
			elif delta2D_mean[0] < 2 or delta2D_mean[1] < 2: self.label_meandxdy.setStyleSheet(self.stylesheet_orange)
			else: self.label_meandxdy.setStyleSheet(self.stylesheet_red)
			self.label_rms.setText('{0:.5f}'.format(transf.rmsError))
			self.label_rms.setStyleSheet(self.stylesheet_green if transf.rmsError < 1 else self.stylesheet_orange)

			self.widget_matplotlib.setupScatterCanvas(width=4,height=4,dpi=52,toolbar=False)
			self.widget_matplotlib.scatterPlot(x=delta2D[0,:],y=delta2D[1,:],frame=frame,framesize=framesize,xlabel="px",ylabel="px")

			## Populate tableView_results
			self.modelResults.removeRows(0,self.modelResults.rowCount())
			if self.checkBox_resultsAbsolute.isChecked():
				delta2D = np.absolute(delta2D)
			for i in range(delta2D.shape[1]):
				item = [
					QtGui.QStandardItem(str(i+1)),
					QtGui.QStandardItem('{0:.5f}'.format(delta2D[0,i])),
					QtGui.QStandardItem('{0:.5f}'.format(delta2D[1,i]))]
				self.modelResults.appendRow(item)
			self.modelResults.setHeaderData(0, QtCore.Qt.Horizontal,'Nr.')
			self.modelResults.setHeaderData(1, QtCore.Qt.Horizontal,'dx')
			self.modelResults.setHeaderData(1, QtCore.Qt.Horizontal,'dx')
			self.modelResults.setHeaderData(2, QtCore.Qt.Horizontal,'dy')
			self.tableView_results.setColumnWidth(1, 86)
			self.tableView_results.setColumnWidth(2, 86)

		else:
			# QtGui.QMessageBox.critical(self, "Error", "No data to display!")
			pass

	def showSelectedResidual(self,doubleclick=False):
		"""Show position of selected residual (results tab)

		Simply selected will color the corresponding point in the image green.
		A double click will center and zoom on the selected point.
		"""
		indices = self.tableView_results.selectedIndexes()
		if '{0:b}'.format(self.sceneLeft.imagetype)[-1] == '1':
			tableView1 = self.tableView_left
			tableView2 = self.tableView_right
			graphicsView = self.graphicsView_left
		else:
			tableView2 = self.tableView_left
			tableView1 = self.tableView_right
			graphicsView = self.graphicsView_right
		if indices:
			## Filter selected rows
			rows = set(index.row() for index in indices)
			## Select rows (only one row selectable in the results table)
			for row in rows:
				markerNr = int(self.modelResultsProxy.data(self.modelResultsProxy.index(row, 0)).toString())-1
				tableView1.selectRow(markerNr)
				tableView2.selectRow(markerNr)
		else:
			tableView1.clearSelection()
			tableView2.clearSelection()
		if doubleclick is True:
			if debug is True: print clrmsg.DEBUG + 'double click'
			if debug is True: print clrmsg.DEBUG, graphicsView.transform().m11(), graphicsView.transform().m22()
			graphicsView.setTransform(QtGui.QTransform(
				20,  # m11
				graphicsView.transform().m12(),
				graphicsView.transform().m13(),
				graphicsView.transform().m21(),
				20,  # m22
				graphicsView.transform().m23(),
				graphicsView.transform().m31(),
				graphicsView.transform().m32(),
				graphicsView.transform().m33(),
				))
			if debug is True: print clrmsg.DEBUG, graphicsView.transform().m11(), graphicsView.transform().m22()
			## Center on coordinate
			graphicsView.centerOn(
				float(tableView1._model.data(tableView1._model.index(markerNr, 0)).toString()),
				float(tableView1._model.data(tableView1._model.index(markerNr, 1)).toString()))

	def cmTableViewResults(self,pos):
		"""Context menu for residuals table (results tab)"""
		indices = self.tableView_results.selectedIndexes()
		if indices:
			cmApplyShift = QtGui.QAction('Apply shift to marker', self)
			cmApplyShift.triggered.connect(self.applyResidualShift)
			self.contextMenu = QtGui.QMenu(self)
			self.contextMenu.addAction(cmApplyShift)
			self.contextMenu.popup(QtGui.QCursor.pos())

	def applyResidualShift(self):
		"""Applies the selected residual from the correlation to the corresponding clicked 2D values

		The correlation returns the delta between the clicked fiducial 2D and the calculated 2D coordinates derived
		from the applied correlation to the corresponding fiducial 3D coordinate.
		"""
		indices = self.tableView_results.selectedIndexes()
		if '{0:b}'.format(self.sceneLeft.imagetype)[-1] == '1':
			tableView = self.tableView_left
			scene = self.sceneLeft
		else:
			tableView = self.tableView_right
			scene = self.sceneRight
		items = []
		for item in scene.items():
			if isinstance(item, QtGui.QGraphicsEllipseItem):
				items.append(item)
		if indices:
			## Filter selected rows
			rows = set(index.row() for index in indices)
			## Select rows (only one row selectable in the results table)
			for row in rows:
				markerNr = int(self.modelResultsProxy.data(self.modelResultsProxy.index(row, 0)).toString())-1
				if debug is True: print clrmsg.DEBUG + 'Marker number/background color (Qrgba)', markerNr, \
					self.modelResults.itemFromIndex(
						self.modelResultsProxy.mapToSource((self.modelResultsProxy.index(row, 0)))).background().color().rgba()
				if self.modelResults.itemFromIndex(self.modelResultsProxy.mapToSource((
					self.modelResultsProxy.index(row, 0)))).background().color().rgba() == 4278190080:
					BackColor = (50,220,175,100)
					ForeColor = (180,180,180,255)
					items[markerNr].setPos(
						float(tableView._model.data(
							tableView._model.index(markerNr, 0)).toString())+self.correlation_results[3][0,markerNr],
						float(tableView._model.data(
							tableView._model.index(markerNr, 1)).toString())+self.correlation_results[3][1,markerNr])
					self.modelResults.itemFromIndex(self.modelResultsProxy.mapToSource((
						self.modelResultsProxy.index(row, 0)))).setBackground(QtGui.QColor(*BackColor))
					self.modelResults.itemFromIndex(self.modelResultsProxy.mapToSource((
						self.modelResultsProxy.index(row, 1)))).setBackground(QtGui.QColor(*BackColor))
					self.modelResults.itemFromIndex(self.modelResultsProxy.mapToSource((
						self.modelResultsProxy.index(row, 2)))).setBackground(QtGui.QColor(*BackColor))
					self.modelResults.itemFromIndex(self.modelResultsProxy.mapToSource((
						self.modelResultsProxy.index(row, 0)))).setForeground(QtGui.QColor(*ForeColor))
					self.modelResults.itemFromIndex(self.modelResultsProxy.mapToSource((
						self.modelResultsProxy.index(row, 1)))).setForeground(QtGui.QColor(*ForeColor))
					self.modelResults.itemFromIndex(self.modelResultsProxy.mapToSource((
						self.modelResultsProxy.index(row, 2)))).setForeground(QtGui.QColor(*ForeColor))
		scene.itemsToModel()
		self.tableView_results.clearSelection()

												##################### END #####################
												######            Correlation           #######
												###############################################


class SplashScreen():
	def __init__(self):
		"""Splash screen

		The splash screen, besides being fancy, shows the path to image being loaded at the moment.
		"""
		QtGui.QApplication.processEvents()
		## Load splash screen image
		splash_pix = QtGui.QPixmap(os.path.join(execdir,'icons','SplashScreen.png'))
		## Add version
		painter = QtGui.QPainter()
		painter.begin(splash_pix)
		painter.setPen(QtCore.Qt.white)
		painter.drawText(
			0,0,
			splash_pix.size().width()-3,splash_pix.size().height()-1,QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight, __version__)
		painter.end()
		## Show splash screen
		self.splash = QtGui.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
		self.splash.setMask(splash_pix.mask())
		self.splash.show()
		self.splash.showMessage("Initializing...",color=QtCore.Qt.white)
		## Needed to receive mouse clicks to hide splash screen
		QtGui.QApplication.processEvents()

		# Simulate something that takes time
		time.sleep(1)
		self.splash.showMessage("Loading images...",color=QtCore.Qt.white)


class Main():
	def __init__(self,leftImage=None,rightImage=None,nosplash=False,workingdir=None):
		"""Class for running this application either as standalone or as imported QT Widget

		args:
				self:		self is another QT (main) widget passed as parent when this file's main widget is called
							from it.

		kwargs:
				leftImage:	string, required
							Path to first image.
							The image has to be a tiff file. It can be a gray-scale 2D image (y,x)
							or 3D image stack (z,y,x). Color channels are supported as well like (y,x,c) or (z,c,y,x)
							respectively. Color channels are detected by checking the third (images with 3 dimensions)
							or the second (images with 4 dimensions) dimension for values equal or less then 3. That
							means, if the image contains more than 3 channels, the color channel detection can result
							in funny and wrong image reads.

				rightImage:	string, required
							Path to first image.
							See "leftImage".

				nosplash:	bool, optional
							If True, a splash screen showing which image is being loaded at the moment is rendered at
							startup.

				workingdir:	string, optional
							If None, the execution directory is used as the working directory.


		For standalone mode, just run python -u TDCT_correlation.py
		For loading this widget from another main QT application:

		import TDCT_correlation
		# inside of the qt (main) widget:
			...
			self.correlationModul = TDCT_correlation.Main(
														leftImage="path/to/first/image.tif",
														rightImage="path/to/second/image.tif",
														nosplash=False,
														workingdir="path/to/workingdir")
		"""
		self.exitstatus = 1
		if leftImage is None or rightImage is None:
			sys.exit("Please pass 'leftImage=PATH' and 'rightImage=PATH' to this function")

		if nosplash is False:
			global splashscreen
			splashscreen = SplashScreen()

		if workingdir is None:
			workingdir = execdir

		self.window = MainWidget(parent=self,leftImage=leftImage, rightImage=rightImage,workingdir=workingdir)
		self.window.show()
		self.window.raise_()

		if nosplash is False:
			splashscreen.splash.finish(self.window)

	def cleanUp(self):
		"""Clean up instance mostly for external call case, to check if the window still exists."""
		try:
			del self.window
		except Exception as e:
			if debug is True: print clrmsg.DEBUG + str(e)


if __name__ == "__main__":
	if debug is True:
		print clrmsg.DEBUG + 'Debug Test'
		print clrmsg.OK + 'OK Test'
		print clrmsg.ERROR + 'Error Test'
		print clrmsg.INFO + 'Info Test'
		print clrmsg.INFO + 'Info Test'
		print clrmsg.WARNING + 'Warning Test'
		print '='*20, 'Initializing', '='*20

	app = QtGui.QApplication(sys.argv)

	## File dialogs for standalone mode
	## *.png *.jpg *.bmp not yet supported
	left = str(QtGui.QFileDialog.getOpenFileName(
		None,"Select first image file for correlation", execdir,"Image Files (*.tif *.tiff);; All (*.*)"))
	if left == '': sys.exit()
	right = str(QtGui.QFileDialog.getOpenFileName(
		None,"Select second image file for correlation", execdir,"Image Files (*.tif *.tiff);; All (*.*)"))
	if right == '': sys.exit()
	# left = '/Users/jan/Desktop/correlation_test_dataset/IB_030.tif'
	# right = '/Users/jan/Desktop/correlation_test_dataset/LM_green_image_stack_reslized.tif'
	# right = '/Users/jan/Desktop/correlation_test_dataset/single_tif_files/single_tif_files_0.tif'

	main = Main(leftImage=left,rightImage=right)

	sys.exit(app.exec_())
