from qgis.core import *
from qgis.gui import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

# Define our memory-based layer

layer = QgsVectorLayer("Point?crs=EPSG:4326&field=name:string(255)" +
                       "&field=height:double", "Memory Layer", "memory")

# Add layer to map

QgsMapLayerRegistry.instance().addMapLayer(layer)

# Define the features to display in the layer

provider = layer.dataProvider()
fields   = provider.fields()
features = []

feature = QgsFeature()
feature.setGeometry(QgsGeometry.fromWkt("POINT(2.2945 48.8582)"))
feature.setFields(fields)
feature.setAttribute("height", 301)
feature.setAttribute("name", "Eiffel Tower")
features.append(feature)

feature = QgsFeature()
feature.setGeometry(QgsGeometry.fromWkt("POINT(0.0761 51.5081)"))
feature.setFields(fields)
feature.setAttribute("height", 27)
feature.setAttribute("name", "Tower of London")
features.append(feature)

feature = QgsFeature()
feature.setGeometry(QgsGeometry.fromWkt("POINT(10.3964 43.7231)"))
feature.setFields(fields)
feature.setAttribute("height", 56)
feature.setAttribute("name", "Leaning Tower of Pisa")
features.append(feature)

# Add and display the features

provider.addFeatures(features)
layer.updateExtents()
iface.mapCanvas().zoomToFullExtent()
