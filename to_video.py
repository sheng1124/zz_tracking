# -*- coding: utf-8 -*-
# 圖片資料夾轉成影片

import cv2
import time
import os
import pic_input

#生成圖片路徑和時間，send_interval每隔幾張傳一次 20 就是每隔20張圖傳一張 1 全部傳
def get_pictures(pic_floder_list):
    for pic_floder in pic_floder_list:
        if not os.path.isdir(pic_floder):
            continue
        i = 0
        print('start time', pic_floder, time.asctime(time.localtime(time.time())))
        # 取的資料夾下所有檔案
        fp_list = os.listdir(pic_floder)
        #整理文件排序 按時間大小排序
        fp_list = sorted(fp_list, key = lambda id:float(id[:-4]))
        for filename in fp_list:
            #解析所有圖檔路徑並解析時間
            if filename[-4:] in ('.jpg', '.png') :
                filepath = os.path.join(pic_floder, filename)
                ftime = float(filename[:-4])
                yield (filepath, ftime)
            i+=1

# 取得影像尺寸
def get_shape(arg):
    print(arg)
    filepath, ftime = arg
    img = cv2.imread(filepath, cv2.IMREAD_COLOR)
    return img.shape

# 整理資料夾影像並計算出影片要的 FPS ， 參數資料夾
def count_fps(f_path):
    #整理資料夾所有影像出現的時間
    time_list = [int(ftime) for filepath, ftime in get_pictures(f_path)]
    #秒數(整數)不重複列表，等一下要用來計算每個秒數有多少張影像 就是那一秒的 fps
    x_time_list = []
    for e in time_list:
        if e not in x_time_list:
            x_time_list.append(e)
    #計算每個秒數有多少張影像
    count_list = [time_list.count(e) for e in x_time_list]
    #計算平均每秒有多少影像就是等遺下影片要設定的播放FPS
    fps = sum(count_list) / len(count_list)
    return fps

if __name__ == '__main__':
    f_path = pic_input.get_pic_floder_list()
    print(f_path)

    # 取得影像尺寸
    shape = get_shape(next(get_pictures(f_path)))

    #計算影片要得fps
    fps = count_fps(f_path)
    print(fps)

    #宣告影片編輯器
    fourcc = cv2.VideoWriter_fourcc('X', 'V', 'I', 'D')
    out = cv2.VideoWriter('output.avi', fourcc, fps, (shape[1], shape[0]))

    for filepath, ftime in get_pictures(f_path):
        #讀取每個影像
        frame = cv2.imread(filepath, cv2.IMREAD_COLOR)
        #寫入影像
        out.write(frame)
    
    #關閉並儲存 若不正常關閉程式沒有執行到這一行將不會存到影片，可用 try while 預防
    out.release()
    