import cv2
import socket
import struct
import numpy as np
import time
import os

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
		print("connect to ", self.remote_ip, self.remote_port)

	#傳輸資料
	def send_data(self, message):
		self.remote_server.sendall(message)

	#關閉連線
	def close(self):
		self.remote_server.close()

#相機端
class Monitor_Client_Cam(Monitor_Client):
	def __init__(self, remote_ip, remote_port):
		super(Monitor_Client_Cam, self).__init__(remote_ip, remote_port)
	
	#影像打包加入長度資訊
	def pack_img(self, img_byte):
		img_byte_size = len(img_byte)
		pack_img = struct.pack(self.payload, img_byte_size) + img_byte
		return pack_img

	#傳輸串流
	def send_data(self, cam):
		while True:
			stream = cam.get_encode_image()
			#print("img_size=",len(stream))
			#加入長度資訊
			pack_img = self.pack_img(stream)
			#print("pack_img=",len(pack_img))
			self.remote_server.sendall(pack_img)
	
	#傳輸一次串流
	def send_data_debug(self, cam):
		stream = cam.get_encode_image()
		print("img_size=",len(stream))
		#加入長度資訊
		pack_img = self.pack_img(stream)
		print("pack_img_size=",len(pack_img))
		self.remote_server.sendall(pack_img)

#運算端
class Monitor_Client_Cpu(Monitor_Client):
	def __init__(self, remote_ip, remote_port):
		super(Monitor_Client_Cpu, self).__init__(remote_ip, remote_port)
		self.buffer = b""
		self.payload_size = struct.calcsize(self.payload)
		self.recv_size = 4096
		self.img_count, self.recv_img_total_time, self.frame_count = (0, 0, 0)
		self.pre_second_frame_c, self.timer = (0, 0)

	#計算接收影像的平均速度
	def __count_recv_speed(self):
		avg_time = self.recv_img_total_time / self.img_count if self.img_count else 0 
		return avg_time 

	#取得壓縮影像長度
	def __request_img_size(self, conn):
		#接收head資訊
		while len(self.buffer) < self.payload_size:
			self.buffer += conn.recv(self.recv_size)
		#擷取、解析壓縮影像長度資訊
		packed_img_size_inf = self.buffer[:self.payload_size]
		img_size = struct.unpack(self.payload, packed_img_size_inf)[0]
		#移除buffer中擷取過的影像長度資訊
		self.buffer = self.buffer[self.payload_size:]
		#print("recv_img_size=", img_size)
		return img_size

	#取得壓縮影像資料
	def __request_img_debug(self, conn, img_size):
		s = time.perf_counter()
		#接收body
		while len(self.buffer) < img_size:
			#self.buffer += conn.recv(img_size - len(self.buffer))
			self.buffer += conn.recv(self.recv_size)
		#擷取、解析壓縮影像資訊
		encode_img = self.buffer[:img_size]
		#移除buffer中擷取過的影像資訊
		self.buffer = self.buffer[img_size:]
		self.recv_img_total_time += time.perf_counter() - s
		self.img_count += 1
		#print("avg_time=", self.__count_recv_speed())
		return encode_img

	#處裡客戶
	def __handle_stream(self, conn):
		#取得壓縮影像長度
		img_size = self.__request_img_size(conn)
		#取得壓縮影像資料
		encode_img = self.__request_img_debug(conn, img_size)
		#影像解碼
		img = self.__img_decode(encode_img)
		#顯示影像
		self.__show_img(img)
		#儲存影像
		name = time.time()
		savepath = os.path.join("../data/test", "{}.jpg".format(name))
		cv2.imwrite(savepath, img)
		#跑辨識
		#結果插入資料庫

#中繼伺服器


class Monitor_Server():
	def __init__(self, ip, port): #127.0.0.1 , 9987
		(self.ip, self.port) = (ip, port)
		self.buffer = b""
		self.payload = ">L"
		self.payload_size = struct.calcsize(self.payload)
		self.recv_size = 4096
		self.img_count = 0
		self.recv_img_total_time = 0
		self.frame_count = 0
		self.pre_second_frame_c = 0
		self.timer = 0
		print("payload_size: {}".format(self.payload_size))
		#串接伺服器 (於伺服器與伺服器之間進行串接, 使用TCP(資料流)的方式提供可靠、雙向、串流的通信頻道)
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		print("server set")
	
	#計算接收影像的平均速度
	def __count_recv_speed(self):
		avg_time = self.recv_img_total_time / self.img_count if self.img_count else 0 
		return avg_time
	
	#取得壓縮影像長度
	def __request_img_size(self, conn):
		#接收head資訊
		while len(self.buffer) < self.payload_size:
			self.buffer += conn.recv(self.recv_size)
		#擷取、解析壓縮影像長度資訊
		packed_img_size_inf = self.buffer[:self.payload_size]
		img_size = struct.unpack(self.payload, packed_img_size_inf)[0]
		#移除buffer中擷取過的影像長度資訊
		self.buffer = self.buffer[self.payload_size:]
		#print("recv_img_size=", img_size)
		return img_size
		
	#取得壓縮影像資料
	def __request_img_debug(self, conn, img_size):
		s = time.perf_counter()
		#接收body
		while len(self.buffer) < img_size:
			#self.buffer += conn.recv(img_size - len(self.buffer))
			self.buffer += conn.recv(self.recv_size)
		#擷取、解析壓縮影像資訊
		encode_img = self.buffer[:img_size]
		#移除buffer中擷取過的影像資訊
		self.buffer = self.buffer[img_size:]
		self.recv_img_total_time += time.perf_counter() - s
		self.img_count += 1
		#print("avg_time=", self.__count_recv_speed())
		
		return encode_img
	
	#處裡客戶
	def __handle_stream(self, conn):
		#取得壓縮影像長度
		img_size = self.__request_img_size(conn)
		#取得壓縮影像資料
		encode_img = self.__request_img_debug(conn, img_size)
		#影像解碼
		img = self.__img_decode(encode_img)
		#顯示影像
		self.__show_img(img)
		#儲存影像
		name = time.time()
		savepath = os.path.join("../data/test", "{}.jpg".format(name))
		cv2.imwrite(savepath, img)
		#跑辨識
		#結果插入資料庫
		
	#計算fps
	def get_fps(self):
		if time.perf_counter() - self.timer > 1:
			#重置碼表、每秒f數
			self.timer = time.perf_counter()
			self.pre_second_frame_c = self.frame_count
			self.frame_count = 0
		return self.pre_second_frame_c
	
	#顯示影像
	def __show_img(self, img):
		if type(img) != type(None):
			#計算fps
			fps = self.get_fps()
			#顯示fps
			img2 = draw_fps(img, fps)
			cv2.imshow("live", img2)
			cv2.waitKey(1)
			
	#等待客戶端連線
	def __wait_connection(self, handle_func):
		while True:
			print("wait for connect")
			conn, addr = self.server.accept()
			with conn:
				print("connect by ", addr)
				self.timer = time.perf_counter()
				while True:
					#處裡客戶
					handle_func(conn)
					#計算每秒處裡速度
					self.frame_count +=1
	
	#壓縮影像解碼
	def __img_decode(self, encode_data):
		data = np.frombuffer(encode_data, dtype = "uint8")
		img = cv2.imdecode(data, cv2.IMREAD_COLOR)
		#print("decode len=", len(img.tobytes()))
		return img
	
	#伺服器開始監聽
	def listening(self):
		#host ip port
		self.server.bind((self.ip, self.port))
		self.server.listen(5)
		print("start listen on", self.ip, self.port)

		#等待客戶端連線
		self.__wait_connection(self.__handle_stream)