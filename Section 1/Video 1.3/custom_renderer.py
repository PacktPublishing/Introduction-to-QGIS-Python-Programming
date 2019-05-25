from qgis.core import *
from qgis.gui import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import random


class RedGreenBlueRenderer(QgsFeatureRendererV2):
    def __init__(self):
        QgsFeatureRendererV2.__init__(self, "RedGreenBlueRenderer")

        self.redSymbol = QgsMarkerSymbolV2.createSimple({})
        self.redSymbol.setColor(QColor("Red"))

        self.greenSymbol = QgsMarkerSymbolV2.createSimple({})
        self.greenSymbol.setColor(QColor("Green"))

        self.blueSymbol = QgsMarkerSymbolV2.createSimple({})
        self.blueSymbol.setColor(QColor("Blue"))

    def clone(self):
        return RedGreenBlueRenderer()

    def startRender(self, context, layer):
        self.redSymbol.startRender(context)
        self.greenSymbol.startRender(context)
        self.blueSymbol.startRender(context)

    def stopRender(self, context):
        self.redSymbol.stopRender(context)
        self.greenSymbol.stopRender(context)
        self.blueSymbol.stopRender(context)

    def symbolForFeature(self, feature):
        color = random.choice(["RED", "GREEN", "BLUE"])
        if color == "RED":
            return self.redSymbol
        elif color == "GREEN":
            return self.greenSymbol
        else:
            return self.blueSymbol

    def usedAttributes(self):
        return []


renderer = RedGreenBlueRenderer()
layer = iface.activeLayer()
layer.setRendererV2(renderer)
layer.triggerRepaint()
