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


counter = Value('i', 0)


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


def read_json(json_path):
    try:
        with open(json_path, 'r') as file:
            label = json.load(file)
    except:
        raise error("JSON not found!")

    return label


def read_dicom(file_path):
    try:
        dataset = pydicom.dcmread(file_path)
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


def read_cases_from_json(json_path="/media/tuan/Data1/DATA_RAW/BVHNVX_VERIFIED/FILTER/mark.json"):
    try:
        with open(json_path, 'r') as fr:
            data = json.load(fr)
    except:
        data = {}
    return data


def read_folder(folder_path, json_path, num_thread=8):
    folder_path = os.path.abspath(folder_path)
    file_paths = glob.glob(os.path.join(folder_path, '*'))
    print(f'READING {len(file_paths)} FILES FROM "{folder_path}"')

    global counter
    counter = Value('i', 0)
    with ThreadPoolExecutor(num_thread) as pool:
        data = list(pool.map(read_dicom, file_paths))

    label_data = read_json(json_path)

    file_paths, imgs_data, labels = [], [], []
    file_paths_none, imgs_data_none, labels_none = [], [], []
    count = 0
    for item in data:
        if item[0] is not None:
            try:
                label_ = label_data[item[0]]
            except:
                count += 1
                label_ = 'NO_LABEL'

            if label_.upper() == 'NONE':
                file_paths_none.append(item[0])
                imgs_data_none.append(item[1])
                labels_none.append(label_)
            elif label_.upper() == 'NO_LABEL':
                file_paths.insert(0, item[0])
                imgs_data.insert(0, item[1])
                labels.insert(0, label_)
            else:
                file_paths.append(item[0])
                imgs_data.append(item[1])
                labels.append(label_)

    file_paths = file_paths + file_paths_none
    imgs_data = imgs_data + imgs_data_none
    labels = labels + labels_none
    print("NUM DICOMs: ", len(file_paths))
    print(f"NO_LABEL: {count} files")

    return {'file_paths': file_paths,
            'imgs_data': imgs_data,
            'labels': labels}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=str,
        help="path to dicom folder")
    parser.add_argument("--json", type=str,
        help="path to dicom folder")
    parser.add_argument("--checklist", type=str,
        help="path to dicom folder")
    args = parser.parse_args()
    return args


def on_grid_click(event, x, y, flags, param):
    global vis
    if event == cv2.EVENT_LBUTTONDOWN:
        vis.on_grid_click(x, y)


def on_button_click(event, x, y, flags, param):
    global vis
    if event == cv2.EVENT_LBUTTONDOWN:
        vis.on_button_click(x, y)


def on_trackbar(val):
    global vis
    vis.on_trackbar(val)


def pick_a_folder(root, checklist_path):
    paths = glob.glob(os.path.join(root, "*"))
    paths = [os.path.abspath(path) for path in paths if os.path.isdir(path)]
    data = read_cases_from_json()
    old_data = data
    tmp = []
    for path in paths:
        value = path.split('/')[-1]
        try:
            oke = data[value] in ['vinif', 'kc']
            if oke:
                tmp.append(path)
        except:
            pass
    paths = tmp

    try:
        with open(checklist_path, 'r') as f:
            data = json.load(f)
            check_list = data.keys()
    except:
        check_list = []

    for path in paths:
        if path not in check_list:
            value = path.split('/')[-1]
            print('*'*20, old_data[value].upper())
            return path

    return None


def save_check_list(checklist_path, folder, key):
    values = {'n': 'normal', 'y': 'yes', 'b': 'LBBB', 'o': 'ag', 'l': 'later', 'x': 'DONE', 'p': 'postsystolic'}

    try:
        with open(checklist_path, 'r') as f:
            data = json.load(f)
    except:
        data = {}

    data[folder] = values[chr(key)]

    with open(checklist_path, 'w') as f:
        json.dump(data, f)

    print(f"MARK {folder} AS {values[chr(key)]}\n")


def get_json_path(folder_path, json_root):
    # check if local-json exits otherwise use global-json
    json_path = os.path.join(folder_path, os.path.basename(folder_path) + '.json')
    if not os.path.isfile(json_path):
        print(f'CAN NOT FIND JSON FROM {folder_path}, READ GLOBAL FROM {json_root}')
        return json_root, json_path
    else:
        print(f'READ LOCAL JSON FROM {json_path}')
        return json_path, json_path


if __name__ == '__main__':
    args = parse_args()

    while True:
        print('\n\n')
        folder = pick_a_folder(args.root, args.checklist)
        if folder is None:
            print("DONE")
            exit(0)

        # check if local-json exits otherwise use global-json
        json_path = os.path.join(folder, os.path.basename(folder) + '.json')
        if not os.path.isfile(json_path):
            if not os.path.isfile(args.json):
                print(f'CAN NOT FIND JSON from {args.json}')
            else:
                json_data = args.json
                print(f'CAN NOT FIND JSON FOR {folder}, READ FROM {json_data}')
        else:
            json_data = json_path

        # init visualizer
        dataset = read_folder(folder, json_data)
        vis = VIS(dataset, json_path, args.json)
        counter = Value('i', 0)

        # init cv2 window and functions
        window_grid = os.path.basename(folder)
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

        list_keys = [ord(k) for k in ['n', 'l', 'y', 'o', 'b', 'x', 'p']]
        while True:
            grid, full_video, img_button = vis.get_ui()

            cv2.imshow(window_grid, grid)
            cv2.imshow(window_video, full_video)
            cv2.imshow(window_button, img_button)

            key = cv2.waitKey(30)
            if key == ord("q"):
                cv2.destroyAllWindows()
                exit(0)
            elif key in list_keys:
                save_check_list(args.checklist, folder, key)
            elif key == ord('u'):
                cv2.destroyAllWindows()
                break
