import cv2
import socket
import struct
import numpy as np

from client_api import Video_povider_client

class Camera():
    def __init__(self, resolution, fps, cam_id = 0):#resolution = (640, 480)
        self.resolution = resolution
        self.fps = fps
        self.encode_parm=[int(cv2.IMWRITE_JPEG_QUALITY), 100]
        #開啟攝影機
        self.cam = cv2.VideoCapture(cam_id)
        # 設定擷取影像的尺寸大小
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

    #讀取攝影機 回傳可以串流的資料
    def get_encode_image(self):
        ret, img = self.cam.read()
        #cv2.imwrite("raw.jpg", img)
        #encode
        #print("img len", len(img.tobytes()))
        ret, img_encode = cv2.imencode(".jpg", img, self.encode_parm)#, self.param)
        #to byte format'
        encode_data = img_encode.tobytes()
        #print(type(img_encode), "encode_data = ",len(encode_data))
        return encode_data
        
    #解碼壓縮過的串流資料
    def img_decode(self, encode_data):
        #decode
        print(type(encode_data))
        data = np.frombuffer(encode_data, dtype = "uint8")
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        #print("iimg_data_len = ",len(img.tobytes()))
        #cv2.imwrite("decode.jpg", img)
        return img


class Monitor_Client():
    def __init__(self, remote_ip, remote_port):
        (self.remote_ip, self.remote_port) = (remote_ip, remote_port)
        self.payload = ">L"
        #遠端伺服器串接 
        self.remote_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #連線到遠端伺服器
    def connect(self):
        self.remote_server.connect((self.remote_ip, self.remote_port))
        self.send_data(bytes("video_source", "UTF-8"))
        self.remote_server.recv(1)
        print("connect to ", self.remote_ip, self.remote_port)

    #傳輸資料
    def send_data(self, message):
        self.remote_server.sendall(message)

    #影像打包加入長度資訊
    def pack_img(self, img_byte):
        img_byte_size = len(img_byte)
        pack_img = struct.pack(self.payload, img_byte_size) + img_byte
        return pack_img

    #傳輸串流
    def send_stream(self, cam):
        while True:
            stream = cam.get_encode_image()
            #print("img_size=",len(stream))
            #加入長度資訊
            pack_img = self.pack_img(stream)
            #print("pack_img=",len(pack_img))
            self.remote_server.sendall(pack_img)

    #傳輸一次串流
    def send_stream_once(self, cam):
        stream = cam.get_encode_image()
        print("img_size=",len(stream))
        #加入長度資訊
        pack_img = self.pack_img(stream)
        print("pack_img_size=",len(pack_img))
        self.remote_server.sendall(pack_img)

    #關閉連線
    def close(self):
        self.remote_server.close()


if __name__ == '__main__2':
    cam = Camera((640, 480), 15)#"rtsp://admin:ppcb1234@192.168.154.15:554/unicast/c7/s1/live") #640 480
    #x = cam.get_encode_image()
    #cam.img_decode(x)

    ms = Monitor_Client("163.25.103.111", 9987)#"192.168.2.5", 9987)163.25.103.111 "6.tcp.ngrok.io", 16690
    ms.connect()
    #ms.send_stream_once(cam)
    ms.send_stream(cam)
    ms.close()


if __name__ == '__main__':
    vp = Video_povider_client("163.25.103.111", 9987, "video_source")
    vp.connect()
    cam = cv2.VideoCapture(0)

    while True:
        vp.send_image_from_cam(cam)

