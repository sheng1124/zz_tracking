# zz_tracking
* 人工智慧應用於行人影像虛實整合系統

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