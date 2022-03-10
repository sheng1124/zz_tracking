#取得在資料集中某個時間點的圖片
import time
import os
import shutil

import pic_input


#輸入時間
def input_time():
    time_set = set()
    ftime = input('輸入時間 輸入q 離開\n')
    while ftime != 'q':
        try:
            inttime = int(ftime)
        except Exception:
            continue
        else:
            for i in [-2, -1, 0, 1, 2]:
                time_set.add(inttime + i)
        finally:
            ftime = input('輸入時間 輸入q 離開\n')
    return time_set

#從某個資料夾整理秒數
def sort_file_second():
    print('整理秒數輸入資料夾路徑')
    pic_floder_list = pic_input.get_pic_floder_list()
    time_set = set()
    for pic_floder in pic_floder_list:
        if not os.path.isdir(pic_floder):
            continue
        
        #取的資料夾下所有檔案
        fp_list = os.listdir(pic_floder)
        #整理文件排序
        fp_list = sorted(fp_list, key = lambda id:float(id[:-4]))
        for filename in fp_list:
            #解析所有解析時間
            try:
                ftime = float(filename[:-4])
                inttime = int(ftime)
            except Exception:
                continue
            else:
                for i in [-2, -1, 0, 1, 2]:
                    time_set.add(inttime + i)
    return time_set

#複製符合時間的文件到新資料夾
def copy_file(time_set):
    print('輸入來源資料夾')
    pic_floder_list = pic_input.get_pic_floder_list()
    print('輸入輸出資料夾')
    pic_out_put_path = input()
    if not os.path.exists(pic_out_put_path):
        os.makedirs(pic_out_put_path)
    for pic_floder in pic_floder_list:
        if not os.path.isdir(pic_floder):
            continue
        #取的資料夾下所有檔案
        fp_list = os.listdir(pic_floder)
        #整理文件排序
        fp_list = sorted(fp_list, key = lambda id:float(id[:-4]))
        for filename in fp_list:
            try:
                ftime = float(filename[:-4])
                inttime = int(ftime)
            except Exception:
                continue
            else:
                if inttime in time_set:
                    #複製文件到新資料夾
                    filepath = os.path.join(pic_floder, filename)
                    outputpath = os.path.join(pic_out_put_path, filename)
                    shutil.copyfile(filepath, outputpath)

if __name__ == '__main__':
    time_set = sort_file_second()
    if not time_set:
        #手動輸入時間
        time_set = input_time()
    
    for e in time_set:
        print(e)
    
    #複製符合時間的文件到新資料夾
    copy_file(time_set)
