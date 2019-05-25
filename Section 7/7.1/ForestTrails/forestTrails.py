import os
import os.path
import sys

from qgis.core import *
from qgis.gui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ui_mainWindow import Ui_MainWindow

import resources
from constants import *
from mapTools import *

class ForestTrailsWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.setupUi(self)

        self.connect(self.actionZoomIn, SIGNAL("triggered()"), self.zoomIn)
        self.connect(self.actionZoomOut, SIGNAL("triggered()"), self.zoomOut)
        self.connect(self.actionQuit, SIGNAL("triggered()"), self.quit)
        self.connect(self.actionPan, SIGNAL("triggered()"), self.setPanMode)
        self.connect(self.actionEdit, SIGNAL("triggered()"), self.setEditMode)
        self.connect(self.actionAddTrack, SIGNAL("triggered()"), self.addTrack)
        self.connect(self.actionEditTrack, SIGNAL("triggered()"),
                     self.editTrack)
        self.connect(self.actionDeleteTrack, SIGNAL("triggered()"),
                     self.deleteTrack)
        self.connect(self.actionGetInfo, SIGNAL("triggered()"),
                     self.getInfo)
        self.connect(self.actionSetStartPoint, SIGNAL("triggered()"),
                     self.setStartPoint)
        self.connect(self.actionSetEndPoint, SIGNAL("triggered()"),
                     self.setEndPoint)
        self.connect(self.actionFindShortestPath, SIGNAL("triggered()"),
                     self.findShortestPath)

        self.mapCanvas = QgsMapCanvas()
        self.mapCanvas.useImageToRender(False)
        self.mapCanvas.setCanvasColor(Qt.white)
        self.mapCanvas.show()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.mapCanvas)
        self.centralWidget.setLayout(layout)

        self.editing  = False
        self.modified = False


    def setupDatabase(self):
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        db_name = os.path.join(cur_dir, "data", "tracks.sqlite")
        if not os.path.exists(db_name):
            fields = QgsFields()
            fields.append(QgsField("id",        QVariant.Int))
            fields.append(QgsField("type",      QVariant.String))
            fields.append(QgsField("name",      QVariant.String))
            fields.append(QgsField("direction", QVariant.String))
            fields.append(QgsField("status",    QVariant.String))

            crs = QgsCoordinateReferenceSystem(4326,
                    QgsCoordinateReferenceSystem.EpsgCrsId)

            writer = QgsVectorFileWriter(db_name, "utf-8", fields,
                                         QGis.WKBLineString,
                                         crs, "SQLite",
                                         ["SPATIALITE=YES"])
            if writer.hasError() != QgsVectorFileWriter.NoError:
                print "Error creating tracks database!"

            del writer


    def setupMapLayers(self):
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        layers = []

        # Setup the base layer.

        filename = os.path.join(cur_dir, "data", "basemap.tif")
        self.baseLayer = QgsRasterLayer(filename, "basemap")
        QgsMapLayerRegistry.instance().addMapLayer(self.baseLayer)
        layers.append(QgsMapCanvasLayer(self.baseLayer))

        # Setup the track layer.

        uri = QgsDataSourceURI()
        uri.setDatabase(os.path.join(cur_dir, "data", "tracks.sqlite"))
        uri.setDataSource("", "tracks", "GEOMETRY")

        self.trackLayer = QgsVectorLayer(uri.uri(), "Tracks",
                                         "spatialite")
        QgsMapLayerRegistry.instance().addMapLayer(self.trackLayer)
        layers.append(QgsMapCanvasLayer(self.trackLayer))

        # Setup the shortest path layer.

        self.shortestPathLayer = QgsVectorLayer("LineString?crs=EPSG:4326",
                                                "shortestPathLayer", "memory")
        QgsMapLayerRegistry.instance().addMapLayer(self.shortestPathLayer)
        layers.append(QgsMapCanvasLayer(self.shortestPathLayer))

        # Setup the start point layer.

        self.startPointLayer = QgsVectorLayer("Point?crs=EPSG:4326",
                                              "startPointLayer", "memory")
        QgsMapLayerRegistry.instance().addMapLayer(self.startPointLayer)
        layers.append(QgsMapCanvasLayer(self.startPointLayer))

        # Setup the end point layer.

        self.endPointLayer = QgsVectorLayer("Point?crs=EPSG:4326",
                                            "endPointLayer", "memory")
        QgsMapLayerRegistry.instance().addMapLayer(self.endPointLayer)
        layers.append(QgsMapCanvasLayer(self.endPointLayer))

        # Add all the layers to the map canvas.

        layers.reverse()
        self.mapCanvas.setLayerSet(layers)
        self.mapCanvas.setExtent(self.baseLayer.extent())


    def setupRenderers(self):
        # Setup the renderer for our track layer.

        root_rule = QgsRuleBasedRendererV2.Rule(None)

        for track_type in (TRACK_TYPE_ROAD, TRACK_TYPE_WALKING,
                           TRACK_TYPE_BIKE, TRACK_TYPE_HORSE):
            if track_type == TRACK_TYPE_ROAD:
                width = ROAD_WIDTH
            else:
                width = TRAIL_WIDTH

            line_colour  = "light gray"
            arrow_colour = "light gray"

            for track_status in (TRACK_STATUS_OPEN, TRACK_STATUS_CLOSED):

                for track_direction in (TRACK_DIRECTION_BOTH,
                                        TRACK_DIRECTION_FORWARD,
                                        TRACK_DIRECTION_BACKWARD):

                    symbol = self.createTrackSymbol(width,
                                                    line_colour,
                                                    arrow_colour,
                                                    track_status,
                                                    track_direction)
                    expression = ("(type='%s') and " +
                                  "(status='%s') and " +
                                  "(direction='%s')") % (
                                  track_type, track_status, track_direction)

                    rule = QgsRuleBasedRendererV2.Rule(symbol,
                                                       filterExp=expression)
                    root_rule.appendChild(rule)

        symbol = QgsLineSymbolV2.createSimple({'color' : "black"})
        rule = QgsRuleBasedRendererV2.Rule(symbol, elseRule=True)
        root_rule.appendChild(rule)

        renderer = QgsRuleBasedRendererV2(root_rule)
        self.trackLayer.setRendererV2(renderer)

        # Setup the renderer for our shortest path layer.

        symbol = QgsLineSymbolV2.createSimple({'color' : "blue"})
        symbol.setWidth(ROAD_WIDTH)
        symbol.setOutputUnit(QgsSymbolV2.MapUnit)

        renderer = QgsSingleSymbolRendererV2(symbol)
        self.shortestPathLayer.setRendererV2(renderer)

        # Setup the renderer for our start point layer.

        symbol = QgsMarkerSymbolV2.createSimple({'color' : "green"})
        symbol.setSize(POINT_SIZE)
        symbol.setOutputUnit(QgsSymbolV2.MapUnit)

        renderer = QgsSingleSymbolRendererV2(symbol)
        self.startPointLayer.setRendererV2(renderer)

        # Setup the renderer for our end point layer.

        symbol = QgsMarkerSymbolV2.createSimple({'color' : "red"})
        symbol.setSize(POINT_SIZE)
        symbol.setOutputUnit(QgsSymbolV2.MapUnit)

        renderer = QgsSingleSymbolRendererV2(symbol)
        self.endPointLayer.setRendererV2(renderer)


    def createTrackSymbol(self, width, line_colour, arrow_colour,
                          status, direction):
        symbol = QgsLineSymbolV2.createSimple({})
        symbol.deleteSymbolLayer(0) # Remove default symbol layer.

        symbol_layer = QgsSimpleLineSymbolLayerV2()
        symbol_layer.setWidth(width)
        symbol_layer.setWidthUnit(QgsSymbolV2.MapUnit)
        symbol_layer.setColor(QColor(line_colour))
        if status == TRACK_STATUS_CLOSED:
            symbol_layer.setPenStyle(Qt.DotLine)
        symbol.appendSymbolLayer(symbol_layer)

        if direction == TRACK_DIRECTION_FORWARD:
            registry = QgsSymbolLayerV2Registry.instance()
            marker_line_metadata = registry.symbolLayerMetadata("MarkerLine")
            marker_metadata      = registry.symbolLayerMetadata("SimpleMarker")

            symbol_layer = marker_line_metadata.createSymbolLayer({
                            "width"     : "0.26",
                            "color"     : arrow_colour,
                            "rotate"    : "1",
                            "placement" : "interval",
                            "interval"  : "20",
                            "offset"    : "0"})
            sub_symbol = symbol_layer.subSymbol()
            sub_symbol.deleteSymbolLayer(0)

            triangle = marker_metadata.createSymbolLayer({
                            "name"          : "filled_arrowhead",
                            "color"         : arrow_colour,
                            "color_border"  : arrow_colour,
                            "offset"        : "0.0",
                            "size"          : "3",
                            "outline_width" : "0.5",
                            "output_unit"   : "mapunit",
                            "angle"         : "0"})
            sub_symbol.appendSymbolLayer(triangle)
            symbol.appendSymbolLayer(symbol_layer)
        elif direction == TRACK_DIRECTION_BACKWARD:
            registry = QgsSymbolLayerV2Registry.instance()
            marker_line_metadata = registry.symbolLayerMetadata("MarkerLine")
            marker_metadata      = registry.symbolLayerMetadata("SimpleMarker")

            symbol_layer = marker_line_metadata.createSymbolLayer({
                            "width"     : "0.26",
                            "color"     : arrow_colour,
                            "rotate"    : "1",
                            "placement" : "interval",
                            "interval"  : "20",
                            "offset"    : "0"})
            sub_symbol = symbol_layer.subSymbol()
            sub_symbol.deleteSymbolLayer(0)

            triangle = marker_metadata.createSymbolLayer({
                            "name"          : "filled_arrowhead",
                            "color"         : arrow_colour,
                            "color_border"  : arrow_colour,
                            "offset"        : "0.0",
                            "size"          : "3",
                            "outline_width" : "0.5",
                            "output_unit"   : "mapunit",
                            "angle"         : "180"})
            sub_symbol.appendSymbolLayer(triangle)
            symbol.appendSymbolLayer(symbol_layer)

        return symbol


    def setupMapTools(self):
        self.panTool = PanTool(self.mapCanvas)
        self.panTool.setAction(self.actionPan)

        self.addTrackTool = AddTrackTool(self.mapCanvas,
                                         self.trackLayer,
                                         self.onTrackAdded)
        self.addTrackTool.setAction(self.actionAddTrack)

        self.editTrackTool = EditTrackTool(self.mapCanvas,
                                           self.trackLayer,
                                           self.onTrackEdited)
        self.editTrackTool.setAction(self.actionEditTrack)

        self.deleteTrackTool = DeleteTrackTool(self.mapCanvas,
                                               self.trackLayer,
                                               self.onTrackDeleted)
        self.deleteTrackTool.setAction(self.actionDeleteTrack)

        self.getInfoTool = GetInfoTool(self.mapCanvas,
                                       self.trackLayer,
                                       self.onGetInfo)
        self.getInfoTool.setAction(self.actionGetInfo)


    def adjustActions(self):
        if self.editing:
            self.actionAddTrack.setEnabled(True)
            self.actionEditTrack.setEnabled(True)
            self.actionDeleteTrack.setEnabled(True)
            self.actionGetInfo.setEnabled(True)
            self.actionSetStartPoint.setEnabled(False)
            self.actionSetEndPoint.setEnabled(False)
            self.actionFindShortestPath.setEnabled(False)
        else:
            self.actionAddTrack.setEnabled(False)
            self.actionEditTrack.setEnabled(False)
            self.actionDeleteTrack.setEnabled(False)
            self.actionGetInfo.setEnabled(False)
            self.actionSetStartPoint.setEnabled(True)
            self.actionSetEndPoint.setEnabled(True)
            self.actionFindShortestPath.setEnabled(True)


    def onTrackAdded(self):
        self.modified = True
        self.mapCanvas.refresh()
        self.actionAddTrack.setChecked(False)
        self.setPanMode()


    def onTrackEdited(self):
        self.modified = True
        self.mapCanvas.refresh()


    def onTrackDeleted(self):
        self.modified = True
        self.mapCanvas.refresh()
        self.actionDeleteTrack.setChecked(False)
        self.setPanMode()


    def onGetInfo(self, feature):
        dialog = TrackInfoDialog(self)
        dialog.loadAttributes(feature)
        if dialog.exec_():
            dialog.saveAttributes(feature)
            self.trackLayer.updateFeature(feature)
            self.modified = True
            self.mapCanvas.refresh()


    def closeEvent(self, event):
        self.quit()


    def zoomIn(self):
        self.mapCanvas.zoomIn()


    def zoomOut(self):
        self.mapCanvas.zoomOut()


    def quit(self):
        if self.editing and self.modified:
            reply = QMessageBox.question(self, "Confirm",
                                         "Save Changes?",
                                         QMessageBox.Yes | QMessageBox.No
                                                         | QMessageBox.Cancel,
                                         QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.trackLayer.commitChanges()
            elif reply == QMessageBox.No:
                self.trackLayer.rollBack()

            if reply != QMessageBox.Cancel:
                qApp.quit()
        else:
            qApp.quit()



    def setPanMode(self):
        self.mapCanvas.setMapTool(self.panTool)


    def setEditMode(self):
        if self.editing:
            if self.modified:
                reply = QMessageBox.question(self, "Confirm",
                                             "Save Changes?",
                                             QMessageBox.Yes | QMessageBox.No,
                                             QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    self.trackLayer.commitChanges()
                else:
                    self.trackLayer.rollBack()
            else:
                self.trackLayer.commitChanges()
            self.trackLayer.triggerRepaint()
            self.editing = False
            self.setPanMode()
        else:
            self.trackLayer.startEditing()
            self.trackLayer.triggerRepaint()
            self.editing  = True
            self.modified = False

        self.adjustActions()


    def addTrack(self):
        if self.actionAddTrack.isChecked():
            self.mapCanvas.setMapTool(self.addTrackTool)
        else:
            self.setPanMode()
        self.adjustActions()


    def editTrack(self):
        if self.actionEditTrack.isChecked():
            self.mapCanvas.setMapTool(self.editTrackTool)
        else:
            self.setPanMode()


    def deleteTrack(self):
        if self.actionDeleteTrack.isChecked():
            self.mapCanvas.setMapTool(self.deleteTrackTool)
        else:
            self.setPanMode()


    def getInfo(self):
        if self.actionGetInfo.isChecked():
            self.mapCanvas.setMapTool(self.getInfoTool)
        else:
            self.setPanMode()


    def setStartPoint(self):
        pass


    def setEndPoint(self):
        pass


    def findShortestPath(self):
        pass



class TrackInfoDialog(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.setWindowTitle("Track Info")

        self.types = ["Road",
                      "Walking Trail",
                      "Bike Trail",
                      "Horse Trail"]

        self.directions = ["Both",
                           "Forward",
                           "Backward"]

        self.statuses = ["Open",
                         "Closed"]

        self.typeField = QComboBox(self)
        self.typeField.addItems(self.types)

        self.nameField = QLineEdit(self)

        self.directionField = QComboBox(self)
        self.directionField.addItems(self.directions)

        self.statusField = QComboBox(self)
        self.statusField.addItems(self.statuses)

        self.form = QFormLayout()
        self.form.addRow("Type",      self.typeField)
        self.form.addRow("Name",      self.nameField)
        self.form.addRow("Direction", self.directionField)
        self.form.addRow("Status",    self.statusField)

        self.okButton = QPushButton("OK", self)
        self.connect(self.okButton, SIGNAL("clicked()"), self.accept)

        self.cancelButton = QPushButton("Cancel", self)
        self.connect(self.cancelButton, SIGNAL("clicked()"), self.reject)

        self.buttons = QHBoxLayout()
        self.buttons.addStretch(1)
        self.buttons.addWidget(self.okButton)
        self.buttons.addWidget(self.cancelButton)

        self.layout = QVBoxLayout(self)
        self.layout.addLayout(self.form)
        self.layout.addSpacing(10)
        self.layout.addLayout(self.buttons)

        self.setLayout(self.layout)
        self.resize(self.sizeHint())

    def loadAttributes(self, feature):
        type_attr      = feature.attribute("type")
        name_attr      = feature.attribute("name")
        direction_attr = feature.attribute("direction")
        status_attr    = feature.attribute("status")

        if   type_attr == TRACK_TYPE_ROAD:    index = 0
        elif type_attr == TRACK_TYPE_WALKING: index = 1
        elif type_attr == TRACK_TYPE_BIKE:    index = 2
        elif type_attr == TRACK_TYPE_HORSE:   index = 3
        else:                                 index = 0
        self.typeField.setCurrentIndex(index)

        if name_attr != None:
            self.nameField.setText(name_attr)
        else:
            self.nameField.setText("")

        if   direction_attr == TRACK_DIRECTION_BOTH:     index = 0
        elif direction_attr == TRACK_DIRECTION_FORWARD:  index = 1
        elif direction_attr == TRACK_DIRECTION_BACKWARD: index = 2
        else:                                            index = 0
        self.directionField.setCurrentIndex(index)

        if   status_attr == TRACK_STATUS_OPEN:   index = 0
        elif status_attr == TRACK_STATUS_CLOSED: index = 1
        else:                                    index = 0
        self.statusField.setCurrentIndex(index)

    def saveAttributes(self, feature):
        index = self.typeField.currentIndex()
        if   index == 0: type_attr = TRACK_TYPE_ROAD
        elif index == 1: type_attr = TRACK_TYPE_WALKING
        elif index == 2: type_attr = TRACK_TYPE_BIKE
        elif index == 3: type_attr = TRACK_TYPE_HORSE
        else:            type_attr = TRACK_TYPE_ROAD

        name_attr = self.nameField.text()

        index = self.directionField.currentIndex()
        if   index == 0: direction_attr = TRACK_DIRECTION_BOTH
        elif index == 1: direction_attr = TRACK_DIRECTION_FORWARD
        elif index == 2: direction_attr = TRACK_DIRECTION_BACKWARD
        else:            direction_attr = TRACK_DIRECTION_BOTH

        index = self.statusField.currentIndex()
        if   index == 0: status_attr = TRACK_STATUS_OPEN
        elif index == 1: status_attr = TRACK_STATUS_CLOSED
        else:            status_attr = TRACK_STATUS_OPEN

        feature.setAttribute("type",      type_attr)
        feature.setAttribute("name",      name_attr)
        feature.setAttribute("direction", direction_attr)
        feature.setAttribute("status",    status_attr)






def main():
    app = QApplication(sys.argv)

    QgsApplication.setPrefixPath(os.environ['QGIS_PREFIX'], True)
    QgsApplication.initQgis()

    window = ForestTrailsWindow()
    window.show()
    window.raise_()
    window.setupDatabase()
    window.setupMapLayers()
    window.setupRenderers()
    window.setupMapTools()
    window.adjustActions()

    app.exec_()
    app.deleteLater()
    window.close()
    QgsApplication.exitQgis()

if __name__ == "__main__":
    main()

