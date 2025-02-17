from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt6.QtCore import QPropertyAnimation, QParallelAnimationGroup, Qt, QPointF
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPen
import sys

class HourglassLoader(QWidget):
    def __init__(self):
        super().__init__()
        
        # Initialize the window properties
        self.setWindowTitle('Loading...')
        self.setFixedSize(130, 130)
        self.setStyleSheet("background-color: rgb(71, 60, 60); border-radius: 65px;")
        
        # Initialize private animation properties
        self._rotation_angle = 0
        self._sand_stream_height = 0
        self._sand_top_height = 17
        self._sand_bottom_height = 0
        
        # Create rotation animation
        self.rotation_anim = QPropertyAnimation(self, b'rotation_angle')
        self.rotation_anim.setDuration(2000)  # 2 seconds
        self.rotation_anim.setStartValue(0)
        self.rotation_anim.setEndValue(180)
        
        # Create sand stream animation
        self.stream_anim = QPropertyAnimation(self, b'sand_stream_height')
        self.stream_anim.setDuration(2000)
        self.stream_anim.setStartValue(0)
        self.stream_anim.setEndValue(35)
        
        # Create animation group and set properties
        self.anim_group = QParallelAnimationGroup()
        self.anim_group.addAnimation(self.rotation_anim)
        self.anim_group.addAnimation(self.stream_anim)
        self.anim_group.setLoopCount(-1)  # Infinite loop
        
        # Start the animation
        self.anim_group.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Translate to center
        painter.translate(65, 65)
        painter.rotate(self._rotation_angle)
        
        # Draw hourglass body
        glass_color = QColor(153, 153, 153)
        painter.setPen(QPen(glass_color, 2))
        painter.setBrush(glass_color)
        
        # Draw top and bottom bulbs
        painter.drawEllipse(-22, -35, 44, 44)  # Top bulb
        painter.drawEllipse(-22, -9, 44, 44)   # Bottom bulb
        painter.drawRect(-5, -15, 10, 30)      # Center connection
        
        # Draw sand
        sand_color = QColor(255, 255, 255)  # White sand
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(sand_color)
        
        # Draw top sand pile
        painter.drawRect(-19, -32, 38, self._sand_top_height)
        
        # Draw bottom sand pile
        painter.drawRect(-19, 15 - self._sand_bottom_height, 38, self._sand_bottom_height)
        
        # Draw sand stream
        if self._sand_stream_height > 0:
            painter.drawRect(-1, -15, 2, self._sand_stream_height)

    # Property getters and setters
    @property
    def rotation_angle(self):
        return self._rotation_angle

    @rotation_angle.setter
    def rotation_angle(self, value):
        self._rotation_angle = value
        self.update()

    @property
    def sand_stream_height(self):
        return self._sand_stream_height

    @sand_stream_height.setter
    def sand_stream_height(self, value):
        self._sand_stream_height = value
        self.update()

    @property
    def sand_top_height(self):
        return self._sand_top_height

    @sand_top_height.setter
    def sand_top_height(self, value):
        self._sand_top_height = value
        self.update()

    @property
    def sand_bottom_height(self):
        return self._sand_bottom_height

    @sand_bottom_height.setter
    def sand_bottom_height(self, value):
        self._sand_bottom_height = value
        self.update()

def main():
    app = QApplication(sys.argv)
    window = HourglassLoader()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
