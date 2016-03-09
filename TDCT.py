#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Title			: TDCT
# @Project			: 3DCTv2
# @Description		: 3D Correlation Toolbox - 3DCT
# @Author			: Jan Arnold
# @Email			: jan.arnold (at) coraxx.net
# @Credits			: Vladan Lucic for the 3D to 2D correlation code
# 					: and the stackoverflow community for all the bits and pieces
# @Maintainer		: Jan Arnold
# 					  Max-Planck-Instute of Biochemistry
# 					  Department of Molecular Structural Biology
# @Date				: 2015/08
# @Version			: 2.0
# @Status			: developement
# @Usage			: python -u TDCT.py
# @Notes			:
# @Python_version	: 2.7.10
# @Last Modified	: 2016/03/09
# ============================================================================

import sys
import os
import time
import shutil
import fileinput
# from functools import partial
from subprocess import call
from PyQt4 import QtCore, QtGui, uic
import numpy as np
import tifffile as tf
# add working directory temporarily to PYTHONPATH
execdir = os.path.dirname(os.path.realpath(__file__))
workingdir = execdir
sys.path.append(execdir)
# import modules from working directory
try:
	import csv_handler
	# import stack_processing
	import image_navigation_quad
	import bead_pos
	## Colored stdout
	import clrmsg
except Exception as e:
	print e
	sys.exit()

### debug stuff ###
# import pdb
# import inspect
# import pyqtDebug
###################


########## GUI layout file #######################################################
##################################################################################
qtCreatorFile_main = os.path.join(execdir, "TDCT_main.ui")
qtCreatorFile_pointselection = os.path.join(execdir, "TDCT_pointselect_wo_ctrl.ui")
qtCreatorFile_sort = os.path.join(execdir, "TDCT_sort.ui")
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile_main)
Ui_pointSelectionWindow, QtBaseClassMM = uic.loadUiType(qtCreatorFile_pointselection)
Ui_sortWindow, QtBaseClassSort = uic.loadUiType(qtCreatorFile_sort)

########## Main Application Class ################################################
##################################################################################


class APP(QtGui.QMainWindow, Ui_MainWindow):
	def __init__(self):
		QtGui.QMainWindow.__init__(self)
		Ui_MainWindow.__init__(self)
		self.setupUi(self)
		self.stackProcessStatus.setVisible(False)
		self.menuDebug.menuAction().setVisible(False)
		# Menu, set shortcuts
		self.actionQuit.triggered.connect(self.close)
		self.actionQuit.setShortcuts(['Ctrl+Q','Esc'])
		self.actionQuit.setStatusTip('Exit application')

		QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_0), self, self.showDebugMenu)
		self.actionLoad_Test_Dataset.triggered.connect(self.loadTestDataset)
		self.actionLoad_Test_Dataset_sort.triggered.connect(self.loadTestDatasetSort)

		self.actionAbout.triggered.connect(self.about)

		# Setting up Child exit status - see closeEvent()
		self.childExitStatus_ps = True
		self.childExitStatus_sort = True

		# Buttons
		self.pushButton_selectWorkingDir.clicked.connect(lambda: self.selectpath(self.lineEdit_workingDir))
		self.pushButton_openWorkingDir.clicked.connect(lambda: self.openDirectoy(self.lineEdit_workingDir.displayText()))
		self.pushButton_saveTo.clicked.connect(lambda: self.selectpath(self.lineEdit_saveToPath))
		self.pushButton_selectTif.clicked.connect(lambda: self.selectpath(self.lineEdit_selectTifPath))
		self.pushButton_openSaveToPath.clicked.connect(lambda: self.openDirectoy(self.lineEdit_saveToPath.displayText()))
		self.pushButton_runStack.clicked.connect(self.runFiji)
		self.testButton.clicked.connect(self.tester)
		self.pushButton_LMselect.clicked.connect(lambda: self.selectpath(self.selectLMcoordEx_line))
		self.pushButton_EMselect.clicked.connect(lambda: self.selectpath(self.selectEMcoordEx_line))
		self.toolButton_reloadFileLists.clicked.connect(self.reloadFileLists)
		self.pushButton_sortData.clicked.connect(self.initSortData)
		self.commandLinkButton_extract3D.clicked.connect(self.extract3D)
		self.commandLinkButton_extract2D.clicked.connect(self.extract2D)

		# Checkbox
		self.checkBox_cubeVoxels.stateChanged.connect(lambda: self.cubeVoxels(self.checkBox_cubeVoxels.isChecked()))

		# Init Working directory
		self.lineEdit_workingDir.setText(workingdir)

	def focusInEvent(self, event):
		print('Got focus')

		# List Widget Test
		# self.listWidget_coordEx_LMfiles.itemSelectionChanged.connect(self.dostuff)

	# def dostuff(self):
	# 	print self.listWidget_coordEx_LMfiles.itempath+"/"+self.listWidget_coordEx_LMfiles.selectedItems()[0].text()
	# 	print os.path.join(self.listWidget_coordEx_LMfiles.itempath, str(self.listWidget_coordEx_LMfiles.selectedItems()[0].text()))

	## only for quick load of test datasets - REMOVE FROM FINAL VERSION
	def showDebugMenu(self):
		self.menuDebug.menuAction().setVisible(True)
		self.loadTestDatasetSort()

	## only for quick load of test datasets - REMOVE FROM FINAL VERSION
	def loadTestDataset(self):
		self.lineEdit_selectTifPath.setText("/Volumes/Silver/input")
		self.lineEdit_saveToPath.setText("/Volumes/Silver/output")
		self.pushButton_openSaveToPath.setEnabled(True)
		self.pushButton_runStack.setEnabled(True)

	## only for quick load of test datasets - REMOVE FROM FINAL VERSION
	def loadTestDatasetSort(self):
		self.initSortData()

		self.sortData.model_left = csv_handler.csv2model(execdir+"/testdata/set2/LM_for_FIB_woh.txt",delimiter="\t",parent=self,sniff=True)
		self.sortData.toolButton_copy_left.setEnabled(True)
		self.sortData.toolButton_showimg_left.setEnabled(True)
		self.sortData.toolButton_edit_left.setEnabled(True)

		self.sortData.model_right = csv_handler.csv2model(execdir+"/testdata/set2/FIB_woh.txt",delimiter="\t",parent=self,sniff=True)
		self.sortData.toolButton_copy_right.setEnabled(True)
		self.sortData.toolButton_showimg_right.setEnabled(True)
		self.sortData.toolButton_edit_right.setEnabled(True)

		self.sortData.tableView_left.setModel(self.sortData.model_left)
		self.sortData.tableView_right.setModel(self.sortData.model_right)

		self.sortData.imgpath_left = execdir+"/testdata/set2/MAX_SD_area5-0.jpg"
		self.sortData.imgpath_right = execdir+"/testdata/set2/IB_030.tif"
		self.img_left_loaded = True
		self.img_right_loaded = True
		self.sortData.initializeImageWidget()
		self.sortData.checkBox_saveimage.setChecked(True)
		self.sortData.checkBox_saveimage.show()

		self.sortData.tableView_left.selectionModel().selectionChanged.connect(lambda: self.sortData.drawPoint(tableview=self.sortData.tableView_left))
		self.sortData.tableView_left_sort.selectionModel().selectionChanged.connect(lambda: self.sortData.drawPoint(tableview=self.sortData.tableView_left_sort))
		self.sortData.tableView_right.selectionModel().selectionChanged.connect(lambda: self.sortData.drawPoint(tableview=self.sortData.tableView_right))
		self.sortData.tableView_right_sort.selectionModel().selectionChanged.connect(lambda: self.sortData.drawPoint(tableview=self.sortData.tableView_right_sort))

	## only for quick load of test datasets - REMOVE FROM FINAL VERSION
	def tester(self):
		# self.showDebugMenu()
		# self.addItem_coordEx_list('yes')
		# print QtCore.QDir.currentPath()
		# self.populate_coordEx_list( QtCore.QDir.currentPath() )
		# self.listWidget_coordEx_files.findItems(self, QString text, Qt.MatchFlags item.setCheckState)
		# print 'LM Files:'
		# for index in xrange(self.listWidget_coordEx_LMfiles.count()):
		# 	#check_box = self.listWidget_coordEx_files.itemWidget(self.listWidget_coordEx_files.item(index))
		# 	foo = self.listWidget_coordEx_LMfiles.item(index)
		# 	#state = foo.checkStateSet()
		# 	if foo.checkState() == 2:
		# 		print foo.text()
		# print ' '
		# print 'EM Files:'
		# for index in xrange(self.listWidget_coordEx_EMfiles.count()):
		# 	#check_box = self.listWidget_coordEx_files.itemWidget(self.listWidget_coordEx_files.item(index))
		# 	foo = self.listWidget_coordEx_EMfiles.item(index)
		# 	#state = foo.checkStateSet()
		# 	if foo.checkState() == 2:
		# 		print foo.text()
		# img = "/Users/jan/Desktop/pyPhoOvTest/IB_030.tif"
		# img = "F:/jan_temp/test.tif"
		img = execdir+"/testdata/px_test.tif"
		if os.path.isfile(img)is True:
			self.getPoints(img)

	## About
	def about(self):
		QtGui.QMessageBox.about(
								self, "About 3DCT", "3DCT v0.1\n\ndeveloped by:\n\nMax-Planck-Institute of Biochemistry\n\n" +
								"3D Correlation Toolbox:	Jan Arnold\nCorrelation Algorithm:	Vladan Lucic"
								)

	## Open directory
	def openDirectoy(self,targetDirectory):
		targetDirectory = str(targetDirectory)
		if sys.platform == 'darwin':
			call(['open', '-R', targetDirectory])
		elif sys.platform == 'linux2':
			call(['gnome-open', '--', targetDirectory])
		elif sys.platform == 'win32':
			call(['explorer', targetDirectory])

	## Exit Warning
	def closeEvent(self, event):
		quit_msg = "Are you sure you want to exit the program?"
		reply = QtGui.QMessageBox.question(self, 'Message', quit_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes:
			# if loaded, close pointselection tool widget and sub windows
			if hasattr(self, "pointselect"):
				self.pointselect.close()
			# if loaded, close data sort widget and sub windows
			if hasattr(self, "sortData"):
				self.sortData.close()
			try:
				if self.childExitStatus_ps is True and self.childExitStatus_sort is True:
					event.accept()
				elif self.childExitStatus_ps is False or self.childExitStatus_sort is False:
					event.ignore()
			except:
				event.accept()
		else:
			event.ignore()

	## Select Paths
	def selectpath(self, pathLine):
		global workingdir
		sender = self.sender()
		path = str(QtGui.QFileDialog.getExistingDirectory(self, "Select Directory", workingdir))
		if path:
			pathLine.setText(path)
			# Open Save to directory button
			if sender == self.pushButton_saveTo:
				self.pushButton_openSaveToPath.setEnabled(True)
			# Working directory
			if sender == self.pushButton_selectWorkingDir:
				# global workingdir ## moved to top of def
				workingdir = path
				if (self.lineEdit_saveToPath.displayText() == ""):
					self.lineEdit_saveToPath.setText(path)
					self.pushButton_openSaveToPath.setEnabled(True)
					self.populate_coordEx_list(path,self.listWidget_coordEx_LMfiles)
					self.selectLMcoordEx_line.setText(path)
			# Save new Stack to directoy
			if (self.lineEdit_saveToPath.displayText() != "") and (self.lineEdit_selectTifPath.displayText() != ""):
				self.pushButton_runStack.setEnabled(True)
			# Populate file lists
			if sender == self.pushButton_LMselect:
				self.populate_coordEx_list(path,self.listWidget_coordEx_LMfiles)
				self.LMselect_path = path
			if sender == self.pushButton_EMselect:
				self.populate_coordEx_list(path,self.listWidget_coordEx_EMfiles)
				self.EMselect_path = path

	## Cube Voxels button state handling
	def cubeVoxels(self, checkstate):
		if checkstate is True:
			self.doubleSpinBox_focusStepsize.setEnabled(True)
			self.radioButton_20x.setEnabled(True)
			self.radioButton_40x.setEnabled(True)
			self.radioButton_63x.setEnabled(True)
			self.radioButton_customFocusStepsize.setEnabled(True)
			self.doubleSpinBox_customFocusStepsize.setEnabled(True)

		else:
			self.doubleSpinBox_focusStepsize.setEnabled(False)
			self.radioButton_20x.setEnabled(False)
			self.radioButton_40x.setEnabled(False)
			self.radioButton_63x.setEnabled(False)
			self.radioButton_customFocusStepsize.setEnabled(False)
			self.doubleSpinBox_customFocusStepsize.setEnabled(False)

	## Run image stack processing
	def runFiji(self):
		# button visibility
		def StackProcessStatusVisability(state):
			if state is True and self.stackProcessStatus.isVisible() is False:
				self.stackProcessStatus.setVisible(True)
				app.processEvents()
			else:
				return
			if state is False and self.stackProcessStatus.isVisible() is True:
				self.stackProcessStatus.setVisible(False)
				app.processEvents()
			else:
				return
		StackProcessStatusVisability(False)
		# setting up paths
		pathMACRO = execdir + '/fiji_macro.ijm'
		if sys.platform == 'win32':
			str_lineEdit_selectTifPath = str(self.lineEdit_selectTifPath.displayText())
			str_lineEdit_saveToPath = str(self.lineEdit_saveToPath.displayText())
			print clrmsg.DEBUG, str_lineEdit_selectTifPath, str_lineEdit_saveToPath
			print clrmsg.DEBUG, str_lineEdit_selectTifPath.encode('string-escape'), str_lineEdit_saveToPath.encode('string-escape')
			print clrmsg.DEBUG, str_lineEdit_selectTifPath.encode('string-escape').replace('\\\\','\\'), \
				str_lineEdit_saveToPath.encode('string-escape').replace('\\\\','\\')
			pathFROM = "PATH = " + '"' + str_lineEdit_selectTifPath.encode('string-escape') + '/";'
			pathTO = "PATHSAVETO = " + '"' + str_lineEdit_saveToPath.encode('string-escape') + '/";'
		else:
			pathFROM = "PATH = " + '"' + self.lineEdit_selectTifPath.displayText() + '/";'
			pathTO = "PATHSAVETO = " + '"' + self.lineEdit_saveToPath.displayText() + '/";'
		template_path = os.path.join(execdir,"fiji_macro_template.ijm")
		macro_path = os.path.join(execdir,"fiji_macro.ijm")
		# check for cube voxels option
		if self.checkBox_cubeVoxels.isChecked() is True and self.doubleSpinBox_focusStepsize.value() == 0:
			StackProcessStatusVisability(True)
			self.stackProcessStatus.setStyleSheet("color: rgb(255, 80, 0);")
			self.stackProcessStatus.setText('Set stepsize!')
			app.processEvents()
			return 0
		## create macro template for FIJI run
		# Copy template
		with open(template_path) as f:
			with open(macro_path, "w") as f1:
				for line in f:
					f1.write(line)
		# Add path to template
		for line in fileinput.input(macro_path, inplace=1):
			print line,
			if line.startswith('//PARAMETERS'):
				print pathFROM
				print pathTO
				if self.checkBox_cubeVoxels.isChecked() is True:
					print """cubeVoxels = "True";"""
					print "STEPSIZE = " + str(self.doubleSpinBox_focusStepsize.value()) + ";"
					if self.radioButton_20x.isChecked() is True:
						print """PIXELSIZE = 322.5;"""
					elif self.radioButton_40x.isChecked() is True:
						print """PIXELSIZE = 161.25;"""
					elif self.radioButton_63x.isChecked() is True:
						print """PIXELSIZE = 102.38;"""
		StackProcessStatusVisability(True)
		self.stackProcessStatus.setStyleSheet("color: rgb(255, 125, 0);")
		self.stackProcessStatus.setText('Fiji is running ...')
		app.processEvents()
		# run FIJI with macro
		if sys.platform == 'darwin':
			self.runFiji_return_code = call([execdir + "/Fiji/Contents/MacOS/ImageJ-macosx", "--headless", "-macro", pathMACRO, "&"])
		elif sys.platform == 'linux2':
			self.runFiji_return_code = call([execdir + "/Fiji/ImageJ-linux64", "-macro", pathMACRO, "&"])
		elif sys.platform == 'win32':
			self.runFiji_return_code = call([execdir + "/Fiji/ImageJ-win64.exe", "-macro", pathMACRO])
		if self.runFiji_return_code == 0:
			self.stackProcessStatus.setStyleSheet("color: rgb(0, 225, 90);")
			self.stackProcessStatus.setText('Yeay, done!')
		else:
			self.stackProcessStatus.setStyleSheet("color: rgb(255, 0, 0);")
			self.stackProcessStatus.setText('Fiji failed!')
			restart_msg = "Fiji closed with an error. Do you want to restart it?"
			reply = QtGui.QMessageBox.question(self, 'Message', restart_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
			if reply == QtGui.QMessageBox.Yes:
				self.runFiji()
		# clean up
		try:
			os.remove(macro_path)
		except OSError:
			pass

	## Populate List widget for listing files needed for coordinate extraction
	def populate_coordEx_list(self,path,listWidget):
		listWidget.clear()
		listWidget.itempath = path
		for fname in os.listdir(path):
			checkdir = os.path.join(path, fname)
			if (
				os.path.isdir(checkdir) is False and
				fname.startswith(".") is False and
				fname.startswith("$") is False
				):
				item = QtGui.QListWidgetItem()
				item.setText(fname)
				# item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
				# item.setCheckState(QtCore.Qt.Unchecked)
				listWidget.addItem(item)

	## Refresh file list
	def reloadFileLists(self):
		if hasattr(self, "LMselect_path"):
			self.populate_coordEx_list(self.LMselect_path,self.listWidget_coordEx_LMfiles)
		if hasattr(self, "EMselect_path"):
			self.populate_coordEx_list(self.EMselect_path,self.listWidget_coordEx_EMfiles)

	## Add single Item to List widget
	def addItem_coordEx_list(self,fname):
		if self.listWidget_coordEx_files.count() == 5:
			self.listWidget_coordEx_files.clear()
		item = QtGui.QListWidgetItem()
		item.setText(fname)
		# item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
		# item.setCheckState(QtCore.Qt.Unchecked)
		self.listWidget_coordEx_files.addItem(item)

	def extract2D(self):
		if hasattr(self.listWidget_coordEx_EMfiles, "itempath"):
			try:
				self.getPoints(os.path.join(self.listWidget_coordEx_EMfiles.itempath, str(self.listWidget_coordEx_EMfiles.selectedItems()[0].text())))
			except:
				print "Please select a 2D image file"

	def extract3D(self):
		if hasattr(self.listWidget_coordEx_LMfiles, "itempath"):
			try:
				self.getPoints(os.path.join(self.listWidget_coordEx_LMfiles.itempath, str(self.listWidget_coordEx_LMfiles.selectedItems()[0].text())),z=True)
			except:
				print "Please select a 3D image stack"

	## Start Point Selection
	def getPoints(self,img,z=False):
		if (
			img.endswith(".tif") is True or
			img.endswith(".tiff") is True or
			img.endswith(".jpg") is True or
			img.endswith(".bmp") is True or
			img.endswith(".png") is True
			):
			self.childExitStatus_ps = False
			if z is False:
				self.pointselect = pointSelection(img,parent=self,z=False)
			elif z is True:
				self.pointselect = pointSelection(img,parent=self,z=True)
			self.pointselect.initialize()
		else:
			QtGui.QMessageBox.critical(self, "File Type","Please select a tif, jpg, bmp or png image file")

	## Initialize sort data widget
	def initSortData(self):
		self.childExitStatus_sort is False
		self.sortData = sortData()
		self.sortData.initialize()

########## Point Selection Class #################################################
##################################################################################


class pointSelection(QtGui.QWidget,Ui_pointSelectionWindow):
	def __init__(self,img,parent=None,z=False):
		QtGui.QWidget.__init__(self)
		Ui_pointSelectionWindow.__init__(self)
		self.setupUi(self)

		self.forcequit = False
		self.parent = parent
		self.z = z

		# Save image path and create model to store coordinates
		self.img = img
		self.model_pointselect = QtGui.QStandardItemModel(self)
		self.tableView_pointselect.setModel(self.model_pointselect)
		self.tableView_pointselect.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

		## Move Window
		point = self.rect().bottomRight()
		global_point = self.mapToGlobal(point)
		self.move(global_point - QtCore.QPoint(self.width(), 0))

		## Buttons
		self.toolButton_export.clicked.connect(self.exportPoints)
		self.toolButton_import.clicked.connect(self.importPoints)
		self.toolButton_getz.clicked.connect(self.get_z)
		self.toolButton_getz_opt.clicked.connect(lambda: self.get_z(optimize=True))
		self.toolButton_addEntry.clicked.connect(self.addPointMan)
		self.toolButton_delEntry.clicked.connect(self.delPoint)
		self.buttonBox.accepted.connect(self.autosave)
		self.buttonBox.rejected.connect(self.close)
		self.toolButton_saveMIP.clicked.connect(self.saveMIP)

		## Tableview interactions
		# self.tableView_pointselect.selectionModel().selectionChanged.connect(self.drawPoint)
		self.tableView_pointselect.clicked.connect(self.drawPoint)

	def initialize(self):
		self.show()
		if self.z is False:
			self.minimap = image_navigation_quad.MINIMAP(self.img,parent=self)
		elif self.z is True:
			## Create temp folder
			if not os.path.exists(os.path.join(execdir,'.3dct_tmp')):
				os.makedirs(os.path.join(execdir,'.3dct_tmp'))

			## Enable buttons only shown with 3D image stacks loaded
			self.toolButton_getz.setEnabled(True)
			self.toolButton_getz_opt.setEnabled(True)
			self.toolButton_saveMIP.setEnabled(True)

			img = tf.imread(self.img)
			self.img_MIP = np.zeros((img.shape[1],img.shape[2]), dtype=img.dtype)
			for i in range(0,img.shape[1]):
				for ii in range(0,img.shape[2]):
					self.img_MIP[i,ii] = img[:,i,ii].max()
			self.img_MIP_path = os.path.join(execdir,'.3dct_tmp','MIP.tif')
			tf.imsave(os.path.join(execdir,'.3dct_tmp','MIP.tif'), self.img_MIP)
			self.minimap = image_navigation_quad.MINIMAP(self.img_MIP_path,normalize=False,parent=self)
		self.minimap.main()

	def drawPoint(self, index):
		indices = self.tableView_pointselect.selectedIndexes()
		data = []

		# QtCore.pyqtRemoveInputHook()
		# pdb.set_trace()

		if len(indices) == 2:
			# print 'row: %s  column: %s  data: %s'%(index.row(), index.column(), index.data().toString() )
			for column in range(2):
				indexm = self.model_pointselect.index(index.row(), column)
				data.append(str(self.model_pointselect.data(indexm).toString()))
			self.minimap.mainImageDrawPoint(float(data[0]),float(data[1]))

		elif len(indices) > 2:
			rows = []
			for i in range(len(indices)):
				if indices[i].column() == 0:
					rows.append(indices[i].row())
			for i in rows:
				x = self.model_pointselect.index(i, 0)
				y = self.model_pointselect.index(i, 1)
				self.minimap.mainImageDrawPoint(
					float(self.model_pointselect.data(x).toString()),
					float(self.model_pointselect.data(y).toString()),
					add=True)

	def saveMIP(self):
		if self.z is True:
			img_exp = self.minimap.norm_img(self.img_MIP,copy=True)
			tf.imsave(os.path.join(workingdir, os.path.splitext(self.img)[0]+'_MIP.tif'), img_exp)
		else:
			pass

	def autosave(self):
		## Export Dioalog. Needs check for extension or add default extension
		csv_file_out = os.path.splitext(self.img)[0]+'_coordinates.txt'
		if self.z is True:
			img_exp = self.minimap.norm_img(self.img_MIP,copy=True)
			tf.imsave(os.path.join(workingdir, os.path.splitext(self.img)[0]+'_MIP.tif'), img_exp)
		csv_handler.model2csv(self.model_pointselect,csv_file_out,delimiter="\t")
		self.forcequit = True
		self.close()

	def exportPoints(self):
		## Export Dioalog. Needs check for extension or add default extension
		csv_file_out, filterdialog = QtGui.QFileDialog.getSaveFileNameAndFilter(
			self, 'Export file as', os.path.dirname(self.img), "Tabstop sepperated (*.csv *.txt);;Comma sepperated (*.csv *.txt)")
		if str(filterdialog).startswith('Comma') is True:
			csv_handler.model2csv(self.model_pointselect,csv_file_out,delimiter=",")
		elif str(filterdialog).startswith('Tabstop') is True:
			csv_handler.model2csv(self.model_pointselect,csv_file_out,delimiter="\t")

	def importPoints(self):
		csv_file_in, filterdialog = QtGui.QFileDialog.getOpenFileNameAndFilter(
			self, 'Import file as', os.path.dirname(self.img), "Tabstop sepperated (*.csv *.txt);;Comma sepperated (*.csv *.txt)")
		if str(filterdialog).startswith('Comma') is True:
			self.model_pointselect = csv_handler.csv2model(csv_file_in,delimiter=",",parent=self,sniff=True)
		elif str(filterdialog).startswith('Tabstop') is True:
			self.model_pointselect = csv_handler.csv2model(csv_file_in,delimiter="\t",parent=self,sniff=True)
		self.tableView_pointselect.setModel(self.model_pointselect)

	def addPoint(self,x,y):
		items = [QtGui.QStandardItem(str(x)), QtGui.QStandardItem(str(y))]
		self.model_pointselect.appendRow(items)
		self.model_pointselect.setHeaderData(0, QtCore.Qt.Horizontal,'x')
		self.model_pointselect.setHeaderData(1, QtCore.Qt.Horizontal,'y')

	def addPointMan(self):
		try:
			point = (self.minimap.px,self.minimap.py)
		except Exception as e:
			print e
			return

		# calculate scale to original image
		sfactor_CropToOrig = float((self.minimap.cc[1]-self.minimap.cc[0]))/(self.minimap.main_window_width)
		self.minimap.px_backscale = self.minimap.cc[0]+sfactor_CropToOrig*point[0]
		self.minimap.py_backscale = self.minimap.cc[2]+sfactor_CropToOrig*point[1]

		self.addPoint(self.minimap.px_backscale,self.minimap.py_backscale)

	def delPoint(self):
		rows = sorted(set(index.row() for index in self.tableView_pointselect.selectedIndexes()))
		i = 0
		for row in rows:
			QtGui.QStandardItemModel.removeRows(self.model_pointselect,row-i,1)
			# print('Row %d is deleted' % row)
			i += 1

	def get_z(self,optimize=False):
		try:
			point = (self.minimap.px,self.minimap.py)
		except Exception as e:
			print e
			return

		# calculate scale to original image
		sfactor_CropToOrig = float((self.minimap.cc[1]-self.minimap.cc[0]))/(self.minimap.main_window_width)
		self.minimap.px_backscale = self.minimap.cc[0]+sfactor_CropToOrig*point[0]
		self.minimap.py_backscale = self.minimap.cc[2]+sfactor_CropToOrig*point[1]

		if optimize is False:
			z = bead_pos.getz(self.minimap.px_backscale,self.minimap.py_backscale,self.img,n=None)
			items = [
					QtGui.QStandardItem(str(self.minimap.px_backscale)),
					QtGui.QStandardItem(str(self.minimap.py_backscale)),
					QtGui.QStandardItem(str(z))]
		elif optimize is True:
			x,y,z = bead_pos.getz(self.minimap.px_backscale,self.minimap.py_backscale,self.img,n=None,optimize=True)
			items = [
					QtGui.QStandardItem(str(x)),
					QtGui.QStandardItem(str(y)),
					QtGui.QStandardItem(str(z))]
		self.model_pointselect.appendRow(items)
		self.model_pointselect.setHeaderData(0, QtCore.Qt.Horizontal,'x')
		self.model_pointselect.setHeaderData(1, QtCore.Qt.Horizontal,'y')
		self.model_pointselect.setHeaderData(2, QtCore.Qt.Horizontal,'z')

	## Exit Warning
	def closeEvent(self,event):
		if hasattr(window, "pointselect"):
			if self.forcequit is False:
				quit_msg = "Are you sure you want to close the Point Selection Tool?"
				reply = QtGui.QMessageBox.question(
					self, 'Message', quit_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
				if reply == QtGui.QMessageBox.Yes:
					self.minimap.closeWindows()
					del window.pointselect
					## Delete up temp folder
					try:
						shutil.rmtree(os.path.join(execdir,'.3dct_tmp'))
					except Exception as e:
						QtGui.QMessageBox.critical(self, "Warning", "Could not delete temp folder! %s" % e)
					window.childExitStatus_ps = True
					event.accept()
				else:
					window.childExitStatus_ps = False
					event.ignore()
			elif self.forcequit is True:
				self.minimap.closeWindows()
				del window.pointselect
				window.childExitStatus_ps = True
				event.accept()

########## Sort Data Class #######################################################
##################################################################################


class sortData(QtGui.QWidget,Ui_sortWindow):
	def __init__(self):
		QtGui.QWidget.__init__(self)
		Ui_pointSelectionWindow.__init__(self)
		self.setupUi(self)

		point = self.rect().bottomRight()
		print self.mapToGlobal(point)
		point = self.rect().topLeft()
		print self.mapToGlobal(point)

		## Move Window
		self.move(0,0)

		# hide results dock widget
		self.dockWidget_results.hide()
		# hide save image checkbox
		self.checkBox_saveimage.setChecked(False)
		self.checkBox_saveimage.hide()

		## Create temp folder
		if not os.path.exists(os.path.join(execdir,'.3dct_tmp')):
			os.makedirs(os.path.join(execdir,'.3dct_tmp'))

		## TableView settings
		# create models
		self.model_left = QtGui.QStandardItemModel(self)
		self.model_left_sort = QtGui.QStandardItemModel(self)
		self.model_right = QtGui.QStandardItemModel(self)
		self.model_right_sort = QtGui.QStandardItemModel(self)
		# connect models to tableViews
		self.tableView_left.setModel(self.model_left)
		self.tableView_left_sort.setModel(self.model_left_sort)
		self.tableView_right.setModel(self.model_right)
		self.tableView_right_sort.setModel(self.model_right_sort)
		# set selection from single to rows
		self.tableView_left.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.tableView_left_sort.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.tableView_right.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.tableView_right_sort.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		# Interactions
		self.tableView_left.selectionModel().selectionChanged.connect(lambda: self.drawPoint(tableview=self.tableView_left))
		self.tableView_left_sort.selectionModel().selectionChanged.connect(lambda: self.drawPoint(tableview=self.tableView_left_sort))
		self.tableView_right.selectionModel().selectionChanged.connect(lambda: self.drawPoint(tableview=self.tableView_right))
		self.tableView_right_sort.selectionModel().selectionChanged.connect(lambda: self.drawPoint(tableview=self.tableView_right_sort))

		## Connect buttons
		# open and edit
		self.toolButton_open_left.clicked.connect(lambda: self.importPoints('left'))
		self.toolButton_edit_left.clicked.connect(lambda: self.editModel(self.model_left))
		self.toolButton_open_right.clicked.connect(lambda: self.importPoints('right'))
		self.toolButton_edit_right.clicked.connect(lambda: self.editModel(self.model_right))
		# left
		self.toolButton_copy_left.clicked.connect(lambda: self.copyPoint('left'))
		self.toolButton_delsel_left.clicked.connect(lambda: self.delPoint('left'))
		self.toolButton_export_left.clicked.connect(lambda: self.exportSortModel(self.model_left_sort))
		self.toolButton_showimg_left.clicked.connect(lambda: self.openImage('left'))
		# right
		self.toolButton_copy_right.clicked.connect(lambda: self.copyPoint('right'))
		self.toolButton_delsel_right.clicked.connect(lambda: self.delPoint('right'))
		self.toolButton_export_right.clicked.connect(lambda: self.exportSortModel(self.model_right_sort))
		self.toolButton_showimg_right.clicked.connect(lambda: self.openImage('right'))
		# correlate
		self.Button_correlate.clicked.connect(self.correlate)

		## Checkbox
		self.checkBox_rotcenter.stateChanged.connect(lambda: self.setRotCenter(self.checkBox_rotcenter.isChecked()))
		self.checkBox_poi.stateChanged.connect(lambda: self.setpoi(self.checkBox_poi.isChecked()))
		self.checkBox_scattframe.stateChanged.connect(lambda: self.drawScattFrame(self.checkBox_scattframe.isChecked()))
		## Spinbox
		self.doubleSpinBox_scattframe.valueChanged.connect(lambda: self.drawScattFrame(self.checkBox_scattframe.isChecked()))
		self.doubleSpinBox_scattframe.setKeyboardTracking(False)

		## init image sbs widget paths
		self.imgpath_left = None
		self.imgpath_right = None
		self.img_left_loaded = False
		self.img_right_loaded = False
		## test init image sbs widget
		# self.initializeImageWidget(imgleft='/Users/jan/Desktop/pyPhoOvTest/IB_030.tif',imgright='/Volumes/Silver/Dropbox/Dokumente/Code/px_test.tif')

	def lol(self):
		print "lol"

	## Handle close events
	def closeEvent(self,event):
		if hasattr(window, "sortData"):
			quit_msg = "Are you sure you want to close the Sort Data Tool?"
			reply = QtGui.QMessageBox.question(
				self, 'Message', quit_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
			if reply == QtGui.QMessageBox.Yes:
				del window.sortData
				## Delete up temp folder
				try:
					shutil.rmtree(os.path.join(execdir,'.3dct_tmp'))
				except Exception as e:
					QtGui.QMessageBox.critical(self, "Warning", "Could not delete temp folder! %s" % e)
					## Close all matplotlib windows
				if hasattr(self, "correlation_results"):
					try:
						scatterHistPlot.closeAll()
						self.dockWidget_results.hide()
					except Exception as e:
						QtGui.QMessageBox.critical(self, "Warning", "Could not close matplotlib windows! %s" % e)
				if hasattr(self, "isbswidget"):
					self.isbswidget.close()
				if hasattr(self, "teWidget"):
					self.teWidget.close()
				window.childExitStatus_sort = True
				event.accept()
			else:
				window.childExitStatus_sort = False
				event.ignore()

	def initialize(self):
		# show main widget window
		self.show()

	def importPoints(self,model):
		csv_file_in, filterdialog = QtGui.QFileDialog.getOpenFileNameAndFilter(
			self, 'Import file as', workingdir, "Tabstop sepperated (*.csv *.txt);;Comma sepperated (*.csv *.txt)")
		if str(filterdialog).startswith('Comma') is True:
			if model == 'left':
				self.model_left = csv_handler.csv2model(csv_file_in,delimiter=",",parent=self,sniff=True)
				self.toolButton_copy_left.setEnabled(True)
				self.toolButton_showimg_left.setEnabled(True)
				self.toolButton_edit_left.setEnabled(True)
			elif model == 'right':
				self.model_right = csv_handler.csv2model(csv_file_in,delimiter=",",parent=self,sniff=True)
				self.toolButton_copy_right.setEnabled(True)
				self.toolButton_showimg_right.setEnabled(True)
				self.toolButton_edit_right.setEnabled(True)
		elif str(filterdialog).startswith('Tabstop') is True:
			if model == 'left':
				self.model_left = csv_handler.csv2model(csv_file_in,delimiter="\t",parent=self,sniff=True)
				self.toolButton_copy_left.setEnabled(True)
				self.toolButton_showimg_left.setEnabled(True)
				self.toolButton_edit_left.setEnabled(True)
			elif model == 'right':
				self.model_right = csv_handler.csv2model(csv_file_in,delimiter="\t",parent=self,sniff=True)
				self.toolButton_copy_right.setEnabled(True)
				self.toolButton_showimg_right.setEnabled(True)
				self.toolButton_edit_right.setEnabled(True)
		self.tableView_left.setModel(self.model_left)
		self.tableView_right.setModel(self.model_right)
		self.tableView_left.selectionModel().selectionChanged.connect(lambda: self.drawPoint(tableview=self.tableView_left))
		self.tableView_right.selectionModel().selectionChanged.connect(lambda: self.drawPoint(tableview=self.tableView_right))

	def copyPoint(self,side):
		rows = set(index.row() for index in getattr(self, "%s" % "tableView_"+side).selectedIndexes())
		for rowNumber in rows:
			items = [
					getattr(self, "%s" % "model_"+side).itemFromIndex(getattr(self, "%s" % "model_"+side).index(rowNumber, 0)).clone(),
					getattr(self, "%s" % "model_"+side).itemFromIndex(getattr(self, "%s" % "model_"+side).index(rowNumber, 1)).clone(),
					(getattr(self, "%s" % "model_"+side).itemFromIndex(getattr(self, "%s" % "model_"+side).index(rowNumber, 2)).clone()
						if getattr(self, "%s" % "model_"+side).columnCount() == 3 else QtGui.QStandardItem('0'))]
			getattr(self, "%s" % "model_"+side+"_sort").appendRow(items)
		getattr(self, "%s" % "model_"+side+"_sort").setHeaderData(0, QtCore.Qt.Horizontal,'x')
		getattr(self, "%s" % "model_"+side+"_sort").setHeaderData(1, QtCore.Qt.Horizontal,'y')
		getattr(self, "%s" % "model_"+side+"_sort").setHeaderData(2, QtCore.Qt.Horizontal,'z')
		getattr(self, "%s" % "toolButton_export_"+side).setEnabled(True)
		getattr(self, "%s" % "toolButton_delsel_"+side).setEnabled(True)

	def delPoint(self,side):
		rows = sorted(set(index.row() for index in getattr(self, "%s" % "tableView_"+side+"_sort").selectedIndexes()))
		i = 0
		for row in rows:
			QtGui.QStandardItemModel.removeRows(getattr(self, "%s" % "model_"+side+"_sort"),row-i,1)
			i += 1
		if getattr(self, "%s" % "model_"+side+"_sort").rowCount() == 0:
			getattr(self, "%s" % "toolButton_export_"+side).setEnabled(False)
			getattr(self, "%s" % "toolButton_delsel_"+side).setEnabled(False)

	def editModel(self,model):
		import tableeditor
		self.teWidget = tableeditor.MainWidget(model=model, parent=self)
		self.teWidget.show()

	def model2np(self,model):
		listarray = []
		for rowNumber in range(model.rowCount()):
			fields = [
					model.data(model.index(rowNumber, columnNumber), QtCore.Qt.DisplayRole).toFloat()[0]
					for columnNumber in range(model.columnCount())]
			listarray.append(fields)
		return np.array(listarray).astype(np.float)

	def correlate(self):
		l_rc = self.model_left.rowCount()
		r_rc = self.model_right.rowCount()
		ls_rc = self.model_left_sort.rowCount()
		rs_rc = self.model_right_sort.rowCount()
		self.rotation_center = [self.doubleSpinBox_psi.value(),self.doubleSpinBox_phi.value(),self.doubleSpinBox_theta.value()]

		## create model for poi (QtModel for consistency in handling data between functions. Can also be extended in the future for multiple POIs)
		if self.checkBox_poi.isChecked() is True:
			self.model_pois = QtGui.QStandardItemModel()
			items = ([
					QtGui.QStandardItem(str(self.doubleSpinBox_poi_x.value())),
					QtGui.QStandardItem(str(self.doubleSpinBox_poi_y.value())),
					QtGui.QStandardItem(str(self.doubleSpinBox_poi_z.value()))])
			self.model_pois.appendRow(items)
		else:
			self.model_pois = QtGui.QStandardItemModel()

		if l_rc != 0 and r_rc != 0:
			import correlation
			timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
			if ls_rc != 0 and rs_rc != 0:
				if ls_rc == rs_rc:
					if ls_rc >= 3:
						self.correlation_results = correlation.main(
														markers_3d=self.model2np(self.model_left_sort),
														markers_2d=self.model2np(self.model_right_sort),
														spots_3d=self.model2np(self.model_pois),
														rotation_center=self.rotation_center,
														results_file=''.join([workingdir,'/',timestamp, '_correlation.txt'])
														)
						self.displayResults()
					else:
						QtGui.QMessageBox.critical(self, "Data Structur",'At least THREE markers are needed to do the correlation')

				else:
					QtGui.QMessageBox.critical(
						self, "Data Structur",	'The two datasets do not contain the same amount of markers!\n\n'
						'Please use the copy function (double click entries or arrow button) to create two lists '
						'with the correspondent markers from both datasets in the same row.')
			else:
				if l_rc == r_rc:
					if l_rc >= 3:
						self.correlation_results = correlation.main(
														markers_3d=self.model2np(self.model_left),
														markers_2d=self.model2np(self.model_right),
														spots_3d=self.model2np(self.model_pois),
														rotation_center=self.rotation_center,
														results_file=''.join([workingdir,'/',timestamp, '_correlation.txt'])
														)
						self.displayResults()
					else:
						QtGui.QMessageBox.critical(self, "Data Structur",'At least THREE markers are needed to do the correlation')

				else:
					QtGui.QMessageBox.critical(self, "Data Structur", "The two datasets do not contain the same amount of markers!")
		else:
			if self.model_left.rowCount() == 0 and self.model_right.rowCount() == 0:
				QtGui.QMessageBox.information(self, "Import Data", "Please import data to correlate!")
			elif self.model_left.rowCount() != 0 or self.model_right.rowCount() != 0:
				QtGui.QMessageBox.information(self, "Import Data", "Please import two datasets to correlate!")

		if self.checkBox_saveimage.isChecked() is True:
			import cv2
			try:
				image = cv2.imread(unicode(self.imgpath_right.toUtf8(), encoding="UTF-8"))
			except:
				image = cv2.imread(self.imgpath_right)
			transf_3d = self.correlation_results[1]
			for i in range(transf_3d.shape[1]):
				cv2.circle(image, (int(round(transf_3d[0,i])), int(round(transf_3d[1,i]))), 3, (0,255,0), -1)
			if self.checkBox_poi.isChecked() is True:
				calc_spots_2d = self.correlation_results[2]
				# draw POI cv2.circle(img, (center x, center y), radius, [b,g,r], thickness(-1 for filled))
				cv2.circle(image, (int(round(calc_spots_2d[0,0])), int(round(calc_spots_2d[1,0]))), 1, (0,0,255), -1)
			cv2.imwrite(os.path.join(workingdir,timestamp+"_correlated.tif"), image)

	def displayResults(self,frame=False,framesize=None):
		if self.correlation_results:
			global scatterHistPlot
			import scatterHistPlot
			## get data
			transf = self.correlation_results[0]
			# transf_3d = self.correlation_results[1]			## unused atm
			# calc_spots_2d = self.correlation_results[2]		## unused atm
			delta2D = self.correlation_results[3]
			delta2D_mean = np.absolute(delta2D).mean(axis=1)
			# cm_3D_markers = self.correlation_results[4]		## unused atm
			modified_translation = self.correlation_results[5]
			eulers = transf.extract_euler(r=transf.q, mode='x', ret='one')
			eulers = eulers * 180 / np.pi
			# scale = transf.s_scalar
			# translation = (transf.d[0], transf.d[1], transf.d[2])

			## display data
			# rotation
			self.lcdNumber_psi.display(eulers[2])
			self.lcdNumber_phi.display(eulers[0])
			self.lcdNumber_theta.display(eulers[1])
			# translation and scale
			self.label_rotcenter.setText('[%5.2f, %5.2f, %5.2f]' % (
				self.rotation_center[0],
				self.rotation_center[1],
				self.rotation_center[2]))
			self.lcdNumber_transxRotCenter.display(modified_translation[0])
			self.lcdNumber_transyRotCenter.display(modified_translation[1])
			self.lcdNumber_transx.display(transf.d[0])
			self.lcdNumber_transy.display(transf.d[1])
			self.lcdNumber_scale.display(transf.s_scalar)
			# error
			self.lcdNumber_RMS.display(transf.rmsError)
			self.lcdNumber_meandx.display(delta2D_mean[0])
			self.lcdNumber_meandy.display(delta2D_mean[1])

			# show results dock widget
			self.dockWidget_results.show()
			# generic thread - this was implemanted to keep a matplot graph from freezing up the main application
			# under windows. but it seems to be a matplotlib backend issue.
			# self.genericThread = GenericThread(scatterHistPlot.main,x = delta2D[:1,:][0],y = delta2D[1:,:][0],\
			# frame=frame,framesize=framesize,xlabel="px",ylabel="px")
			# self.genericThread.start()

			# simple plt show in own window. Stops execution of main thred under windows (default tkinter backend).
			# Own generic thread works under windows, not under mac os x.
			# changed default backend to pyqt4 which works fine under both systems.
			scatterHistPlot.main(x=delta2D[:1,:][0],y=delta2D[1:,:][0],frame=frame,framesize=framesize,xlabel="px",ylabel="px")

		else:
			QtGui.QMessageBox.critical(self, "Error", "No data to display!")

	def setRotCenter(self,checkstate):
		if checkstate is True:
			self.doubleSpinBox_psi.setEnabled(True)
			self.doubleSpinBox_phi.setEnabled(True)
			self.doubleSpinBox_theta.setEnabled(True)
		else:
			self.doubleSpinBox_psi.setEnabled(False)
			self.doubleSpinBox_phi.setEnabled(False)
			self.doubleSpinBox_theta.setEnabled(False)

	def setpoi(self,checkstate):
		if checkstate is True:
			self.doubleSpinBox_poi_x.setEnabled(True)
			self.doubleSpinBox_poi_y.setEnabled(True)
			self.doubleSpinBox_poi_z.setEnabled(True)
		else:
			self.doubleSpinBox_poi_x.setEnabled(False)
			self.doubleSpinBox_poi_y.setEnabled(False)
			self.doubleSpinBox_poi_z.setEnabled(False)

	def drawScattFrame(self,checkstate):
		if checkstate is True:
			self.doubleSpinBox_scattframe.setEnabled(True)
			scatterHistPlot.closeAll()
			self.displayResults(frame=True,framesize=self.doubleSpinBox_scattframe.value())
		else:
			self.doubleSpinBox_scattframe.setEnabled(False)
			scatterHistPlot.closeAll()
			self.displayResults()

	def exportSortModel(self,model):
		## Export Dioalog. Needs check for extension or add default extension
		csv_file_out, filterdialog = QtGui.QFileDialog.getSaveFileNameAndFilter(
			self, 'Export file as', workingdir, "Tabstop sepperated (*.csv *.txt);;Comma sepperated (*.csv *.txt)")
		if str(filterdialog).startswith('Comma') is True:
			csv_handler.model2csv(model,csv_file_out,delimiter=",")
		elif str(filterdialog).startswith('Tabstop') is True:
			csv_handler.model2csv(model,csv_file_out,delimiter="\t")

	def openImage(self, location):
		imgpath = QtGui.QFileDialog.getOpenFileName(
			self, 'Open Image', workingdir, "Image Files (*.tif *.tiff *.png *.jpg *.gif *.bmp);;All files (*.*)")
		if location == 'left':
			self.imgpath_left = imgpath
			self.img_left_loaded = True
		if location == 'right':
			self.imgpath_right = imgpath
			self.img_right_loaded = True
			self.checkBox_saveimage.setChecked(True)
			self.checkBox_saveimage.show()
		self.initializeImageWidget()

	def initializeImageWidget(self):
		if hasattr(self, "isbswidget"):
			self.isbswidget.close()
		global isbs
		import isbs
		size = 400
		self.isbswidget = isbs.MainWidget(size=size, left=self.imgpath_left, right=self.imgpath_right)
		self.isbswidget.show()
		## Move Window
		self.isbswidget.move(801,0)

	def drawPoint(self, tableview=None):
		if self.isbswidget.isHidden() is False:
			tableView = self.sender()
			if tableview:
				tableView = tableview
			indices = tableView.selectedIndexes()
			model = tableView.model()
			data = []
			if tableView == self.tableView_left or tableView == self.tableView_left_sort:
				self.isbswidget.initImage1()
			elif tableView == self.tableView_right or tableView == self.tableView_right_sort:
				self.isbswidget.initImage2()
			if len(indices) < 4:
				for column in range(2):
					indexm = model.index(indices[0].row(), column)
					data.append(str(model.data(indexm).toString()))
				# print int(float(data[0])), int(float(data[1]))
				if tableView == self.tableView_left or tableView == self.tableView_left_sort:
					self.isbswidget.addCircle1(int(float(data[0])), int(float(data[1])))
				elif tableView == self.tableView_right or tableView == self.tableView_right_sort:
					self.isbswidget.addCircle2(int(float(data[0])), int(float(data[1])))

			elif len(indices) >= 4:
				rows = []
				for i in range(len(indices)):
					if indices[i].column() == 0:
						rows.append(indices[i].row())
				for i in rows:
					x = model.index(i, 0)
					y = model.index(i, 1)
					# print	int(float(model.data(x).toString())), int(float(model.data(y).toString()))
					if tableView == self.tableView_left or tableView == self.tableView_left_sort:
						self.isbswidget.addCircle1(int(float(model.data(x).toString())), int(float(model.data(y).toString())))
					elif tableView == self.tableView_right or tableView == self.tableView_right_sort:
						self.isbswidget.addCircle2(int(float(model.data(x).toString())), int(float(model.data(y).toString())))

## Class to outsource work to an independant thread. Not used anymore at the moment.


class GenericThread(QtCore.QThread):
	def __init__(self, function, *args, **kwargs):
		QtCore.QThread.__init__(self)
		self.function = function
		self.args = args
		self.kwargs = kwargs

	def __del__(self):
		self.wait()

	def run(self):
		self.function(*self.args,**self.kwargs)
		return


print clrmsg.DEBUG + 'Debug Test'
print clrmsg.OK + 'OK Test'
print clrmsg.ERROR + 'Error Test'
print clrmsg.INFO + 'Info Test'
print clrmsg.WARNING + 'Warning Test'
########## Executed when running in standalone ###################################
##################################################################################

if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	window = APP()
	window.show()
	sys.exit(app.exec_())
