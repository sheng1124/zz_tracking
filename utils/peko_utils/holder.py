import socket
import struct
import time
import numpy as np
import cv2
from typing import Dict
import tracker

#Holder 必須要用 multli processing or multi threading 執行

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
        self.queue = self.queue_dict['video_queue']
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
    def set_conn(self, client_conn: socket.socket, queue_dict: Dict):
        super().set_conn(client_conn, queue_dict)
        self.request_queue = queue_dict['request_queue']

    def run(self):
        if not self.request_queue.empty():
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

#影像辨識要求者
class Detect_request(Image_holder):
    def set_conn(self, client_conn: socket.socket, queue_dict: Dict):
        super().set_conn(client_conn, queue_dict)
        self.detect_queue = queue_dict['detect_queue']
        self.request_queue = queue_dict['request_queue']
        self.request_queue.put('time')
        self.start_time = time.time()
        self.max_time = 3600.0
    
    def run(self):
        try:
            self.recive_message()
        except Exception as e:
            self.pop_request()
            raise e

    def recive_message(self):
        if time.time() - self.start_time > self.max_time:
            raise AttributeError("out max limit")
        data = self.detect_queue.get()
        self.conn.sendall(data[0] + data[1] + data[2] + data[3])

    #清掉要求queue避免佔用
    def pop_request(self):
        self.request_queue.get()

#影像辨識者
class Video_detector(Image_holder):
    def set_conn(self, client_conn: socket.socket, queue_dict: Dict):
        super().set_conn(client_conn, queue_dict)
        self.detect_queue = queue_dict['detect_queue']
        self.encode_parm=[int(cv2.IMWRITE_JPEG_QUALITY), 100]

    def run(self):
        self.detect()
    
    #畫人框
    def draw_frame(self, img, results):
        w = int(img.shape[1])
        h = int(img.shape[0])
        for box in results:
            (x1, y1, x2, y2) = (int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h))
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)

    #接收辨識結果
    def get_detect_result(self) -> list:
        results = self.conn.recv(2048)
        results = eval(results.decode())
        return results

    def write_image(self, results, img):
        if len(results) < 1:
            return
        #寫入檔案
        imgpath = os.path.join("data","image","raw",str(time.time())+'.jpg')
        cv2.imwrite(imgpath, img)

    def show_image(self, img):
        cv2.imshow('live', img)
        cv2.waitKey(1)

    #解碼
    def data_decode(self, data):
        t_int = struct.unpack(self.payload, data[1])[0]
        t_float = struct.unpack(self.payload, data[2])[0]
        t = float('{}.{}'.format(t_int, t_float))
        img_packed = np.frombuffer(data[3], dtype = "uint8")
        img = cv2.imdecode(img_packed, cv2.IMREAD_COLOR)
        return (t, img)

    #影像壓縮取得壓縮後的長度和img
    def data_encode(self, img):
        ret, img_encode = cv2.imencode(".jpg", img, self.encode_parm)
        img_encode_byte = img_encode.tobytes()
        img_encode_byte_size = len(img_encode_byte)
        size_en = struct.pack(self.payload, img_encode_byte_size)
        return size_en, img_encode_byte

    
    def tracking(self, results):
        #
        for box in results:
            #如果tracking list < 1 建立新的tracker
            pass

    def detect(self):
        #傳送影像資料給辨識端
        data = self.queue.get()
        self.conn.sendall(data[0] + data[3])
        newdata = [data[0], data[1], data[2], data[3]]
        #解碼
        (t, img) = self.data_decode(data)
        #接收辨識結果
        results = self.get_detect_result()
        #追蹤 bounding box


        if len(results) > 0:
            #有解果就畫圖像
            self.draw_frame(img, results)
            #圖像壓縮計算長度
            (size_img_pack, img_pack) = self.data_encode(img)
            newdata[0], newdata[3] = size_img_pack, img_pack
        
        #丟進辨識進結果queue
        self.detect_queue.put(newdata)
        #上傳資料庫
