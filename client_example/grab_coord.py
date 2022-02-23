#抓圖上某個點在 cv 的座標

import cv2
import os

import math

refPt = []
cropping = False

def show_img(img):
    print(type(img))
    while True:
        cv2.imshow('image', img)
        key = cv2.waitKey(10)
        if key == 27 : #esc
            break

#點擊並選擇
def click_and_crop(event, x, y, flags, param):
    global refPt, cropping
    if event == cv2.EVENT_LBUTTONDOWN:
        refPt = [(x, y)]
        cropping = True
    elif event == cv2.EVENT_LBUTTONUP:
        refPt.append((x, y))
        cropping = False
        #d印出點一座標
        print('p1: ', refPt[0])
        print('p2: ', refPt[1])
        dx = abs(refPt[0][0] - refPt[1][0])
        dy = abs(refPt[0][1] - refPt[1][1])
        #印出兩點曼哈頓距離(dx,dy)
        print('md_abs: ', (dx, dy))
        #印出像素絕對距離
        d = math.sqrt(dx*dx + dy*dy)
        print('d: ', d)


if __name__ == '__main__':
    #輸入圖片或資料夾路徑
    file_path = input('輸入圖片或資料夾路徑\n')
    if os.path.isdir(file_path):
        file_folder = file_path
        file_path = None
    
    #cv2 設置窗口
    cv2.namedWindow("image")
    cv2.setMouseCallback("image", click_and_crop)

    #讀取圖片並顯示
    if file_path:
        img = cv2.imread(file_path)
        show_img(img)
    elif file_folder:
        for file in os.listdir(file_folder):
            file_path = os.path.join(file_folder, file)
            print(file_path)
            img = cv2.imread(file_path)
            show_img(img)
