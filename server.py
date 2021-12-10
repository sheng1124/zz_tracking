# -*- coding: utf-8 -*-
import cv2
import numpy as np
import socket
import struct
import time
import os
import threading
import multiprocessing as mp


#伺服器處理連線
class Connect_handler(threading.Thread):

    #顯示影像
    def __show_packed_img(self, packed_img):
        data = np.frombuffer(packed_img, dtype = "uint8")
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        cv2.imshow(self.windowname, img)
        cv2.waitKey(1)


    #存圖片
    def __write_img(self, packed_img):
        data = np.frombuffer(packed_img, dtype = "uint8")
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        cv2.imwrite(str(time.time())+'.jpg', img)
    
    #辨識影像客戶端
    def video_detect_hand(self):
        #取得影像來源
        source_conn = self.get_video_source()

        #解析影像長度
        (img_size, buffer, packed_img_size) = self.__img_len_decode(source_conn)
        
        #接收壓縮資料
        (packed_img, buffer) = self.__get_packed_img(source_conn, img_size, buffer)

        #傳送長度資訊+壓縮影像給 detecter
        self.conn.sendall(packed_img_size + packed_img)
            
        #接受辨識結果
        results = self.conn.recv(2048)
        results = eval(results.decode())
        #有人就存圖
        if len(results) > 0:
            #儲存圖片
            self.__write_img(packed_img)
    


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

    #等待客戶端連線
    def wait_connection(self):
        #聆聽
        self.server.listen(2)
        while True:
            #等待連接
            print("wait for connect")
            conn, addr = self.server.accept()
            connector = Connector(conn, addr)
            mp1 = mp.Process(target=connector.run, args=(self.resource_queue,))
            mp1.start()

#連線處理者模板
class Holder():
    #設置連線
    def set_conn(self, client_conn:socket.socket, queue:mp.Queue):
        print(type(self), "set conn")
        self.conn = client_conn
        self.queue = queue

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

class Image_holder(Holder):
    def set_conn(self, client_conn: socket.socket, queue: mp.Queue):
        super().set_conn(client_conn, queue)
        #設置影像解碼參數
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
            
        #接收壓縮資料
        (packed_img, buffer) = self.get_packed_img(self.conn, img_size, buffer)
        
        #資料重組 推送訊息到佇列
        data = packed_img_size + packed_img
        if self.queue.full():
            print("queue full")
            self.queue.get()
        self.queue.put(data)
        #print("put")

class Video_reciver(Holder):
    def run(self):
        self.recive_message()
    
    def recive_message(self):
        data = self.queue.get()
        self.conn.sendall(data)

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
        "video_detect" : "self.video_detect_hand"
    }
    return idd[identify]

if __name__ == "__main__":
    mm = Server("163.25.103.111", 9987)
    mm.wait_connection()
    