# -*- coding: utf-8 -*-
#背景相差找動態物件
#輸入背景 、後續的楨 輸出動態的物件

import sys
import os
import cv2

#背景比較動態物件
class Background():
	def __init__(self, bg_path):
		self.bg = cv2.imread(bg_path)
	
	#計算與背景的影像差值
	def compare(self, frame):
		abs = cv2.absdiff(frame, self.bg)
		return abs

	
#讀取楨
def load_frame(image_dir, filename):
	if not filename[-4:] in (".jpg", ".png"):
		return
	filepath = os.path.join(image_dir, filename)
	frame = cv2.imread(filepath)
	return frame
	

if __name__ == '__main__':	
	#背景圖片路徑
	bg_path = sys.argv[1]
	bg = Background(bg_path)
	
	#影片截圖資料夾路徑
	images_path = sys.argv[2]
	
	#讀取資料夾的圖片
	for filename in os.listdir(images_path):
		#讀取圖片
		frame = load_frame(images_path, filename)
		
		#與背景比較不同的地方
		newframe = bg.compare(frame)
		
		#另存差異
		save_path = os.path.join("../data/images/backgroung_compare", filename)
		cv2.imwrite(save_path, newframe)
	
