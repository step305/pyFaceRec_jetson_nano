# encode_faces.py
from imutils import paths # 헬퍼 라이브러리
import face_recognition
import pickle
import cv2
import os

print("[정보] 얼굴 인코딩을 시작합니다...")
# 어제 사진 넣어둔 'dataset' 폴더 경로
dataset_path = "dataset" 

# dataset 폴더 안의 모든 이미지 경로를 가져오기
imagePaths = list(paths.list_images(dataset_path))

# 인코딩(특징 벡터)과 이름을 저장할 리스트 초기화
knownEncodings = []
knownNames = []

# 이미지 경로들을 하나씩 처리
for (i, imagePath) in enumerate(imagePaths):
    # 폴더 이름이 곧 그 사람의 이름 (예: dataset/user1/1.jpg -> 'user1')
    name = imagePath.split(os.path.sep)[-2]
    print(f"[정보] {i+1}/{len(imagePaths)}번째 이미지 처리 중: {imagePath} (이름: {name})")

    # 이미지를 불러오고 BGR -> RGB로 변환 (face_recognition은 RGB를 씀)
    image = cv2.imread(imagePath)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # 이미지에서 얼굴 영역(bounding box) 찾기
    boxes = face_recognition.face_locations(rgb, model="hog") # hog가 cnn보다 빠름

    # 찾은 얼굴 영역을 128차원 벡터(인코딩)로 변환
    encodings = face_recognition.face_encodings(rgb, boxes)

    # (보통 사진 1장에 1명) 인코딩된 벡터를 저장
    for encoding in encodings:
        knownEncodings.append(encoding)
        knownNames.append(name)

# 인코딩과 이름을 딕셔너리(사전) 형태로 저장
print("[정보] 인코딩된 데이터를 파일로 저장합니다...")
data = {"encodings": knownEncodings, "names": knownNames}

# "encodings.pickle"이라는 파일에 '정답지'를 저장
with open("encodings.pickle", "wb") as f:
    f.write(pickle.dumps(data))

print("[완료] 얼굴 인코딩이 완료되었습니다.")