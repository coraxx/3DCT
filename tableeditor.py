#!/usr/bin/env python
#title				: tableeditor.py
#description		: Edit model in tableview
#author				: Jan Arnold
#email				: jan.arnold (at) coraxx.net
#credits			: 
#maintainer			: 
#date				: 2015/10
#version			: 0.1
#status				: developement
#usage				: python tableeditor.py
#notes				: 
#python_version		: 2.7.10 
#=================================================================================

import sys
import os
from PyQt4 import QtCore, QtGui, uic
# add working directory temporarily to PYTHONPATH
execdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(execdir)
# import modules from working directory
import csv_handler

qtCreatorFile_main =  os.path.join(execdir, "TDCT_tableeditor.ui")
Ui_WidgetWindow, QtBaseClass = uic.loadUiType(qtCreatorFile_main)

class MainWidget(QtGui.QWidget, Ui_WidgetWindow):
	def __init__(self, parent=None, model=None):
		QtGui.QWidget.__init__(self)
		Ui_WidgetWindow.__init__(self)
		self.setupUi(self)

		self.parent = parent
		self.model_in = model
		self.model = QtGui.QStandardItemModel(self)

		for rows in range(self.model_in.rowCount()):
			items = [ self.model_in.item(rows,columns).clone() for columns in range(self.model_in.columnCount()) ]
			self.model.appendRow(items)

		self.tableView.setModel(self.model)

		## Connect buttons
		self.buttonBox.accepted.connect(self.returnModel)
		self.buttonBox.rejected.connect(self.quit)
		self.toolButton_delRow.clicked.connect(self.delRows)
		self.toolButton_delColumns.clicked.connect(self.delColumns)

	def quit(self):
		self.close()

	def returnModel(self):
		self.model_in.clear()
		for rows in range(self.model.rowCount()):
			items = [ self.model.item(rows,columns).clone() for columns in range(self.model.columnCount()) ]
			self.model_in.appendRow(items)
		self.quit()
		# indexm = self.parent.returnModel.index(1, 1)
		# print str(self.parent.returnModel.data(indexm).toString())
		# print "-"*10
		# indexm = test.returnModel.index(1, 1)
		# print str(test.returnModel.data(indexm).toString())

	def delRows(self):
		rows = sorted(set(index.row() for index in self.tableView.selectedIndexes()))
		i = 0
		for row in rows:
			QtGui.QStandardItemModel.removeRows(self.model,row-i,1)
			i += 1

	def delColumns(self):
		columns = sorted(set(index.column() for index in self.tableView.selectedIndexes()))
		i = 0
		for column in columns:
			QtGui.QStandardItemModel.removeColumns(self.model,column-i,1)
			i += 1

class TEST():
	def __init__(self):
		self.model = csv_handler.csv2model("/Volumes/Silver/Dropbox/Dokumente/Code/Python/3DCT/testdata/set2/LM.txt",
											delimiter="\t",parent=self,sniff=True)

if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	test = TEST()
	widget = MainWidget(model=test.model, parent=test)
	widget.show()
	sys.exit(app.exec_())