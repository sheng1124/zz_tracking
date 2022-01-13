# -*- coding: utf-8 -*-
from typing import Dict
import socket
import multiprocessing as mp
from utils.peko_utils import holder
from utils.peko_utils import manager

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
        manager = mp.Manager()
        self.source_dict = manager.dict()
        self.request_dict = manager.list()
        #sd['123'] = None => 來源123有掛機沒輸出
        #sd['123'] = 1 => 使用1號辨識機
        self.detect_output_list = manager.list()
        #dod[1] = None => 1號辨識機有掛機沒輸出
        #dod[1] = 1 => 1號辨識機輸出到1號要求端
        #來源佇列 把辨識輸入給來源 hander 傳輸
        
        #辨識佇列 輸入
        self.detect_input_q1 = mp.Queue(20)

        #辨識佇列 輸出會把資料丟給 要求 handler

        #要求佇列 最多就5個要求吧
        self.request_queue_1 = mp.Queue(20)
        self.request_queue_2 = mp.Queue(20)
        self.request_queue_3 = mp.Queue(20)
        self.request_queue_4 = mp.Queue(20)
        self.request_queue_5 = mp.Queue(20)

        #設定 process 共享參數，別用一般list or dict 當共享 毛很多
        self.shared_args = (
            self.source_dict,
            self.detect_output_list,
            self.request_dict,
            self.detect_input_q1,
            self.request_queue_1,
            self.request_queue_2,
            self.request_queue_3,
            self.request_queue_4,
            self.request_queue_5
        )

        #客戶端佇列

    #等待客戶端連線
    def wait_connection(self):
        #聆聽
        self.server.listen(20)
        while True:
            #等待連接
            print("wait for connect")
            conn, addr = self.server.accept()
            connector = Connector(conn, addr)
            mp1 = mp.Process(target=connector.run, args=self.shared_args)
            mp1.start()

#連線管理者
class Connector():
    def __init__(self, client_conn:socket.socket, client_addr):
        (self.conn, self.addr) = (client_conn, client_addr)
    
    #識別連線
    def conn_identify(self) -> holder.Holder:
        #連線開始 先接受驗證訊息
        data = self.conn.recv(100)
        
        #訊息解碼確認身分
        identify = data.decode('UTF-8', errors='ignore')
        self.conn.sendall(b'1')
        print("identification: ", identify)

        #驗證身分 錯誤的身分會引發例外中斷thread
        return get_identify_holder(identify)

    def run(self, *shared_args):
        #識別連線
        handler = self.conn_identify()
        #處理連線
        handler.set_conn(self.conn, shared_args)
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

def get_identify_holder(identify:str) -> holder.Holder:
    idd = {
        "msg_source" : holder.Msg_provider(),  
        "msg_request" : holder.Msg_reciver(),
        "video_source" : holder.Video_provider(),
        "video_request" : holder.Video_reciver(),
        "video_detect" : holder.Video_detector(),
        "detect_request" : holder.Detect_request()
    }
    return idd[identify]


if __name__ == "__main__":
    mm = Server("163.25.103.111", 9987)
    mm.wait_connection()

    