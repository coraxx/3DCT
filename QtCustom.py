from PyQt4 import QtCore, QtGui
import clrmsg
##############################
## QTableViewCustom

class QTableViewCustom(QtGui.QTableView):
	def __init__(self, parent=None):
		QtGui.QTableView.__init__(self,parent)
		self.parent = parent
		self.debug = True
		self._drop = False

		## Enable Drag'n'Drop
		self.setDragDropOverwriteMode(False)
		self.setDragEnabled(True)
		self.setDragDropMode(QtGui.QAbstractItemView.InternalMove)

	def mouseMoveEvent(self,event):
		super(QTableViewCustom, self).mouseMoveEvent(event)
		## Drop Flag to trigger item update only when there was a row move
		if self._drop == True:
			self.updateItems()
			self._drop = False

	def dropEvent(self,event):
		## Drop Flag to trigger item update only when there was a row move
		self._drop = True
		super(QTableViewCustom, self).dropEvent(event)

	# def contextMenuEvent(self, event):
	# 	self.menu = QtGui.QMenu(self)
	# 	renameAction = QtGui.QAction('Rename', self)
	# 	renameAction.triggered.connect(self.renameSlot)
	# 	self.menu.addAction(renameAction)
	# 	# add other required actions
	# 	self.menu.popup(QtGui.QCursor.pos())

	# def renameSlot(self):
	# 	print "renaming slot called"

												###############################################
												#######          Update items           #######
												#################### START ####################
	def updateItems(self):
		items = []
		for item in self._scene.items():
			if isinstance(item, QtGui.QGraphicsEllipseItem):
				items.append(item)
		if self.debug == True: print clrmsg.DEBUG + "Update items check - Nr. of items/rows:", len(items), self._model.rowCount()
		if len(items) == self._model.rowCount():
			row = 0
			for item in items:
				if self.debug == True: print clrmsg.DEBUG + 'Row:', row, '|', self._model.data(self._model.index(row, 0)).toString(),self._model.data(self._model.index(row, 1)).toString()
				item.setPos(float(self._model.data(self._model.index(row, 0)).toString()),float(self._model.data(self._model.index(row, 1)).toString()))
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
		self.cs = 20

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



