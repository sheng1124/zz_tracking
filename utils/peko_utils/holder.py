import socket
import struct
import time
import numpy as np
import cv2

from utils.peko_utils import tracker
from utils.peko_utils import manager
import multiprocessing as mp

#Holder 必須要用 multli processing or multi threading 執行

#連線處理者模板
class Holder():
    #設置連線
    def set_conn(self, client_conn:socket.socket, shared_args):
        print(type(self), "set conn")
        self.conn = client_conn
        self.source_dict = shared_args[0]
        self.detect_output_list = shared_args[1]
        self.request_list = shared_args[2]
        self.shared_args = shared_args

    #從來源端取得來源名稱
    def get_source_name(self):
        print(type(self), 'set source name')
        data = self.conn.recv(100)
        if data is None:
            raise ConnectionError("source no name")
        name = data.decode('UTF-8', errors='ignore')
        print(type(self), 'source name', name)
        self.conn.sendall(b'1')
        return name

    #檢視共享參數狀態
    def print_shared_args(self):
        print('source:', self.source_dict)
        print('detector:', self.detect_output_list)
        print('request', self.request_list)

    #檢查有沒有斷線
    def is_socket_closed(self) -> bool:
        try:
            data = self.conn.recv(16)
            if len(data) == 0:
                return True
        except BlockingIOError:
            return False  # socket is open and reading from it would block
        except ConnectionResetError:
            return True  # socket was closed for some other reason
        except Exception as e:
            print(type(e), e)
            return False
        return False

    #取得辨識機的輸入佇列
    def get_detect_input_queue(self, i):
        ii = i + 3
        if 3 <= ii < 4:
            return self.shared_args[ii]
        else:
            return None

    #取得辨識機的輸出佇列
    def get_detect_output_queue(self):
        i = self.detect_output_list[self.detector_id]
        if i is None:
            return None
        i += 4
        if 4 <= i < 8 :
            return self.shared_args[i]
        else:
            return None

    #取得要求佇列
    def get_request_queue(self, request_id):
        i = request_id + 4
        if 4 <= i < 8:
            return self.shared_args[i]
        else:
            return None

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
    def set_conn(self, client_conn: socket.socket, shared_args):
        super().set_conn(client_conn, shared_args)
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
    def set_conn(self, client_conn: socket.socket, shared_args):
        super().set_conn(client_conn, shared_args)
        #取得來源名稱
        self.name = self.get_source_name()
        #設定公開來源
        self.source_dict[self.name] = None
        print('source set up')
        self.print_shared_args()

    #釋放在本機的公開資源，用例外來中斷 process
    def release_source(self, err):
        del self.source_dict[self.name]
        print('release source')
        self.print_shared_args()
        raise err

    #取得目標輸出佇列 
    def get_target_queue(self):
        detect_id = self.source_dict[self.name] # sd['123'] = 0 or sd['123'] = None
        if detect_id is None:
            return None
        #取得辨識機輸入佇列 用於把影像傳輸給他 辨識機會自動辨識
        return self.get_detect_input_queue(detect_id)

    def run(self):
        #若有指定的目標佇列 才傳資料
        source_target_queue = self.get_target_queue()
        try:
            self.push_image(source_target_queue)
        
        #沒有向來源要求的客戶端 #要求端要設定佇列給來源端(申請)才會傳資料
        except (TypeError, AttributeError):
            #傳送不允許傳輸控制碼
            self.conn.sendall(b'0')
            #取得回應，若沒回應即關閉連線
            if self.is_socket_closed():
                self.release_source(ConnectionError)
            #待機
            time.sleep(3)

        except Exception as e:
            #可能的錯誤 來源端沒有網路連線 解碼錯誤
            print(type(e), 'source no connect or decode error')
            self.release_source(e)

    def push_image(self, target_queue:mp.Queue):
        if target_queue is None:
            raise TypeError('target_queue is none')
        
        #傳送允許控制碼
        self.conn.sendall(b'1')

        #解析影像長度
        (img_size, buffer, packed_img_size) = self.img_len_decode(self.conn)

        #解析時間
        (t_int, t_float, buffer, packed_t_int, packed_t_float) = self.img_time_decode(self.conn, buffer)
        
        #接收壓縮資料
        (packed_img, buffer) = self.get_packed_img(self.conn, img_size, buffer)
        
        #資料重組 推送訊息到佇列
        data = (packed_img_size, packed_t_int, packed_t_float, packed_img)
        while target_queue.full():
            pass
        target_queue.put(data)

#影像要求者
class Video_reciver(Image_holder):
    def set_conn(self, client_conn: socket.socket, hmanager: manager.Manager, plock: mp.Lock):
        super().set_conn(client_conn, hmanager, plock)
        #設定要求來源名稱
        self.request_name = self.get_source_name()
        #取得來源資源
        print('hh', self.request_name)
        if self.hmanager.is_source_in(self.request_name):
            print('match source')
            self.queue = self.hmanager.get_source(self.request_name)
            #加入要求清單
            self.hmanager.add_request(self.plock, self.request_name)
        else:
            print('no source for', self.request_name)

    def run(self):
        self.recive_message()
    
    def recive_message(self):
        data = self.queue.get()
        self.conn.sendall(data[0] + data[1] + data[2] + data[3])

#影像辨識要求者
class Detect_request(Image_holder):
    def set_conn(self, client_conn: socket.socket, shared_args):
        super().set_conn(client_conn, shared_args)

        #設定要求來源名稱(詢問使用者要用哪個來源的資料來辨識)
        self.request_name = self.get_source_name()
        #新增新的佇列資源 用來接收辨識後的影像

        #若沒可用資源可待機
        for i in range(5):
            #取得閒置的辨識機
            idle_detector_id = self.get_idle_detector_id()
            self.detector_id = idle_detector_id
    
            #檢查有沒有來源
            if idle_detector_id is not None and self.is_request_in_source():
                print('idle detector:', idle_detector_id)
                #設定要求者的 queue 給辨識機，讓辨識機丟影像到要求端
                self.request_id = self.add_request()
                print('request id:', self.request_id)
                #辨識機，並設為占用
                self.set_detector_output(idle_detector_id, self.request_id)
    
                #設定辨識資源的 input queue給來源，讓來源丟影像到辨識資源queue
                self.set_source_output(idle_detector_id)
                print('request setup')
                self.print_shared_args()
                break

            #沒可用資源可待機
            time.sleep(5)

        self.start_time = time.time()
        self.max_time = 3600.0
    
    def run(self):
        try:
            self.recive_message()
        except Exception as e:
            self.delete_request()
            raise e

    #設定影像來源影像要傳要到哪邊
    def set_source_output(self, detector_id):
        if self.request_name in self.source_dict:
            self.source_dict[self.request_name] = detector_id

    #設定辨識機的輸出到這個要求佇列
    def set_detector_output(self, detector_id, request_id):
        self.detect_output_list[detector_id] = request_id

    #設定要求者的 queue 給辨識機，並設為占用，讓辨識機丟影像到要求端
    def add_request(self):
        request_id = len(self.request_list)
        self.request_list.append(self.request_name)
        self.request_queue = self.get_request_queue(request_id)
        return request_id

    #取得閒置的辨識機
    def get_idle_detector_id(self):
        for i in range(len(self.detect_output_list)):
            if self.detect_output_list[i] is None:
                return i
        return None

    #來源中有符合的要求
    def is_request_in_source(self):
        return self.request_name in self.source_dict

    def recive_message(self):
        if time.time() - self.start_time > self.max_time:
            raise AttributeError("out max limit")
        data = self.request_queue.get()
        self.conn.sendall(data[0] + data[1] + data[2] + data[3])

    #清掉要求避免來源占用網路頻寬
    def delete_request(self):
        #設定來源queue = None，讓來源影像不再丟影像到辨識資源queue
        self.set_source_output(None)

        #設定辨識機output queue = None，讓辨識機不再丟影像給要求端
        self.set_detector_output(self.detector_id, None)

        #刪除要求
        self.request_list.pop(self.request_id)

        print('release request')
        self.print_shared_args()

#影像辨識者
class Video_detector(Image_holder):
    def set_conn(self, client_conn: socket.socket, shared_args):
        super().set_conn(client_conn, shared_args)
        self.set_detect_input_queue() 
        self.track_manager = tracker.Tracker_manager()
        self.encode_parm=[int(cv2.IMWRITE_JPEG_QUALITY), 100]

    #新增辨識機
    def add_detector(self):
        self.detect_output_list.append(None)
        if self.detector_id == 0:
            self.input_queue = self.shared_args[2]

    #設置輸入的佇列辨識裡面的影像
    def set_detect_input_queue(self):
        print('set detect input queue')
        self.detector_id = len(self.detect_output_list)
        self.detect_output_list.append(None)
        self.input_queue =self.get_detect_input_queue(self.detector_id)
        print('detector set up')
        self.print_shared_args()
        

    def run(self):
        #佇列內有東西即辨識 內的東西由管理者分配 辨識者是伺服器資源並非客戶端 可由伺服器端分配
        try:
            self.detect()
        
        #沒有輸出佇列 可能沒有要求者 即待機
        except AttributeError:
            time.sleep(3)
        
        except Exception as e :
            print(e)
            raise e
    
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
        site_id = self.detect_output_list[self.detector_id]
        try:
            site = self.request_list[site_id]
        except Exception:
            #如果要求離線會 error
            site = 'None'
        sitestr = 'On Place={}'.format(site)
        self.draw_text(img, sitestr, ((int(w * 0.0104)), int(h * 0.047)))
        
        #畫時間
        (y, M, d, hr, m, s, *_) = time.localtime(t)
        dateti = 'On Time={}/{}/{}T{}:{}:{}'.format(y, M, d, hr, m, s)
        self.draw_text(img, dateti, ((int(w * 0.0104)), int(h * 0.094)))

        #畫人數
        cp = 'Count People={}'.format(count_people)
        self.draw_text(img, cp, ((int(w * 0.0104)), int(h * 0.141)))

        return site

    #打點
    def draw_dot(self, img, tracker_list):
        for tracker in tracker_list:
            #取的tracker過去所有足跡
            id, box_list = tracker.get_box_list()
            for coord in box_list:
                center = tracker.count_center(coord)
                cv2.circle(img, center, 1, (255, 0, 0), 5)

    #標註檢查點位置
    def draw_check_area(self, img, check_area_list):
        for x1, y1, x2, y2 in check_area_list: #[[0, 0, 1,1], [2, 1, 5,6]]
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
            

    #標註 tracker list 資訊
    def draw_tracker_list(self, img, track_list):
        (h, w, *_) = img.shape # h 1080 w 1920
        mline = [int(w * 0.623), int(h * 0.141)] #標註資訊位置(cv2畫筆位置)
        td = int(h * 0.047) #行距
        try:
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
                if avg_v:
                    self.draw_text(img, 'average speed :', (*mline,))
                    mline[1] += td
                    self.draw_text(img, '{:.4}'.format(avg_v), (*mline,))
                mline[1] += td * 2
                
        except Exception as e:
            print(e)

    #接收辨識結果
    def get_detect_result(self) -> list:
        results = self.conn.recv(2048)
        results = eval(results.decode())
        return results

    def write_image(self, site, img):
        import os
        folder = os.path.join("data","image","raw",site)
        imgpath = os.path.join(folder, str(time.time())+'.jpg')
        if not os.path.exists(folder):
            os.mkdir(folder)
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


    def detect(self):
        #傳送影像資料給辨識端
        data = self.input_queue.get()
        self.conn.sendall(data[0] + data[3])
        newdata = [data[0], data[1], data[2], data[3]]
        
        #解碼
        (t, img) = self.data_decode(data)
        
        #存原始影像圖?
        #接收辨識結果
        results = self.get_detect_result()
        
        #追蹤 bounding box
        self.track_manager.input_boxs(results, t, img.shape)
        
        #取得所有box的追蹤資訊(by time)
        tracking_results = self.track_manager.get_tracking_result(t)
        #取得追蹤清單
        #寫出有速度資訊的追蹤者並標記追蹤id

        #依據追蹤資訊畫圖 標記id 中心點 足跡
        self.draw_frame(img, tracking_results)

        tracker_list = self.track_manager.get_tracker_list()
        #標註場景資訊
        site = self.draw_site_inf(img, t, len(tracker_list))
        #標註檢查點
        self.draw_check_area(img, self.track_manager.check_area_list)
        #標註所有tracker路線
        self.draw_dot(img, tracker_list)
        #標註速度資訊(所有tracker 的資訊)
        self.draw_tracker_list(img, tracker_list)
        #新圖像壓縮計算長度
        (size_img_pack, img_pack) = self.data_encode(img)
        newdata[0], newdata[3] = size_img_pack, img_pack

        self.write_image(site, img)
        
        #丟進queue用來傳送資料
        output_queue = self.get_detect_output_queue()
        if output_queue is not None:
            output_queue.put(newdata)
        #上傳資料庫
