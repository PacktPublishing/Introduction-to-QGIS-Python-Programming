from qgis.core import *
from qgis.gui import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *


class CompassRoseItem(QgsMapCanvasItem):
    def __init__(self, canvas):
        QgsMapCanvasItem.__init__(self, canvas)
        self.center = QgsPoint(0, 0)
        self.size   = 100

    def setCenter(self, center):
        self.center = center

    def setSize(self, size):
        self.size = size

    def boundingRect(self):
        return QRectF(self.center.x() - self.size/2,
                      self.center.y() - self.size/2,
                      self.center.x() + self.size/2,
                      self.center.y() + self.size/2)

    def paint(self, painter, option, widget):
        fontSize = int(18 * self.size/100)
        painter.setFont(QFont("Times", pointSize=fontSize, weight=75))
        metrics   = painter.fontMetrics()
        labelSize = metrics.height()
        margin    = 5

        # Calculate rose position and size

        x = self.center.x()
        y = self.center.y()
        size = self.size - labelSize - margin

        # Draw light grey four-pointed star

        path = QPainterPath()
        path.moveTo(x, y - size * 0.23)
        path.lineTo(x - size * 0.45, y - size * 0.45)
        path.lineTo(x - size * 0.23, y)
        path.lineTo(x - size * 0.45, y + size * 0.45)
        path.lineTo(x, y + size * 0.23)
        path.lineTo(x + size * 0.45, y + size * 0.45)
        path.lineTo(x + size * 0.23, y)
        path.lineTo(x + size * 0.45, y - size * 0.45)
        path.closeSubpath()

        painter.fillPath(path, QColor("light gray"))

        # Draw black four-pointed star

        path = QPainterPath()
        path.moveTo(x, y - size)
        path.lineTo(x - size * 0.18, y - size * 0.18)
        path.lineTo(x - size, y)
        path.lineTo(x - size * 0.18, y + size * 0.18)
        path.lineTo(x, y + size)
        path.lineTo(x + size * 0.18, y + size * 0.18)
        path.lineTo(x + size, y)
        path.lineTo(x + size * 0.18, y - size * 0.18)
        path.closeSubpath()

        painter.fillPath(path, QColor("black"))

        # Draw labels

        labelX = x - metrics.width("N")/2
        labelY = y - self.size + labelSize - metrics.descent()
        painter.drawText(QPoint(labelX, labelY), "N")

        labelX = x - metrics.width("S")/2
        labelY = y + self.size - labelSize + metrics.ascent()
        painter.drawText(QPoint(labelX, labelY), "S")

        labelX = x - self.size + labelSize/2 - metrics.width("W")/2
        labelY = y - metrics.height()/2 + metrics.ascent()
        painter.drawText(QPoint(labelX, labelY), "W")
        
        labelX = x + self.size - labelSize/2 - metrics.width("E")/2
        labelY = y - metrics.height()/2 + metrics.ascent()
        painter.drawText(QPoint(labelX, labelY), "E")


# Add map canvas item to the map canvas

canvas = iface.mapCanvas()

rose = CompassRoseItem(canvas)
rose.setCenter(QPointF(150, 400))
rose.setSize(80)

canvas.refresh()

# Remove the map canvas item from the map canvas

canvas.scene.removeItem(rose)
canvas.refresh()

