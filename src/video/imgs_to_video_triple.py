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
def imgs_to_video(dir_path_1, dir_path_2,dir_path_3, output_path, fps):
	#讀取所有圖片的路徑
	imgs_list_1 = sorted(get_imgs_path_list(dir_path_1))
	imgs_list_2 = sorted(get_imgs_path_list(dir_path_2))
	imgs_list_3 = sorted(get_imgs_path_list(dir_path_3))
	#取的圖片的長寬
	img_shape_1 = cv2.imread(imgs_list_1[0]).shape #(y, x, channel)
	img_shape_2 = cv2.imread(imgs_list_2[0]).shape #(y, x, channel)
	img_shape_3 = cv2.imread(imgs_list_3[0]).shape #(y, x, channel)
	#建立影片編輯器
	fourcc = cv2.VideoWriter_fourcc(*'MJPG')
	v_shape = (img_shape_1[1], img_shape_1[0])
	video_writer = cv2.VideoWriter(output_path, fourcc, fps, v_shape)
	#讀取每張圖片並寫入影片
	for i in range(len(imgs_list_1)):
		img1 = cv2.imread(imgs_list_1[i])
		img2 = cv2.imread(imgs_list_2[i])
		img3 = cv2.imread(imgs_list_3[i])
		img_combine= np.hstack((img1, img2))
		all_zeros = np.zeros(img3.shape).astype("uint8")
		img_combine2= np.hstack((img3, all_zeros))#水平方向補零 因為vstack 水平維度要一致
		img_combine = np.vstack((img_combine,img_combine2))
		img_combine = cv2.resize(img_combine, v_shape, interpolation = cv2.INTER_AREA)
		
		video_writer.write(img_combine)
	video_writer.release()
	

#py imgs_to_video_triple.py ../data/images/0721/red_diff_dl ../data/images/0721/green_diff_dl ../data/images/0721/blue_diff_dl rgb_diff_c.avi 12

if __name__ == '__main__':
	#圖片資料夾參數
	dir_path_1 = sys.argv[1]
	dir_path_2 = sys.argv[2]
	dir_path_3 = sys.argv[3]
	if not os.path.isdir(dir_path_1):
		sys.exit('錯誤的輸入路徑，輸入正確的圖片資料夾路徑')
	#輸出路徑參數
	output_path = sys.argv[4]
	#輸出影片 Fps 參數
	fps = int(sys.argv[5])
	#圖片集合成影片
	imgs_to_video(dir_path_1, dir_path_2,dir_path_3, output_path, fps)

