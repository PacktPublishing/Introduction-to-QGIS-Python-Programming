from qgis.core import *
from qgis.gui import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

symbol = QgsFillSymbolV2.createSimple({'color' : "#ff8080"})

renderer = QgsSingleSymbolRendererV2(symbol)
layer = iface.activeLayer()
layer.setRendererV2(renderer)
layer.triggerRepaint()

