import robomaster
from robomaster import robot
from robomaster import camera
import time
import cv2
import pygame
import threading
import numpy as np

camera_end = True   #camera_display thread 종료 여부 변수
area = 0    #탐지한 색상 크기 (얼마나 떨어져있는가)
location = [0,0]   #드론 뒤치 정보(공유변수)
sem = threading.Semaphore(2)
state_go = 0

def init_key():
    """ pygame 초기화
    """
    pygame.init()
    win = pygame.display.set_mode((400,400))

def get_key(keyName):
    """ 해당 키(키보드 입력)가 입력되었는지 확인

    Args: keyName (string): Key Name

    Returns: bool: keyName이 눌렸는지 반환
    """
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
    """ 현재 어떤 키입력들이 있는가

    Returns: List: [좌우, 앞뒤, 위아래, 좌우회전, 이륙, 착륙]
    좌우, 앞뒤, 위아래, 좌우회전: [-100,100]의 값 전달
    이륙, 착륙: bool
    """
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
    """ 드론 이륙
    """
    t1_flight.takeoff().wait_for_completed()
    #.wait_for_completed()는 해당 동작이 마무리 될때까지 대기

def detectBlock():
    """ 장애물 유무 확인

    Returns: bool: 장애물 유무
    """
    dis = get_distance()   #tof 거리센서로 거리측정
    print("distance: ",dis)
    if dis < 900:   #0.9m안에 장애물있는가
        return True
    
    return False

def battery_display():
    """ 현재 배터리 잔량 확인후 매트릭스 LED에 표시
    
    """
    now_battery = t1_battery.get_battery()
    format_battery = now_battery%8 + 1
    led_value = "00000000"*7 + "b"*format_battery + "r"*(8-format_battery)
    t1_led.set_mled_boot(led_value)

def get_distance():
    """ 현재 거리 측정

    Returns:
        flaot: 거리 (mm 단위)
    """
    sem.acquire()
    dis = t1_sensor.get_ext_tof()
    while dis == None:
        dis = t1_sensor.get_ext_tof()
    sem.release()
    return dis

def go():
    global state_go
    t1_flight.rc(a=0,b=30,c=0,d=0)  # 전방으로 이동
    while state_go == 0:
        state_go = 1

def stop():
    global state_go
    
    t1_flight.rc(a=0,b=0,c=0,d=0)
    while state_go == 1:
        state_go = 0
    
    
def auto_pilot():
    """ 자율주행
    단순히 전방으로 이동하면서 장애물을 만나면
    기체 좌,우를 살핀 후 더 넓은 구역으로 회전 후 다시 전방 주행
    """
    init_key()    # key입력받기 초기화
    takeoffDrone()  #드론 이륙
    count = 0   #자율주행 진행상황, 동작 횟수 기입할 변수
    pre_rotate = -1 # -1: 좌, 1: 우
    temp = 100
    while True:
        vals = get_keyboard_input()     #키보드 input 받아오기
        if vals[5]:    #u키를 꾹 눌러서 강제 종료
            break
        if count % 30 == 0:
            print("Current Battery: ", t1_battery.get_battery(), "%")
        time.sleep(0.02)
        isDetect = detectBlock()
        # while isDetect == None:
        #     isDetect = detectBlock()
        if isDetect:   # 장애물을 감지하면
            stop()
            time.sleep(0.02)
            if temp >= 1 and temp <= 4:
                t1_flight.rotate(-90*pre_rotate).wait_for_completed()   #원래 가던 방향 바라보기
                temp = 25
                continue
            temp = 0
            t1_flight.rotate(-90).wait_for_completed() # 왼쪽으로 기체 90도 회전
            # sem.acquire()
            dis_left = get_distance()   # 진행하던 방향의 왼쪽 편의 거리 측정, 저장
            # while dis_left == None:
            #     dis_left = get_distance() 
            time.sleep(0.02)
            t1_flight.rotate(180).wait_for_completed()  # 오른쪽으로 기체 90도 회전
            dis_right = get_distance()  # 진행하던 방향의 왼쪽 편의 거리 측정, 저장
            # while dis_right == None:
            #     dis_right = get_distance()
            time.sleep(0.02)
            # sem.release()
            print("Left: ",dis_left,",    Right: ",dis_right)
            if dis_left >= dis_right:    # 더 트인 공간을 찾아 기체 회전
                print("Select Left, ", end=" ")
                pre_rotate = -1
                t1_flight.rotate(-180).wait_for_completed()
            else:
                print("Select Right", end=" ")
                pre_rotate = 1
                
            print("End rotate ", count)
        else:   # 장애물이 없을 시
            count += 1
            temp += 1   #벽이 아닌 장애물이였을때 우회를 위해 다시 가던 방향을 확인해보는 변수 (일정 거리를 갔을 때 확인)
            if temp == 15:
                stop()
                time.sleep(0.02)
                t1_flight.rotate(-90*pre_rotate).wait_for_completed()   #원래 가던 방향 바라보기
                # sem.acquire()
                isDetect = detectBlock()
                # while isDetect == None:
                #     isDetect = detectBlock()
                # sem.release()
                if isDetect:
                    t1_flight.rotate(90*pre_rotate).wait_for_completed()    #다시 돌려서 가기
                else:
                    #좌표 갱신하는거 dxy 바꾸기
                    pre_rotate = -pre_rotate
                temp = 25
            go()

        time.sleep(0.25)
    
    # 동작 종류후 착륙
    t1_flight.land().wait_for_completed()
    t1_drone.close()

def human_controll():
    """ 키보드 입력을 통한 드론 직접 컨트롤
    방향키: 앞,뒤,좌,우
    y: 이륙, u: 착륙
    w: 위, s: 아래
    """
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
            while True:
                print(t1_drone.get_attitude())
                vals = get_keyboard_input()
                if vals[5]:  #'u' key가 눌렸을때 착륙
                    t1_flight.land().wait_for_completed()
                    t1_drone.close()
                    break
                print("Go:",vals[0],vals[1],vals[2], sep = " ")
                # 키입력대로 이동, 주행 
                t1_flight.rc(a=vals[0],b=vals[1],c=vals[2],d=vals[3])
                time.sleep(0.05)

def empty(a):
    """Trackbar 생성을 위한 동작이 없는 함수

    Args:
        a (none): 무시
    """
    pass
    
def camera_display():
    """camera diplay
    camera를 통해 받아온 frame을 cv2로 display
    """
    global camera_end
    global area
    t1_camera.start_video_stream(display=False) #카메라 비디오 스트림 시작
    
    while camera_end:
        img = t1_camera.read_video_frame(timeout=10)  #프레임 받아오기
        
        cv2.imshow("Drone Camera", img) #display
        cv2.waitKey(1)  #fps 조절
        
    t1_camera.stop_video_stream()   #비디오 스트림 종료

def location_based_imu():
    global state_go
    pre_pitch = 0
    sem.acquire()
    imu = t1_drone.get_attitude()
    time.sleep(0.01)
    sem.release()
    time.sleep(0.25)
    while camera_end:
        try:
            if state_go == 1:
                sem.acquire()
                imu = t1_drone.get_attitude()
                time.sleep(0.01)
                sem.release()
                now_yaw = imu['yaw']
                now_pitch = abs(imu['pitch'])
                if  -45 < now_yaw < 45:
                    location[0] += (pre_pitch + now_pitch) / 2 * 6.85
                elif 45 < now_yaw < 135:
                    location[1] += (pre_pitch + now_pitch) / 2 * 6.85
                elif 135 < now_yaw <= 180 or -180 <= now_yaw < -135:
                    location[0] -= (pre_pitch + now_pitch) / 2 * 6.85
                elif -135 < now_yaw < -45:
                    location[1] -= (pre_pitch + now_pitch) / 2 * 6.85
                pre_pitch = now_pitch
        except:
            print("--")
        print(int(location[0]),", ", int(location[1]))
        time.sleep(0.25)

def strart_action(type):
    """비행 동작 실행
    type에 따른 드론 동작 실행
    Args:
        type (int): 비행 조종타입   1: auto, 2: human controll
    """
    global camera_end
    if type == 1:
        # auto_pilot thread 생성
        flight_threading = threading.Thread(target=auto_pilot)
    elif type == 2:
        # human_controll thread 생성
        flight_threading = threading.Thread(target=human_controll)
    else:
        # Invalid Type
        print("error: 잘못된 타입 선택")
        return
    # 카메라 관련 thread 생성
    camera_threading = threading.Thread(target=camera_display)
    imu_threading = threading.Thread(target=location_based_imu)

    #각 스레드 시작
    flight_threading.start()
    #camera_threading.start()
    imu_threading.start()

    # flght thread 종료까지 대기
    flight_threading.join()
    # camera thread 종료를 위한 변수 변경
    camera_end = False
    # camera thread 종료까지 대기
    #camera_threading.join()
    imu_threading.join()
    

################## main 실행영역 ##################
#드론, 변수 초기화
try:
    t1_drone = robot.Drone()    # 드론 객체 생성
    t1_drone.initialize()   # 드론 초기화
    t1_flight = t1_drone.flight     #드론 주행관련 변수
    t1_led = t1_drone.led   #드론 LED관련 변수
    t1_camera = t1_drone.camera     #드론 카메라관련 변수
    t1_battery = t1_drone.battery   #드론 배터리관련 변수
    t1_sensor = t1_drone.sensor     #드론 센서관련 변수
    print("연결 성공")
    print("Current Battery: ", t1_battery.get_battery(), "%")
    print(t1_drone.get_wifi())
except Exception as e:    
    # 드론 연결 실패시 프로그램 종료
    print("연결 실패")
    exit()

#조종 타입 선택
type_select = int(input("1. 자동비행\n2. 직접 조종\n비행 타입을 선택하세요:"))
strart_action(type_select) #타입에 맞는 동작 실행

print("END")