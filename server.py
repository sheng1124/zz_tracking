import cv2
import socket
import struct
import numpy as np
import time
import os

#伺服器處理連線
class Connect_handler(threading.Thread):
    def __init__(self, client_conn, client_addr, connect_list):
        threading.Thread.__init__(self)
        (self.conn, self.addr) = (client_conn, client_addr)
        self.connect_list = connect_list
        self.set_video_decode_para()
    
    def run(self):
        print ("handle Connection from : ", self.addr)
        #識別連線者
        connecter = self.conn_identify()
        if connecter:
            print(self.connect_list)
        while connecter:
            if not connecter():
                break
        self.conn.close()
        print("Client at ", self.addr , " disconnected...")
        print(self.connect_list)
    
    def conn_identify(self):
        #連線開始 先接受驗證訊息
        print("identify connection")
        data = self.conn.recv(2048)
        
        #訊息解碼確認身分
        identify = data.decode()
        print("identification: ", identify)

        #驗證身分
        identify_dict = {
            "msg_source" : self.msg_soucre_hand,
            "msg_request" : self.msg_request_hand,
            "video_source" : self.video_sorce_hand,
            "video_request" : self.video_request_hand
        }
        
        if identify in identify_dict:
            #合格的身分
            self.connect_list[identify] = [self.conn, self.addr]
            return identify_dict[identify]
        else:
            return False

    #保持 source 連線
    def msg_soucre_hand(self):
        if not "msg_request" in self.connect_list:
            data = self.conn.recv(2048)
        return True
    
    #解析影像長度
    def __img_len_decode(self, conn):
        buffer = b""
        while len(buffer) < self.payload_size:
            buffer += conn.recv(self.recv_size)
        packed_img_size = buffer[:self.payload_size]
        img_size = struct.unpack(self.payload, packed_img_size)[0]
        return img_size, buffer
    
    #接收壓縮資料
    def __get_packed_img(self, conn, img_size, buffer):
        while len(buffer) < img_size:
            buffer += conn.recv(img_size - len(buffer))
        #擷取、解析壓縮影像資訊
        packed_img = buffer[:img_size]
        #移除buffer中擷取過的影像資訊
        buffer = buffer[img_size:]
        #print(len(buffer))
        return packed_img, buffer
    
    #顯示影像
    def __show_packed_img(self, packed_img):
        data = np.frombuffer(packed_img, dtype = "uint8")
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        cv2.imshow("live", img)
        cv2.waitKey(1)
    
    #影像來源管理
    def video_sorce_hand(self):
        if len(self.connect_list["video_source"]) < 3:
            #設定資源不公開
            self.connect_list["video_source"][2] = False
            self.public = self.connect_list["video_source"][2]
        if not "video_request" in self.connect_list:
            #設定資源不公開
            self.public = False
            #解析影像長度
            (img_size, buffer) = self.__img_len_decode(self.conn)
            print(img_size)
            
            #接收壓縮資料
            (packed_img, buffer) = self.__get_packed_img(self.conn, img_size, buffer)

            #顯示影像
            self.__show_packed_img(packed_img)
        
        elif not self.public:
            #有video_request就設定成公開資源
            cv2.destroyAllWindows()
            self.public = True
        return True
    
    #設置影像解碼參數
    def set_video_decode_para(self):
        self.payload = ">L"
        self.payload_size = struct.calcsize(self.payload)
        self.recv_size = 4096
    
    def video_request_hand(self):
        if not "video_source" in self.connect_list:
            #沒有來源
            print("requester no video source")
            del self.connect_list["video_request"]
            return False
            
        #選擇來源
        source = self.connect_list["video_source"]
        source_conn = source[0]
        print("available video source for requester, from", source[1])
        buffer = b""
        
        #接收長度資訊
        while len(buffer) < self.payload_size:
            buffer += source_conn.recv(self.recv_size)
        packed_img_size = buffer[:self.payload_size]
        img_size = struct.unpack(self.payload, packed_img_size)[0]
        #移除buffer中擷取過的影像長度資訊
        buffer = buffer[self.payload_size:]
        print(img_size)

        #接收壓縮影像
        while len(buffer) < img_size:
            buffer += source_conn.recv(img_size - len(buffer))
        #擷取、解析壓縮影像資訊
        packed_img = buffer[:img_size]
        #移除buffer中擷取過的影像資訊
        buffer = buffer[img_size:]
        
        #傳送長度資訊+壓縮影像給requester
        self.conn.sendall(packed_img_size + packed_img)
        return True

    #傳送訊息給遠端要求者
    def msg_request_hand(self):
        #選擇來源
        if "msg_source" in self.connect_list:
            source = self.connect_list["msg_source"]
            source_conn = source[0]
            print("available source", source[1])
            data = source_conn.recv(2048)
            if not data:
                print("source is not available")
                del self.connect_list["msg_request"]
                return False
            try:
                self.conn.sendall(data)
                return True
            except Exception as e:
                print(e)
                print("connect error\n")
                del self.connect_list["msg_request"]
                return False
        else:
            data = bytes("no source conn\n", 'UTF-8')
            self.conn.sendall(data)
            del self.connect_list["msg_request"]
            return False

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
        self.connect_list = {}
        
    #等待客戶端連線
    def wait_connection(self):
        #聆聽
        self.server.listen(2)
        while True:
            #等待連接
            print("wait for connect")
            conn, addr = self.server.accept()
            print("dadda")
            connect_handler = Connect_handler(conn, addr, self.connect_list)
            connect_handler.start()

if __name__ == "__main__":
    mm = Server("163.25.103.111", 9987)
    mm.wait_connection()