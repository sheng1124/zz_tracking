from utils.peko_utils.client import Video_povider_client

import cv2
import time
import multiprocessing as mp

#傳輸影像
def send(recive_queue, source):
    #設定相機位址、參數
    cam_id = 0
    cam = cv2.VideoCapture(cam_id)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    #設定連接到伺服器
    vp = Video_povider_client("163.25.103.111", 9987)
    vp.connect()
    vp.set_source_name(source)
    
    
    #生成新的執行緒負責從伺服器取得辨識後的影像
    r = mp.Process(target = recive, args = (vp, recive_queue))
    r.start()

    while True:
        #傳送影像給伺服器
        vp.send_image_from_cam(cam)

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
    source = input('enter source name\n')
    
    #設定伺服器傳送資料的佇列
    recive_queue = mp.Queue(100)
    
    #多工處裡 子執行緒傳送/接受資料給伺服器 主執行緒顯示影像
    s = mp.Process(target = send, args = (recive_queue, source))
    s.start()
    
    #顯示影像
    while True:
        image, gtime = recive_queue.get()
        cv2.imshow('holive', image)
        cv2.waitKey(1)



