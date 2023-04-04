import robomaster
from robomaster import robot
from robomaster import camera
import time
import cv2
import pygame


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
    t1_led.set_led(r=255,g=0,b=0)
    t1_led.set_led_breath(freq=1, r=0, g=0, b=255)
    time.sleep(3)
    t1_led.set_led(r=0,g=255,b=0)
    time.sleep(1) 
    t1_flight.takeoff().wait_for_completed()
    #.wait_for_completed()는 해당 동작이 마무리 될때까지 대기

def detectBlock():
    """ 장애물 유무 확인

    Returns: bool: 장애물 유무
    """
    dis = t1_sensor.get_ext_tof()   #tof 거리센서로 거리측정
    print("distance: ",dis)
    if dis < 600:   #60cm안에 장애물있는가
        return True
    
    return False

def battery_display():
    """ 현재 배터리 잔량 확인후 매트릭스 LED에 표시
    
    """
    now_battery = t1_battery.get_battery()
    format_battery = now_battery%8 + 1
    led_value = "00000000"*7 + "b"*format_battery + "r"*(8-format_battery)
    t1_led.set_mled_boot(led_value)
    
def auto_pilot():
    """ 자율주행
    단순히 전방으로 이동하면서 장애물을 만나면
    기체 왼쪽 회전 후 다시 전방 주행
    """
    takeoffDrone()
    count = 0   #일정 횟수동안만 전진하도록 확인하는 변수
    trap_count = 0  #트랩(사방이 막힌상황)인지 확인하는 변수

    while True:
        print("count: ", count)
        if count > 10:
            # 일정 동작 수행후 행동 종료
            break
        if count % 3 == 0:
            # 일정 주기마다 현재 배터리 잔량 최신화
            battery_display()
        if detectBlock():   # 장애물을 감지하면
            if trap_count >= 3:
                # 트랩시 비상착륙
                print("트랩상황")
                break
            t1_flight.rc(a=0,b=0,c=0,d=0)  # 앞으로 가던거 멈추기
            time.sleep(0.05)
            trap_count += 1
            t1_flight.rotate(-90).wait_for_completed() # 왼쪽으로 기체 90도 회전
            print("End rotate")
        else:   # 장애물이 없을 시
            count += 1
            trap_count = 0  # trap_count 초기화
            #go_forward(30)
            t1_flight.rc(a=0,b=30,c=0,d=0)  # 전방으로 이동
            time.sleep(0.05)
            print("End go forward")
        time.sleep(3)
    
    # 동작 종류후 착륙
    t1_flight.land().wait_for_completed()
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
            while True:
                vals = get_keyboard_input()
                if vals[5]:  #'u' key가 눌렸을때 착륙
                    t1_flight.land().wait_for_completed()
                    t1_drone.close()
                    break
                print("Go:",vals[0],vals[1],vals[2], sep = " ")
                # 키입력대로 이동, 주행 
                t1_flight.rc(a=vals[0],b=vals[1],c=vals[2],d=vals[3])
                time.sleep(0.05)


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
    t1_led.set_mled_bright(bright=50)   # 매트릭스 LED 밝기 조절
    # 매트릭스 LED 세팅
    t1_led.set_mled_boot("0000000000r00r000r0rr0r000r00r00000rr000")
    print("연결 성공")
    print("Current Battery: ", t1_battery.get_battery(), "%")
except Exception as e:
    # 드론 연결 실패시 프로그램 종료
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
