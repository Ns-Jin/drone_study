import robomaster
from robomaster import robot
from robomaster import camera
import time
import cv2
import pygame

def init_key():
    pygame.init()
    win = pygame.display.set_mode((400,400))

def get_key(keyName):
    result = False
    for eve in  pygame.event.get():
        pass
    keyInput = pygame.key.get_pressed()
    myKey = getattr(pygame, 'K_{}'.format(keyName))
    if keyInput[myKey]:
        result = True
    pygame.display.update()
    
    return result

def get_keyboard_input():
    start = False
    end = False
    lr,fb,ud,ro = 0,0,0,0
    dis = 30
    
    if get_key("LEFT"):
        lr = dis
    elif get_key("RIGHT"):
        lr = -dis
    if get_key("UP"):
        fb = dis
    elif get_key("DOWN"):
        fb = -dis
    if get_key("w"):
        ud = dis
    elif get_key("s"):
        ud = -dis
    if get_key("y"):
        start = True
    elif get_key("u"):
        end = True
    
    return [lr, fb, ud, ro, start, end]
        
def takeoffDrone():
    t1_led.set_led(r=255,g=0,b=0)
    t1_led.set_led_breath(freq=1, r=0, g=0, b=255)
    time.sleep(3)
    t1_led.set_led(r=0,g=255,b=0)
    time.sleep(1) 
    t1_flight.takeoff().wait_for_completed()
    t1_led.set_led(r=0,g=0,b=0)

def detectBlock():
    dis = t1_sensor.get_ext_tof()
    print("distance: ",dis)
    if dis < 600:
        return True
    
    return False

def go_forward(dis):
    t1_flight.forward(distance = dis).wait_for_completed()

def battery_display():
    now_battery = t1_battery.get_battery()
    format_battery = now_battery%8 + 1
    led_value = "00000000"*7 + "b"*format_battery + "r"*(8-format_battery)
    t1_led.set_mled_boot(led_value)
    
def auto_pilot():
    takeoffDrone()
    t1_camera.start_video_stream(display=False)
    count = 0
    trap_count = 0

    while True:
        print("count: ", count)
        # img = t1_camera.read_cv2_image()
        # img = cv2.resize(img, (360,240))
        # cv2.imshow("Image", img)
        # cv2.waitKey(1)
        if count > 10:
            break
        if count % 3 == 0:
            battery_display()
        if detectBlock():
            if trap_count >= 3:
                print("트랩상황")
                break
            t1_flight.rc(a=0,b=0,c=0,d=0)  #앞으로 가던거 멈추기
            time.sleep(0.05)
            trap_count += 1
            t1_flight.rotate(-90).wait_for_completed()
            print("End rotate")
        else:
            count += 1
            trap_count = 0
            #go_forward(30)
            t1_flight.rc(a=0,b=30,c=0,d=0)
            time.sleep(0.05)
            print("End go forward")
        time.sleep(3)
        
    t1_flight.land().wait_for_completed()
    t1_camera.stop_video_stream()
    t1_drone.close()

def human_controll():
    init_key()    # key입력받기 초기화
    flight_status = False     # 현재 비행 상태인지 확인, 상태에 따라 입력값이 달라짐
    while True:
        if flight_status:  #한번 날리고 착륙했으면 종료
            break
        #key 입력이 있을시 그 정보 받아오기
        vals = get_keyboard_input()
        if vals[4]:  #'y' key가 눌렸을때 이륙
            flight_status = True  #비행상태 갱신
            takeoffDrone()
            time.sleep(0.05)
            t1_camera.start_video_stream(display=False)
            while True:
                vals = get_keyboard_input()
                if vals[5]:  #'u' key가 눌렸을때 착륙
                    t1_flight.land().wait_for_completed()
                    t1_camera.stop_video_stream()
                    t1_drone.close()
                    break
                print("Go:",vals[0],vals[1],vals[2], sep = " ")
                t1_flight.rc(a=vals[0],b=vals[1],c=vals[2],d=vals[3])
                time.sleep(0.05)
        
################## main 실행영역 ##################
#드론, 변수 초기화
try:
    t1_drone = robot.Drone()
    t1_drone.initialize()
    t1_flight = t1_drone.flight
    t1_led = t1_drone.led
    t1_camera = t1_drone.camera
    t1_battery = t1_drone.battery
    t1_sensor = t1_drone.sensor
    t1_led.set_mled_bright(bright=50)
    t1_led.set_mled_boot("0000000000r00r000r0rr0r000r00r00000rr000")
    print("연결 성공")
    print("Current Battery: ", t1_battery.get_battery(), "%")
except Exception as e:
    print("연결 실패")
    exit()
    
#조종 타입 선택
type_select = int(input("1. 자동비행\n2. 직접 조종\n비행 타입을 선택하세요:"))

if type_select == 1:
    auto_pilot()   #자동비행
elif type_select == 2:
    human_controll()    #직접 컨트롤
else:
    print("error: 잘못된 타입 선택")
