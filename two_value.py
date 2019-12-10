import cv2
import time
import numpy


def two_value_():
    img = cv2.imread("TargetImg//2467x1.jpg")
    img = cv2.resize(img, (108*4, 196*4))
    # img = cv2.resize(img, (196 * 4, 108 * 4))
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # print(img_gray)
    for i in range(img_gray.shape[0]):
        for j in range(img_gray.shape[1]):
            if img_gray[i][j] < 100 or img_gray[i][j] > 150:
                img_gray[i][j] = 255
            else:
                img_gray[i][j] = 0
    print(img_gray.shape)
    _, img_at_mean = cv2.threshold(img, 100, 255, cv2.THRESH_BINARY)

    # image, contours, hierarchy = cv2.findContours(img_gray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # img_at_mean = cv2.adaptiveThreshold(img_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 5, 0)
    cv2.imshow("contours_img", img_gray)
    # cv2.imshow("caon_img", img_at_mean)
    # cv2.imshow("con_img", 255 - img_gray)
    cv2.imwrite("smilw_tv.jpg", img_at_mean)
    cv2.imwrite("x.jpg", img_gray)
    # cv2.imwrite("x.jpg", 255 - img_gray)

    cv2.waitKey()
    cv2.destroyWindow("img")


def get_contours_area(contour, img, edge_le=5):
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

    if x+h+edge_le > img.shape[0]:
        x2 = x + h
    else:
        x2 = x + h + edge_le

    if y+w+edge_le > img.shape[1]:
        y2 = y + w
    else:
        y2 = y + w + edge_le

    con_img = img[y1: y2, x1: x2]

    # 计算新轮廓
    for cont in contour:
        nx = cont[0][0] - x - edge_le
        ny = cont[0][1] - y - edge_le
        new_contour.append([[nx, ny]])

    new_contour = numpy.array(new_contour)

    return new_contour, con_img


def get_contours_minarea(contour, img):
    new_contour = []
    # 计算轮廓的外围矩形
    # x, y, w, h = cv2.boundingRect(contour)
    point, area, r = cv2.minAreaRect(contour)
    point = tuple(int(i) for i in point)
    area = tuple(int(i) for i in area)
    r = int(r)

    # 获得轮廓图
    con_img = img[point[1]: point[1]+area[1], point[0]: point[0]+area[0]]

    # 计算新轮廓
    for cont in contour:
        nx = cont[0][0] - point[0]
        ny = cont[0][1] - point[1]
        new_contour.append([[nx, ny]])

    new_contour = numpy.array(new_contour)

    return new_contour, con_img


def color_img_equal(img):
    img1 = img[:, :, 0]
    img2 = img[:, :, 1]
    img3 = img[:, :, 2]

    equal1 = cv2.equalizeHist(img1)
    equal2 = cv2.equalizeHist(img2)
    equal3 = cv2.equalizeHist(img3)

    img = cv2.merge([equal1, equal2, equal3])

    return img


def read_digital():
    img = cv2.imread("8.png")
    # img = cv2.resize(img, (108*4, 196*4))
    img = cv2.resize(img, (196 * 4, 108 * 4))
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # cv2.imshow("gray", img_gray)

    # 自适应二值化
    img_at_mean = cv2.adaptiveThreshold(img_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 5, -2)

    # 寻找轮廓
    contours, hierarchy = cv2.findContours(img_at_mean, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # print(len(contours))

    for x in range(len(contours)):
        # imag = cv2.drawContours(img, contours, 1, (0, 0, 255), 1)

        # 获得新轮廓、轮廓图并放大
        new_contour, con_img = get_contours_area(contours[x], img)
        con_img = cv2.resize(con_img, (28, 28))

        # 计算轮廓的质心
        M = cv2.moments(new_contour)

        cv2.imshow("con_img", con_img)

        # print(M)
        # cv2.imshow("have_contours_img", imag)
        cv2.waitKey()
        # cv2.destroyWindow("have_contours_img")
        cv2.destroyWindow("con_img")

    # cv2.waitKey()
    # cv2.destroyWindow("img")


def judge_dig(img):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    low_hsv = numpy.array([0, 43, 46])
    high_hsv = numpy.array([10, 255, 255])
    mask = cv2.inRange(img_hsv, lowerb=low_hsv, upperb=high_hsv)

    sum_edge = 0
    sum_center = 0
    (x, y) = mask.shape
    # print(x, y, end='  ')
    xi = (x-1) // 4
    yi = (y-1) // 4
    # print(xi, yi)
    for i in range(5):
        for j in [0, 4]:
            point_gray = mask[i * xi, j * yi]
            if point_gray > 240:
                sum_edge += 1
    for j in range(5):
        for i in [0, 4]:
            point_gray = mask[i * xi, j * yi]
            if point_gray > 240:
                sum_edge += 1

    for j in [1, 2, 3]:
        for i in [1, 2, 3]:
            point_gray = mask[i * xi, j * yi]
            if point_gray < 20:
                sum_center += 1

    if 8 < sum_edge < 21 and sum_center >= 7:
        print("sum points", sum_edge, sum_center, end='  ')
        return mask, 1, sum_edge, sum_center
    return mask, 0, sum_edge, sum_center


def draw_contours(path):
    img = cv2.imread(path)
    # img = cv2.resize(img, (108*4, 196*4))
    # img = cv2.resize(img, (196 * 4, 108 * 4))
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # cv2.imshow("gray", img_gray)

    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    low_hsv = numpy.array([35, 43, 46])
    high_hsv = numpy.array([90, 255, 255])
    mask = cv2.inRange(img_hsv, lowerb=low_hsv, upperb=high_hsv)
    cv2.imshow("mask", mask)
    cv2.imshow("mask1", img)

    # 显示拉普拉斯效果
    # gray_lap = cv2.Laplacian(img, cv2.CV_16S, ksize=3)
    # dst = cv2.convertScaleAbs(gray_lap)
    # cv2.imshow("dst", dst)

    # 直方图均衡化
    # equal = cv2.equalizeHist(img_gray)
    # cv2.imshow("equal", equal)

    # 灰度图反向直方图均衡
    # img_gray = 255 - equal
    # cv2.imshow("inv_equal_gray", img_gray)

    # 高斯模糊
    # gauss = cv2.GaussianBlur(img_gray, (7, 7), 0)
    # cv2.imshow("gaussianblur", gauss)

    # 灰度图经高斯模糊
    # img_gray = gauss

    # 二值化
    # _, img_at_mean = cv2.threshold(img_gray, 150, 255, cv2.THRESH_BINARY_INV)

    # 自适应二值化
    # img_at_mean = cv2.adaptiveThreshold(img_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 5, -2)
    # cv2.imshow("two_value", img_at_mean)
    # cv2.imwrite("x.jpg", img_at_mean)

    # canny(): 边缘检测
    # canny = cv2.Canny(gauss, 55, 80)
    # cv2.imshow("canny", canny)

    # 二值图经canny边缘检测
    # img_at_mean = 255 - canny

    # 形态学：边缘检测
    # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))  # 定义矩形结构元素
    # gradient = cv2.morphologyEx(img_gray, cv2.MORPH_GRADIENT, kernel)  # 梯度
    # cv2.imshow("gradient", gradient)

    # 寻找轮廓
    # contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # print(len(contours))

    # 绘制所有轮廓
    # imag = cv2.drawContours(img, contours, -1, (0, 255, 0), 1)
    # cv2.imshow("contours_img", imag)
    # 绘制第x个轮廓
    # for i in range(len(contours)):
    #     # if len(contours[i]) in [16, 30, 29, 20]:
    #     # if len(contours[i]) in [49]:
    #     if len(contours[i]) > 20:
    #         # imag = cv2.drawContours(img, contours, i, (0, 0, 255), 1)
    #
    #         # 获得新轮廓、轮廓图并放大
    #         s = time.time()
    #         new_contour, con_img = get_contours_area(contours[i], img)
    #         m, ret, sum_edge, sum_center = judge_dig(con_img)
    #         # cv2.imshow("mask_con_fig", m)
    #
    #         con_img = color_img_equal(con_img)
    #
    #         con_img = cv2.resize(con_img, (80, 80))
    #
    #         # 计算轮廓的外围矩形
    #         # x, y, w, h = cv2.boundingRect(contours[i])
    #
    #         # 绘制轮廓外围矩形
    #         # cv2.rectangle(img, (x, y), (w, h), (0, 255, 0), 1)
    #
    #         # 计算轮廓的质心
    #         # M = cv2.moments(new_contour)
    #
    #         # 计算切割图的二值图
    #         # con_img_gray = cv2.cvtColor(con_img, cv2.COLOR_BGR2GRAY)
    #         # con_img_tv = cv2.adaptiveThreshold(con_img_gray, 255,
    #         #                                    cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 5, -1)
    #         # cv2.imshow("con_img_tv", con_img_tv)
    #
    #         # if M['m00'] > 20:
    #         # cv2.imshow("con_img", con_img)
    #         name = "Con_Img//%s_%s__%s_%s.jpg" % (str(sum_edge), str(sum_center), str(i), str(len(new_contour)))
    #         # print(name)
    #         if ret:
    #             cv2.imwrite(name, con_img)
    #             print(name, "contours points: ", len(new_contour))
    #             print("Use time is :", time.time() - s)
    #
    #         # cv2.imshow("have_contours_img", imag)
    #         # cv2.waitKey()
    #         # cv2.destroyWindow("have_contours_img")
    #         # cv2.destroyWindow("con_img")
    #         # cv2.destroyWindow("con_img_tv")

    cv2.waitKey()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # two_value_()
    # for i in range(3302, 5400):
    #     path = "TargetImg//" + str(i) + ".jpg"
    #     draw_contours(path)
    draw_contours("TargetImg//2467x1.jpg")
    # read_digital()
    print(" ")


