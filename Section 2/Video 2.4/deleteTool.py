from qgis.core import *
from qgis.gui import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class DeleteTool(QgsMapToolIdentify):
    def __init__(self, mapCanvas, layer):
        QgsMapToolIdentify.__init__(self, mapCanvas)
        self.layer      = layer
        self.feature_id = None
        self.setCursor(Qt.CrossCursor)

    def canvasPressEvent(self, event):
        found_features = self.identify(event.x(), event.y(),
                                       self.TopDownStopAtFirst,
                                       self.VectorLayer)
        if len(found_features) > 0:
            self.feature_id = found_features[0].mFeature.id()

    def canvasReleaseEvent(self, event):
        found_features = self.identify(event.x(), event.y(),
                                       self.TopDownStopAtFirst,
                                       self.VectorLayer)
        if len(found_features) > 0:
            if self.feature_id == found_features[0].mFeature.id():
                self.layer.deleteFeature(self.feature_id)
                self.canvas().refresh()

canvas = iface.mapCanvas()
layer  = iface.activeLayer()
tool = DeleteTool(canvas, layer)
iface.mapCanvas().setMapTool(tool)
