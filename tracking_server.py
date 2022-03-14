# -*- coding: utf-8 -*-
import sys
sys.path.append("yolov4")
from yolov4.tool.utils import *
from yolov4.tool.torch_utils import *
from yolov4.tool.darknet2pytorch import Darknet

import argparse
import torch
torch.cuda.empty_cache()

import socket
import struct
import numpy as np
import cv2

import multiprocessing as mp

from utils.peko_utils import tracker
from utils.peko_utils import sop

USE_CUDA = True
#要不要用資料庫 不設定->None
DB_NAME = 'object_tracking'
IP = '163.25.103.111'
PORT = 9987


#設定 yolo 模型的參數
def set_args():
    parser = argparse.ArgumentParser('Test your image or video by trained model.')
    parser.add_argument('-cfgfile', type=str, default='data/cfg/yolov4.cfg',
                        help='path of cfg file', dest='cfgfile')
    parser.add_argument('-weightfile', type=str,
                        default='data/weights/yolov4.weights',
                        help='path of trained model.', dest='weightfile')
    args = parser.parse_args()

    return args

#Yolo v4 辨識者
class Detector():
    def __init__(self, cfgfile, weightfile) -> None:
        #載入網路模型
        m = Darknet(cfgfile)
        #m.print_network()
        #載入權重
        m.load_weights(weightfile)
        if USE_CUDA:
            m.cuda()
        self.m = m

        #設定辨識類別名稱
        num_classes = m.num_classes
        if num_classes == 80:
            namesfile = 'data/coco.names'
        else:
            print("no names file")
        class_names = load_class_names(namesfile)
        self.class_names = class_names
    
    #辨識圖片
    def detect(self, img):
        sized = cv2.resize(img, (self.m.width, self.m.height)) # size 608 * 608 3e-4 sec
        sized = cv2.cvtColor(sized, cv2.COLOR_BGR2RGB) #4e-4 sec
        boxes = do_detect(self.m, sized, 0.4, 0.6, USE_CUDA) #5e-2 sec
        return boxes
    
    #辨識人 只取有人的類別的框
    def get_person(self, boxes):
        results =[]
        for box in boxes:
            if box[6] == 0:
                results.append(box)
        return results
    
    def run(self, source_queue:mp.Queue, d_result_queue:mp.Queue):
        while True:
            img, gtime, site = source_queue.get()
            #辨識影像
            boxes = self.detect(img)
            #print(boxes)
            results = self.get_person(boxes[0])
            #插入佇列結果
            while d_result_queue.full():
                #print('d_result_queue full')
                pass
            d_result_queue.put((img, gtime, site, results)) #2 e-5

            


class Monitor():
    def __init__(self) -> None:
        #設定控制
        pass

    def run(self, output_queue:mp.Queue):
        while True:
            #取得影像
            img = output_queue.get()
            
            #顯示圖片
            self.show_image(img) #0.01 ~ 0.007

    #顯示圖片
    def show_image(self, img):
        cv2.imshow('holive', img)
        cv2.waitKey(1)


    

#影像來源
class Image_source():
    def __init__(self, ip, port):
        #設定IP PORT
        (self.ip, self.port) = (ip, port)
        
        #設定伺服器物件
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        #綁定IP PORT
        self.server.bind((self.ip, self.port))
        print("Server bind at ",self.ip, self.port)

        #設置影像解碼參數
        self.payload = ">L"
        self.payload_size = struct.calcsize(self.payload)
        self.recv_size = 4096
        
        #設置地點
        self.site = None


    def run(self, source_queue:mp.Queue):
        #聆聽
        self.server.listen(5)
        while True:
            #等待連接
            print("wait for any connect")
            self.conn, self.addr = self.server.accept()
            print("connection from", self.addr)

            #取得場域名稱
            self.site = self.get_site()
            print('from', self.site)

            self.handle(source_queue)


    #取得場域名稱
    def get_site(self):
        site = None
        try:
            data = self.conn.recv(1024)
            self.conn.sendall(b'1')
            site = data.decode('UTF-8')
        except Exception as e:
            print("error in get site name". e)
        return site

    def handle(self, source_queue:mp.Queue):
        #設定資源
        try:
            while True:
                #取得時間和 影像
                #s = time.perf_counter() #測試效能
                img, gtime = self.get_image() #4e-3 ~ 8e-3
                #e = time.perf_counter()
                #print('input image time', e - s)
                #s = e
                while source_queue.full():
                    #print('source_queue full')
                    pass
                source_queue.put((img, gtime, self.site))

        except Exception as e:
            #關閉連線
            self.close_conn(e)
            #raise e
        print(self.addr, "exit...")
    
    #關閉連線
    def close_conn(self, reason):
        self.conn.close()
        print("Client at ", self.addr , " disconnected... for", reason)
    
    #取得影像
    def get_image(self):
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
            data = self.conn.recv(self.recv_size)
            if data:
                buffer += data
            else:
                raise ConnectionError("no data from video_source")
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
            data = self.conn.recv(img_size - len(buffer))
            if data:
                buffer += data
            else:
                raise ConnectionError("no data from video_source")
        #擷取、解析壓縮影像資訊
        encode_img = buffer[:img_size]
        return encode_img

#後處理
class Post_producer():
    def __init__(self) -> None:
        #設置管理追蹤者
        self.track_manager = tracker.Tracker_manager()
        self.saved_gtime = 0.0
        self.site = None

        #設置影像解碼參數
        self.payload = ">L"
        self.payload_size = struct.calcsize(self.payload)
        self.recv_size = 4096

    def run(self, d_result_queue:mp.Queue, output_queue:mp.Queue):
        self.track_manager.set_database(DB_NAME)
        try:
            while True:
                #取得辨識結果
                (img, gtime, self.site, results) = d_result_queue.get()
                #儲存原始影像
                self.save_raw_image(img, gtime, results) # 5e-3
                #追蹤 bounding box
                self.track_manager.input_boxs(img.shape, gtime, self.site, results)
                #取得所有box的追蹤資訊(by time)
                tracking_results = self.track_manager.get_tracking_result(gtime) #7e-4
                #依據追蹤資訊畫圖 標記id 中心點 足跡 寫出有速度資訊的追蹤者並標記追蹤id
                self.draw_frame(img, tracking_results) #5e-4
                #取得追蹤清單
                tracker_list = self.track_manager.get_tracker_list()
                #標註場景資訊 標註人數
                self.draw_site_inf(img, gtime, len(tracker_list))
                #標註檢查點
                self.draw_check_area(img, self.track_manager.check_area_list)
                #標註所有tracker路線
                self.draw_dot(img, tracker_list)
                #標註速度資訊(所有tracker 的資訊)
                self.draw_tracker_list(img, tracker_list) #7e-4
                #把影像結果傳到輸出佇列
                output_queue.put(img)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(e)


    #畫人框
    def draw_frame(self, img, results):
        #results = [[id, coord, ...], ]
        for id, coord in results:
            (x1, y1, x2, y2) = coord
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(img, str(id) , (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,0,0), 2)

    #寫文字
    def draw_text(self, img, text, coord):
        cv2.putText(img, text, coord, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 50, 50), 2)
    
    #畫場景資訊
    def draw_site_inf(self, img, t, count_people):
        (h, w, *_) = img.shape
        #畫地點
        sitestr = 'On Place={}'.format(self.site)
        self.draw_text(img, sitestr, ((int(w * 0.0104)), int(h * 0.047)))
        
        #畫時間
        (y, ms, d, hr, m, s, *_) = time.localtime(t)
        dateti = 'On Time={}/{}/{}T{}:{}:{}'.format(y, ms, d, hr, m, s)
        self.draw_text(img, dateti, ((int(w * 0.0104)), int(h * 0.094)))

        #畫人數
        cp = 'Count People={}'.format(count_people)
        self.draw_text(img, cp, ((int(w * 0.0104)), int(h * 0.141)))

    #打點
    def draw_dot(self, img, tracker_list):
        for tracker in tracker_list:
            #取的tracker過去所有足跡
            id, box_list = tracker.get_box_list()
            for coord in box_list:
                center = tracker.count_center(coord)
                cv2.circle(img, center, 1, (255, 0, 0), 5)
            
            #畫出經過檢查點的點
            passed_point_list = tracker.get_passed_point()
            for p in passed_point_list:
                cv2.circle(img, p, 1, (0, 0, 255), 5)

    #標註檢查點位置
    def draw_check_area(self, img, check_area_list):
        for x1, y1, x2, y2 in check_area_list: #[[0, 0, 1,1], [2, 1, 5,6]]
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
    #標註 tracker list 資訊
    def draw_tracker_list(self, img, track_list):
        (h, w, *_) = img.shape # h 1080 w 1920
        mline = [int(w * 0.623), int(h * 0.141)] #標註資訊位置(cv2畫筆位置)
        td = int(h * 0.047) #行距
        for tracker in track_list:
            id = tracker.id
            #瞬間像素速度(與前一張 frame 比)
            piv = tracker.get_piv()
            #平均像素速度(沒檢查點的話就是出現到現在的位置)
            pav = tracker.get_pav()
            #平均速率(總距離 / 總時間)
            avg_v = tracker.get_avg_v()
            #在螢幕的右方標註tracker id 資訊
            self.draw_text(img, 'id : {}'.format(id), (*mline,))
            mline[1] += td
            #標註速度
            self.draw_text(img, 'avg pixel velocity :', (*mline,))
            mline[1] += td
            self.draw_text(img, '{:.4}, {:.4}'.format(*pav), (*mline,))
            mline[1] += td
            self.draw_text(img, 'instance pixel velocity :', (*mline,))
            mline[1] += td
            self.draw_text(img, '{:.4}, {:.4}'.format(*piv), (*mline,))
            mline[1] += td
            #標註平均速率
            if avg_v > 0:
                self.draw_text(img, 'average speed :', (*mline,))
                mline[1] += td
                self.draw_text(img, '{:.4} m/s'.format(avg_v), (*mline,))
            mline[1] += td * 2

    #接收辨識結果
    def get_detect_result(self) -> list:
        results = self.conn.recv(2048)
        results = eval(results.decode())
        return results

    #存圖
    def write_image(self, img_type, img, gtime):
        folder = os.path.join("data","image", img_type, self.site)
        imgpath = os.path.join(folder, str(gtime)+'.jpg')
        if not os.path.exists(folder):
            os.mkdir(folder)
        cv2.imwrite(imgpath, img)
    
    #儲存原始影像
    def save_raw_image(self, img, gtime, dresult):
        #如果有辨識到人存圖
        if len(dresult) > 0:
            self.saved_gtime = gtime
            self.write_image("raw", img, gtime)
            return

        #沒辨識到人但是前3秒有辨識到人就存圖
        if gtime - self.saved_gtime < 3.0:
            self.write_image("raw", img, gtime)


if __name__ == "__main__":
    #設定辨識模組
    args = set_args()
    yolo4 = Detector(args.cfgfile, args.weightfile)
    
    #設定來源佇列 和辨識輸出的佇列
    source_queue = mp.Queue(100)
    d_result_queue = mp.Queue(100)
    out_put_queue = mp.Queue(100)
    
    #設定來源，影像會透過這個連近來
    img_source = Image_source(IP, PORT)
    img_source_mp = mp.Process(target = img_source.run, args = (source_queue, ))
    img_source_mp.start()

    #設置後製 (追蹤、計算速度、計算人數)
    pp = Post_producer()
    pp_mp = mp.Process(target = pp.run, args = (d_result_queue, out_put_queue))
    pp_mp.start()

    #設定影像顯示
    mo = Monitor()
    mo_mp = mp.Process(target = mo.run, args = (out_put_queue, ))
    mo_mp.start()

    print('run yolo')
    yolo4.run(source_queue, d_result_queue)
    