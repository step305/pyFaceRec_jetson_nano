import cv2
from pycoral.adapters.common import input_size
from pycoral.adapters.detect import get_objects
from pycoral.utils.edgetpu import make_interpreter
from pycoral.utils.edgetpu import run_inference
import face_recognition
import os
from parameters import *


def calc_face_embeddings(cv2_im_rgb, faces):
    boxes = []
    for face in faces:
        bbox = face.bbox
        x0, y0 = int(bbox.xmin), int(bbox.ymin)
        x1, y1 = int(bbox.xmax), int(bbox.ymax)
        w = x1 - x0
        h = y1 - y0
        x0 = int(x0 + w / 10)
        y0 = int(y0 + h / 4)
        x1 = int(x1 - w / 10)
        y1 = int(y1)
        boxes.append((y0, x1, y1, x0))
    enc = face_recognition.face_encodings(cv2_im_rgb, known_face_locations=boxes)
    return enc


class FaceDetector:
    def __init__(self):
        self.face_model = os.path.join(os.path.dirname(__file__),
                                       'models/mobilenet_ssd_v2_face_quant_postprocess_edgetpu.tflite')
        self.max_faces = 10
        self.threshold = FACE_DETECTOR_THRESHOLD
        self.interpreter = make_interpreter(self.face_model)
        self.interpreter.allocate_tensors()
        self.inference_size = input_size(self.interpreter)

    def get_rgb_image(self, frame):
        cv2_im_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        cv2_im_rgb = cv2.resize(cv2_im_rgb, self.inference_size)
        return cv2_im_rgb

    def detect(self, cv2_im_rgb):
        run_inference(self.interpreter, cv2_im_rgb.tobytes())
        objs = get_objects(self.interpreter, self.threshold)[:self.max_faces]
        return objs
