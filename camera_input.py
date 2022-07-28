from utils.peko_utils.client import VideoClient

import cv2
import time
import multiprocessing as mp
import numpy as np

IP = '172.20.10.9' #
PORT = 9987

#傳輸影像
def send(recive_queue, source, shutdown:mp.Queue):
    #設定相機位址、參數
    cam_id = 0
    cam = cv2.VideoCapture(cam_id)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    #設定連接到伺服器
    vp = VideoClient(IP, PORT)
    vp.connect()
    vp.set_source_name(source)
    
    #生成新的執行緒負責從伺服器取得辨識後的影像
    r = mp.Process(target = recive, args = (vp, recive_queue))
    r.start()

    while shutdown.empty():
        #傳送影像給伺服器
        vp.send_image_from_cam(cam)
    
    #關閉連練
    r.terminate()
    vp.close()
    r.join()
    print('close connection')

#從伺服器取得
def recive(vp:VideoClient, recive_queue:mp.Queue):
    while True:
        image, gtime = vp.recive_image()
        #影像放到共享記憶體讓主執行緒存取並顯示
        recive_queue.put((image, gtime))

#顯示影像
def show_image(recive_queue:mp.Queue, shutdown:mp.Queue, bulletin):
    while True :#not recive_queue.empty() or s.is_alive():
        try:
            image, gtime = recive_queue.get(timeout=3)
        except Exception as e:
            #超時佇列是空的
            image = bulletin
            
        cv2.imshow('holive', image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            shutdown.put(1)
            break

if __name__ == '__main__':
    #"rtsp://admin:ppcb1234@192.168.154.15:554/unicast/c7/s1/live") #640 480
    source = input('enter source name\n')
    
    #設定伺服器傳送資料的佇列
    recive_queue = mp.Queue(100)
    #控制
    shutdown = mp.Queue(5)
    
    #多工處裡 子執行緒傳送/接受資料給伺服器 主執行緒顯示影像
    s = mp.Process(target = send, args = (recive_queue, source, shutdown))
    s.start()

    #布告欄
    bulletin = np.zeros((480,640,3), dtype='uint8')
    
    #顯示影像
    try:
        show_image(recive_queue, shutdown, bulletin)
    except Exception as e:
        shutdown.put(1)
        print(e)

    cv2.destroyAllWindows()



