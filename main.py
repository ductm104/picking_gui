import os
import glob
import argparse
import numpy
import cv2


from visualizer import *
from utils import *


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=str,
        help="path to dicom folder")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()

    dataset = read_folder(args.folder)
    json_path = os.path.join(args.folder, os.path.basename(args.folder) + '.json')
    vis = VIS(dataset, json_path)

    # init cv2 window and functions
    window_grid = "all_data"
    window_video = "full_video"
    window_button = "button"

    cv2.namedWindow(window_video)
    cv2.moveWindow(window_video, 1100, 0)

    cv2.namedWindow(window_button, cv2.WINDOW_AUTOSIZE)
    cv2.moveWindow(window_button, 0, 0)

    cv2.namedWindow(window_grid, cv2.WINDOW_AUTOSIZE)
    cv2.resizeWindow(window_grid, vis.win_width, vis.win_height)
    cv2.moveWindow(window_grid, 400, 0)
    cv2.createTrackbar('Scroll bar', window_grid, 0, 100, on_trackbar)

    cv2.setMouseCallback(window_grid, on_grid_click)
    cv2.setMouseCallback(window_button, on_button_click)

    while True:
        grid, full_video, img_button = vis.get_ui()

        cv2.imshow(window_grid, grid)
        cv2.imshow(window_video, full_video)
        cv2.imshow(window_button, img_button)

        key = cv2.waitKey(30)
        if key == ord("q"):
            cv2.destroyAllWindows()
            exit(0)
        elif key == ord(" "):
            pass
