import socket
import cv2
import numpy as np
import time
from utils.peko_utils import imged

class Client():
    def __init__(self, remote_ip:str, remote_port:int):
        (self.remote_ip, self.remote_port) = (remote_ip, remote_port)
        #遠端伺服器串接 
        self.remote_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    #連線到遠端伺服器
    def connect(self):
        self.remote_server.connect((self.remote_ip, self.remote_port))
        print("connect to ", self.remote_ip, self.remote_port)

    #設定來源名稱
    def set_source_name(self, source_name):
        self.remote_server.sendall(bytes(source_name, "UTF-8"))
        self.remote_server.recv(1)

    #關閉連線
    def close(self):
        self.remote_server.close()

#影像相關客戶端
class VideoClient(Client):
    def __init__(self, remote_ip: str, remote_port: int):
        super().__init__(remote_ip, remote_port)
        self.ie = imged.ImageEd()

    #傳送 cv2 cam 相機的照片請確認相機可用
    def send_image_from_cam(self, cam):
        ret, img = cam.read()
        t = time.time()
        self.send_image(img, t)
    
    #傳送路徑的照片
    def send_image_by_path(self, filepath, ftime:float):
        #print(type(ftime), ftime)
        img = cv2.imread(filepath)
        if type(ftime) != type(0.0) or ftime <= 0.0:
            self.send_image(img, time.time())
        else:
            self.send_image(img, ftime)
    
    #傳送圖片
    def send_image(self, img, t:float):
        #打包影像
        packed = self.ie.pack(img, t)
        
        #傳送給伺服器
        self.remote_server.sendall(packed)
        #print('send time = ', t)
    
    #接受影像
    def recive_image(self):
        #影像解包
        img, gtime = self.ie.unpack(self.remote_server)
        return (img, gtime)