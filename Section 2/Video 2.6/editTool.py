from qgis.core import *
from qgis.gui import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import math

class EditTool(QgsMapTool):
    def __init__(self, canvas, layer, onGeometryChanged):
        QgsMapTool.__init__(self, canvas)
        self.canvas            = canvas
        self.layer             = layer
        self.onGeometryChanged = onGeometryChanged
        self.dragging          = False
        self.feature           = None
        self.vertex            = None

    def canvasPressEvent(self, event):
        feature = self.findFeatureAt(event.pos())
        if feature == None:
            return
        mapPt,layerPt = self.transformCoordinates(event.pos())
        geometry = feature.geometry()

        vertexCoord,vertex,prevVertex,nextVertex,distSquared = \
            geometry.closestVertex(layerPt)

        distance = math.sqrt(distSquared)

        tolerance = self.calcTolerance(event.pos())
        if distance > tolerance: return

        if event.button() == Qt.LeftButton:
            # Left click -> move vertex.
            self.dragging = True
            self.feature  = feature
            self.vertex   = vertex
            self.moveVertexTo(event.pos())
            self.canvas.refresh()
        elif event.button() == Qt.RightButton:
            # Right click -> delete vertex.
            self.deleteVertex(feature, vertex)
            self.canvas.refresh()

    def canvasMoveEvent(self, event):
        if self.dragging:
            self.moveVertexTo(event.pos())
            self.canvas.refresh()

    def canvasReleaseEvent(self, event):
        if self.dragging:
            self.moveVertexTo(event.pos())
            self.layer.updateExtents()
            self.canvas.refresh()
            self.dragging = False
            self.feature  = None
            self.vertex   = None

    def canvasDoubleClickEvent(self, event):
        feature = self.findFeatureAt(event.pos())
        if feature == None: return

        mapPt,layerPt = self.transformCoordinates(event.pos())
        geometry = feature.geometry()

        distSquared,closestPt,beforeVertex = \
            geometry.closestSegmentWithContext(layerPt)

        distance = math.sqrt(distSquared)
        tolerance = self.calcTolerance(event.pos())
        if distance > tolerance: return

        geometry.insertVertex(closestPt.x(), closestPt.y(), beforeVertex)
        self.layer.changeGeometry(feature.id(), geometry)
        self.canvas.refresh()

    def transformCoordinates(self, canvasPt):
        return (self.toMapCoordinates(canvasPt),
                self.toLayerCoordinates(self.layer, canvasPt))

    def findFeatureAt(self, pos):
        mapPt,layerPt = self.transformCoordinates(pos)
        tolerance = self.calcTolerance(pos)
        searchRect = QgsRectangle(layerPt.x() - tolerance,
                                  layerPt.y() - tolerance,
                                  layerPt.x() + tolerance,
                                  layerPt.y() + tolerance)

        request = QgsFeatureRequest()
        request.setFilterRect(searchRect)
        request.setFlags(QgsFeatureRequest.ExactIntersect)

        for feature in self.layer.getFeatures(request):
            return feature

        return None

    def calcTolerance(self, pos):
        pt1 = QPoint(pos.x(), pos.y())
        pt2 = QPoint(pos.x() + 10, pos.y())

        mapPt1,layerPt1 = self.transformCoordinates(pt1)
        mapPt2,layerPt2 = self.transformCoordinates(pt2)
        tolerance = layerPt2.x() - layerPt1.x()

        return tolerance

    def moveVertexTo(self, pos):
        geometry = self.feature.geometry()
        layerPt = self.toLayerCoordinates(self.layer, pos)
        geometry.moveVertex(layerPt.x(), layerPt.y(), self.vertex)
        self.layer.changeGeometry(self.feature.id(), geometry)
        self.onGeometryChanged()

    def deleteVertex(self, feature, vertex):
        geometry = feature.geometry()

        if geometry.wkbType() == QGis.WKBLineString:
            linestring = geometry.asPolyline()
            if len(linestring) <= 2:
                return
        elif geometry.wkbType() == QGis.WKBPolygon:
            polygon = geometry.asPolygon()
            exterior = polygon[0]
            if len(exterior) <= 4:
                return

        if geometry.deleteVertex(vertex):
            self.layer.changeGeometry(feature.id(), geometry)
            self.onGeometryChanged()

canvas = iface.mapCanvas()
layer = iface.activeLayer()

def onGeometryChanged():
    print("We changed a geometry")

layer.startEditing()
layer.triggerRepaint()
tool = EditTool(canvas, layer, onGeometryChanged)
canvas.setMapTool(tool)