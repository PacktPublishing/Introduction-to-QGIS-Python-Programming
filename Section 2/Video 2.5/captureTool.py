from qgis.core import *
from qgis.gui import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class CaptureTool(QgsMapTool):
    CAPTURE_LINE    = 1
    CAPTURE_POLYGON = 2

    def __init__(self, canvas, layer, onGeometryAdded, captureMode):
        QgsMapTool.__init__(self, canvas)
        self.canvas          = canvas
        self.layer           = layer
        self.onGeometryAdded = onGeometryAdded
        self.captureMode     = captureMode
        self.rubberBand      = None
        self.tempRubberBand  = None
        self.capturedPoints  = []
        self.capturing       = False
        self.setCursor(Qt.CrossCursor)

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.capturing:
                self.startCapturing()
            self.addVertex(event.pos())
        elif event.button() == Qt.RightButton:
            points = self.getCapturedGeometry()
            self.stopCapturing()
            if points != None:
                self.geometryCaptured(points)

    def canvasMoveEvent(self, event):
        if self.tempRubberBand != None and self.capturing:
            mapPt,layerPt = self.transformCoordinates(event.pos())
            self.tempRubberBand.movePoint(mapPt)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
            self.removeLastVertex()
            event.ignore()
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            points = self.getCapturedGeometry()
            self.stopCapturing()
            if points != None:
                self.geometryCaptured(points)

    def transformCoordinates(self, canvasPt):
        return (self.toMapCoordinates(canvasPt),
                self.toLayerCoordinates(self.layer, canvasPt))

    def startCapturing(self):
        color = QColor("red")
        color.setAlphaF(0.78)

        self.rubberBand = QgsRubberBand(self.canvas, self.bandType())
        self.rubberBand.setWidth(2)
        self.rubberBand.setColor(color)
        self.rubberBand.show()

        self.tempRubberBand = QgsRubberBand(self.canvas, self.bandType())
        self.tempRubberBand.setWidth(2)
        self.tempRubberBand.setColor(color)
        self.tempRubberBand.setLineStyle(Qt.DotLine)
        self.tempRubberBand.show()

        self.capturing = True

    def bandType(self):
        if self.captureMode == CaptureTool.CAPTURE_POLYGON:
            return QGis.Polygon
        else:
            return QGis.Line

    def stopCapturing(self):
        if self.rubberBand:
            self.canvas.scene().removeItem(self.rubberBand)
            self.rubberBand = None
        if self.tempRubberBand:
            self.canvas.scene().removeItem(self.tempRubberBand)
            self.tempRubberBand = None
        self.capturing = False
        self.capturedPoints = []
        self.canvas.refresh()

    def addVertex(self, canvasPt):
        mapPt,layerPt = self.transformCoordinates(canvasPt)

        self.rubberBand.addPoint(mapPt)
        self.canvas.clearCache()
        self.canvas.refresh()

        self.capturedPoints.append(layerPt)

        self.tempRubberBand.reset(self.bandType())
        if self.captureMode == CaptureTool.CAPTURE_LINE:
            self.tempRubberBand.addPoint(mapPt)
        elif self.captureMode == CaptureTool.CAPTURE_POLYGON:
            firstPt = self.rubberBand.getPoint(0, 0)
            self.tempRubberBand.addPoint(firstPt)
            self.tempRubberBand.movePoint(mapPt)
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
            self.tempRubberBand.reset(self.bandType())

        del self.capturedPoints[-1]

    def getCapturedGeometry(self):
        points = self.capturedPoints
        if self.captureMode == CaptureTool.CAPTURE_LINE:
            if len(points) < 2:
                return None
        if self.captureMode == CaptureTool.CAPTURE_POLYGON:
            if len(points) < 3:
                return None
        if self.captureMode == CaptureTool.CAPTURE_POLYGON:
            points.append(points[0]) # Close polygon.
        return points

    def geometryCaptured(self, layerCoords):
        if self.captureMode == CaptureTool.CAPTURE_LINE:
            geometry = QgsGeometry.fromPolyline(layerCoords)
        elif self.captureMode == CaptureTool.CAPTURE_POLYGON:
            geometry = QgsGeometry.fromPolygon([layerCoords])

        fields = self.layer.dataProvider().fields()

        feature = QgsFeature()
        feature.setFields(fields)
        feature.setGeometry(geometry)

        self.layer.addFeature(feature)
        self.layer.updateExtents()
        self.canvas.clearCache()
        self.canvas.refresh()

        self.onGeometryAdded()

canvas = iface.mapCanvas()
layer = iface.activeLayer()

def onCaptured():
    print("We captured a geometry")

layer.startEditing()
layer.triggerRepaint()
tool = CaptureTool(canvas, layer, onCaptured, CaptureTool.CAPTURE_LINE)
canvas.setMapTool(tool)
