#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Custom Qt classes. Some widgets in QT Designer are promoted to these classes:
	- QTableView
	- QSortFilterProxyModel
	- QStandardItemModel
	- QGraphicsScene
	- a custom QWidget for Matplotlib integration

# @Title			: QtCustom
# @Project			: 3DCTv2
# @Description		: Custom Qt classes
# @Author			: Jan Arnold
# @Email			: jan.arnold (at) coraxx.net
# @Credits			:
# @Maintainer		: Jan Arnold
# @Date				: 2016/02/27
# @Version			: 3DCT 2.0.0 module rev. 1
# @Status			: development
# @Usage			: part of 3D Correlation Toolbox
# @Notes			: Some widgets in QT Designer are promoted to these classes
# @Python_version	: 2.7.11
"""
# ======================================================================================================================

import sys
from PyQt4 import QtCore, QtGui
import numpy as np

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.patches as patches
from mpl_toolkits.axes_grid1 import make_axes_locatable

import math
import beadPos
import clrmsg

debug = True
##############################
# QTableViewCustom


class QTableViewCustom(QtGui.QTableView):
	def __init__(self,parent=None):
		"""
		Test bla bla
		"""
		QtGui.QTableView.__init__(self,parent)

		"""The parent is not mainWidget but QSplitter i.e. the main parent is callable by
		self.parent().parent() and not self.parent() when not using QSplitter. This may be
		subject to change, so to be flexible there is a check for QSplitter.
		UPDATE: GUI now QMainWindow, i.e. aditional parent call"""
		if isinstance(self.parent(), QtGui.QSplitter):
			self.mainParent = self.parent().parent().parent()

		self._drop = False

		## Enable Drag'n'Drop
		self.setDragDropOverwriteMode(False)
		self.setDragEnabled(True)
		self.setDragDropMode(QtGui.QAbstractItemView.InternalMove)

		'''associated model and scene are passed from TDCT_correlation and are available as self._model and self._scene'''

	def mouseMoveEvent(self,event):
		super(QTableViewCustom, self).mouseMoveEvent(event)
		## Drop Flag to trigger item update only when there was a row move
		if self._drop is True:
			self.updateItems()
			self._drop = False

	def dropEvent(self,event):
		## Drop Flag to trigger item update only when there was a row move
		self._drop = True
		super(QTableViewCustom, self).dropEvent(event)

												###############################################
												#######          Update items           #######
												#################### START ####################
	def updateItems(self):
		items = []
		for item in self._scene.items():
			if isinstance(item, QtGui.QGraphicsEllipseItem):
				items.append(item)
		if debug is True: print clrmsg.DEBUG + "Update items check - Nr. of items/rows:", len(items), self._model.rowCount()
		if len(items) == self._model.rowCount():
			row = 0
			for item in items:
				if debug is True:
					print clrmsg.DEBUG + 'Row:', row, '|', \
						self._model.data(self._model.index(row, 0)).toString(),\
						self._model.data(self._model.index(row, 1)).toString(),\
						self._model.data(self._model.index(row, 2)).toString()
				item.setPos(
					float(self._model.data(self._model.index(row, 0)).toString()),
					float(self._model.data(self._model.index(row, 1)).toString()))
				self._scene.zValuesDict[item] = [
												self._model.data(self._model.index(row, 2)).toString(),
												self._model.itemFromIndex(self._model.index(row, 2)).foreground().color().getRgb()]
				row += 1
		self.mainParent.colorModels()

	def showSelectedItem(self):
		indices = self.selectedIndexes()
		## Color all circles red and nly get ellipses, not text, to iterate through in green coloring process.
		activeitems = []
		for item in self._scene.items():
			if isinstance(item, QtGui.QGraphicsEllipseItem):
				item.setPen(self._scene.pen)
				activeitems.append(item)
		## Color selected items green
		if indices:
			## Filter selected rows
			rows = set(index.row() for index in indices)
			## Paint selected rows green
			for row in rows:
				activeitems[row].setPen(QtGui.QPen(QtCore.Qt.green))

	def deleteItem(self):
		indices = self.selectedIndexes()
		## Only get ellipses, not text.
		activeitems = []
		for item in self._scene.items():
			if isinstance(item, QtGui.QGraphicsEllipseItem):
				activeitems.append(item)
		## Deleting selected
		if indices:
			## Filter selected rows
			rows = set(index.row() for index in indices)
			## Delete selected rows in scene.
			for row in rows:
				self._scene.removeItem(activeitems[row])
				self._scene.enumeratePoints()
			self._scene.itemsToModel()

	## Context menu
	def contextMenuEvent(self, event):
		indices = self.selectedIndexes()
		if indices:
			cmDelete = QtGui.QAction('Delete', self)
			cmDelete.triggered.connect(self.deleteItem)
			cmGetZpoly = QtGui.QAction('get z poly', self)
			cmGetZpoly.triggered.connect(self.getz)
			cmGetZpolyOpt = QtGui.QAction('get z poly optimized', self)
			cmGetZpolyOpt.triggered.connect(lambda: self.getz(optimize=True))
			cmGetZgauss = QtGui.QAction('get z gauss', self)
			cmGetZgauss.triggered.connect(lambda: self.getz(gauss=True))
			cmGetZgaussOpt = QtGui.QAction('get z gauss optimized', self)
			cmGetZgaussOpt.triggered.connect(lambda: self.getz(gauss=True,optimize=True))
			if self.img is None:
				cmGetZpoly.setEnabled(False)
				cmGetZpolyOpt.setEnabled(False)
				cmGetZgauss.setEnabled(False)
				cmGetZgaussOpt.setEnabled(False)
			self.contextMenu = QtGui.QMenu(self)
			self.contextMenu.addAction(cmDelete)
			self.contextMenu.addAction(cmGetZpoly)
			self.contextMenu.addAction(cmGetZpolyOpt)
			self.contextMenu.addAction(cmGetZgauss)
			self.contextMenu.addAction(cmGetZgaussOpt)
			self.contextMenu.popup(QtGui.QCursor.pos())

	def getz(self,optimize=False,gauss=False):
		indices = self.selectedIndexes()
		## Determine z for selected rows
		if indices:
			activeitems = []
			for item in self._scene.items():
				if isinstance(item, QtGui.QGraphicsEllipseItem):
					activeitems.append(item)
			## Filter selected rows
			rows = set(index.row() for index in indices)
			## Delete selected rows in scene.
			for row in rows:
				if debug is True:
					print clrmsg.DEBUG + 'Row:', row, '|', \
						self._model.data(self._model.index(row, 0)).toString(),\
						self._model.data(self._model.index(row, 1)).toString(),\
						self._model.data(self._model.index(row, 2)).toString()
				x = float(self._model.data(self._model.index(row, 0)).toString())
				y = float(self._model.data(self._model.index(row, 1)).toString())

				if gauss is True:
					if optimize is False:
						zopt = beadPos.getzGauss(x,y,self.img,parent=self.mainParent)
						if debug is True: print clrmsg.DEBUG + str(self.img.shape), zopt
						if 0 <= zopt <= self.img.shape[-3]:
							self._scene.zValuesDict[activeitems[row]][1] = (0,0,0)
							self._model.itemFromIndex(self._model.index(row, 2)).setForeground(QtCore.Qt.black)
						else:
							self._scene.zValuesDict[activeitems[row]][1] = (255,0,0)
							self._model.itemFromIndex(self._model.index(row, 2)).setForeground(QtCore.Qt.red)
						self._model.itemFromIndex(self._model.index(row, 2)).setText(str(zopt))
					else:
						xopt,yopt,zopt = beadPos.getzGauss(
							x,y,self.img,parent=self.mainParent,optimize=True,threshold=True,
							threshVal=self.mainParent.doubleSpinBox_treshVal.value(),cutout=self._scene.markerSize)
						if debug is True: print clrmsg.DEBUG + str(self.img.shape), xopt,yopt,zopt
						if (
							abs(x-xopt) <= 2*self._scene.markerSize and
							abs(y-yopt) <= 2*self._scene.markerSize and
							0 <= zopt <= self.img.shape[-3]):
							self._scene.zValuesDict[activeitems[row]][1] = (255,0,0)
							self._model.itemFromIndex(self._model.index(row, 2)).setForeground(QtCore.Qt.black)
						else:
							self._scene.zValuesDict[activeitems[row]][1] = (0,0,0)
							self._model.itemFromIndex(self._model.index(row, 2)).setForeground(QtCore.Qt.red)
							xopt, yopt = x, y
						self._model.itemFromIndex(self._model.index(row, 0)).setText(str(xopt))
						self._model.itemFromIndex(self._model.index(row, 1)).setText(str(yopt))
						self._model.itemFromIndex(self._model.index(row, 2)).setText(str(zopt))
				elif optimize is False:
					zopt = beadPos.getzPoly(x,y,self.img,n=None)
					if debug is True: print clrmsg.DEBUG + str(self.img.shape), zopt
					if 0 <= zopt <= self.img.shape[-3]:
						self._scene.zValuesDict[activeitems[row]][1] = (0,0,0)
						self._model.itemFromIndex(self._model.index(row, 2)).setForeground(QtCore.Qt.black)
					else:
						self._scene.zValuesDict[activeitems[row]][1] = (255,0,0)
						self._model.itemFromIndex(self._model.index(row, 2)).setForeground(QtCore.Qt.red)
					self._model.itemFromIndex(self._model.index(row, 2)).setText(str(zopt))
				elif optimize is True:
					xopt,yopt,zopt = beadPos.getzPoly(x,y,self.img,n=None,optimize=True)
					if debug is True: print clrmsg.DEBUG + str(self.img.shape), xopt,yopt,zopt
					if 0 <= xopt <= self.img.shape[-1] and 0 <= yopt <= self.img.shape[-2] and 0 <= zopt <= self.img.shape[-3]:
						self._scene.zValuesDict[activeitems[row]][1] = (255,0,0)
						self._model.itemFromIndex(self._model.index(row, 2)).setForeground(QtCore.Qt.black)
					else:
						self._scene.zValuesDict[activeitems[row]][1] = (0,0,0)
						self._model.itemFromIndex(self._model.index(row, 2)).setForeground(QtCore.Qt.red)
					self._model.itemFromIndex(self._model.index(row, 0)).setText(str(xopt))
					self._model.itemFromIndex(self._model.index(row, 1)).setText(str(yopt))
					self._model.itemFromIndex(self._model.index(row, 2)).setText(str(zopt))

												##################### END #####################
												#######          Update items           #######
												###############################################


class NumberSortModel(QtGui.QSortFilterProxyModel):
	def lessThan(self,left,right):
		lvalue = left.data().toDouble()[0]
		rvalue = right.data().toDouble()[0]
		return lvalue < rvalue

##############################
## QStandardItemModelCustom


class QStandardItemModelCustom(QtGui.QStandardItemModel):
	def __init__(self, parent=None):
		QtGui.QStandardItemModel.__init__(self,parent)

	def dropMimeData(self,data,action,row,column,parent):
		return QtGui.QStandardItemModel.dropMimeData(self,data,action,row,0,parent)


##############################
## QGraphicsSceneCustom

class QGraphicsSceneCustom(QtGui.QGraphicsScene):
	def __init__(self,parent=None,mainWidget=None,side=None,model=None):
		## parent is QGraphicsView
		QtGui.QGraphicsScene.__init__(self,parent)
		self.mainWidget = mainWidget
		self.side = side
		self._model = model
		self.parent().setDragMode(QtGui.QGraphicsView.NoDrag)
		## set standard pen color
		self.pen = QtGui.QPen(QtCore.Qt.red)
		## Initialize variables
		self.lastScreenPos = QtCore.QPoint(0, 0)
		self.lastScenePos = 0
		self.selectionmode = False
		self.pointidx = 1
		self.rotangle = 0
		## Circle size
		self.markerSize = 10
		self.zValuesDict = {}

	def wheelEvent(self, event):
		## Scaling
		if event.delta() > 0:
			scalingFactor = 1.15
		else:
			scalingFactor = 1 / 1.15
		self.parent().scale(scalingFactor, scalingFactor)
		## Center on mouse pos only if mouse moved mor then 25px
		if (event.screenPos()-self.lastScreenPos).manhattanLength() > 25:
			self.parent().centerOn(event.scenePos().x(), event.scenePos().y())
			self.lastScenePos = event.scenePos()
		else:
			self.parent().centerOn(self.lastScenePos.x(), self.lastScenePos.y())
		## Save pos for precise scrolling, i.e. centering view only when mouse moved
		self.lastScreenPos = event.screenPos()

	def mousePressEvent(self, event):
		modifiers = QtGui.QApplication.keyboardModifiers()
		if event.button() == QtCore.Qt.LeftButton and modifiers != QtCore.Qt.ControlModifier:
			self.parent().setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
			## Model does not to be refreshed every time while navigating
			return
		elif event.button() == QtCore.Qt.LeftButton and modifiers == QtCore.Qt.ControlModifier:
			self.parent().setDragMode(QtGui.QGraphicsView.RubberBandDrag)
			self.selectionmode = True
			## Model does not have to be refreshed every time while selecting
			return
		elif event.button() == QtCore.Qt.RightButton:
			self.addCircle(event.scenePos().x(), event.scenePos().y())
		elif event.button() == QtCore.Qt.MiddleButton:
			item = self.itemAt(event.scenePos())
			if isinstance(item, QtGui.QGraphicsEllipseItem):
				self.removeItem(item)
				self.enumeratePoints()
		self.itemsToModel()

	def mouseReleaseEvent(self, event):
		## Reinitialize mouseReleaseEvent handling from QtGui.QGraphicsScene for item drag and drop feature
		super(QGraphicsSceneCustom, self).mouseReleaseEvent(event)
		## Only update position when single item is drag and dropped
		if self.selectedItems() and self.selectionmode is False:
			if debug is True: print clrmsg.DEBUG + 'New pos:', self.selectedItems()[0].x(), self.selectedItems()[0].y()
			## Only change color to orange when marker is moved in the 3D image (in order to remind reacquiring z coordinate)
			if '{0:b}'.format(self.imagetype)[-1] == '0':
				for item in self.selectedItems():
					if isinstance(item, QtGui.QGraphicsEllipseItem):
						self.zValuesDict[item] = [self.zValuesDict[item][0],(255, 190, 0)]  # orange
			self.clearSelection()
			self.itemsToModel()
		self.parent().setDragMode(QtGui.QGraphicsView.NoDrag)
		self.selectionmode = False

	def keyPressEvent(self, event):
		## Delete selected points (hold ctrl and draw rubber selection rectangle over the points you want to select)
		if event.key() == QtCore.Qt.Key_Delete:
			for item in self.selectedItems(): self.removeItem(item)
			self.itemsToModel()
		## Zoom in/out with +/- keys
		elif event.key() == QtCore.Qt.Key_Plus:
			self.parent().scale(1.15, 1.15)
		elif event.key() == QtCore.Qt.Key_Minus:
			self.parent().scale(1/1.15, 1/1.15)

	def addCircle(self,x,y,z=0.0):
		## First add at 0,0 then move to get position from item.scenePos() or .x() and y.()
		circle = self.addEllipse(-self.markerSize, -self.markerSize, self.markerSize*2, self.markerSize*2, self.pen)
		circle.setPos(x,y)
		circle.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
		circle.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
		## store placeholder z value in dictionary (QGraphicsitems cannot store additional (meta)data)
		## and flag for color (rgba)
		if self._z and z == 0:
			self.zValuesDict[circle] = [z,(255, 190, 0)]  # orange
		else:
			self.zValuesDict[circle] = [z,(0, 0, 0)]  # black
		## Reorder to have them in ascending order in the tableview
		QtGui.QGraphicsItem.stackBefore(circle, self.items()[-2])
		self.enumeratePoints()

		## Arrow test code
		# import time
		# def PointsInCircum(r,n=100):
		# 	return [(math.cos(2*math.pi/n*x)*r,math.sin(2*math.pi/n*x)*r) for x in xrange(0,n+1)]
		# loopcounter = 0
		# for i in PointsInCircum(3,n=10):
		# 	if loopcounter % 2 == 0:
		# 		color = QtCore.Qt.red
		# 	else:
		# 		color = QtCore.Qt.blue
		# 	self.addArrow((500,500),map(lambda a,b: a+b, i, (500,500)),arrowangle=25,color=color)
		# 	time.sleep(0.2)
		# 	self.parent().parent().refreshUI()
		# 	loopcounter += 1

	def addArrow(self,start,end,arrowangle=45,color=QtCore.Qt.red):
		dx, dy = map(lambda a,b: a-b, end, start)
		length = math.hypot(dx,dy)
		angle = -(math.asin(dy/length))
		if dx < 0:
			angle = math.radians(180) - angle
		if debug is True: print clrmsg.DEBUG + 'Radians:', angle, 'Degree', math.degrees(angle)
		path = QtGui.QPainterPath()
		path.moveTo(*start)
		path.lineTo(*end)
		path.arcMoveTo(
			end[0]-0.25*length, end[1]-0.25*length,
			0.5*length, 0.5*length,
			180-arrowangle+math.degrees(angle))
		path.lineTo(*end)
		path.arcMoveTo(
			end[0]-0.25*length, end[1]-0.25*length,
			0.5*length, 0.5*length,
			180+arrowangle+math.degrees(angle))
		path.lineTo(*end)
		self.addPath(path,QtGui.QPen(color))

	def deleteArrows(self):
		for item in self.items():
			if isinstance(item, QtGui.QGraphicsPathItem):
				self.removeItem(item)

	def enumeratePoints(self):
		## Remove numbering
		for item in self.items():
			if isinstance(item, QtGui.QGraphicsSimpleTextItem) or isinstance(item, QtGui.QGraphicsLineItem):
				self.removeItem(item)
		pointidx = 1
		for item in self.items():
			if isinstance(item, QtGui.QGraphicsEllipseItem):
				## Update marker size
				item.setRect(-self.markerSize, -self.markerSize, self.markerSize*2, self.markerSize*2)
				## Adding number
				nr = self.addSimpleText(str(pointidx),QtGui.QFont("Helvetica", pointSize=1.5*self.markerSize))
				nr.setParentItem(item)
				## Counter rotate number so it stays level
				nr.setRotation(-self.rotangle)
				## Convert degree to rad plus a 30 offset to place the number in the lower right corner of the marker
				radangle = math.radians(390-self.rotangle)
				## Number's position has to be angle dependant -> sin cos
				nr.setPos(math.cos(radangle)*self.markerSize,math.sin(radangle)*self.markerSize)
				# nr.setPen(self.pen) # outline
				nr.setBrush(QtCore.Qt.cyan)  # fill
				## Adding crosshair
				hline = self.addLine(-self.markerSize-2,0,self.markerSize+2,0)
				hline.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 128)))  # r,g,b,alpha, white transparent
				hline.setParentItem(item)
				## Counter rotate crosshair (horizontal line) so it stays level
				hline.setRotation(-self.rotangle)
				vline = self.addLine(0,-self.markerSize-2,0,self.markerSize+2)
				vline.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 128)))  # r,g,b,alpha, white transparent
				vline.setParentItem(item)
				## Counter rotate crosshair (vertical line) so it stays level
				vline.setRotation(-self.rotangle)
				## Counter
				pointidx += 1

	def itemsToModel(self):
		self._model.removeRows(0,self._model.rowCount())
		for item in self.items():
			if isinstance(item, QtGui.QGraphicsEllipseItem):
				x_item = QtGui.QStandardItem(str(item.x()))
				y_item = QtGui.QStandardItem(str(item.y()))
				z_item = QtGui.QStandardItem(str(self.zValuesDict[item][0]))
				# x_item.setBackground(QtGui.QColor(220,25,105))
				# y_item.setBackground(QtGui.QColor(50,220,175))
				# z_item.setBackground(QtGui.QColor(220,25,105))

				z_item.setForeground(QtGui.QColor(*self.zValuesDict[item][1]))

				x_item.setFlags(x_item.flags() & ~QtCore.Qt.ItemIsDropEnabled)
				y_item.setFlags(y_item.flags() & ~QtCore.Qt.ItemIsDropEnabled)
				z_item.setFlags(z_item.flags() & ~QtCore.Qt.ItemIsDropEnabled)
				items = [x_item, y_item, z_item]
				self._model.appendRow(items)
				self._model.setHeaderData(0, QtCore.Qt.Horizontal,'x')
				self._model.setHeaderData(1, QtCore.Qt.Horizontal,'y')
				self._model.setHeaderData(2, QtCore.Qt.Horizontal,'z')
		self.mainWidget.colorModels()


##############################
## Scatter Plot


class MatplotlibWidgetCustom(QtGui.QWidget):
	def __init__(self, parent=None):
		super(MatplotlibWidgetCustom, self).__init__(parent)
		self._setup = False
		# self.setupScatterCanvas(dpi)
		# self.scatterPlot(x='random',y='random',frame=True,framesize=6,xlabel="lol",ylabel="rofl")

	def setupScatterCanvas(self,width=5,height=5,dpi=72,toolbar=False):
		if self._setup is False:
			self.figure = Figure(figsize=(width,height),dpi=dpi)
			self.canvas = FigureCanvas(self.figure)
			layout = QtGui.QVBoxLayout()
			layout.addWidget(self.canvas)
			if toolbar is True:
				self.figure.set_figheight(height+0.5)
				self.toolbar = NavigationToolbar(self.canvas, self)
				layout.addWidget(self.toolbar)
			self.setLayout(layout)
			self._setup = True
		else:
			self.clearAll()
			self._setup = False
			self.setupScatterCanvas(width,height,dpi,toolbar)

	def clearAll(self):
		QtGui.QWidget().setLayout(self.layout())
		self._setup = False

	def scatterPlot(self,x='random',y='random',frame=False,framesize=None,xlabel="",ylabel=""):
		if x == 'random' or y == 'random':
			# the random data
			x = np.random.randn(1000)
			y = np.random.randn(1000)
		# the scatter plot:
		# if not hasattr(self,'subplotScatter'):
		self.subplotScatter = self.figure.add_subplot(111)
		self.subplotScatter.clear()
		self.subplotScatter.scatter(x, y)
		self.subplotScatter.set_aspect(1.)
		print x.min(), x.max(), y.min(), y.max()
		limit = max([abs(x.min()), abs(x.max()), abs(y.min()), abs(y.max())]) + 0.2
		print limit
		self.subplotScatter.set_xlim(-limit, limit)
		self.subplotScatter.set_ylim(-limit, limit)
		self.subplotScatter.set_xlabel(xlabel)
		self.subplotScatter.set_ylabel(ylabel)
		self.subplotScatter.xaxis.set_label_coords(0.1,0.08)
		self.subplotScatter.yaxis.set_label_coords(0.08,0.12)
		self.subplotScatter.plot([0], '+', mew=1, ms=10, c="red")

		if frame is True and framesize is not None:
			self.subplotScatter.add_patch(patches.Rectangle(
				(-framesize*0.5, -framesize*0.5), framesize, framesize, fill=False, edgecolor="red"))
		elif frame is True and framesize is None:
			print "Please specify frame size in px as e.g. framesize=1.86"

		# create new axes on the right and on the top of the current axes
		# The first argument of the new_vertical(new_horizontal) method is
		# the height (width) of the axes to be created in inches.
		self.divider = make_axes_locatable(self.subplotScatter)
		self.axHistx = self.divider.append_axes("top", size="25%", pad=0.1)
		self.axHisty = self.divider.append_axes("right", size="25%", pad=0.1)

		# # make some labels invisible
		# # plt.setp(self.axHistx.get_xticklabels() + self.axHisty.get_yticklabels(), visible=False)
		self.axHistx.set_xticklabels(self.axHistx.get_xticklabels(),visible=False)
		self.axHisty.set_yticklabels(self.axHisty.get_yticklabels(),visible=False)
		# self.axHistx.set_yticks([0,0.5,1])
		# self.axHisty.set_xticks([0,0.5,1])

		# now determine nice limits by hand:
		binwidth = 0.25
		xymax = np.max([np.max(np.fabs(x)), np.max(np.fabs(y))])
		lim = (int(xymax/binwidth) + 1) * binwidth

		bins = np.arange(-lim, lim + binwidth, binwidth)
		self.axHistx.hist(x, bins=bins)
		self.axHisty.hist(y, bins=bins, orientation='horizontal')

		# the xaxis of self.axHistx and yaxis of self.axHisty are shared with self.subplotScatter,
		# thus there is no need to manually adjust the xlim and ylim of these
		# axis.

		# self.axHistx.axis["bottom"].major_ticklabels.set_visible(False)
		for tl in self.axHistx.get_xticklabels():
			tl.set_visible(False)
		self.axHistx.set_yticks([])

		# self.axHisty.axis["left"].major_ticklabels.set_visible(False)
		for tl in self.axHisty.get_yticklabels():
			tl.set_visible(False)
		self.axHisty.set_xticks([])

		# self.figure.set_dpi(200)
		self.canvas.draw()

	def xyPlot(self,*args,**kwargs):
		self.subplotXY = self.figure.add_subplot(111)
		try:
			clear = kwargs.pop('clear')
		except:
			clear = False
		if clear is True:
			self.subplotXY.clear()
		self.subplotXY.plot(*args,**kwargs)
		leg = self.subplotXY.legend(fontsize='small')
		leg.get_frame().set_alpha(0.5)
		self.canvas.draw()

	def matshowPlot(self,mat=None,contour=None,labelContour=''):
		# import tifffile as tf
		n = len(self.figure.axes)
		if n < 2:
			for i in range(n):
				self.figure.axes[i].change_geometry(n+1, 1, i+1)
			# self.figure.subplots_adjust(hspace=0.5)
			self.figure.tight_layout()
			self.subplotMat = self.figure.add_subplot(n+1, 1, n+1)
		# self.subplotMat.plot(np.arange(100),np.random.random(100)*10)
		# mat = tf.imread('/Users/jan/Desktop/dot2.tif')
		self.subplotMat.clear()
		self.subplotMat.matshow(mat)
		self.subplotMat.contour(contour, cmap='Greys')
		self.subplotMat.text(
							0.95, 0.03, labelContour, fontsize=12, horizontalalignment='right',
							verticalalignment='bottom', transform=self.figure.transFigure)
		self.subplotMat.set_anchor('W')
		self.canvas.draw()


##############################
## QLineedit drops


class QLineEditFilePath(QtGui.QLineEdit):
	def __init__(self,parent):
		super(QLineEditFilePath, self).__init__(parent)
		self.setDragEnabled(True)
		if sys.platform == 'darwin':
			global objc
			global CF
			try:
				import objc
				import CoreFoundation as CF
				if debug is True: print clrmsg.DEBUG + '"objc" and "CoreFoundation" import successful'
			except Exception as e:
				if debug is True: print clrmsg.ERROR + str(e)
				objc = None

	def dragEnterEvent(self,event):
		urls = event.mimeData().urls()
		if (urls and urls[0].scheme() == 'file'):
			event.acceptProposedAction()

	def dragMoveEvent(self,event):
		urls = event.mimeData().urls()
		if (urls and urls[0].scheme() == 'file'):
			event.acceptProposedAction()

	def dropEvent(self,event):
		data = event.mimeData()
		urls = data.urls()
		if (urls and urls[0].scheme() == 'file'):
			# for some reason, this doubles up the intro slash
			filepath = str(urls[0].path())[1:]
			if filepath.startswith('.file/id=') and objc:
				if debug is True: print clrmsg.DEBUG + 'File id bug in PyQt4 for:', filepath
				filepath = self.getUrlFromLocalFileID(urls[0])
				if debug is True: print clrmsg.DEBUG + '						->', filepath
			elif filepath.startswith('.file/id=') and not objc:
				if debug is True:
					print clrmsg.DEBUG + (
						"File id bug in PyQt4 under mac. Please make sure that PyObjC is installed (pip install PyObjC).\n"
						"		  With PyObjC installed, this programm can work around this bug.\n"
						"\n"
						"		  Reference:\n"
						"		  http://stackoverflow.com/questions/34689562/pyqt-mimedata-filename")
			self.setText(filepath)

	## http://stackoverflow.com/questions/34689562/pyqt-mimedata-filename
	def getUrlFromLocalFileID(self, localFileID):
		localFileQString = QtCore.QString(localFileID.toLocalFile())
		relCFStringRef = CF.CFStringCreateWithCString(
			CF.kCFAllocatorDefault,
			localFileQString.toUtf8(),
			CF.kCFStringEncodingUTF8
			)
		relCFURL = CF.CFURLCreateWithFileSystemPath(
			CF.kCFAllocatorDefault,
			relCFStringRef,
			CF.kCFURLPOSIXPathStyle,
			False  # is directory
			)
		absCFURL = CF.CFURLCreateFilePathURL(
			CF.kCFAllocatorDefault,
			relCFURL,
			objc.NULL
			)
		return QtCore.QUrl(str(absCFURL[0])).toLocalFile()
