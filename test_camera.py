# test_camera.py
import cv2

print("카메라를 켭니다...")
# 0번 카메라(기본 웹캠)에 연결
cap = cv2.VideoCapture(0)

# 카메라가 켜졌는지 확인
if not cap.isOpened():
    print("오류: 카메라를 열 수 없습니다.")
    exit()

print("카메라가 켜졌습니다. 'q' 키를 누르면 종료됩니다.")

# 카메라가 켜져있는 동안 계속 반복
while True:
    # 카메라에서 현재 프레임(이미지)을 읽어오기
    # ret: 성공 여부 (True/False), frame: 실제 이미지
    ret, frame = cap.read()

    # 프레임을 성공적으로 읽어왔다면
    if ret:
        # "Camera Test"라는 이름의 창에 현재 프레임을 보여주기
        cv2.imshow("Camera Test", frame)

        # 1밀리초 동안 키 입력을 기다림
        # 만약 'q' 키가 눌리면
        key = cv2.waitKey(1)
        if key == ord('q'):
            print("'q' 키가 입력되어 종료합니다.")
            break
    # 프레임 읽기에 실패했다면
    else:
        print("오류: 프레임을 읽을 수 없습니다.")
        break

# 사용이 끝난 카메라와 창을 모두 해제
cap.release()
cv2.destroyAllWindows()