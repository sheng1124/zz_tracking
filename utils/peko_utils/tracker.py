

class Tracker_manager():
    def __init__(self) -> None:
        pass

    def input_boxs(self, results):
        if len(results) == 1:
            #指派給時間空間最接近的tracker
            #不符合條件及新的人出現
            pass

class Tracker():
    def __init__(self) -> None:
        self.frame_list = []
        self.direct = 0 # 1 右下 2 右上 3 左下 4 左上
        
    #與上一個框比較 計算新方向