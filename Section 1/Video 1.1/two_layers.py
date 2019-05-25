from qgis.core import *
from qgis.gui import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

symbol = QgsFillSymbolV2()
symbol.deleteSymbolLayer(0)

symbol_layer_1 = QgsSimpleFillSymbolLayerV2()
symbol_layer_1.setFillColor(QColor("#e2fee2"))

symbol_layer_2 = QgsLinePatternFillSymbolLayer()
symbol_layer_2.setLineAngle(30)
symbol_layer_2.setDistance(2.0)
symbol_layer_2.setLineWidth(0.5)
symbol_layer_2.setColor(QColor("black"))

symbol.appendSymbolLayer(symbol_layer_1)
symbol.appendSymbolLayer(symbol_layer_2)

renderer = QgsSingleSymbolRendererV2(symbol)
layer = iface.activeLayer()
layer.setRendererV2(renderer)
layer.triggerRepaint()
