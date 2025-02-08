#面部检测工具

import cv2
import mediapipe as mp
import time
from numpy import greater
import utils
import numpy as np

def euclidean_distance(point1, point2):
    return np.linalg.norm(np.array(point1) - np.array(point2))


def eye_aspect_ratio(eye_points):
    vertical = euclidean_distance(eye_points[4], eye_points[12])
    horizontal = euclidean_distance(eye_points[0], eye_points[10])
    return vertical / horizontal


def mouth_aspect_ratio(mouth_points):
    vertical = euclidean_distance(mouth_points[16], mouth_points[25])
    horizontal = euclidean_distance(mouth_points[0], mouth_points[6])
    return vertical / horizontal


FONTS = cv2.FONT_HERSHEY_COMPLEX
# bounder indices
FACE_OVAL = [
    10,
    338,
    297,
    332,
    284,
    251,
    389,
    356,
    454,
    323,
    361,
    288,
    397,
    365,
    379,
    378,
    400,
    377,
    152,
    148,
    176,
    149,
    150,
    136,
    172,
    58,
    132,
    93,
    234,
    127,
    162,
    21,
    54,
    103,
    67,
    109,
]
LIPS = [
    61,
    146,
    91,
    181,
    84,
    17,
    314,
    405,
    321,
    375,
    291,
    308,
    324,
    318,
    402,
    317,
    14,
    87,
    178,
    88,
    95,
    185,
    40,
    39,
    37,
    0,
    267,
    269,
    270,
    409,
    415,
    310,
    311,
    312,
    13,
    82,
    81,
    42,
    183,
    78,
]
LOWER_LIPS = [
    61,
    146,
    91,
    181,
    84,
    17,
    314,
    405,
    321,
    375,
    291,
    308,
    324,
    318,
    402,
    317,
    14,
    87,
    178,
    88,
    95,
]
UPPER_LIPS = [
    185,
    40,
    39,
    37,
    0,
    267,
    269,
    270,
    409,
    415,
    310,
    311,
    312,
    13,
    82,
    81,
    42,
    183,
    78,
]
LEFT_EYE = [
    362,
    382,
    381,
    380,
    374,
    373,
    390,
    249,
    263,
    466,
    388,
    387,
    386,
    385,
    384,
    398,
]
RIGHT_EYE = [
    33,
    7,
    163,
    144,
    145,
    153,
    154,
    155,
    133,
    173,
    157,
    158,
    159,
    160,
    161,
    246,
]

map_face_mesh = mp.solutions.face_mesh


def landmarksDetection(img, results, draw=False):
    img_height, img_width = img.shape[:2]
    mesh_coord = [
        (int(point.x * img_width), int(point.y * img_height))
        for point in results.multi_face_landmarks[0].landmark
    ]
    if draw:
        [cv2.circle(img, p, 2, utils.GREEN, -1) for p in mesh_coord]
    return mesh_coord
