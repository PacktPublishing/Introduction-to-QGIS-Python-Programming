from qgis.core import *
from qgis.gui import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

window = iface.mainWindow()
layer = iface.activeLayer()

if layer.selectedFeatureCount() == 0:
    QMessageBox.information(window, "Info", "There is nothing selected.")
else:
    msg = []
    msg.append("Selected Features:")
    for feature in layer.selectedFeatures():
        msg.append("   " + feature.attribute("NAME"))
    QMessageBox.information(window, "Info", "\n".join(msg))
