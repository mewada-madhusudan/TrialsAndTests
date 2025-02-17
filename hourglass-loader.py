from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt6.QtCore import QPropertyAnimation, QParallelAnimationGroup, QSequentialAnimationGroup, Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPen
import sys

class HourglassLoader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Loading...')
        self.setFixedSize(130, 130)
        self.setStyleSheet("background-color: rgb(71, 60, 60); border-radius: 65px;")
        
        # Initialize animation properties
        self.rotation_angle = 0
        self.sand_stream_height = 0
        self.sand_top_height = 17
        self.sand_bottom_height = 0
        self.stream_opacity = 1.0
        
        # Setup rotation animation
        self.rotation_anim = QPropertyAnimation(self, b"rotation_angle")
        self.rotation_anim.setDuration(2000)
        self.rotation_anim.setStartValue(0)
        self.rotation_anim.setEndValue(180)
        self.rotation_anim.setLoopCount(-1)
        
        # Setup sand stream animation
        self.stream_anim = QPropertyAnimation(self, b"sand_stream_height")
        self.stream_anim.setDuration(2000)
        self.stream_anim.setStartValue(0)
        self.stream_anim.setEndValue(35)
        self.stream_anim.setLoopCount(-1)
        
        # Setup sand depletion animation
        self.sand_top_anim = QPropertyAnimation(self, b"sand_top_height")
        self.sand_top_anim.setDuration(2000)
        self.sand_top_anim.setStartValue(17)
        self.sand_top_anim.setEndValue(0)
        self.sand_top_anim.setLoopCount(-1)
        
        # Setup sand accumulation animation
        self.sand_bottom_anim = QPropertyAnimation(self, b"sand_bottom_height")
        self.sand_bottom_anim.setDuration(2000)
        self.sand_bottom_anim.setStartValue(0)
        self.sand_bottom_anim.setEndValue(17)
        self.sand_bottom_anim.setLoopCount(-1)
        
        # Create animation group
        self.animation_group = QParallelAnimationGroup()
        self.animation_group.addAnimation(self.rotation_anim)
        self.animation_group.addAnimation(self.stream_anim)
        self.animation_group.addAnimation(self.sand_top_anim)
        self.animation_group.addAnimation(self.sand_bottom_anim)
        self.animation_group.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw hourglass
        painter.translate(65, 65)  # Center of widget
        painter.rotate(self.rotation_angle)
        
        # Draw glass container
        glass_color = QColor(153, 153, 153)
        painter.setPen(QPen(glass_color, 2))
        painter.setBrush(glass_color)
        
        # Top bulb
        painter.drawEllipse(-22, -35, 44, 44)
        
        # Bottom bulb
        painter.drawEllipse(-22, -9, 44, 44)
        
        # Center connection
        painter.drawRect(-5, -15, 10, 30)
        
        # Draw sand
        sand_color = Qt.GlobalColor.white
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(sand_color))
        
        # Top sand
        painter.drawRect(-19, -32, 38, self.sand_top_height)
        
        # Bottom sand
        painter.drawRect(-19, 15 - self.sand_bottom_height, 38, self.sand_bottom_height)
        
        # Sand stream
        if self.sand_stream_height > 0:
            stream_path = QPainterPath()
            stream_path.moveTo(0, -15)
            stream_path.lineTo(1.5, -15)
            stream_path.lineTo(1.5, -15 + self.sand_stream_height)
            stream_path.lineTo(-1.5, -15 + self.sand_stream_height)
            stream_path.lineTo(-1.5, -15)
            painter.drawPath(stream_path)

    # Property getters/setters for animations
    def get_rotation_angle(self):
        return self._rotation_angle
        
    def set_rotation_angle(self, angle):
        self._rotation_angle = angle
        self.update()
        
    def get_sand_stream_height(self):
        return self._sand_stream_height
        
    def set_sand_stream_height(self, height):
        self._sand_stream_height = height
        self.update()
        
    def get_sand_top_height(self):
        return self._sand_top_height
        
    def set_sand_top_height(self, height):
        self._sand_top_height = height
        self.update()
        
    def get_sand_bottom_height(self):
        return self._sand_bottom_height
        
    def set_sand_bottom_height(self, height):
        self._sand_bottom_height = height
        self.update()

    # Define properties for animation
    rotation_angle = property(get_rotation_angle, set_rotation_angle)
    sand_stream_height = property(get_sand_stream_height, set_sand_stream_height)
    sand_top_height = property(get_sand_top_height, set_sand_top_height)
    sand_bottom_height = property(get_sand_bottom_height, set_sand_bottom_height)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = HourglassLoader()
    window.show()
    sys.exit(app.exec())
