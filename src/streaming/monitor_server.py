import cv2
import numpy as np
import socket
import struct
import time
import os

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
		
		
def draw_fps(img, fps):
	#影像, 輸出文字, 文字座標, 字型, 字元大小, 文字顏色, 線條寬度, 線條種類
	msg = "fps: {}".format(fps)
	cv2.putText(img, msg, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1, cv2.LINE_AA)
	return img

	
	
	
if __name__ == "__main__":
	ms = Monitor_Server("192.168.2.5", 9987)
	ms.listening()