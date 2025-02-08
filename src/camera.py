'''
因为pyqt6与树莓派5的picamera2库存在调用冲突 无奈之下只好使用此笨方法捕获摄像头照片
运行clock.py前 要将此程序运行到后台
原理很简单 用cam.ini控制读写状态 此py文件不断写入照片 clock.py负责读取照片
'''

from picamera2 import Picamera2
import time
picam2 = Picamera2()
picam2.options["quality"] = 50
picam2.start()

with open('cam.ini', 'w') as f:
    f.write('r')

while True:
    picam2.capture_file("now.jpg")
    with open('cam.ini', 'w') as f:
        f.write('d')
    while 1:    #写入照片后 将cam.ini内容修改为d 并等待clock.py读取照片并将cam.ini修改为r后继续写入照片
        with open('cam.ini', 'r') as f:
            data = f.read()
        if data=='r':
            break



