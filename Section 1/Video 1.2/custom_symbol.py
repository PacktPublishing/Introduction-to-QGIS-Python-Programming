from qgis.core import *
from qgis.gui import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class CrossSymbolLayer(QgsMarkerSymbolLayerV2):
    def __init__(self, length=10.0, width=2.0):
        QgsMarkerSymbolLayerV2.__init__(self)
        self.length = length
        self.width  = width

    def layerType(self):
        return "Cross"

    def properties(self):
        return {'length' : self.length,
                 'width' : self.width}

    def clone(self):
        return CrossSymbolLayer(self.length,
                                self.width)

    def startRender(self, context):
        self.pen = QPen()
        self.pen.setWidth(self.width)

    def stopRender(self, context):
        self.pen = None

    def renderPoint(self, point, context):
        left = point.x() - self.length
        right = point.x() + self.length
        bottom = point.y() - self.length
        top = point.y() + self.length

        if context.selected():
            self.pen.setColor(context.selectionColor())
        else:
            self.pen.setColor(self.color())

        painter = context.renderContext().painter()
        painter.setPen(self.pen)
        painter.drawLine(left, bottom, right, top)
        painter.drawLine(right, bottom, left, top)


class CrossSymbolLayerWidget(QgsSymbolLayerV2Widget):
    def __init__(self, parent=None):
        QgsSymbolLayerV2Widget.__init__(self, parent)
        self.layer = None

        self.lengthField = QSpinBox(self)
        self.lengthField.setMinimum(1)
        self.lengthField.setMaximum(100)
        self.connect(self.lengthField,
                     SIGNAL("valueChanged(int)"),
                     self.lengthChanged)

        self.widthField = QSpinBox(self)
        self.widthField.setMinimum(1)
        self.widthField.setMaximum(100)
        self.connect(self.widthField,
                     SIGNAL("valueChanged(int)"),
                     self.widthChanged)

        self.form = QFormLayout()
        self.form.addRow("Length", self.lengthField)
        self.form.addRow("Width",  self.widthField)

        self.setLayout(self.form)

    def setSymbolLayer(self, layer):
        if layer.layerType() == "Cross":
            self.layer = layer
            self.lengthField.setValue(layer.length)
            self.widthField.setValue(layer.width)

    def symbolLayer(self):
        return self.layer

    def lengthChanged(self, n):
        self.layer.length = n
        self.emit(SIGNAL("changed()"))

    def widthChanged(self, n):
        self.layer.width = n
        self.emit(SIGNAL("changed()"))


class CrossSymbolLayerMetadata(QgsSymbolLayerV2AbstractMetadata):
    def __init__(self):
        QgsSymbolLayerV2AbstractMetadata.__init__(self,
                                                  "Cross",
                                                  "Cross Marker",
                                                  QgsSymbolV2.Marker)

    def createSymbolLayer(self, properties):
        if "length" in properties:
            length = int(properties['length'])
        else:
            length = 10
        if "width" in properties:
            width = int(properties['width'])
        else:
            width = 2
        return CrossSymbolLayer(length, width)

    def createSymbolLayerWidget(self, layer):
        return CrossSymbolLayerWidget()


registry = QgsSymbolLayerV2Registry.instance()
registry.addSymbolLayerType(CrossSymbolLayerMetadata())
