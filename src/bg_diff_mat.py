# -*- coding: utf-8 -*-
#背景相差找動態物件
#輸入背景 、後續的楨 輸出動態的物件

import sys
import os
from PIL import Image

#背景比較動態物件
class Background():
	def __init__(self, bg_path):
		self.bg = Image.open(bg_path)
	
	def compare(self, frame):
		xsize, ysize = self.bg.size[0], self.bg.size[1]
		if(frame.size[0] != xsize or frame.size[1] != ysize):
			print('兩張圖的像素長度不對')
			return
		#像素比較
		for x in range(xsize):
			for y in range(ysize):
				(r1, g1, b1) = self.bg.getpixel((x,y))
				(r2, g2, b2) = frame.getpixel((x,y))
				(R, G, B) = (abs(r1 - r2) ,abs(g1 - g2), abs(b1 - b2))
				frame.putpixel((x,y), (R,G,B))
	
#讀取楨
def load_frame(image_dir, filename):
	if not filename[-4:] in (".jpg", ".png"):
		return
	filepath = os.path.join(image_dir, filename)
	frame = Image.open(filepath)
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
		bg.compare(frame)
		
		#另存差異
		save_path = os.path.join("../data/images/backgroung_compare", filename)
		frame.save(save_path)
	
