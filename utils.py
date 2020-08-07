import os
import threading
import time
import glob
import argparse
import numpy
import cv2
import pydicom
import json

from concurrent.futures import ThreadPoolExecutor
from multiprocessing.pool import ThreadPool
from multiprocessing import Value
from visualizer import *
from button import Button


def convert_images(images):
    # convert to N*H*W*3
    if len(images.shape) == 2:
        # only one GRAY frame
        images = np.stack([images]*3).transpose(1, 2, 0)[None,...]
    elif len(images.shape) == 3:
        if images.shape[-1] <= 3:
            images = images[None, ...]
            # only one RGB frame
        else:
            # video of GRAY frames
            images = np.repeat(images[..., None], 3, axis=-1)
    else:
        # video of RGB frames
        pass
    return images


def get_thumbnail(images):
    if images.shape[0] > 10:
        return images[10, ...]
    return images[-1, ...]


def read_json(folder_path):
    json_path = os.path.join(folder_path, os.path.basename(folder_path) + '.json')

    try:
        with open(json_path, 'r') as file:
            label = json.load(file)
    except:
        raise error("JSON not found!")

    return label


counter = Value('i', 0)
def read_dicom(file_path):
    try:
        dataset = pydicom.dcmread(file_path)
    except:
        return None, None

    try:
        imgs = dataset.pixel_array
    except:
        return None, None

    imgs = convert_images(imgs)

    # just for print progress
    global counter
    with counter.get_lock():
        counter.value += 1
        print(f'Read {counter.value} files', end='\r')

    return file_path, imgs


def read_folder(folder_path, num_thread=8):
    folder_path = os.path.abspath(folder_path)
    file_paths = glob.glob(os.path.join(folder_path, '*'))
    print(f'READING {len(file_paths)} FILES FROM "{folder_path}]"')

    with ThreadPoolExecutor(num_thread) as pool:
        data = list(pool.map(read_dicom, file_paths))

    label_data = read_json(folder_path)
    file_paths, imgs_data, labels = [], [], []

    for item in data:
        if item[0] is not None:
            file_paths.append(item[0])
            imgs_data.append(item[1])
            labels.append(label_data[item[0]])

    print("NUM DICOMs: ", len(file_paths))

    return {'file_paths': file_paths,
            'imgs_data': imgs_data,
            'labels': labels}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=str,
        help="path to dicom folder")
    args = parser.parse_args()
    return args


def on_grid_click(event, x, y, flags, param):
    global vis
    if event == cv2.EVENT_LBUTTONDBLCLK:
        vis.on_grid_click(x, y)


def on_button_click(event, x, y, flags, param):
    global vis
    if event == cv2.EVENT_LBUTTONDBLCLK:
        vis.on_button_click(x, y)


def on_trackbar(val):
    global vis
    vis.on_trackbar(val)


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
    cv2.moveWindow(window_video, 1000, 0)

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
