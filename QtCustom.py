#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Title			: QtCustom{{project_name}}
# @Project			: 3DCTv2
# @Description		: Custom Qt classes
# @Author			: Jan Arnold
# @Email			: jan.arnold (at) coraxx.net
# @Credits			:
# @Maintainer		: Jan Arnold
# @Date				: 2016/02/27
# @Version			: 0.1
# @Status			: developement
# @Usage			: part of 3D Correlation Toolbox
# @Notes			: Some widgets in QT Designer are promoted to these classes
# @Python_version	: 2.7.10
# @Last Modified	: 2016/03/07 by {{author}}
# ============================================================================

from PyQt4 import QtCore, QtGui
import numpy as np

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.patches as patches
from mpl_toolkits.axes_grid1 import make_axes_locatable

import math
import clrmsg
import bead_pos

##############################
## QTableViewCustom


class QTableViewCustom(QtGui.QTableView):
	def __init__(self, parent=None,):
		## parent is mainWidget
		QtGui.QTableView.__init__(self,parent)
		self.parent = parent
		if hasattr(parent, "debug"):
			self.debug = parent.debug
			if self.debug is True: print clrmsg.DEBUG + 'Debug bool inherited'
		else:
			self.debug = True
			if self.debug is True: print clrmsg.DEBUG + 'Debug messages enabled'
		self._drop = False

		## Enable Drag'n'Drop
		self.setDragDropOverwriteMode(False)
		self.setDragEnabled(True)
		self.setDragDropMode(QtGui.QAbstractItemView.InternalMove)

		'''associated model and scene are passed from correlation_widget and are available as self._model and self._scene'''

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
		if self.debug is True: print clrmsg.DEBUG + "Update items check - Nr. of items/rows:", len(items), self._model.rowCount()
		if len(items) == self._model.rowCount():
			row = 0
			for item in items:
				if self.debug is True:
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
			cmGetZ = QtGui.QAction('get z', self)
			cmGetZ.triggered.connect(self.getz)
			cmGetZopt = QtGui.QAction('get z optimized', self)
			cmGetZopt.triggered.connect(lambda: self.getz(optimize=True))
			if self.img is None:
				cmGetZ.setEnabled(False)
				cmGetZopt.setEnabled(False)
			self.contextMenu = QtGui.QMenu(self)
			self.contextMenu.addAction(cmDelete)
			self.contextMenu.addAction(cmGetZ)
			self.contextMenu.addAction(cmGetZopt)
			self.contextMenu.popup(QtGui.QCursor.pos())

	def getz(self,optimize=False):
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
				if self.debug is True:
					print clrmsg.DEBUG + 'Row:', row, '|', \
						self._model.data(self._model.index(row, 0)).toString(),\
						self._model.data(self._model.index(row, 1)).toString(),\
						self._model.data(self._model.index(row, 2)).toString()
				x = float(self._model.data(self._model.index(row, 0)).toString())
				y = float(self._model.data(self._model.index(row, 1)).toString())

				if optimize is False:
					z = bead_pos.getz(x,y,self.img,n=None)
					# z = 45
					print self.img.shape, z
					if 0 <= z <= self.img.shape[-3]:
						self._scene.zValuesDict[activeitems[row]][1] = (0,0,0)
						self._model.itemFromIndex(self._model.index(row, 2)).setForeground(QtCore.Qt.black)
					else:
						self._scene.zValuesDict[activeitems[row]][1] = (255,0,0)
						self._model.itemFromIndex(self._model.index(row, 2)).setForeground(QtCore.Qt.red)
					self._model.itemFromIndex(self._model.index(row, 2)).setText(str(z))
				elif optimize is True:
					x,y,z = bead_pos.getz(x,y,self.img,n=None,optimize=True)
					# x,y,z = 50,50,90
					print self.img.shape, x,y,z
					if 0 <= x <= self.img.shape[-1] and 0 <= y <= self.img.shape[-2] and 0 <= z <= self.img.shape[-3]:
						self._scene.zValuesDict[activeitems[row]][1] = (255,0,0)
						self._model.itemFromIndex(self._model.index(row, 2)).setForeground(QtCore.Qt.black)
					else:
						self._scene.zValuesDict[activeitems[row]][1] = (0,0,0)
						self._model.itemFromIndex(self._model.index(row, 2)).setForeground(QtCore.Qt.red)
					self._model.itemFromIndex(self._model.index(row, 0)).setText(str(x))
					self._model.itemFromIndex(self._model.index(row, 1)).setText(str(y))
					self._model.itemFromIndex(self._model.index(row, 2)).setText(str(z))

												##################### END #####################
												#######          Update items           #######
												###############################################

##############################
## QStandardItemModelCustom


class QStandardItemModelCustom(QtGui.QStandardItemModel):
	def __init__(self, parent=None):
		QtGui.QStandardItemModel.__init__(self,parent)
		self.parent = parent

	def dropMimeData(self,data,action,row,column,parent):
		return QtGui.QStandardItemModel.dropMimeData(self,data,action,row,0,parent)


##############################
## QGraphicsSceneCustom

class QGraphicsSceneCustom(QtGui.QGraphicsScene):
	def __init__(self, parent=None,side=None,model=None):
		## parent is QGraphicsView
		QtGui.QGraphicsScene.__init__(self,parent)
		self.parent = parent
		self.side = side
		self._model = model
		self.parent.setDragMode(QtGui.QGraphicsView.NoDrag)
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
			# print 'New pos:', self.selectedItems()[0].x(), self.selectedItems()[0].y()
			for item in self.selectedItems():
				if isinstance(item, QtGui.QGraphicsEllipseItem):
					self.zValuesDict[item] = [self.zValuesDict[item][0],(255, 190, 0)]  # orange
			self.clearSelection()
			self.itemsToModel()
		self.parent.setDragMode(QtGui.QGraphicsView.NoDrag)
		self.selectionmode = False

	def keyPressEvent(self, event):
		## Delete selected points (hold ctrl and draw rubber selection rectangle over the points you want to select)
		if event.key() == QtCore.Qt.Key_Delete:
			for item in self.selectedItems(): self.removeItem(item)
			self.itemsToModel()
		## Zoom in/out with +/- keys
		elif event.key() == QtCore.Qt.Key_Plus:
			self.parent.scale(1.15, 1.15)
		elif event.key() == QtCore.Qt.Key_Minus:
			self.parent.scale(1/1.15, 1/1.15)

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

				z_item.setForeground(QtGui.QColor(*self.zValuesDict[item][1]))

				x_item.setFlags(x_item.flags() & ~QtCore.Qt.ItemIsDropEnabled)
				y_item.setFlags(y_item.flags() & ~QtCore.Qt.ItemIsDropEnabled)
				z_item.setFlags(z_item.flags() & ~QtCore.Qt.ItemIsDropEnabled)
				items = [x_item, y_item, z_item]
				self._model.appendRow(items)
				self._model.setHeaderData(0, QtCore.Qt.Horizontal,'x')
				self._model.setHeaderData(1, QtCore.Qt.Horizontal,'y')
				self._model.setHeaderData(2, QtCore.Qt.Horizontal,'z')


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
			self.axScatter = self.figure.add_subplot(111)
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

	def scatterPlot(self,x='random',y='random',frame=False,framesize=None,xlabel="",ylabel=""):
		if x == 'random' or y == 'random':
			# the random data
			x = np.random.randn(1000)
			y = np.random.randn(1000)
		# the scatter plot:
		self.axScatter.clear()
		self.axScatter.scatter(x, y)
		self.axScatter.set_aspect(1.)
		print x.min(), x.max(), y.min(), y.max()
		limit = max([abs(x.min()), abs(x.max()), abs(y.min()), abs(y.max())]) + 0.2
		print limit
		self.axScatter.set_xlim(-limit, limit)
		self.axScatter.set_ylim(-limit, limit)
		self.axScatter.set_xlabel(xlabel)
		self.axScatter.set_ylabel(ylabel)
		self.axScatter.xaxis.set_label_coords(0.1,0.08)
		self.axScatter.yaxis.set_label_coords(0.08,0.12)
		self.axScatter.plot([0], '+', mew=1, ms=10, c="red")

		if frame is True and framesize is not None:
			self.axScatter.add_patch(patches.Rectangle((-framesize*0.5, -framesize*0.5), framesize, framesize, fill=False, edgecolor="red"))
		elif frame is True and framesize is None:
			print "Please specify frame size in px as e.g. framesize=1.86"

		# create new axes on the right and on the top of the current axes
		# The first argument of the new_vertical(new_horizontal) method is
		# the height (width) of the axes to be created in inches.
		self.divider = make_axes_locatable(self.axScatter)
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

		# the xaxis of self.axHistx and yaxis of self.axHisty are shared with self.axScatter,
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
