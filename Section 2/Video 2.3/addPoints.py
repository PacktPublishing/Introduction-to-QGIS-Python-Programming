from qgis.core import *
from qgis.gui import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class AddPointTool(QgsMapTool):
    def __init__(self, canvas, layer):
        QgsMapTool.__init__(self, canvas)
        self.layer = layer
        self.setCursor(Qt.CrossCursor)

    def canvasReleaseEvent(self, event):
        point = self.toLayerCoordinates(self.layer, event.pos())

        fields = self.layer.dataProvider().fields()

        feature = QgsFeature()
        feature.setFields(fields)
        feature.setGeometry(QgsGeometry.fromPoint(point))

        self.layer.addFeature(feature)
        self.layer.updateExtents()
        self.layer.triggerRepaint()

canvas = iface.mapCanvas()
layer = iface.activeLayer()

layer.startEditing()
layer.triggerRepaint()
tool = AddPointTool(canvas, layer)
canvas.setMapTool(tool)
