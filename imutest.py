import robomaster
from robomaster import robot
from robomaster import camera
import time
import cv2
import pygame
import threading
import numpy as np

t1_drone = robot.Drone()    # 드론 객체 생성
t1_drone.initialize()   # 드론 초기화
t1_flight = t1_drone.flight     #드론 주행관련 변수
t1_battery = t1_drone.battery
print("Current Battery: ", t1_battery.get_battery(), "%")

a = int(input("시작?"))
if a == 1:
    t1_flight.takeoff().wait_for_completed()
    count = 0
    while count < 5:
        t1_flight.rc(a=0,b=30,c=0,d=0)
        time.sleep(0.05)
        print("count ",count,"  ",t1_drone.get_attitude())
        time.sleep(0.5)
        count+=1
    t1_flight.rc(a=0,b=0,c=0,d=0)
    time.sleep(1)
    t1_flight.land().wait_for_completed()
    t1_drone.close()
    print("End")
else:
    print("End2")