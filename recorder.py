#定時截圖
#可設定時間範圍 ex: 8am ~ 17am
import cv2
import time
import os

CAMERA_ID = 0 #"rtsp://admin:ppcb1234@192.168.154.15:554/unicast/c7/s1/live"

class Camera():
    def __init__(self, cam_id = 0, resolution = None, encode_parm = 100):#resolution = (640, 480)
        #壓縮比例(有損壓縮)
        self.encode_parm=[int(cv2.IMWRITE_JPEG_QUALITY), encode_parm]
        self.cam_id = cam_id
        #開啟攝影機 cam_id 是攝影機位址 0 是本地0號攝影機 http://... 是網路攝影機
        self.cam = cv2.VideoCapture(cam_id)
        #設定解析度 有的要設定有的不用 預設不用設解析度
        self.resolution = resolution
        self.set_resolution()
        self.pretime = 0
        
    #設定解析度
    def set_resolution(self):
        if not self.resolution is None:
            self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

    #當攝影機掛掉需要重製
    def reset(self):
        try:
            self.cam.release()
            self.cam = cv2.VideoCapture(self.cam_id)
            self.set_resolution()
        except Exception as e:
            print(e)

    #截圖
    def record(self, outputpath, fps):
        while True:
            try:
                #讀取影像
                *_, img = self.cam.read()
                
                #設定時間
                twtime = time.time()
                twlocaltime = time.localtime(twtime)
                localtime = time.asctime(twlocaltime)
                
                #不允許的時間範圍 continue
                hour = int(localtime[11:13])
                week = localtime[0:3]
                if not (7 < hour < 20) or week in ('Sat', 'Sun'):
                    continue

                #用時間設定檔案夾名稱 年-月-日-小時
                dirpath = '{}-{}-{}-{}'.format(
                    localtime[-4:],
                    localtime[4:7],
                    localtime[8:10],
                    localtime[11:13])
                dirpath = os.path.join(outputpath, 'record', dirpath)

                if not os.path.isdir(dirpath):
                    os.makedirs(dirpath)
                filepath = os.path.join(dirpath, str(twtime) + '.jpg')
                if fps > 0 and twtime - self.pretime > 1/(fps+1):
                    cv2.imwrite(filepath, img)
                    self.pretime = twtime

            except Exception as e:
                print(e)
                #攝影機可能無法連線 重置
                self.reset()

if __name__ == '__main__':
    cam = Camera(CAMERA_ID) #640 480
    cam.record('./recode', 3)
    

