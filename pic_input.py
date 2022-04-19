import time
import os

from utils.peko_utils.client import Video_povider_client
import multiprocessing as mp
import cv2

#取得資料夾列表
def get_pic_floder_list():
    pic_floder_list = []
    pic_floder = input('輸入資料夾路徑 輸入q 離開\n')
    while pic_floder != 'q':
        pic_floder_list.append(pic_floder)
        pic_floder = input('輸入資料夾路徑 輸入q 離開\n')
    return pic_floder_list

#生成圖片路徑和時間，send_interval每隔幾張傳一次 20 就是每隔20張圖傳一張 1 全部傳
def get_pictures(pic_floder_list, send_interval=1):
    for pic_floder in pic_floder_list:
        if not os.path.isdir(pic_floder):
            continue
        i = 0
        print('start send images from', pic_floder, time.asctime(time.localtime(time.time())))
        #取的資料夾下所有檔案
        fp_list = os.listdir(pic_floder)
        #整理文件排序 按時間大小排序
        fp_list = sorted(fp_list, key = lambda id:float(id[:-4]))
        for filename in fp_list:
            #解析所有圖檔路徑並解析時間
            if filename[-4:] in ('.jpg', '.png') and not (i % send_interval):
                filepath = os.path.join(pic_floder, filename)
                ftime = float(filename[:-4])
                yield (filepath, ftime)
            i+=1

#傳輸影像
def send(recive_queue, source, pic_floder_list):    
    #設定連接到伺服器
    vp = Video_povider_client('163.25.103.111', 9987)
    vp.connect()
    vp.set_source_name(source)
    
    #生成新的執行緒負責從伺服器取得辨識後的影像
    r = mp.Process(target = recive, args = (vp, recive_queue))
    r.start()

    #整理資料夾下所有圖片路徑
    pictures = get_pictures(pic_floder_list)
    print('ready to send start time = ', time.ctime())
    while True:
        try:
            #從圖片堆疊取出一張影像的路徑和影像的時間
            filepath, ftime = next(pictures)
            #傳送影像給伺服器
            vp.send_image_by_path(filepath, ftime)
        except StopIteration:
            #已傳送所有圖片 輸出結束時間 endtime = time.time()
            print('end to send, time = ', time.ctime())
            vp.close()
            break

#從伺服器取得
def recive(vp:Video_povider_client, recive_queue:mp.Queue):
    while True:
        image, gtime = vp.recive_image()
        #影像放到共享記憶體讓主執行緒存取並顯示
        recive_queue.put((image, gtime))

#顯示影像
def show(recive_queue:mp.Queue):
    while True:
        image, gtime = recive_queue.get()
        cv2.imshow('holive', image)
        cv2.waitKey(1)


if __name__ == '__main__':
    #"rtsp://admin:ppcb1234@192.168.154.15:554/unicast/c7/s1/live") #640 480
    #輸入來源名稱
    source = input('enter source name\n')
    #輸入/設定來源資料夾
    pic_floder_list = get_pic_floder_list()

    #設定伺服器傳送資料的佇列
    recive_queue = mp.Queue(100)
    
    #多工處裡 子執行緒傳送/接受資料給伺服器 主執行緒顯示影像
    s = mp.Process(target = send, args = (recive_queue, source, pic_floder_list))
    s.start()

    #顯示影像
    while True:
        image, gtime = recive_queue.get()
        cv2.imshow('holive', image)
        cv2.waitKey(1)
