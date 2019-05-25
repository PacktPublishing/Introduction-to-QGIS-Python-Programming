from qgis.core import *
from qgis.gui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from constants import *

import math

class MapToolMixin:
    def setLayer(self, layer):
        self.layer = layer

    def transformCoordinates(self, screenPt):
        return (self.toMapCoordinates(screenPt),
                self.toLayerCoordinates(self.layer, screenPt))

    def calcTolerance(self, pos):
        pt1 = QPoint(pos.x(), pos.y())
        pt2 = QPoint(pos.x() + 10, pos.y())

        mapPt1,layerPt1 = self.transformCoordinates(pt1)
        mapPt2,layerPt2 = self.transformCoordinates(pt2)
        tolerance = layerPt2.x() - layerPt1.x()

        return tolerance

    def findFeatureAt(self, pos, exclude_feature=None):
        mapPt,layerPt = self.transformCoordinates(pos)
        tolerance     = self.calcTolerance(pos)

        searchRect = QgsRectangle(layerPt.x() - tolerance,
                                  layerPt.y() - tolerance,
                                  layerPt.x() + tolerance,
                                  layerPt.y() + tolerance)

        request = QgsFeatureRequest()
        request.setFilterRect(searchRect)
        request.setFlags(QgsFeatureRequest.ExactIntersect)

        for feature in self.layer.getFeatures(request):
            if exclude_feature != None:
                if feature.id() == exclude_feature.id():
                    continue
            return feature

        return None

    def findVertexAt(self, feature, pos):
        mapPt,layerPt = self.transformCoordinates(pos)
        tolerance     = self.calcTolerance(pos)

        vertexCoord,vertex,prevVertex,nextVertex,distSquared = \
                feature.geometry().closestVertex(layerPt)

        distance = math.sqrt(distSquared)
        if distance > tolerance:
            return None
        else:
            return vertex

    def snapToNearestVertex(self, pos, exclude_feature=None):
        mapPt,layerPt = self.transformCoordinates(pos)
        feature = self.findFeatureAt(pos, exclude_feature)
        if feature == None: return layerPt

        vertex = self.findVertexAt(feature, pos)
        if vertex == None: return layerPt

        return feature.geometry().vertexAt(vertex)


class PanTool(QgsMapTool):
    def __init__(self, mapCanvas):
        QgsMapTool.__init__(self, mapCanvas)
        self.setCursor(Qt.OpenHandCursor)
        self.dragging = False


    def canvasMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.dragging = True
            self.canvas().panAction(event)


    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragging:
            self.canvas().panActionEnd(event.pos())
            self.dragging = False


class AddTrackTool(QgsMapTool, MapToolMixin):
    def __init__(self, canvas, layer, onTrackAdded):
        QgsMapTool.__init__(self, canvas)

        self.canvas         = canvas
        self.onTrackAdded   = onTrackAdded
        self.rubberBand     = None
        self.tempRubberBand = None
        self.capturedPoints = []
        self.capturing      = False

        self.setLayer(layer)
        self.setCursor(Qt.CrossCursor)

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.capturing:
                self.startCapturing()
            self.addVertex(event.pos())
        elif event.button() == Qt.RightButton:
            points = self.getCapturedPoints()
            self.stopCapturing()
            if points != None:
                self.pointsCaptured(points)

    def canvasMoveEvent(self, event):
        if self.tempRubberBand != None and self.capturing:
            mapPt,layerPt = self.transformCoordinates(event.pos())
            self.tempRubberBand.movePoint(mapPt)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
            self.removeLastVertex()
            event.ignore()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            points = self.getCapturedPoints()
            self.stopCapturing()
            if points != None:
                self.pointsCaptured(points)

    def startCapturing(self):
        color = QColor("red")
        color.setAlphaF(0.78)

        self.rubberBand = QgsRubberBand(self.canvas, QGis.Line)
        self.rubberBand.setWidth(2)
        self.rubberBand.setColor(color)
        self.rubberBand.show()

        self.tempRubberBand = QgsRubberBand(self.canvas, QGis.Line)
        self.tempRubberBand.setWidth(2)
        self.tempRubberBand.setColor(color)
        self.tempRubberBand.setLineStyle(Qt.DotLine)
        self.tempRubberBand.show()

        self.capturing = True

    def stopCapturing(self):
        if self.rubberBand != None:
            self.canvas.scene().removeItem(self.rubberBand)
            self.rubberBand = None

        if self.tempRubberBand != None:
            self.canvas.scene().removeItem(self.tempRubberBand)
            self.tempRubberBand = None

        self.capturing = False
        self.capturedPoints = []
        self.canvas.refresh()

    def addVertex(self, canvasPoint):
        snapPt = self.snapToNearestVertex(canvasPoint)
        mapPt = self.toMapCoordinates(self.layer, snapPt)

        self.rubberBand.addPoint(mapPt)
        self.canvas.clearCache()
        self.canvas.refresh()

        self.capturedPoints.append(snapPt)

        self.tempRubberBand.reset(QGis.Line)
        self.tempRubberBand.addPoint(mapPt)

    def removeLastVertex(self):
        if not self.capturing: return

        bandSize     = self.rubberBand.numberOfVertices()
        tempBandSize = self.tempRubberBand.numberOfVertices()
        numPoints    = len(self.capturedPoints)

        if bandSize < 1 or numPoints < 1:
            return

        self.rubberBand.removePoint(-1)

        if bandSize > 1:
            if tempBandSize > 1:
                point = self.rubberBand.getPoint(0, bandSize-2)
                self.tempRubberBand.movePoint(tempBandSize-2, point)
        else:
            self.tempRubberBand.reset(QGis.Line)

        del self.capturedPoints[-1]

    def getCapturedPoints(self):
        if len(self.capturedPoints) < 2:
            return None
        else:
            return self.capturedPoints

    def pointsCaptured(self, points):
        fields = self.layer.dataProvider().fields()

        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromPolyline(points))
        feature.setFields(fields)
        feature.setAttribute("type",      TRACK_TYPE_ROAD)
        feature.setAttribute("status",    TRACK_STATUS_OPEN)
        feature.setAttribute("direction", TRACK_DIRECTION_BOTH)

        self.layer.addFeature(feature)
        self.layer.updateExtents()
        self.onTrackAdded()


class EditTrackTool(QgsMapTool, MapToolMixin):
    def __init__(self, canvas, layer, onTrackEdited):
        QgsMapTool.__init__(self, canvas)
        self.onTrackEdited = onTrackEdited
        self.dragging      = False
        self.feature       = None
        self.vertex        = None
        self.setLayer(layer)
        self.setCursor(Qt.CrossCursor)

    def canvasPressEvent(self, event):
        feature = self.findFeatureAt(event.pos())
        if feature == None:
            return

        vertex = self.findVertexAt(feature, event.pos())
        if vertex == None:
            return

        if event.button() == Qt.LeftButton:
            # Left click -> move vertex.
            self.dragging = True
            self.feature  = feature
            self.vertex   = vertex
            self.moveVertexTo(event.pos())
            self.canvas().refresh()
        elif event.button() == Qt.RightButton:
            # Right click -> delete vertex.
            self.deleteVertex(feature, vertex)
            self.canvas().refresh()

    def canvasMoveEvent(self, event):
        if self.dragging:
            self.moveVertexTo(event.pos())
            self.canvas().refresh()

    def canvasReleaseEvent(self, event):
        if self.dragging:
            self.moveVertexTo(event.pos())
            self.layer.updateExtents()
            self.canvas().refresh()
            self.dragging = False
            self.feature  = None
            self.vertex   = None

    def canvasDoubleClickEvent(self, event):
        feature = self.findFeatureAt(event.pos())
        if feature == None:
            return

        mapPt,layerPt = self.transformCoordinates(event.pos())
        geometry      = feature.geometry()

        distSquared,closestPt,beforeVertex = \
                geometry.closestSegmentWithContext(layerPt)

        distance = math.sqrt(distSquared)
        tolerance = self.calcTolerance(event.pos())
        if distance > tolerance: return

        geometry.insertVertex(closestPt.x(), closestPt.y(), beforeVertex)
        self.layer.changeGeometry(feature.id(), geometry)
        self.onTrackEdited()
        self.canvas().refresh()

    def moveVertexTo(self, pos):
        snappedPt = self.snapToNearestVertex(pos, self.feature)
        geometry  = self.feature.geometry()
        layerPt   = self.toLayerCoordinates(self.layer, pos)

        geometry.moveVertex(snappedPt.x(), snappedPt.y(), self.vertex)
        self.layer.changeGeometry(self.feature.id(), geometry)
        self.onTrackEdited()

    def deleteVertex(self, feature, vertex):
        geometry = feature.geometry()

        linestring = geometry.asPolyline()
        if len(linestring) <= 2:
            return

        if geometry.deleteVertex(vertex):
            self.layer.changeGeometry(feature.id(), geometry)
            self.onTrackEdited()


class DeleteTrackTool(QgsMapTool, MapToolMixin):
    def __init__(self, canvas, layer, onTrackDeleted):
        QgsMapTool.__init__(self, canvas)
        self.onTrackDeleted = onTrackDeleted
        self.feature_id     = None
        self.setLayer(layer)
        self.setCursor(Qt.CrossCursor)

    def canvasPressEvent(self, event):
        feature = self.findFeatureAt(event.pos())
        if feature != None:
            self.feature_id = feature.id()
        else:
            self.feature_id = None

    def canvasReleaseEvent(self, event):
        feature = self.findFeatureAt(event.pos())
        if feature != None and feature.id() == self.feature_id:
            self.layer.deleteFeature(feature.id())
            self.onTrackDeleted()


class GetInfoTool(QgsMapTool, MapToolMixin):
    def __init__(self, canvas, layer, onGetInfo):
        QgsMapTool.__init__(self, canvas)
        self.onGetInfo = onGetInfo
        self.setLayer(layer)
        self.setCursor(Qt.WhatsThisCursor)

    def canvasReleaseEvent(self, event):
        if event.button() != Qt.LeftButton: return
        feature = self.findFeatureAt(event.pos())
        if feature != None:
            self.onGetInfo(feature)


class SelectVertexTool(QgsMapTool, MapToolMixin):
    def __init__(self, canvas, trackLayer, onVertexSelected):
        QgsMapTool.__init__(self, canvas)
        self.onVertexSelected = onVertexSelected
        self.setLayer(trackLayer)
        self.setCursor(Qt.CrossCursor)


    def canvasReleaseEvent(self, event):
        feature = self.findFeatureAt(event.pos())
        if feature != None:
            vertex = self.findVertexAt(feature, event.pos())
            if vertex != None:
                self.onVertexSelected(feature, vertex)

