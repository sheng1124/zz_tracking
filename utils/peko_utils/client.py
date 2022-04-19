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

    #接受影像
    def recive_image(self):
        #取得/解析影像長度資料
        img_size, buffer, encode_img_size = self.get_image_len()

        #取得/解析時間
        (t_int, t_float, buffer, encode_t_int, encode_t_float) = self.get_image_time(buffer)
        t = float('{}.{}'.format(t_int, t_float))

        #取得壓縮影像資料
        encode_img = self.get_encode_img(buffer, img_size)
        image = cv2.imdecode(np.frombuffer(encode_img, dtype = "uint8"), cv2.IMREAD_COLOR)

        return (image, t)

    #取得影像長度資料 ex: 211385
    def get_image_len(self):
        buffer = b""
        while len(buffer) < self.payload_size:
            #先 recv 固定長度去解析 影像長度資料
            data = self.remote_server.recv(4096)
            if data:
                buffer += data
        #影像長度資訊是 recv 過來的資料 位置 [0 ~ payload_size] 區段的位元組
        encode_img_size = buffer[:self.payload_size]
        #解碼長度資訊
        img_size = struct.unpack(self.payload, encode_img_size)[0]
        #清空在 buffer 中的長度資訊 方便後續處理資料
        buffer = buffer[self.payload_size:]
        return img_size, buffer, encode_img_size

    #取得影像時間資料 解碼後影像時間格式: ex: 1234.3333 sec
    def get_image_time(self, buffer):
        encode_t_int = buffer[:self.payload_size] #取得在buffer中的資料區段
        t_int = struct.unpack(self.payload, encode_t_int)[0] #解碼
        buffer = buffer[self.payload_size:] #清空在 buffer 中的資訊 方便後續處理資料
        encode_t_float = buffer[:self.payload_size]
        t_float = struct.unpack(self.payload, encode_t_float)[0]
        buffer = buffer[self.payload_size:]
        return t_int, t_float, buffer, encode_t_int, encode_t_float
    
    #取得壓縮影像
    def get_encode_img(self, buffer, img_size):
        #直接要影像長度的資料
        while len(buffer) < img_size:
            data = self.remote_server.recv(img_size - len(buffer))
            if data:
                buffer += data
        #擷取、解析壓縮影像資訊
        encode_img = buffer[:img_size]
        return encode_img