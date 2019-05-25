from qgis.core import *
from qgis.gui import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

symbol = QgsFillSymbolV2()
symbol.deleteSymbolLayer(0)

symbol_layer = QgsGradientFillSymbolLayerV2()
symbol_layer.setColor2(QColor("dark gray"))
symbol_layer.setColor(QColor("white"))
symbol.appendSymbolLayer(symbol_layer)

symbol_layer = QgsLinePatternFillSymbolLayer()
symbol_layer.setColor(QColor(0, 0, 0, 20))
symbol_layer.setLineWidth(2)
symbol_layer.setDistance(4)
symbol_layer.setLineAngle(70)
symbol.appendSymbolLayer(symbol_layer)

renderer = QgsSingleSymbolRendererV2(symbol)
layer = iface.activeLayer()
layer.setRendererV2(renderer)
layer.triggerRepaint()

