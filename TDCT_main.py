#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
3D Correlation Toolbox - 3DCT

This Toolbox is build for 3D correlative microscopy. It helps with 3D to 2D correlation of three
dimensional confocal image stacks to two dimensional SEM/FIB dual beam microscope images.
But it is not limited to that.

The Toolbox comes with a PyQt4 GUI. Further dependencies as of now are:

	- PyQt4
	- numpy
	- scipy
	- matplotlib
	- cv2 (opencv)
	- tifffile (Christoph Gohlke)

A test dataset can be downloaded from the "testdata" folder:
	https://bitbucket.org/splo0sh/3dctv2/src/ab8914cf71aea77949bc5037ba090df42cfa3abc/testdata/?at=master

# @Title			: TDCT_main
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
# @Version			: 3DCT 2.0.0
# @Status			: developement
# @Usage			: python -u TDCT_main.py
# @Notes			:
# @Python_version	: 2.7.10
"""
# ======================================================================================================================

import sys
import os
import fileinput
# from functools import partial
from subprocess import call
from PyQt4 import QtCore, QtGui, uic
# add working directory temporarily to PYTHONPATH
execdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(execdir)
try:
	## Colored stdout
	from tdct import clrmsg
	import TDCT_correlation
except Exception as e:
	print e
	sys.exit()

__version__ = 'v2.0.0'


########## GUI layout file #######################################################
##################################################################################
qtCreatorFile_main = os.path.join(execdir, "TDCT_main.ui")
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile_main)

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

		self.actionAbout.triggered.connect(self.about)

		# Buttons
		self.pushButton_selectWorkingDir.clicked.connect(lambda: self.selectpath(self.lineEdit_workingDir))
		self.pushButton_openWorkingDir.clicked.connect(lambda: self.openDirectoy(self.lineEdit_workingDir.text()))
		self.pushButton_saveTo.clicked.connect(lambda: self.selectpath(self.lineEdit_saveToPath))
		self.pushButton_selectTif.clicked.connect(lambda: self.selectpath(self.lineEdit_selectTifPath))
		self.pushButton_openSaveToPath.clicked.connect(lambda: self.openDirectoy(self.lineEdit_saveToPath.text()))
		self.pushButton_runStack.clicked.connect(self.runStackProcessing)
		self.toolButton_selectImage1.clicked.connect(self.selectImage1)
		self.toolButton_selectImage2.clicked.connect(self.selectImage2)
		self.toolButton_reloadFileList.clicked.connect(self.reloadFileList)
		self.commandLinkButton_correlate.clicked.connect(self.runCorrelationModule)
		self.testButton.clicked.connect(self.tester)

		# QLineEdits
		self.lineEdit_selectTifPath.textChanged.connect(lambda: self.isValidPath(self.lineEdit_selectTifPath))
		self.lineEdit_selectImage1.textChanged.connect(lambda: self.isValidFile(self.lineEdit_selectImage1))
		self.lineEdit_selectImage2.textChanged.connect(lambda: self.isValidFile(self.lineEdit_selectImage2))
		self.lineEdit_workingDir.textChanged.connect(lambda: self.isValidPath(self.lineEdit_workingDir))
		self.lineEdit_saveToPath.textChanged.connect(lambda: self.isValidPath(self.lineEdit_saveToPath))

		# Checkbox
		self.checkBox_cubeVoxels.stateChanged.connect(lambda: self.cubeVoxels(self.checkBox_cubeVoxels.isChecked()))

		# Init Working directory
		self.workingdir = os.path.expanduser("~")
		self.lineEdit_workingDir.setText(self.workingdir)
		self.populate_filelist(self.workingdir)

	def isValidFile(self,lineEdit):
		if lineEdit.text() == "":
			lineEdit.setStyleSheet(
				"QLineEdit{background-color: white;} QLineEdit:hover{border: 1px solid grey; background-color white;}")
		elif os.path.isfile(lineEdit.text()):
			if os.path.splitext(str(lineEdit.text()))[1] in ['.tif','.tiff']:
				lineEdit.setStyleSheet(
					"QLineEdit{background-color: rgb(0,255,0,120);} QLineEdit:hover{border: 1px solid grey; background-color rgb(0,255,0,120);}")
				lineEdit.fileIsValid = True
				lineEdit.fileIsTiff = True
			else:
				lineEdit.setStyleSheet(
					"QLineEdit{background-color: rgb(255,120,0,120);} QLineEdit:hover{border: 1px solid grey; background-color rgb(255,120,0,120);}")
				lineEdit.fileIsValid = True
				lineEdit.fileIsTiff = False
		else:
			lineEdit.setStyleSheet(
				"QLineEdit{background-color: rgb(255,0,0,120);} QLineEdit:hover{border: 1px solid grey; background-color rgb(255,0,0,120);}")
			lineEdit.fileIsValid = False

	def isValidPath(self,lineEdit):
		if lineEdit.text() == "":
			lineEdit.setStyleSheet(
				"QLineEdit{background-color: white;} QLineEdit:hover{border: 1px solid grey; background-color white;}")
			if lineEdit.objectName() is 'lineEdit_workingDir':
				self.listWidget_workingDir.clear()
		elif os.path.isdir(lineEdit.text()):
			lineEdit.setStyleSheet(
				"QLineEdit{background-color: rgb(0,255,0,120);} QLineEdit:hover{border: 1px solid grey; background-color rgb(0,255,0,120);}")
			if lineEdit.objectName() is 'lineEdit_workingDir':
				self.workingdir = self.checkWorkingDirPrivileges(str(self.lineEdit_workingDir.text()))
				self.populate_filelist(self.workingdir)
		else:
			lineEdit.setStyleSheet(
				"QLineEdit{background-color: rgb(255,0,0,120);} QLineEdit:hover{border: 1px solid grey; background-color rgb(255,0,0,120);}")

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
		self.loadTestDataset()

	## only for quick load of test datasets - REMOVE FROM FINAL VERSION
	def loadTestDataset(self):
		self.lineEdit_selectTifPath.setText("/Volumes/Silver/input")
		self.lineEdit_saveToPath.setText("/Volumes/Silver/output")
		self.pushButton_openSaveToPath.setEnabled(True)
		self.pushButton_runStack.setEnabled(True)

	## only for quick load of test datasets - REMOVE FROM FINAL VERSION
	def tester(self):
		testpath = '/Users/jan/Desktop/'
		testpath = 'F:/jan_temp/'
		leftImage = testpath+'correlation_test_dataset/IB_030.tif'
		rightImage = testpath+'correlation_test_dataset/LM_green_reslized.tif'
		import TDCT_correlation
		self.correlationModul = TDCT_correlation.Main(leftImage=leftImage,rightImage=rightImage,nosplash=False,workingdir=self.workingdir)

	## About
	def about(self):
		QtGui.QMessageBox.about(
								self, "About 3DCT", "3DCT v0.1\n\ndeveloped by:\n\nMax-Planck-Institute of Biochemistry\n\n" +
								"3D Correlation Toolbox:	Jan Arnold\nCorrelation Algorithm:	Vladan Lucic"
								)

	def checkWorkingDirPrivileges(self,path):
		import tempfile
		try:
			testfile = tempfile.TemporaryFile(dir=path)
			testfile.close()
			return path
		except Exception:
			QtGui.QMessageBox.critical(
				self,"Warning",
				"I cannot write to this folder: {0}\nFalling back to {1} as the working directory".format(path, self.workingdir))
			return self.workingdir

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
		quit_msg = "Are you sure you want to exit the\n3D Correlation Toolbox?\n\nUnsaved data will be lost!"
		reply = QtGui.QMessageBox.question(self, 'Message', quit_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes:
			# if loaded, close pointselection tool widget and sub windows
			if hasattr(self, "correlationModul"):
				if hasattr(self.correlationModul, "widget"):
					exitstatus = self.correlationModul.close()
					if exitstatus == 1:
						event.ignore()
					else:
						event.accept()
		else:
			event.ignore()

	## Select Paths
	def selectpath(self, pathLine):
		sender = self.sender()
		path = str(QtGui.QFileDialog.getExistingDirectory(self, "Select Directory", self.workingdir))
		if path:
			if sender == self.pushButton_selectWorkingDir:
				self.workingdir = self.checkWorkingDirPrivileges(path)
				pathLine.setText(self.workingdir)
				# Populate file lists
				self.populate_filelist(self.workingdir)
			# Open Save to directory button
			if sender == self.pushButton_saveTo:
				self.lineEdit_saveToPath.setText(path)
				self.pushButton_openSaveToPath.setEnabled(True)
			# Working directory
			elif sender == self.pushButton_selectWorkingDir and self.lineEdit_saveToPath.text() == "":
				self.lineEdit_saveToPath.setText(self.workingdir)
				self.pushButton_openSaveToPath.setEnabled(True)
			# Save new Stack to directoy
			if self.lineEdit_saveToPath.text() != "" and self.lineEdit_selectTifPath.text() != "":
				self.pushButton_runStack.setEnabled(True)

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
	def runStackProcessing(self):
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
			str_lineEdit_selectTifPath = str(self.lineEdit_selectTifPath.text())
			str_lineEdit_saveToPath = str(self.lineEdit_saveToPath.text())
			print clrmsg.DEBUG, str_lineEdit_selectTifPath, str_lineEdit_saveToPath
			print clrmsg.DEBUG, str_lineEdit_selectTifPath.encode('string-escape'), str_lineEdit_saveToPath.encode('string-escape')
			print clrmsg.DEBUG, str_lineEdit_selectTifPath.encode('string-escape').replace('\\\\','\\'), \
				str_lineEdit_saveToPath.encode('string-escape').replace('\\\\','\\')
			pathFROM = "PATH = " + '"' + str_lineEdit_selectTifPath.encode('string-escape') + '/";'
			pathTO = "PATHSAVETO = " + '"' + str_lineEdit_saveToPath.encode('string-escape') + '/";'
		else:
			pathFROM = "PATH = " + '"' + self.lineEdit_selectTifPath.text() + '/";'
			pathTO = "PATHSAVETO = " + '"' + self.lineEdit_saveToPath.text() + '/";'
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
			self.runStackProcessing_return_code = call([execdir + "/Fiji/Contents/MacOS/ImageJ-macosx", "--headless", "-macro", pathMACRO, "&"])
		elif sys.platform == 'linux2':
			self.runStackProcessing_return_code = call([execdir + "/Fiji/ImageJ-linux64", "-macro", pathMACRO, "&"])
		elif sys.platform == 'win32':
			self.runStackProcessing_return_code = call([execdir + "/Fiji/ImageJ-win64.exe", "-macro", pathMACRO])
		if self.runStackProcessing_return_code == 0:
			self.stackProcessStatus.setStyleSheet("color: rgb(0, 225, 90);")
			self.stackProcessStatus.setText('Yeay, done!')
		else:
			self.stackProcessStatus.setStyleSheet("color: rgb(255, 0, 0);")
			self.stackProcessStatus.setText('Fiji failed!')
			restart_msg = "Fiji closed with an error. Do you want to restart it?"
			reply = QtGui.QMessageBox.question(self, 'Message', restart_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
			if reply == QtGui.QMessageBox.Yes:
				self.runStackProcessing()
		# clean up
		try:
			os.remove(macro_path)
		except OSError:
			pass

	## Populate List widget for listing files needed for coordinate extraction
	def populate_filelist(self,path):
		self.listWidget_workingDir.clear()
		self.listWidget_workingDir.itempath = path
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
				self.listWidget_workingDir.addItem(item)

	def reloadFileList(self):
		if hasattr(self, "workingdir"):
			self.populate_filelist(self.workingdir)
			print 'reloaded'

	def selectImage1(self):
		self.lineEdit_selectImage1.setText(
			os.path.join(self.listWidget_workingDir.itempath, str(self.listWidget_workingDir.selectedItems()[0].text())))

	def selectImage2(self):
		self.lineEdit_selectImage2.setText(
			os.path.join(self.listWidget_workingDir.itempath, str(self.listWidget_workingDir.selectedItems()[0].text())))

	def runCorrelationModule(self):
		if self.lineEdit_selectImage1.text() != "" and self.lineEdit_selectImage2.text() != "":
			if self.lineEdit_selectImage1.fileIsTiff is True and self.lineEdit_selectImage2.fileIsTiff is True:
				self.correlationModul = TDCT_correlation.Main(
					leftImage=str(self.lineEdit_selectImage1.text()),
					rightImage=str(self.lineEdit_selectImage2.text()),
					nosplash=False,
					workingdir=self.workingdir)
			else:
				if self.lineEdit_selectImage1.fileIsValid is False or self.lineEdit_selectImage2.fileIsValid is False:
					QtGui.QMessageBox.warning(
						self,"Warning",
						"Invalid file path detected. Please check the file paths.")
				elif self.lineEdit_selectImage1.fileIsTiff is False or self.lineEdit_selectImage2.fileIsTiff is False:
					QtGui.QMessageBox.warning(
						self,"Warning",
						"Only *.tif and *.tiff files are supported at the moment")
		else:
			if self.lineEdit_selectImage1.text() == "":
				self.lineEdit_selectImage1.setStyleSheet(
					"QLineEdit{background-color: rgb(255,0,0,120);} QLineEdit:hover{border: 1px solid grey; background-color rgb(255,0,0,120);}")
			if self.lineEdit_selectImage2.text() == "":
				self.lineEdit_selectImage2.setStyleSheet(
					"QLineEdit{background-color: rgb(255,0,0,120);} QLineEdit:hover{border: 1px solid grey; background-color rgb(255,0,0,120);}")


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
