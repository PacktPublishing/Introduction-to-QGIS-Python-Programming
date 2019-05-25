from qgis.core import *
from qgis.gui import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

symbol = QgsLineSymbolV2()
symbol.deleteSymbolLayer(0)

symbol_layer = QgsSimpleLineSymbolLayerV2()
symbol_layer.setWidth(4)
symbol_layer.setColor(QColor("#ffc409"))
symbol_layer.setPenCapStyle(Qt.FlatCap)
symbol.appendSymbolLayer(symbol_layer)

symbol_layer = QgsSimpleLineSymbolLayerV2()
symbol_layer.setWidth(2)
symbol_layer.setColor(QColor("#6c5008"))
symbol_layer.setPenCapStyle(Qt.FlatCap)
symbol.appendSymbolLayer(symbol_layer)

symbol_layer = QgsSimpleLineSymbolLayerV2()
symbol_layer.setWidth(1)
symbol_layer.setColor(QColor("white"))
symbol_layer.setPenStyle(Qt.DotLine)
symbol.appendSymbolLayer(symbol_layer)

renderer = QgsSingleSymbolRendererV2(symbol)
layer = iface.activeLayer()
layer.setRendererV2(renderer)
layer.triggerRepaint()
