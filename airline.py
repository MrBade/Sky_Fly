import os
import sys
import cv2
import numpy
import dronekit
import threading
import evildecorater as ed
from SGe import BlessApi
import targetidentify
from dronekit import connect
import matplotlib
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QTableWidget, QApplication, QMainWindow, QTableWidgetItem, QGridLayout, QGroupBox,\
                            QAbstractItemView
from PyQt5.QtCore import Qt, QRect, QTimer, QCoreApplication
from PyQt5.QtGui import QImage, QPixmap
from ui_interface import Ui_MainWindow
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
matplotlib.use("Qt5Agg")  # 声明使用QT5


class MyFigure(FigureCanvas):
    def __init__(self, width=5, height=4, dpi=100):
        # 第一步：创建一个创建Figure
        self.fig = plt.figure(figsize=(width, height), dpi=dpi)
        # 第二步：在父类中激活Figure窗口
        super(MyFigure, self).__init__(self.fig)  # 此句必不可少，否则不能显示图形
        # 第三步：创建一个子图，用于绘制图形用，111表示子图编号，如matlab的subplot(1,1,1)
        # self.axes = self.fig.add_subplot(111)

    def plotcos(self):
        t = numpy.arange(0.0, 3.0, 0.01)
        s = numpy.sin(2 * numpy.pi * t)
        plt.plot(t, s)


class MyThread(threading.Thread):
    def __init__(self, func, args):
        super(MyThread, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result
        except Exception:
            return None


class LineManager:
    def __init__(self):
        # self.figure = MyFigure()
        self.change_cmd = 0
        self.goto_single = 0
        self.start_control = 0

        self.form_points = []
        self.target_line_id = 0
        self.key_points = {"change_p_id": 0, "line1_p_id": -1, "line2_p_id": -1,
                           "line3_p_id": -1}

    def get_goto_single(self, cmds):
        # print(cmds.next, self.key_points["change_p_id"])
        if cmds.next not in self.form_points:
            self.form_points.append(cmds.next)
        else:
            if cmds.next == self.key_points["change_p_id"]:
                self.change_cmd = 1
            elif self.change_cmd:
                self.goto_single = 1


class AirLinePlanner:
    def __init__(self):
        self.ui = WindowAdminer()
        self.frame_num = 0

    def load_arilines(self):
        # if self.ui.vehicle is None:
        with open("airLine.txt", "r", encoding="gbk") as airLine:
            for index, line in enumerate(airLine.readlines()):
                line = line.rstrip("\n")
                yield index, line.split("\t")
        # else:
            # print("Vehicle is not connect!!!!!!!!!!!")

    def window_run(self):
        app = QApplication(sys.argv)
        window = QMainWindow()
        self.ui.setupUi(window)
        for index, info in self.load_arilines():
            self.ui.setTableWidgetRowInfo(index, info)
        self.ui.setcomboBoxes()
        self.ui.timer_playVideo.timeout.connect(self.ui.playVideo)
        self.ui.timer_playVideo.start(40)
        window.show()
        sys.exit(app.exec_())


class WindowAdminer(Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.line_manager = None
        self.video = None
        self.vid = None
        self.cmds = None
        self.vehicle = None
        self.pic_gen = None
        self.bless_api = None
        self.writer = None

        self.frame_num = 0
        self.a = 1

        self.record = 0

        self.WIDTH = 0
        self.HEIGHT = 0
        self.FPS = 0

    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)
        _translate = QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "￥信大航模俱乐部￥-----庆美好的双十一"))
        self.setTableWidget()
        self.bless_api_init()
        self.road_manager_init()
        self.video_init()
        # self.vehicle_init()
        self.cmds_init()
        self.download_waypoints()

        self.timer_init(MainWindow)

        # self.picWidget_init()
        self.pushButton_init()
        self.comboBox_init()

        self.setstylesheet()

    @ed.print_func_process("Road Manager Init ")
    def road_manager_init(self):
        if self.line_manager is None:
            self.line_manager = LineManager()

    @ed.print_func_process("Bless API Init ")
    def bless_api_init(self):
        if self.bless_api is None:
            self.bless_api = BlessApi.BlessApi()
            self.bless_api.incept_key("生日", "朋友")
            self.bless_api.fill_blscls()
            self.pic_gen = self.out_pic()

    @ed.print_func_process("Video Init ")
    def video_init(self):
        if self.video is None:
            # self.video = cv2.VideoCapture("DCIM//TV_CAM_设备_20191204_155929.avi")
            self.video = cv2.VideoCapture(0)
            self.WIDTH = self.video.get(cv2.CAP_PROP_FRAME_WIDTH)
            self.HEIGHT = self.video.get(cv2.CAP_PROP_FRAME_HEIGHT)
            self.FPS = self.video.get(cv2.CAP_PROP_FPS)
            # print(self.HEIGHT, self.WIDTH)
            # self.HEIGHT = int(640 / self.WIDTH * self.HEIGHT)
            # self.WIDTH = 640
            # print(self.HEIGHT, self.WIDTH)
            # if self.HEIGHT > 480:
            #     self.WIDTH = int(480 / self.HEIGHT * self.WIDTH)
            #     self.HEIGHT = 480
            # self.WIDTH = 640
            # self.HEIGHT = 450
            # print(self.HEIGHT, self.WIDTH)
            self.vid = targetidentify.TargetIdentify()

    @ed.print_func_process("Vehicle Init ")
    def vehicle_init(self):
        if self.vehicle is None:
            try:
                self.vehicle = connect("0.0.0.0:14550", wait_ready=True, timeout=30)
            except:
                self.vehicle = None

    @ed.print_func_process("Cmds Init ")
    def cmds_init(self):
        if self.cmds is None and self.vehicle is not None:
            self.cmds = self.vehicle.commands
            self.cmds.download()
            self.cmds.wait_ready()

    @ed.print_func_process("QTimer Init ")
    def timer_init(self, MainWindow):
        self.timer_playVideo = QTimer(MainWindow)
        self.timer_playVideo.timeout.connect(self.playVideo)

        if self.bless_api is not None:
            self.timer_showPic = QTimer(MainWindow)
            self.timer_showPic.timeout.connect(self.show_pic)
            self.timer_showPic.start(3000)

        self.timer_liner = QTimer(MainWindow)
        self.timer_liner.timeout.connect(self.schedule_line)
        self.timer_liner.start(50)

    @ed.print_func_process("PicWidth Init ")
    def picWidget_init(self):
        if self.WIDTH and self.HEIGHT:
            self.label_7.setGeometry(QRect(20, 30, 641, 451))
            self.label_8.setGeometry(QRect(700, 30, 641, 451))

    @ed.print_func_process("PushButton Init ")
    def pushButton_init(self):
        self.pushButton.clicked.connect(self.pushButton1)
        self.pushButton_2.clicked.connect(self.pushButton2)

    @ed.print_func_process("ComboBox Init ")
    def comboBox_init(self):
        self.comboBox.currentIndexChanged.connect(lambda: self.comboBoxChange(self.comboBox.objectName(),
                                                                              self.comboBox.currentIndex()))
        self.comboBox_2.currentIndexChanged.connect(lambda: self.comboBoxChange(self.comboBox_2.objectName(),
                                                                                self.comboBox_2.currentIndex()))
        self.comboBox_3.currentIndexChanged.connect(lambda: self.comboBoxChange(self.comboBox_3.objectName(),
                                                                                self.comboBox_3.currentIndex()))
        self.comboBox_4.currentIndexChanged.connect(lambda: self.comboBoxChange(self.comboBox_4.objectName(),
                                                                                self.comboBox_4.currentIndex()))

    @ed.print_func_process("Downloading Way Points ")
    def download_waypoints(self):
        if self.cmds is not None:
            """
            Save a mission in the Way point file format 
            """
            missionlist = []
            for cmd in self.cmds:
                missionlist.append(cmd)
            output = 'QGC WPL 110\n'
            for cmd in missionlist:
                commandline = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
                cmd.seq, cmd.current, cmd.frame, cmd.command, cmd.param1, cmd.param2, cmd.param3, cmd.param4, cmd.x,
                cmd.y, cmd.z, cmd.autocontinue)
                output += commandline
            with open("airLine.txt", 'w', encoding="gbk") as file_:
                file_.write(output)
                return 1
        return 0

    def setTableWidget(self):
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        QTableWidget.resizeColumnsToContents(self.tableWidget)
        QTableWidget.resizeRowsToContents(self.tableWidget)

    def setTableWidgetRowInfo(self, row_index, infos):
        if self.tableWidget.rowCount() < row_index:
            self.tableWidget.setRowCount(row_index)
        if len(infos) == self.tableWidget.columnCount():
            for clm_index, info in enumerate(infos):
                item = QTableWidgetItem(info)
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.tableWidget.setItem(row_index-1, clm_index, item)

    def setcomboBoxes(self):
        rowcount = self.tableWidget.rowCount()
        comboBoxes = [self.comboBox, self.comboBox_2, self.comboBox_3, self.comboBox_4]
        for comboBox in comboBoxes:
            for i in range(rowcount):
                comboBox.addItem(str(i))

    def comboBoxChange(self, objectName, index):
        line_point_id = index
        if objectName == "comboBox":
            self.line_manager.key_points["change_p_id"] = line_point_id
        elif objectName == "comboBox_2":
            self.line_manager.key_points["line1_p_id"] = line_point_id
        elif objectName == "comboBox_3":
            self.line_manager.key_points["line2_p_id"] = line_point_id
        elif objectName == "comboBox_4":
            self.line_manager.key_points["line3_p_id"] = line_point_id

    def playVideo(self):
        ret, frame = self.video.read()
        self.frame_num += 1
        # print(frame.shape)
        if ret:
            self.label_7.setPixmap(QPixmap.fromImage(
                QImage(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), 640, 450, 13)))
            if not self.line_manager.target_line_id:
                thread = MyThread(func=self.vid.read, args=(self.frame_num, frame))
                thread.start()
                thread.join(33)
                self.line_manager.target_line_id = thread.get_result()
                # print(self.line_manager.target_line_id)
            if self.line_manager.target_line_id and self.a:
                print("检测到红色点是第 %d 个" % int(self.line_manager.target_line_id))
                self.a = 0
        if self.record and frame.any():
            if self.writer is None:
                fourcc = cv2.VideoWriter_fourcc(*"MJPG")
                # self.writer = cv2.VideoWriter('output.mp4', fourcc, self.FPS, (int(self.WIDTH), int(self.HEIGHT)), True)
                # self.writer = cv2.VideoWriter('output.mp4', fourcc, self.FPS, (641, 451), True)
            # print(frame.dtype)
            self.writer.write(frame)

    def schedule_line(self):
        if self.line_manager.start_control:
            if self.line_manager.target_line_id == 1:
                if self.line_manager.goto_single or self.cmds is None:
                    if self.cmds is not None:
                        self.cmds.next = int(self.comboBox_2.currentText())
                    self.label_6.setText("检测到目标位于一号线，将转至%s号节点" % self.comboBox_2.currentText())
            elif self.line_manager.target_line_id == 2:
                if self.line_manager.goto_single:
                    if self.cmds is not None:
                        self.cmds.next = int(self.comboBox_3.currentText())
                    self.label_6.setText("检测到目标位于二号线，将转至%s号节点" % self.comboBox_3.currentText())
            elif self.line_manager.target_line_id == 3:
                if self.line_manager.goto_single:
                    if self.cmds is not None:
                        self.cmds.next = int(self.comboBox_4.currentText())
                    self.label_6.setText("检测到目标位于三号线，将转至%s号节点" % self.comboBox_4.currentText())

    def monitor_nextpoint(self):
        if self.cmds is not None:
            thread = MyThread(func=self.line_manager.get_goto_single, args=(self.cmds, ))
            thread.start()
            thread.join(1)

    def out_pic(self):
        pic_list = os.listdir("Picture\\")
        for pic in pic_list:
            img = cv2.imread("Picture\\" + pic)
            yield cv2.resize(img, (640, 480))

    def show_pic_func(self):
        try:
            pic = next(self.pic_gen)
        except StopIteration as e:
            self.pic_gen = self.out_pic()
        except:
            pass
        try:
            self.label_8.setPixmap(QPixmap.fromImage(QImage(cv2.cvtColor(pic, cv2.COLOR_BGR2RGB), 640, 480, 13)))
        except:
            pass

    def show_pic(self):
        # bless = self.bless_api.get_blsword()
        if self.pic_gen is not None:
            thread = MyThread(func=self.show_pic_func, args=())
            thread.start()
            thread1 = MyThread(func=self.bless_api.get_blsword, args=())
            thread1.start()
            bless = thread1.get_result()
            self.label_9.setText("胜哥: " + bless)

    def pushButton1(self):
        keypoints_indexes = list(self.line_manager.key_points.values())
        if keypoints_indexes.count(0) > 0:
            self.label_6.setText("当前设置存在0号点，有点问题哦～")
        elif len(set(keypoints_indexes)) < 4:
            self.label_6.setText("当前设置点中有重复点哦，请重新设置～")
        else:
            self.label_6.setText("胜哥天下无敌哦～～～～～～")
            self.line_manager.start_control = 1

    def pushButton2(self):
        if self.writer is not None:
            self.writer.release()
        if self.video is not None:
            self.video.release()
        sys.exit()

    def setstylesheet(self):
        self.centralwidget.setStyleSheet("QWidget{background-color: Silver}")

        self.pushButton.setStyleSheet("QPushButton{border-radius:8px;padding:2px 4px;"
                                      "font:20px;"
                                      "font-family:华文新魏;}"
                                      "QPushButton:hover{border:2px solid yellow;border-radius:8px;padding:2px 4px;}"
                                      "QPushButton:pressed{border:2px solid green;"
                                      "border-radius:8px;padding:2px 4px;"
                                      "background-color:cyan}")
        self.pushButton_2.setStyleSheet("QPushButton{border-radius:8px;padding:2px 4px;"
                                        "font:20px;"
                                        "font-family:华文新魏;}"
                                        "QPushButton:hover{border:2px solid red;border-radius:8px;padding:2px 4px;}"
                                        "QPushButton:pressed{border:2px solid skyblue;"
                                        "border-radius:8px;padding:2px 4px;"
                                        "background-color:rosybrown}")

        self.tableWidget.setStyleSheet("QTableWidget{border:2px;border-color:black;border-style:groove;"
                                       "background:transparent;"
                                       "font:15px;"
                                       "font-family:华文新魏;"
                                       "border-radius:5px;"
                                       "column-background-color:transparent;"
                                       "columns-background-color:transparent;}"
                                       "QTableWidget:Columns{background-color:transparent;}")

        self.comboBox.setStyleSheet("QComboBox{border:1px solid brown;border-radius:2px;background:transparent;}")
        self.comboBox_2.setStyleSheet("QComboBox{border:1px solid brown;border-radius:2px;background:transparent;}")
        self.comboBox_3.setStyleSheet("QComboBox{border:1px solid brown;border-radius:2px;background:transparent;}")
        self.comboBox_4.setStyleSheet("QComboBox{border:1px solid brown;border-radius:2px;background:transparent;}")

        self.label.setStyleSheet("QLabel{border:2px solid black;border-radius:4px;font:18px;font-family:华文新魏}")
        self.label_2.setStyleSheet("QLabel{border:2px solid black;border-radius:4px;font:18px;font-family:华文新魏}")
        self.label_3.setStyleSheet("QLabel{border:2px solid black;border-radius:4px;font:18px;font-family:华文新魏}")
        self.label_4.setStyleSheet("QLabel{border:2px solid black;border-radius:4px;font:18px;font-family:华文新魏}")
        self.label_5.setStyleSheet("QLabel{border:2px solid black;border-radius:4px;font:18px;font-family:华文新魏}")
        self.label_6.setStyleSheet("QLabel{border:2px solid black;border-radius:4px;font:18px;font-family:华文新魏}")
        self.label_9.setStyleSheet("QLabel{border:2px solid red;border-radius:4px;font:18px;font-family:华文新魏;"
                                   "color: Ivory;}")
        self.label_9.setText("胜哥: ")
        self.label_7.setStyleSheet("QLabel{border:3px solid white;border-radius:8px;}")
        self.label_8.setStyleSheet("QLabel{border:3px solid white;border-radius:8px;}")


if __name__ == "__main__":
    planner = AirLinePlanner()
    planner.window_run()
    pass


