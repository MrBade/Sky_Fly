import cv2
import numpy
import time
import configparser


class TargetIdentify:
    def __init__(self):
        self.config = self.load_config()
        self.memory_tab = []
        self.memory_time = 0
        self.times = 0

        self.debug = 0
        self.identify_times = 0
        self.memory_start = 0
        self.tabs = [0]
        self.x_times, self.y_times = eval(self.config["param"]["xy_times"])

    @staticmethod
    def load_config():
        config = configparser.ConfigParser()
        config.read("config.ini", encoding="utf-8")
        return config

    def get_contours_area(self, contour, img):
        edge_le = eval(self.config["param"]["edge_le"])
        new_contour = []
        # 计算轮廓的外围矩形
        x, y, w, h = cv2.boundingRect(contour)

        # 获得轮廓图
        if y > edge_le:
            y1 = y - edge_le
        else:
            y1 = y

        if x > edge_le:
            x1 = x - edge_le
        else:
            x1 = x

        if x + h + edge_le > img.shape[0]:
            x2 = x + h
        else:
            x2 = x + h + edge_le

        if y + w + edge_le > img.shape[1]:
            y2 = y + w
        else:
            y2 = y + w + edge_le

        con_img = img[y1: y2, x1: x2]

        # 计算新轮廓
        for cont in contour:
            nx = cont[0][0] - x
            ny = cont[0][1] - y
            new_contour.append([[nx, ny]])

        new_contour = numpy.array(new_contour)

        return new_contour, con_img

    def judge_dig_rect(self, contours):
        s = time.time()
        contours_areas = [cv2.contourArea(cnt) for cnt in contours]
        area_thd_rect = eval(self.config["param"]["area_thd_rect"])
        round_dif = eval(self.config["param"]["round_big_dif"])
        areas = [area for area in contours_areas if area > area_thd_rect]

        rect_dic = {}

        for area in areas:
            contour = contours[contours_areas.index(area)]
            _, radius = cv2.minEnclosingCircle(contour)
            deviation_percent = abs((3.14 * radius * radius) - max(areas)) / max(areas)

            if deviation_percent < round_dif:
                rect = cv2.minAreaRect(contour)
                center = tuple(rect[0])
                rect_dic.update({int(center[1]): contour})
            # print(center[1])
            # center = numpy.int0(center)
        for _, contour in sorted(rect_dic.items(), key=lambda x: x[0], reverse=True):
            # print(_)
            yield contour
        yield numpy.array(())

    def judge_dig_round(self, contours):
        # print("检测到 元")
        contours_areas = [cv2.contourArea(cnt) for cnt in contours]
        area_thd_round = eval(self.config["param"]["area_thd_round"])
        round_dif = eval(self.config["param"]["round_dif"])
        areas = [area for area in contours_areas if area > area_thd_round]

        if areas:
            contour = contours[contours_areas.index(max(areas))]
            _, radius = cv2.minEnclosingCircle(contour)
            deviation_percent = abs((3.14 * radius * radius) - max(areas)) / max(areas)
            if deviation_percent < round_dif:
                return contour
        return numpy.array([])

    def get_contours_img(self, frame):
        x, y = eval(self.config["param"]["tar_img_size"])
        img_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # 白色识别物
        white_low_hsv = numpy.array([0, 0, 180])
        white_high_hsv = numpy.array([180, 50, 255])
        # 红色识别物
        red_low_hsv = numpy.array([156, 43, 46])
        red_high_hsv = numpy.array([180, 255, 255])
        # 蓝色识别物
        blue_low_hsv = numpy.array([100, 43, 46])
        blue_high_hsv = numpy.array([124, 255, 255])
        # 青色识别物
        green_low_hsv = numpy.array([35, 43, 46])
        green_high_hsv = numpy.array([90, 255, 255])

        low_hsvs = [red_low_hsv, blue_low_hsv, green_low_hsv]
        high_hsvs = [red_high_hsv, blue_high_hsv, green_high_hsv]

        color_tabs = eval(self.config["param"]["tab_dict"]).values()

        mask = cv2.inRange(img_hsv, lowerb=white_low_hsv, upperb=white_high_hsv)
        _, contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if self.debug:
            cv2.imshow("frame", frame)
            cv2.imshow("mask_for_rect", mask)

            key = cv2.waitKey(1) & 0xFF
            # if the `q` key was pressed, break from the loop
            if key == ord("q"):
                pass

        contour_rect_gen = self.judge_dig_rect(contours)

        for i, contour_rect in enumerate(contour_rect_gen):
            if contour_rect.any():
                _, con_rect_img = self.get_contours_area(contour_rect, frame)
                if self.debug:
                    cv2.imshow("con_rect_img", con_rect_img)
                    cv2.imwrite("TargetImg//%sx%s.jpg" % (str(frame_num), i), con_rect_img)

                    key = cv2.waitKey(1) & 0xFF
                    # if the `q` key was pressed, break from the loop
                    if key == ord("q"):
                        pass

                con_img_hsv = cv2.cvtColor(con_rect_img, cv2.COLOR_BGR2HSV)
                for low_hsv, high_hsv, tab in zip(low_hsvs, high_hsvs, color_tabs):
                    mask_round = cv2.inRange(con_img_hsv, lowerb=low_hsv, upperb=high_hsv)

                    _, contours, hierarchy = cv2.findContours(mask_round, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    contour = self.judge_dig_round(contours)
                    if contour.any():

                        new_contour, con_img = self.get_contours_area(contour, con_rect_img)
                        if self.debug:
                            cv2.imshow("target_img", con_img)

                            key = cv2.waitKey(1) & 0xFF
                            # if the `q` key was pressed, break from the loop
                            if key == ord("q"):
                                pass
                        con_img = cv2.resize(con_img, (x, y))

                        yield con_img, tab
        yield numpy.array([]), 0

    def read(self, frame_num, frame):
        # print(frame.shape)
        # self.tabs = []
        frame_little = cv2.resize(frame, (64 * self.x_times, 48 * self.y_times))

        dig_img_gen = self.get_contours_img(frame_little)
        now_tab = []
        times_thd = eval(self.config["param"]["times_thd"])
        identify_times_thd = eval(self.config["param"]["identify_times_thd"])
        pre_target = eval(self.config["param"]["test_times"])

        for dig_img, tab in dig_img_gen:
            if dig_img.any():
                now_tab.append(tab)
                tab_path = "TargetImg//%s_%s.jpg" % (str(frame_num), str(tab))
                cv2.imwrite(tab_path,  dig_img)
        # print(self.memory_tab, now_tab)
        if not self.memory_tab and not self.memory_start:
            self.memory_tab = now_tab
            self.memory_start = 1
        if now_tab:
            self.identify_times += 1
        if self.memory_tab == now_tab:
            self.times += 1
        else:
            if self.times > times_thd:
                if self.debug:
                    print(self.times, times_thd, self.memory_tab, now_tab)
                for t in self.memory_tab:
                    if t not in self.tabs and t:
                        self.tabs.append(t)
            self.memory_tab = now_tab
            self.times = 0
        if len(self.tabs) > 1 and self.debug:
            print(self.tabs, self.tabs.index(1) if len(self.tabs) == 4 else 0)

        target_tab = self.tabs.index(1) if len(self.tabs) == 4 else 0

        if self.identify_times > identify_times_thd:
            if not self.memory_time:
                self.memory_time = time.time()
            if time.time() - self.memory_time > 5.5 and 1 < len(self.tabs) < 4:
                if self.debug:
                    print("Not", self.identify_times)
                target_tab = pre_target
        return target_tab


def print_video_info(vid_cap):
    print("Width        :", vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH), "pixel")
    print("Height       :", vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT), "pixel")
    print("Frame rate   :", vid_cap.get(cv2.CAP_PROP_FPS), "/second")
    print("Num of frames:", vid_cap.get(cv2.CAP_PROP_FRAME_COUNT), "frames")


if __name__ == "__main__":
    s = time.time()
    videocap = TargetIdentify()
    videocap.debug = 1
    video = cv2.VideoCapture("DCIM//TV_CAM_设备_20191205_141928.avi")
    frame_num = 0
    index = 0
    ret, frame = video.read()
    # fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    # writer = None
    # print(frame.shape)
    print_video_info(video)
    ret, frame = video.read()
    while ret:
        ret, frame = video.read()
        frame_num += 1
        index = videocap.read(frame_num, frame)

        if index:
            print(index)

















