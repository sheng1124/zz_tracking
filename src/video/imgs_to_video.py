# -*- coding: utf-8 -*-
#圖片集合轉影片
#輸入資料夾路徑 輸出影片名稱(含附檔名) fps 輸出影片

import cv2
import sys
import os

#讀取資料夾底下所有圖片的路徑
def get_imgs_path_list(dir_path):
	path_list = []
	for path in os.listdir(dir_path):
		if path[-4:] in ('.jpg', '.png'):
			path_list.append(os.path.join(dir_path, path))
	return path_list

#圖片集合成影片
def imgs_to_video(dir_path, output_path, fps):
	#讀取所有圖片的路徑
	imgs_list = sorted(get_imgs_path_list(dir_path))
	#取的圖片的長寬
	img_shape = cv2.imread(imgs_list[0]).shape #(y, x, channel)
	#建立影片編輯器
	fourcc = cv2.VideoWriter_fourcc(*'MJPG')
	video_writer = cv2.VideoWriter(output_path, fourcc, fps, (img_shape[1], img_shape[0]))
	#讀取每張圖片並寫入影片
	for img_path in imgs_list:
		img = cv2.imread(img_path)
		video_writer.write(img)
	video_writer.release()
	


if __name__ == '__main__':
	#圖片資料夾參數
	dir_path = sys.argv[1]
	if not os.path.isdir(dir_path):
		sys.exit('錯誤的輸入路徑，輸入正確的圖片資料夾路徑')
	#輸出路徑參數
	output_path = sys.argv[2]
	#輸出影片 Fps 參數
	fps = int(sys.argv[3])
	#圖片集合成影片
	imgs_to_video(dir_path, output_path, fps)

