import math
from qgis.core import *
from qgis.gui import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class GridLayer(QgsPluginLayer):
    def __init__(self):
        QgsPluginLayer.__init__(self, "GridLayer", "Grid Layer")
        self.setValid(True)
        self.setCrs(QgsCoordinateReferenceSystem(4326))
        self.setExtent(QgsRectangle(-180, 90, 180, 90))

    def draw(self, renderContext):
        painter = renderContext.painter()
        extent = renderContext.extent()

        xMin = int(math.floor(extent.xMinimum()))
        xMax = int(math.ceil(extent.xMaximum()))
        yMin = int(math.floor(extent.yMinimum()))
        yMax = int(math.ceil(extent.yMaximum()))

        pen = QPen()
        pen.setColor(QColor("light gray"))
        pen.setWidth(1.0)
        painter.setPen(pen)

        mapToPixel = renderContext.mapToPixel()

        for x in range(xMin, xMax+1):
            coord1 = mapToPixel.transform(x, yMin)
            coord2 = mapToPixel.transform(x, yMax)
            painter.drawLine(coord1.x(), coord1.y(),
                             coord2.x(), coord2.y())

        for y in range(yMin, yMax+1):
            coord1 = mapToPixel.transform(xMin, y)
            coord2 = mapToPixel.transform(xMax, y)
            painter.drawLine(coord1.x(), coord1.y(),
                             coord2.x(), coord2.y())

        return True


class GridLayerType(QgsPluginLayerType):
    def __init__(self):
        QgsPluginLayerType.__init__(self, "GridLayer")

    def createLayer(self):
        return GridLayer()


registry = QgsPluginLayerRegistry.instance()
registry.addPluginLayerType(GridLayerType())

layer = GridLayer()
QgsMapLayerRegistry.instance().addMapLayer(layer)
