# -*- coding: utf-8 -*-
from typing import Dict
import cv2
import numpy as np
import socket
import struct
import time
import os
import threading
import multiprocessing as mp

#伺服器
class Server():
    def __init__(self, ip, port):
        #設定IP PORT
        (self.ip, self.port) = (ip, port)
        #設定伺服器物件
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #綁定IP PORT
        self.server.bind((self.ip, self.port))
        print("Server bind at ",self.ip, self.port)
        #設定連線管理清單
        self.resource_queue = mp.Queue(10)
        self.queue_dict = {'video_resource':mp.Queue(10), 'starttime':mp.Queue(1)}

    #等待客戶端連線
    def wait_connection(self):
        #聆聽
        self.server.listen(2)
        while True:
            #等待連接
            print("wait for connect")
            conn, addr = self.server.accept()
            connector = Connector(conn, addr)
            mp1 = mp.Process(target=connector.run, args=(self.queue_dict,))
            mp1.start()

#連線處理者模板
class Holder():
    #設置連線
    def set_conn(self, client_conn:socket.socket, queue_dict:Dict):
        print(type(self), "set conn")
        self.conn = client_conn
        self.queue_dict = queue_dict

    #執行
    def run(self):
        pass

#訊息提供者
class Msg_provider(Holder):
    def run(self):
        self.push_message()

    #推送訊息到佇列滿的話清掉最舊的
    def push_message(self):
        data = self.conn.recv(1024)
        if not data:
            #print("no connect from msg provider")
            raise ConnectionError("no connect from msg provider")
        if self.queue.full():
            print("queue full")
            self.queue.get()
        self.queue.put(data)

#訊息接收者
class Msg_reciver(Holder):
    def run(self):
        self.recive_message()
    
    def recive_message(self):
        data = self.queue.get()
        self.conn.sendall(data)

#影像處理者模板
class Image_holder(Holder):
    def set_conn(self, client_conn: socket.socket, queue_dict: Dict):
        super().set_conn(client_conn, queue_dict)
        #設置影像解碼參數
        self.queue = self.queue_dict['video_resource']
        self.payload = ">L"
        self.payload_size = struct.calcsize(self.payload)
        self.recv_size = 4096
    
    #解析影像長度
    def img_len_decode(self, conn):
        buffer = b""
        while len(buffer) < self.payload_size:
            data = conn.recv(self.recv_size)
            if data:
                buffer += data
            else:
                raise ConnectionError("no data from video_source")
        packed_img_size = buffer[:self.payload_size]
        img_size = struct.unpack(self.payload, packed_img_size)[0]
        buffer = buffer[self.payload_size:]
        return img_size, buffer, packed_img_size

    #解析影像時間
    def img_time_decode(self, conn, buffer):
        packed_t_int = buffer[:self.payload_size]
        t_int = struct.unpack(self.payload, packed_t_int)[0]
        buffer = buffer[self.payload_size:]
        packed_t_float = buffer[:self.payload_size]
        t_float = struct.unpack(self.payload, packed_t_float)[0]
        #t_str = '{}.{}'.format(t_int, t_float)
        #t = float(t_str)
        buffer = buffer[self.payload_size:]
        return t_int, t_float, buffer, packed_t_int, packed_t_float

    #接收壓縮資料
    def get_packed_img(self, conn, img_size, buffer):
        while len(buffer) < img_size:
            data = conn.recv(img_size - len(buffer))
            #data = conn.recv(4096)
            if data:
                buffer += data
            else:
                raise ConnectionError("no data from video_source")
        #擷取、解析壓縮影像資訊
        packed_img = buffer[:img_size]
        #移除buffer中擷取過的影像資訊
        buffer = buffer[img_size:]
        #print(len(buffer))
        return packed_img, buffer

#影像傳輸者
class Video_provider(Image_holder):
    def run(self):
        self.push_image()
    
    def push_image(self):
        #解析影像長度
        (img_size, buffer, packed_img_size) = self.img_len_decode(self.conn)

        #解析時間
        (t_int, t_float, buffer, packed_t_int, packed_t_float) = self.img_time_decode(self.conn, buffer)
        #接收壓縮資料
        (packed_img, buffer) = self.get_packed_img(self.conn, img_size, buffer)
        
        #資料重組 推送訊息到佇列
        data = (packed_img_size, packed_t_int, packed_t_float, packed_img)
        while self.queue.full():
            
            #print("queue full")
            self.queue.get()
        self.queue.put(data)
        #print("put")

#影像要求者
class Video_reciver(Image_holder):
    def run(self):
        self.recive_message()
    
    def recive_message(self):
        data = self.queue.get()
        self.conn.sendall(data[0] + data[1] + data[2] + data[3])

#影像辨識者
class Video_detector(Image_holder):
    def run(self):
        self.detect()
    
    #接收辨識結果
    def get_detect_result(self) -> list:
        results = self.conn.recv(2048)
        results = eval(results.decode())
        return results

    def write_image(self, results, packed_img):
        if len(results) < 1:
            return
        #影像解碼
        data = np.frombuffer(packed_img, dtype = "uint8")
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        #寫入檔案
        imgpath = os.path.join("data","image","raw",str(time.time())+'.jpg')
        cv2.imwrite(imgpath, img)

    def show_image(self, packed_img):
        #影像解碼
        data = np.frombuffer(packed_img, dtype = "uint8")
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        cv2.imshow('live', img)
        cv2.waitKey(1)

    def detect(self):
        #傳送影像資料給辨識端
        data = self.queue.get()
        self.conn.send(data[0])
        self.conn.sendall(data[1])
        #接收辨識結果
        results = self.get_detect_result()
        #顯示影像
        self.show_image(data[1])
        self.write_image(results, data[1])


#連線管理者
class Connector():
    def __init__(self, client_conn:socket.socket, client_addr):
        (self.conn, self.addr) = (client_conn, client_addr)
    
    #識別連線
    def conn_identify(self) -> Holder:
        #連線開始 先接受驗證訊息
        data = self.conn.recv(100)
        
        #訊息解碼確認身分
        identify = data.decode('UTF-8', errors='ignore')
        self.conn.sendall(b'1')
        print("identification: ", identify)

        #驗證身分 錯誤的身分會引發例外中斷thread
        return get_identify_holder(identify)

    def run(self, resource_queue):
        #識別連線
        handler = self.conn_identify()
        #處理連線
        handler.set_conn(self.conn, resource_queue)
        try:
            while True:
                handler.run()
        except Exception as e:
            #關閉連線
            self.close_conn(e)
        print(type(handler), "exit...")
    
    #關閉連線
    def close_conn(self, reason):
        self.conn.close()
        print("Client at ", self.addr , " disconnected... for", reason)

def get_identify_holder(identify:str) -> Holder:
    idd = {
        "msg_source" : Msg_provider(),  
        "msg_request" : Msg_reciver(),
        "video_source" : Video_provider(),
        "video_request" : Video_reciver(),
        "video_detect" : Video_detector()
    }
    return idd[identify]

if __name__ == "__main__":
    mm = Server("163.25.103.111", 9987)
    mm.wait_connection()
    