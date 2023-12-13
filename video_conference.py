import typing
import cv2
import socket
import numpy
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QHBoxLayout, QWidget, QVBoxLayout
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QObject, Qt, QTimer, pyqtSignal, QThread

SERVER_IP = '192.168.0.2'
CLIENT_IP = '192.168.0.219'

UDP_PORT2 = 9865
UDP_PORT = 9506

class UDPServerThread(QThread):
    '''
    server에서 받는 역할
    '''
    def __init__(self, parent: QObject | None = ...) -> None:
        super().__init__(parent)
        self.parent = parent
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((SERVER_IP, UDP_PORT))
        self.s = [b'\xff' * 46080 for x in range(20)]
    
    def run(self):
        while True:
            picture = b''
            data, addr = self.server_socket.recvfrom(46081)
            self.s[data[0]] = data[1:46081]
            if data[0] == 19:
                for i in range(20):
                    picture += self.s[i]

                self.frame = numpy.frombuffer(picture, dtype=numpy.uint8)
                server_q_image = self.convert_cv_to_qimage(self.frame)
                server_pixmap = QPixmap.fromImage(server_q_image)
                self.parent.server_image_label.setPixmap(server_pixmap)

    def convert_cv_to_qimage(self, frame):
        height = 480
        width = 640
        bytes_per_line = 3 * width
        q_image = QImage(frame, width, height, bytes_per_line, QImage.Format_RGB888)
        return q_image

class UDPClientThread(QThread):
    '''
    client에서 자기 자신 표시 및 보내는 역할
    '''
    def __init__(self, parent: QObject | None = ...) -> None:
        super().__init__(parent)
        self.parent = parent
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.video_capture = cv2.VideoCapture(0)
    
    def run(self):
        while True:
            ret, frame = self.video_capture.read()
            if ret:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width, channel = rgb_image.shape
                q_image = QImage(rgb_image.data, width, height, channel * width, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(q_image)
                self.parent.client_image_label.setPixmap(pixmap)
                d = rgb_image.flatten()
                s = d.tostring()
                for i in range(20):
                    self.client_socket.sendto(bytes([i]) + s[i*46080:(i+1)*46080], (CLIENT_IP, UDP_PORT2))
    
class ServerMainWindow(QMainWindow):    
    def __init__(self):
        super(ServerMainWindow, self).__init__()

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.server_image_label = QLabel(self)
        self.server_image_label.setFixedWidth(640)
        self.server_image_label.setFixedHeight(320)
        self.server_image_label.setAlignment(Qt.AlignCenter)

        self.client_image_label = QLabel(self)
        self.client_image_label.setFixedWidth(640)
        self.client_image_label.setFixedHeight(320)
        self.client_image_label.setAlignment(Qt.AlignCenter)

        layout = QHBoxLayout(self.central_widget)
        server_label = QLabel('상대방 ', self)
        server_label.setAlignment(Qt.AlignCenter)

        client_label = QLabel('당신', self)
        client_label.setAlignment(Qt.AlignCenter)

        self.server_view = QVBoxLayout()
        self.server_view.addWidget(server_label)
        self.server_view.addWidget(self.server_image_label)

        self.client_view = QVBoxLayout()
        self.client_view.addWidget(client_label)
        self.client_view.addWidget(self.client_image_label)

        layout.addLayout(self.server_view)
        layout.addLayout(self.client_view)

        self.client_image = UDPClientThread(self)
        self.server_image = UDPServerThread(self)

        self.client_image.start()
        self.server_image.start()

if __name__ == "__main__":
    app = QApplication([])
    server_window = ServerMainWindow()
    server_window.show()
    app.exec_()
