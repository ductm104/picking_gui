import cv2
import numpy as np

def nothing(val):
    print(val)

cv2.namedWindow("bla")

cv2.createTrackbar('b', 'bla', 0, 100, nothing)

img = np.zeros((512, 512, 3), dtype=np.uint8)
cv2.imshow('bla', img)
cv2.waitKey(0)
