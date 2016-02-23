from PyQt4 import QtCore, QtGui

class QTableViewCustom(QtGui.QTableView):
	def __init__(self, parent=None):
		QtGui.QTableView.__init__(self,parent)
		self.parent = parent

	def mousePressEvent(self,event):
		print "yeay"
		super(QTableViewCustom, self).mousePressEvent(event)

	def contextMenuEvent(self, event):
		self.menu = QtGui.QMenu(self)
		renameAction = QtGui.QAction('Rename', self)
		renameAction.triggered.connect(self.renameSlot)
		self.menu.addAction(renameAction)
		# add other required actions
		self.menu.popup(QtGui.QCursor.pos())

	def renameSlot(self):
		print "renaming slot called"

	def updateItems(self):
		row = 0
		for item in self._scene.items():
			if isinstance(item, QtGui.QGraphicsEllipseItem):
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

