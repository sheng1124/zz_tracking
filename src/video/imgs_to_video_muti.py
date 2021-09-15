# -*- coding: utf-8 -*-
#圖片集合轉影片
#2圖比較
#多個資料夾 可以比較
#輸入資料夾路徑 輸出影片名稱(含附檔名) fps 輸出影片

import cv2
import numpy as np
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
def imgs_to_video(dir_path_1, dir_path_2, output_path, fps):
	#讀取所有圖片的路徑
	imgs_list_1 = sorted(get_imgs_path_list(dir_path_1))
	imgs_list_2 = sorted(get_imgs_path_list(dir_path_2))
	#取的圖片的長寬
	img_shape_1 = cv2.imread(imgs_list_1[0]).shape #(y, x, channel)
	img_shape_2 = cv2.imread(imgs_list_2[0]).shape #(y, x, channel)
	#建立影片編輯器
	fourcc = cv2.VideoWriter_fourcc(*'MJPG')
	v_shape = (img_shape_1[1], img_shape_1[0]//2)
	video_writer = cv2.VideoWriter(output_path, fourcc, fps, v_shape)
	#讀取每張圖片並寫入影片
	for i in range(len(imgs_list_1)):
		img1 = cv2.imread(imgs_list_1[i])
		img2 = cv2.imread(imgs_list_2[i])
		img_combine= np.hstack((img1, img2))
		img_combine = cv2.resize(img_combine, v_shape, interpolation = cv2.INTER_AREA)
		
		video_writer.write(img_combine)
	video_writer.release()
	


if __name__ == '__main__':
	#圖片資料夾參數
	dir_path_1 = sys.argv[1]
	dir_path_2 = sys.argv[2]
	if not os.path.isdir(dir_path_1):
		sys.exit('錯誤的輸入路徑，輸入正確的圖片資料夾路徑')
	#輸出路徑參數
	output_path = sys.argv[3]
	#輸出影片 Fps 參數
	fps = int(sys.argv[4])
	#圖片集合成影片
	imgs_to_video(dir_path_1, dir_path_2, output_path, fps)

