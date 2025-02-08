from eyecheck import *
import sys, os
import threading

from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QWidget,
    QVBoxLayout,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QCameraDevice
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtCore import QTimer, Qt, QDateTime, QUrl

# ---------------------------------------直流电机控制初始化------------------------------------------------------
from gpiozero import LED
from time import sleep

l1 = LED(23)
l2 = LED(24)

# --------------------------------------pyside6界面------------------------------------------------------


# 报警界面
class VideoPlayer(QWidget):
    def __init__(self):
        super().__init__()

        with open("cam.ini", "w") as f:
            f.write("d")
        self.setWindowTitle("Video Player")
        self.setGeometry(0, 0, 800, 800)
        self.target_size = (800, 800)
        self.mp4 = cv2.VideoCapture("warning.mp4")
        self.skip = 0

        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(int(1000 / 66))

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.showFullScreen()
        l1.on()
        l2.off()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q:
            l1.on()
            l2.on()
            self.close()

    def mousePressEvent(self, event):
        self.close()

    def on_duration_changed(self, duration):
        self.duration = duration

    def on_position_changed(self, position):
        if self.duration > 0 and position >= self.duration - 100:
            self.media_player.pause()

    def update_frame(self):
        ret, frame = self.mp4.read()
        if ret:
            frame = cv2.resize(frame, self.target_size, interpolation=cv2.INTER_AREA)
            frame = frame.astype(np.uint8)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            qt_image = QImage(
                rgb_frame.data,
                self.target_size[0],
                self.target_size[1],
                QImage.Format_RGB888,
            )
            self.video_label.setPixmap(QPixmap.fromImage(qt_image))
        else:
            self.mp4.set(cv2.CAP_PROP_POS_FRAMES, 0)


# 待机时钟界面
class Clock(QWidget):
    def __init__(self):
        super().__init__()
        self.FPS = int(1000 / 66)
        self.show_camera = False

        self.setWindowTitle("PYSIDE6 CLOCK")
        self.setFixedSize(800, 800)
        self.load_ui()
        self.angry = 0
        self.frame_counter = 0
        self.check_frame = None
        self.eye = 0
        self.mouth = 0
        self.last = 0
        self.sub_window = None
        thread = threading.Thread(target=self.check_face)
        thread.start()
        self.atimer = QTimer(self)
        self.atimer.timeout.connect(self.check_angry)
        self.atimer.start(100)  # 每100毫秒检查一次
        self.showFullScreen()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q:
            self.cap.release()
            self.close()

    def check_angry(self):
        if self.angry > 240:
            self.open_sub_window()
            self.angry = 0

    def open_sub_window(self):
        if self.sub_window is None or not self.sub_window.isVisible():
            self.sub_window = VideoPlayer()
            self.sub_window.show()

    def check_face(self):
        with map_face_mesh.FaceMesh(
            min_detection_confidence=0.5, min_tracking_confidence=0.5
        ) as face_mesh:
            start_time = time.time()
            while True:
                if self.sub_window is None or not self.sub_window.isVisible():
                    l1.on()
                    l2.on()
                    self.frame_counter += 1
                    ret = True
                    while 1:
                        with open("cam.ini", "r") as f:
                            data = f.read()
                        if data == "d":
                            break
                    frame = cv2.imread("now.jpg")
                    with open("cam.ini", "w") as f:
                        f.write("r")
                    # ret,frame = self.cap.read()
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    results = face_mesh.process(rgb_frame)
                    if results.multi_face_landmarks:
                        mesh_coords = landmarksDetection(frame, results, False)
                        frame = utils.fillPolyTrans(
                            frame,
                            [mesh_coords[p] for p in FACE_OVAL],
                            utils.RED,
                            opacity=0.4,
                        )
                        frame = utils.fillPolyTrans(
                            frame,
                            [mesh_coords[p] for p in LEFT_EYE],
                            utils.GREEN,
                            opacity=0.4,
                        )
                        frame = utils.fillPolyTrans(
                            frame,
                            [mesh_coords[p] for p in RIGHT_EYE],
                            utils.GREEN,
                            opacity=0.4,
                        )
                        frame = utils.fillPolyTrans(
                            frame,
                            [mesh_coords[p] for p in LIPS],
                            utils.BLACK,
                            opacity=0.3,
                        )
                        # 脸部描点
                        [
                            cv2.circle(
                                frame, mesh_coords[p], 1, utils.GREEN, -1, cv2.LINE_AA
                            )
                            for p in LIPS
                        ]
                        [
                            cv2.circle(
                                frame, mesh_coords[p], 1, utils.BLACK, -1, cv2.LINE_AA
                            )
                            for p in RIGHT_EYE
                        ]
                        [
                            cv2.circle(
                                frame, mesh_coords[p], 1, utils.BLACK, -1, cv2.LINE_AA
                            )
                            for p in LEFT_EYE
                        ]
                        [
                            cv2.circle(
                                frame, mesh_coords[p], 1, utils.RED, -1, cv2.LINE_AA
                            )
                            for p in FACE_OVAL
                        ]
                        # 计算比率
                        left_eye = eye_aspect_ratio([mesh_coords[p] for p in LEFT_EYE])
                        right_eye = eye_aspect_ratio([mesh_coords[p] for p in LEFT_EYE])
                        self.mouth = mouth_aspect_ratio([mesh_coords[p] for p in LIPS])
                        self.eye = (left_eye + right_eye) / 2.0
                    else:
                        self.mouth = None
                        self.eye = None
                    if self.mouth != None and self.eye != None:
                        if self.mouth > 0.54:
                            if self.angry < 250:
                                self.angry += 2
                        if self.eye < 0.32:
                            self.last += 1
                            if self.last > 5:
                                if self.angry < 250:
                                    self.angry += 4
                        else:
                            self.last = 0
                    if self.angry > 1:
                        self.angry -= 0.2
                    # print(self.angry)

                    # 计算帧数
                    end_time = time.time() - start_time
                    fps = self.frame_counter / end_time
                    self.check_frame = utils.textWithBackground(
                        frame,
                        f"FPS: {round(fps,1)}",
                        FONTS,
                        1.0,
                        (20, 50),
                        bgOpacity=0.9,
                        textThickness=2,
                    )
                    self.check_frame = frame
                    # print(self.mouth, self.eye)

    def load_ui(self):
        self.target_size = (800, 800)

        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)

        self.mp4 = cv2.VideoCapture("background.mp4")
        # 另一种思路流媒体获取方法 经过测试比较卡顿 所以废弃
        # rtsp_url = "rtsp://192.168.238.6:8554/stream"
        # self.cap = cv2.VideoCapture(rtsp_url)
        # self.cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(3, 800)
        self.cap.set(4, 800)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(self.FPS)

        self.datetime_label = QLabel(self)
        myfont = QFontDatabase.addApplicationFont("font.ttf")
        families = QFontDatabase.applicationFontFamilies(myfont)
        self.datetime_label.setFont(QFont(families[0], 120))
        self.datetime_label.setStyleSheet(
            "color: rgb(106,62,62); background-color: rgba(0, 0, 0, 0);"
        )
        self.datetime_label.setAlignment(Qt.AlignCenter)
        self.datetime_label.setGeometry(150, 120, 500, 200)
        self.datetime_label.setText(QDateTime.currentDateTime().toString("hh:mm"))

        self.switch = QLabel(self)
        self.switch.setFont(QFont(families[0], 60))
        self.switch.setStyleSheet(
            "color: rgb(200,2,2); background-color: rgba(0, 0, 0, 0);"
        )
        self.switch.setGeometry(220, 600, 400, 100)
        self.switch.setText(
            "<a href='https://github.com/muziing/PySide6-Code-Tutorial'>CAMERA</a>"
        )
        self.switch.linkActivated.connect(
            lambda: setattr(self, "show_camera", not self.show_camera)
        )

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def update_frame(self):
        if self.sub_window is None or not self.sub_window.isVisible():
            ret = True
            if self.show_camera:
                ret = True
                frame = self.check_frame
            else:
                ret, frame = self.mp4.read()
            if ret:
                frame = cv2.resize(
                    frame, self.target_size, interpolation=cv2.INTER_AREA
                )
                cv2.rectangle(
                    frame,
                    (275, 550),
                    (275 + int(self.angry), 540 + 25),
                    (226, 179, 213),
                    -1,
                )

                cv2.rectangle(
                    frame,
                    (272, 547),
                    (278 + 250, 540 + 28),
                    (226, 179, 213),
                    2,
                )

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                qt_image = QImage(
                    rgb_frame.data,
                    self.target_size[0],
                    self.target_size[1],
                    QImage.Format_RGB888,
                )
                self.video_label.setPixmap(QPixmap.fromImage(qt_image))
            else:
                self.mp4.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def closeEvent(self, event):
        super().closeEvent(event)

    def update_datetime(self):
        current_datetime = QDateTime.currentDateTime()
        datetime_text = current_datetime.toString("hh:mm")
        self.datetime_label.setText(datetime_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = Clock()
    # player = VideoPlayer()   #测试用 直接打开报警界面
    player.show()
    sys.exit(app.exec())
