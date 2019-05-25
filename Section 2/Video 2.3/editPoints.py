from qgis.core import *
from qgis.gui import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class EditPointTool(QgsMapToolIdentify):
    def __init__(self, canvas, layer):
        QgsMapTool.__init__(self, canvas)
        self.layer      = layer
        self.dragging   = False
        self.feature_id = None
        self.setCursor(Qt.CrossCursor)

    def canvasPressEvent(self, event):
        found_features = self.identify(event.x(), event.y(),
                                       [self.layer],
                                       self.TopDownAll)
        if len(found_features) > 0:
            self.dragging   = True
            self.feature_id = found_features[0].mFeature.id()
        else:
            self.dragging   = False
            self.feature_id = None

    def canvasMoveEvent(self, event):
        if self.dragging:
            point = self.toLayerCoordinates(self.layer, event.pos())
            geometry = QgsGeometry.fromPoint(point)

            self.layer.changeGeometry(self.feature_id, geometry)
            self.canvas().refresh()

    def canvasReleaseEvent(self, event):
        self.dragging  = False
        self.feature_id = None

canvas = iface.mapCanvas()
layer = iface.activeLayer()

layer.startEditing()
layer.triggerRepaint()
tool = EditPointTool(canvas, layer)
canvas.setMapTool(tool)
