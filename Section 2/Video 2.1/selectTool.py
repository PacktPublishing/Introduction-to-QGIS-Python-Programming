from qgis.core import *
from qgis.gui import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class SelectTool(QgsMapToolIdentify):
    def __init__(self, mapCanvas, layer):
        QgsMapToolIdentify.__init__(self, mapCanvas)
        self.layer = layer
        self.setCursor(Qt.ArrowCursor)

    def canvasReleaseEvent(self, event):
        found_features = self.identify(event.x(), event.y(),
                                       self.TopDownStopAtFirst,
                                       self.VectorLayer)
        if len(found_features) > 0:
            layer = found_features[0].mLayer
            feature = found_features[0].mFeature
            layer.setSelectedFeatures([feature.id()])
        else:
            self.layer.removeSelection()

tool = SelectTool(iface.mapCanvas(), iface.activeLayer())
iface.mapCanvas().setMapTool(tool)
