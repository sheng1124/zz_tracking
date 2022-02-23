import cv2
import time
import os

from client_api import Video_povider_client


if __name__ == '__main__':
    vp = Video_povider_client("163.25.103.111", 9987, "video_source")
    vp.connect()
    #"rtsp://admin:ppcb1234@192.168.154.15:554/unicast/c7/s1/live") #640 480

    #讀取資料夾路徑
    pic_floder = input('輸入資料夾路徑\n')
    fp_list = os.listdir(pic_floder)

    #整理文件排序
    fp_list = sorted(fp_list, key = lambda id:float(id[:-4]))

    #設定影像來源名稱
    source = input('輸入來源名稱\n')
    vp.set_source_name(source)

    pftime, pnowtime = 0, 0
    for filename in fp_list:
        filepath = os.path.join(pic_floder, filename)
        print(filepath)
        #檔案時間
        ftime = float(filename[:-4])
        if vp.is_transport():
            #time.sleep(3)
            #模擬時間差 等時間到在傳送
            nowtime = time.time()
            #print('ftime:{} ptime:{} dd:{:.4}'.format(ftime, pftime, ftime - pftime))
            #print('ntime:{} pntime:{} dd:{:.4}'.format(nowtime, pnowtime, nowtime - pnowtime))
            while nowtime - pnowtime < ftime - pftime and pftime and ftime - pftime < 1:
                nowtime = time.time()
            pnowtime = nowtime
            pftime = ftime
            
            #img = cv2.imread(filepath)
            
            #cv2.imshow('fuckcv', img)

            vp.send_image_by_path(filepath, ftime)
        else:
            vp.response()


