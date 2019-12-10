import cv2
import numpy
import time
import socket
import struct
import configparser


class Video2Pic:
    def __init__(self, path=0):
        self.path = path
        self.video_capt = cv2.VideoCapture(path)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.config = self.load_config()

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

    @staticmethod
    def print_video_info(vid_cap):
        print("Width        :", vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH), "pixel")
        print("Height       :", vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT), "pixel")
        print("Frame rate   :", vid_cap.get(cv2.CAP_PROP_FPS), "/second")
        print("Num of frames:", vid_cap.get(cv2.CAP_PROP_FRAME_COUNT), "frames")

    def judge_dig_rect(self, contours):
        s = time.time()
        contours_areas = [cv2.contourArea(cnt) for cnt in contours]
        area_thd_rect = eval(self.config["param"]["area_thd_rect"])
        # round_dif = eval(self.config["param"]["round_dif"])
        areas = [area for area in contours_areas if area > area_thd_rect]

        rect_dic = {}

        for area in areas:
            contour = contours[contours_areas.index(area)]
            rect = cv2.minAreaRect(contour)
            center = tuple(rect[0])
            rect_dic.update({int(center[1]): contour})
            # print(center[1])
            # center = numpy.int0(center)
        for _, contour in sorted(rect_dic.items(), key=lambda x: x[0], reverse=True):
            yield contour
        yield numpy.array(())

    def judge_dig_round(self, contours):
        s = time.time()
        contours_areas = [cv2.contourArea(cnt) for cnt in contours]
        area_thd_round = eval(self.config["param"]["area_thd_round"])
        round_dif = eval(self.config["param"]["round_dif"])
        areas = [area for area in contours_areas if area > area_thd_round]

        # for area in areas:
        #     contour = contours[contours_areas.index(area)]
        #     _, radius = cv2.minEnclosingCircle(contour)
        #     deviation_percent = abs((3.14 * radius * radius) - area) / area
        #     # print("我在检测...", deviation_percent, abs((3.14 * radius * radius) - area), area)
        #     if deviation_percent < round_dif:
        #         # print("判断用时:  ", (time.time() - s))
        #         # print("圆面积: ", area)
        #         return contour
        # return numpy.array([])

        if areas:
            contour = contours[contours_areas.index(max(areas))]
            # print(max(areas))
            _, radius = cv2.minEnclosingCircle(contour)
            deviation_percent = abs((3.14 * radius * radius) - max(areas)) / max(areas)
            # print(deviation_percent)
            # print("我在检测...", deviation_percent, abs((3.14 * radius * radius) - area), area)
            if deviation_percent < round_dif:
                # print("判断用时:  ", (time.time() - s))
                # print("圆面积: ", area)
                return contour
        return numpy.array([])
        # try:
        #     contour = contours[contours_areas.index(max(contours_areas))]
        #     center, _ = cv2.minEnclosingCircle(contour)
        #     center = numpy.int0(center)
        #     return contour, center
        # except Exception as e:
        #     print(e)
        #     return numpy.array([]), numpy.array([])

    def get_contours_img(self, frame):
        # frame = cv2.resize(frame, (196 * 4, 108 * 4))
        s = time.time()
        x, y = eval(self.config["param"]["tar_img_size"])
        img_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # 白色识别物
        white_low_hsv = numpy.array([0, 0, 170])
        white_high_hsv = numpy.array([180, 70, 255])
        # 红色识别物
        red_low_hsv = numpy.array([0, 43, 46])
        red_high_hsv = numpy.array([10, 255, 255])
        # 蓝色识别物
        blue_low_hsv = numpy.array([100, 43, 46])
        blue_high_hsv = numpy.array([124, 255, 255])
        # 青色识别物
        green_low_hsv = numpy.array([35, 43, 46])
        green_high_hsv = numpy.array([99, 255, 255])
        # # 绿色识别物
        # green2_low_hsv = numpy.array([35, 43, 46])
        # green2_high_hsv = numpy.array([99, 255, 255])
        # # # 红蓝绿三色识别物
        # low_hsv = numpy.array([35, 43, 46])
        # high_hsv = numpy.array([180, 255, 255])

        low_hsvs = [red_low_hsv, blue_low_hsv, green_low_hsv]
        high_hsvs = [red_high_hsv, blue_high_hsv, green_high_hsv]
        #
        color_tabs = eval(self.config["param"]["tab_dict"]).values()
        # print(color_tabs)

        mask = cv2.inRange(img_hsv, lowerb=white_low_hsv, upperb=white_high_hsv)
        image, contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # cv2.imshow("mask", mask)
        # if cv2.waitKey(1) == ord("w"):
        #     pass

        contour_rect_gen = self.judge_dig_rect(contours)
        for contour_rect in contour_rect_gen:
            # cv2.drawContours(frame, contour_rect, -1, (0, 255, 255), 7)
            # print(1)
            if contour_rect.any():
                _, con_rect_img = self.get_contours_area(contour_rect, frame)
                # cv2.imshow("con_rect_img", con_rect_img)
                # if cv2.waitKey(1) == ord("w"):
                #     pass
                con_img_hsv = cv2.cvtColor(con_rect_img, cv2.COLOR_BGR2HSV)
                for low_hsv, high_hsv, tab in zip(low_hsvs, high_hsvs, color_tabs):
                    mask_round = cv2.inRange(con_img_hsv, lowerb=low_hsv, upperb=high_hsv)

                    # cv2.imshow("imag", mask_round)
                    # if cv2.waitKey(1) == ord("w"):
                    #     pass

                    image, contours, hierarchy = cv2.findContours(mask_round, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    contour = self.judge_dig_round(contours)
                    if contour.any():
                        # print("%d 号颜色已经被检测到...." % tab)
                        new_contour, con_img = self.get_contours_area(contour, con_rect_img)
                        # cv2.imshow("imag", con_img)
                        # if cv2.waitKey(1) == ord("w"):
                        #     pass
                        con_img = cv2.resize(con_img, (x, y))
                        # print(tab)
                        # imag = cv2.drawContours(frame, contour, -1, (255, 0, 0), 5)
                        # cv2.imshow("mask", imag)
                        # if cv2.waitKey(1) == ord("w"):
                        #     pass
                        # print(tab)
                        yield con_img, tab
                        # print("获取轮廓用时: ", time.time() - s)
                # cv2.circle(con_img, tuple(center), 2, (255, 255, 0), 5)

                # print(center)
                # con_img = cv2.cvtColor(con_img, cv2.COLOR_BGR2CMYK)
                # print(con_img[center[0], center[1]], type(con_img[center[0], center[1]]),
                # numpy.uint8([[con_img[center[0], center[1]]]]))
                # print(cv2.cvtColor(numpy.uint8([[con_img[center[0], center[1]]]]), cv2.COLOR_BGR2HSV))
                # cv2.circle(con_img, tuple(center), 2, (255, 255, 0), 5)
                # imag = cv2.drawContours(con_img, contour, -1, (255, 255, 0), 5)

        # contour_gen = self.judge_dig(contours)
        # for i, contour in enumerate(contour_gen):
        #     if contour.any():
        #         new_contour, con_img = self.get_contours_area(contour, frame)
        #         con_img = cv2.resize(con_img, (x, y))
        #         # print("中心点的RGB值为： ", con_img[x // 2, y // 2])
        #         # tab = color_tabs[list(con_img[x // 2, y // 2]).index(max(con_img[x // 2, y // 2]))]
        #         # print(color)
        #         yield con_img, list(con_img[x // 2, y // 2]).index(max(con_img[x // 2, y // 2]))+1
        #         # print("获取轮廓用时: ", time.time() - s)
        yield numpy.array([]), 0
        # cv2.imshow("mask", mask)
        # cv2.imshow("imag", con_rect_img)
        # if cv2.waitKey(1) == ord("w"):
        #     pass
        # # yield numpy.array([]), 0
        # # 对三种颜色扫描以获取
        # for low_hsv, high_hsv, tab in zip(low_hsvs, high_hsvs, color_tabs):
        #     mask = cv2.inRange(img_hsv, lowerb=low_hsv, upperb=high_hsv)
        #     contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        #
        #     # cv2.imshow("mask", mask)
        #     # if cv2.waitKey(1) == ord("w"):
        #     #     break
        #     # cv2.imshow("frame", frame)
        #     # cv2.imshow("mask", mask)
        #     # # cv2.imshow("con_ing", con_img)
        #     # cv2.waitKey()
        #     contour = self.judge_dig_round(contours)
        #     if contour.any():
        #         new_contour, con_img = self.get_contours_area(contour, frame)
        #         con_img = cv2.resize(con_img, (x, y))
        #         # print(tab)
        #         # imag = cv2.drawContours(frame, contour, -1, (255, 0, 0), 5)
        #         # cv2.imshow("mask", imag)
        #         # if cv2.waitKey(1) == ord("w"):
        #         #     pass
        #         yield con_img, tab
        #         # print("获取轮廓用时: ", time.time() - s)
        #     yield numpy.array([]), 0

    def video2pic(self, vid_cap):
        frame_num = 0
        offset_start = 0.0
        offset_end = 0.0
        # w = vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        # h = vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        if vid_cap.isOpened() is not True:
            print("Error 01: Failed to open")
            exit()

        totalFrameNum = vid_cap.get(cv2.CAP_PROP_FRAME_COUNT)
        rateFrameNum = vid_cap.get(cv2.CAP_PROP_FPS)
        offset_start_frame = int(offset_start * rateFrameNum)
        offset_end_frame = totalFrameNum - int(offset_end * rateFrameNum)
        print("Total frame number :" + str(totalFrameNum))

        memory_tab = []
        times = 0
        tabs = [0]
        s = time.time()

        x_times, y_times = eval(self.config["param"]["xy_times"])

        while vid_cap.isOpened():
            frame_num = frame_num + 1
            # s1 = time.time()
            if (frame_num >= offset_start_frame) and (frame_num <= offset_end_frame):
                # vid_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                success, frame = vid_cap.read()
                # print(frame.shape)
                frame = cv2.resize(frame, (196 * x_times, 108 * y_times))
                # 对摄像头传回图像进行边缘切割
                # incision_start = int(w * (1 - eval(self.config["param"]["incision_rate"])) / 2)
                # incision_end = int(w * (1 - eval(self.config["param"]["incision_rate"]) / 2))
                # frame = frame[incision_start: incision_end, 0: int(h)]

                # 若要更改识别内容，需更改识别物轮廓，调整以下函数
                # s2 = time.time()
                # print("获取帧图用时:  ", s2 - s1)
                dig_img_gen = self.get_contours_img(frame)
                try:
                    dig_img, tab = next(dig_img_gen)
                except StopIteration:
                    continue
                if not frame_num % 1000:
                    print(frame_num, "用时: ", time.time() - s)
                    s = time.time()
                now_tab = []
                # cv2.imshow("Frame", frame)
                # if cv2.waitKey(1) == ord("q"):
                #     break
                while True:
                    now_tab.append(tab)
                    if dig_img.any():
                        cv2.imwrite("Img1//%s.jpg" % str(frame_num), frame)
                        name = "Img1//%s_%s.jpg" % (str(frame_num), str(tab))
                        # print(name)
                        cv2.imwrite(name,  dig_img)
                        # print("检测到目标", frame_num)
                    try:
                        dig_img, tab = next(dig_img_gen)
                    except StopIteration:
                        break
                s3 = time.time()
                # print("目标识别用时: ", s3 - s2)
                # print("判别一帧用时: ", s3 - s1)
                if not memory_tab:
                    memory_tab = now_tab
                if memory_tab == now_tab:
                    times += 1
                else:
                    if times > 10:
                        for t in memory_tab:
                            if t != tabs[-1] and t:
                                tabs.append(t)
                    memory_tab = now_tab
                    times = 0
            if frame_num > totalFrameNum:
                print("Frame Num :", frame_num, "Use Time :", time.time() - s)
                break

        print(tabs)

    def capture2pic(self, vid_cap):
        if vid_cap.isOpened() is not True:
            print("Error 01: Failed to open")
            exit()
        memory_tab = []
        times = 0
        tabs = [0]
        s = time.time()
        frame_num = 0
        x_times, y_times = eval(self.config["param"]["xy_times"])
        while vid_cap.isOpened():
            frame_num += 1
            _, frame = vid_cap.read()
            # print(frame.shape)
            frame = cv2.resize(frame, (64 * x_times, 48 * y_times))
            # 对摄像头传回图像进行边缘切割
            # incision_start = int(w * (1 - eval(self.config["param"]["incision_rate"])) / 2)
            # incision_end = int(w * (1 - eval(self.config["param"]["incision_rate"]) / 2))
            # frame = frame[incision_start: incision_end, 0: int(h)]

            # 若要更改识别内容，需更改识别物轮廓，调整以下函数
            # s2 = time.time()
            # print("获取帧图用时:  ", s2 - s1)
            dig_img_gen = self.get_contours_img(frame)
            try:
                dig_img, tab = next(dig_img_gen)
            except StopIteration:
                continue
            if not frame_num % 1000:
                print(frame_num, "用时: ", time.time() - s)
                s = time.time()
            now_tab = []
            times_thd = eval(self.config["param"]["times_thd"])
            # cv2.imshow("Frame", frame)
            # if cv2.waitKey(1) == ord("q"):
            #     break
            while True:
                if dig_img.any():
                    now_tab.append(tab)
                    # cv2.imwrite("Img1//%s.jpg" % str(frame_num), frame)
                    tab_path = "Img1//%s_%s.jpg" % (str(frame_num), str(tab))
                    cv2.imwrite(tab_path,  dig_img)
                    # print("检测到目标", frame_num)
                try:
                    dig_img, tab = next(dig_img_gen)
                except StopIteration:
                    break
            s3 = time.time()
            # print("目标识别用时: ", s3 - s2)
            # print("判别一帧用时: ", s3 - s1)
            if not memory_tab:
                memory_tab = now_tab
            if memory_tab == now_tab:
                times += 1
            else:
                if times > times_thd:
                    # print(memory_tab, times)
                    for t in memory_tab:
                        if t not in tabs and t:
                            tabs.append(t)
                memory_tab = now_tab
                times = 0
            #     break
            # frame_digs = []
            # _, frame = vid_cap.read()
            # frame = cv2.bilateralFilter(frame, 5, 50, 100)  # smoothing filter
            # # frame = cv2.flip(frame, 1)  # flip the frame horizontally
            # cv2.imshow("Frame", frame)
            # frame_num = frame_num + 1
            # dig_img_gen = self.get_contours_img(frame)
            # try:
            #     dig_img, sum_edge, sum_center = next(dig_img_gen)
            # except StopIteration:
            #     if cv2.waitKey(1) == ord("q"):
            #         break
            #     continue
            # i = 0
            # while dig_img.any():
            #     if not i:
            #         cv2.imwrite("Img2//%s.jpg" % str(frame_num), frame)
            #     i += 1
            #     cv2.imwrite("Img2//%s_%s.jpg" % (str(frame_num), str(i)),
            #                 dig_img)
            #     print("检测到目标", frame_num)
            #     try:
            #         dig_img, sum_edge, sum_center = next(dig_img_gen)
            #     except StopIteration:
            #         break
            #     # if cv2.waitKey(1) == ord("q"):
            #     #     break
            if len(tabs) == 4:
                # print(tabs.index(1))
                try:
                    self.udp_socket.sendto(str(tabs.index(1)).encode("gbk"), ("localhost", 8080))
                except Exception as e:
                    print(e)
                    pass
            # cv2.imshow("Frame", cv2.resize(frame, (196 * 4, 108 * 4)))
            # if cv2.waitKey(1) == ord("q"):
            #     break
        # print(frame_digs)
        #     print(tabs)
        # print(tabs)

    def process_frame(self, frame):
        memory_tab = []
        times = 0
        tabs = [0]
        frame_num = 0
        x_times, y_times = eval(self.config["param"]["xy_times"])

        frame = cv2.resize(frame, (64 * x_times, 48 * y_times))

        dig_img_gen = self.get_contours_img(frame)
        try:
            dig_img, tab = next(dig_img_gen)
        except StopIteration:
            return
        now_tab = []
        while True:
            if dig_img.any():
                now_tab.append(tab)
                # cv2.imwrite("Img1//%s.jpg" % str(frame_num), frame)
                tab_path = "Img1//%s_%s.jpg" % (str(frame_num), str(tab))
                cv2.imwrite(tab_path, dig_img)
                # print("检测到目标", frame_num)
            try:
                dig_img, tab = next(dig_img_gen)
            except StopIteration:
                break
        if not memory_tab:
            memory_tab = now_tab
        if memory_tab == now_tab:
            times += 1
        else:
            if times > 0:
                for t in memory_tab:
                    if t not in tabs and t:
                        tabs.append(t)

        if len(tabs) == 4:
            try:
                self.udp_socket.sendto(str(tabs.index(1)).encode("gbk"), ("localhost", 8080))
            except Exception as e:
                print(e)
                pass

    def run(self):
        self.print_video_info(self.video_capt)
        if not self.path:
            self.capture2pic(self.video_capt)
        else:
            self.video2pic(self.video_capt)


def wait_start():
    udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    local_addr = ("localhost", 8080)
    udp_server.bind(local_addr)
    while True:
        recv_data = udp_server.recvfrom(1024)
        if eval(recv_data[0].decode("gbk")):
            udp_server.close()
            break


if __name__ == "__main__":
    # wait_start()
    s = time.time()
    # video_format = ".mov"
    # video_name = "VideoDemo1"
    # video_path = "./"
    # path = video_path + video_name + video_format
    videocap = Video2Pic(0)
    videocap.run()
    print("Use Sum Time is: ", time.time() - s)

    pass















