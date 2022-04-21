# zz_tracking
## 專案說明

* 人工智慧應用於即時行人影像虛實整合系統
    * 行人追蹤 並顯示足跡
    * 計算人數
    * 計算平均速度 
    * 行人影像消除/遮蔽
    * 虛擬背景合成
    * 虛擬物件互動(移動背景)
    * 視訊多人合成

# 安裝
## 硬體環境
* windows 10
    ```$ dxdiag```
    ![](https://i.imgur.com/RYAQTdM.png)
    ![](https://i.imgur.com/xmGqw9H.png)

## 安裝 CUDA
* 參考:
    [Win10 安裝 CUDA、cuDNN 教學](https://medium.com/ching-i/win10-%E5%AE%89%E8%A3%9D-cuda-cudnn-%E6%95%99%E5%AD%B8-c617b3b76deb)
    
* 官方網站
    [CUDA Toolkit Archive](https://developer.nvidia.com/cuda-toolkit-archive)

* 安裝版本
    * CUDA Toolkit 11.5.1 (November 2021)

## 安裝 cuDNN
* 官方網站
    [cuDNN Archive](https://developer.nvidia.com/rdp/cudnn-archive)

* 安裝版本
    * cuDNN v8.3.0 (November 3rd, 2021), for CUDA 11.5
    * cuDNN Library for Windows (x64)

## 安裝 Python
* 官方網站
    [python](https://www.python.org/)

* 安裝版本
    Python 3.9.9 - Nov. 15, 2021

* 更新 pip
    
    ``` py -m pip install --upgrade pip```

## 安裝 PyTorch
* 官方網站
    [PyTorch](https://pytorch.org/)

* 安裝
    
    ```pip3 install torch==1.10.0+cu113 torchvision==0.11.1+cu113 torchaudio===0.10.0+cu113 -f https://download.pytorch.org/whl/cu113/torch_stable.html```
    ![](https://i.imgur.com/dO7tPod.png)


## python 套件安裝
* Pip更新
    
    ```py -m pip install -upgrade pip```
    
* openCV
    
    ```pip install opencv-python```

* 安裝 mysql
    
    ```pip install mysql-connector-python```

* imageio
    
    ```pip install imageio```

## YOLOv4 設定

* Paper YOLO v4: https://arxiv.org/abs/2004.10934

* GitHub(Author): https://github.com/AlexeyAB/darknet

* GitHub(PyTorch): https://github.com/Tianxiaomo/pytorch-YOLOv4

* Model Weights Download: https://drive.google.com/open?id=1cewMfusmPjYWbrnuJRuKhPMwRe_b9PaT

* 設置 library
    * 把 pytorch-YOLOv4 底下的資料(code)複製到 zz_tracking/yolo4 底下，可直接下載放到雲端的 code

* 設置 weight file
    * 把 .weights file 放到 zz_tracking/data/weights/

* 設置 cfg file
    * 把 .cfg file 放到 zz_tracking/data/cfg/

* 以上設置可從程式碼修改，只要你知道路徑位置

## 資料庫設定

* 安裝 xampp (MySQL)
    * 教學: https://ithelp.ithome.com.tw/articles/10197921

* 資料庫說明:
    * 名稱: konpeko
    * 編碼格式: UTF-8 unicode-ci

## 資料表說明:
* check_area
    
    * 說明: 儲存場域的所有檢查點資訊，至少兩個(check_area_list)，包括已記錄的場域名稱、已量測的實際距離和對應在畫面中像素的距離(distance_matrix)
    
    * 欄位說明
    
        | site_id | site_name | check_area_list |  distance_matrix	   |
        | -------- | -------- | -------- | --- |
        | pk , ai     |   場域名稱   | 檢查點區塊座標列表     |  各檢查點相距矩陣   |

    * 實例:
        
        ![](https://i.imgur.com/B5ntYEc.png)

    * 補充:

        distance_matrix = A， Aij 表示 第 i 檢查點對 j 檢查點實際距離為 Aij 單位m，Aji 表示 第 i 檢查點對 j 檢查點像素距離為 Aji，[0, 2.238, 565.107, 0] 表示 點0 到點1 距離 2.238 公尺， 565.107 格像素
    
* *_box

    * 說明: 儲存每個 Tracker 的 bounding box 資訊，不同的場域會有各自的表
    
    * 實例:
        
        ![](https://i.imgur.com/JqOxP5e.png)


* average_speed
    
    * 說明: 儲存每個 Tracker 的 平均速度 
    
    * 實例:
        
        ![](https://i.imgur.com/e0QwIIM.png)


## 操作說明

* 啟動系統(伺服器端)

    * 執行 zz_tracking/tracking_server.py

* 啟動攝影機端影像來源(使用者端)
    
    * 執行 zz_tracking/camera_input.py
    
    * 輸入場域名稱

* 啟動資料夾影像來源(使用者端)
    
    * 執行 zz_tracking/pic_input.py
    
    * 輸入資料夾路徑位置
    
    * 輸入場域名稱 
    
    * 可更改傳送比率，若需要節省數據傳輸，可調低傳送比率，ex: 辨識到有人的影像就紀錄影像時間，再從那個時間去反推附近的時間，在從那個時間點抓全部的影像

## 伺服器設定說明

* 更改 IP

    * 修改 zz_tracking/tracking_server.py 的 IP 、 PORT 參數

* 更改/使用 資料庫
    
    * 修改 zz_tracking/tracking_server.py 的 DB_NAME 參數
    
    * 若不用資料庫修設為 None

* 回傳辨識後的影像給客戶端
    
    * SEND_IMAGE = True

* 顯示影像
    * SHOW_IMAGE = False

## 輔助工具操作說明

* 抓兩點座標、計算像素點距離
    
    * 執行 zz_tracking/grab_coord.py
    
    * 輸入資料夾路徑或圖片路徑，等待圖片讀取出現
    
    * 在圖片上點擊第一個點拖曳到第二點放開，終端會輸出兩點座標和絕對像素距離、長寬
        ![](https://i.imgur.com/C81OaMX.png)
    
    * 可重複操作點擊
    
    * 按下 esc 鍵預覽下一張或離開

* 視訊流定時保存影像
    
    * 執行 zz_tracking/recorder.py
    
    * 預設是儲存周一至周五早上8點到晚上8點的影像，要更改時間要從code中改
    
    * 修改 CAMERA_ID 攝影機位置

* 影片截圖(video to images)

* 影片合成(images to video)
    * 目的: 圖片合成影片
    * zz_tracking/imgs2gif.py
        * 圖片變gif
        * 輸入資料夾 圖片檔名必須為 秒數名稱.jpg
        * 輸出在 data/gif/目前時間.gif

* 複製特定秒數的影像到新的資料夾
    
    * 目的: 將特定秒數從資料夾轉移到另外一個資料夾
        ![](https://i.imgur.com/gTZ7JoG.png)

    
    * 執行 zz_tracking/select_image.py
    
    * 輸入含有時間的影像的資料夾位置(會自動整理成時間序列)或手動輸入影像時間
    
    * 輸入要抓取影像的資料夾
    
    * 輸入要轉移的目的地資料夾


# 系統說明

## 功能
* 計算平均速度
    * 偵測到行人從 A 區走到 B 區會計算平均速度並把速度顯示在右側資訊欄上
        ![](https://i.imgur.com/g6bzDJs.jpg)
    * 平均速度的結果會存到資料庫中
        ![](https://i.imgur.com/COl5NjH.png)
    * 行人離開 3 秒停止追蹤即不會顯示資訊在螢幕上
        
* 行人追蹤移動足跡
    * 製作軌跡圖
       ![](https://imgur.com/Y1SG5ql.gif)
    


