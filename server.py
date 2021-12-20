# -*- coding: utf-8 -*-
from typing import Dict
import socket
import multiprocessing as mp
from utils import holder

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
        self.queue_dict = {
            'video_queue':mp.Queue(10),
            'request_queue':mp.Queue(1),
            'detect_queue' : mp.Queue(10)
            }

    #等待客戶端連線
    def wait_connection(self):
        #聆聽
        self.server.listen(4)
        while True:
            #等待連接
            print("wait for connect")
            conn, addr = self.server.accept()
            connector = Connector(conn, addr)
            mp1 = mp.Process(target=connector.run, args=(self.queue_dict,))
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
            #raise e
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

    