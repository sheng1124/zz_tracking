import socket
import struct
import cv2
import numpy as np
import time
import os

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
class Video_client(Client):
    def __init__(self, remote_ip: str, remote_port: int):
        super().__init__(remote_ip, remote_port)
        self.payload = ">L"
        self.payload_size = struct.calcsize(self.payload)
    
    #從伺服器取得影像
    def get_image(self):
        buffer = b''
        #長度解碼
        while len(buffer) < self.payload_size:
            buffer += self.remote_server.recv(4096)
        packed_img_size = buffer[:self.payload_size]
        img_size = struct.unpack(self.payload, packed_img_size)[0]
        #時間解碼
        
        buffer = buffer[self.payload_size:]
        packed_t_int = buffer[:self.payload_size]
        t_int = struct.unpack(self.payload, packed_t_int)[0]
        buffer = buffer[self.payload_size:]
        packed_t_float = buffer[:self.payload_size]
        t_float = struct.unpack(self.payload, packed_t_float)[0]
        t_str = '{}.{}'.format(t_int, t_float)
        t = float(t_str)

        #影像解碼
        buffer = buffer[self.payload_size:]
        while len(buffer) < img_size:
            buffer += self.remote_server.recv(img_size - len(buffer))
        packed_image = buffer[:img_size]
        data = np.frombuffer(packed_image, dtype = "uint8")
        image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    
        return (t,image)

class Video_povider_client(Video_client):
    def __init__(self, remote_ip: str, remote_port: int):
        super().__init__(remote_ip, remote_port)
        self.encode_parm=[int(cv2.IMWRITE_JPEG_QUALITY), 100]

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
        #影像壓縮
        ret, img_encode = cv2.imencode(".jpg", img, self.encode_parm)
        img_encode_byte = img_encode.tobytes()
        #取得影像長度並打包
        img_encode_byte_size = len(img_encode_byte)
        packed = struct.pack(self.payload, img_encode_byte_size) 
        #加入時間資訊
        if t:
            str_t = str(t).split('.')
            int_t = int(str_t[0])
            float_t = int(str_t[1])
            packed += struct.pack(self.payload, int_t) + struct.pack(self.payload, float_t)
        #傳送給伺服器
        packed += img_encode_byte
        self.remote_server.sendall(packed)
        #print('send time = ', t)
