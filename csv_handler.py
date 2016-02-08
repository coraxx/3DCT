#!/usr/bin/env python
#title				: csv_handler.py
#description		: Import and export PyQt model data from/to csv fles
#author				: Jan Arnold
#email				: jan.arnold (at) coraxx.net
#credits			: 
#maintainer			: Jan Arnold
#date				: 2015/09
#version			: 0.2
#status				: developement
#usage				: python csv_handler.py
#notes				: 
#python_version		: 2.7.10 
#=================================================================================
import csv
from PyQt4 import QtCore, QtGui

#csv_file_in = "/Users/jan/Desktop/MPI/csfib_test/data/csfib_test.csv"
#csv_file_out = "/Users/jan/Desktop/test.txt"

## read csv/tsv into pyqt model for display in e.g. QTableView
def csv2model(csv_file_in,delimiter="\t",sniff=False,parent=None):
	def main():
		model = QtGui.QStandardItemModel()
		with open(csv_file_in) as csv_file:
			for row in csv.reader(csv_file, delimiter=delimiter):
				items = [ QtGui.QStandardItem(field) for field in row ]
				model.appendRow(items)
		return model

	if sniff == True:
		sniffer = csv.Sniffer()
		## Sniff for delimiter
		with open(csv_file_in) as csv_file:
			dialect = sniffer.sniff(csv_file.read())
		## Decide what to do
		if dialect.delimiter == delimiter:
			return main()
		elif dialect.delimiter != delimiter and parent == None:
			delimiter = dialect.delimiter
			return main()
		elif dialect.delimiter != delimiter and parent:
			# DIALOG Are you sure the delimter is correct? we detected XXX as the correct delimiter and not YYY
			message = ("We detected " + repr(dialect.delimiter) + 
					" as the correct delimiter. Are you sure it is " + 
					repr(delimiter) + 
					" ?\n\nClick yes to use: " + 
					repr(delimiter) + 
					"\nClick no to use: " + 
					repr(dialect.delimiter))
			reply = QtGui.QMessageBox.warning(parent, 'Warning',
							 message, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
			if reply == QtGui.QMessageBox.No:
				## Correct delimiter
				delimiter = dialect.delimiter
				return main()
			else:
				return main()
	else:
		return main()


## write model data to csv/tsv file
def model2csv(model,csv_file_out,delimiter="\t"):
	with open(csv_file_out, "wb") as fileOutput:
		writer = csv.writer(fileOutput, delimiter=delimiter,lineterminator='\n')
		for rowNumber in range(model.rowCount()):
			fields = [ model.data(model.index(rowNumber, columnNumber), QtCore.Qt.DisplayRole).toString()
					for columnNumber in range(model.columnCount()) ]
			writer.writerow(fields)

# if __name__ == "__main__":
# 	print "Import me"

