import os
import glob
import argparse
import numpy as np
import cv2
import json

from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Value

from visualizer import *
from utils import *


list_keys = [ord(k) for k in ['n', 'l', 'y', 'o', 'b', 'p']]
key_maps = {'n': 'normal', 'y': 'yes', 'b': 'LBBB', 'o': 'ag', 'l': 'later', 'p': 'postsystolic'}


def save_check_list(checklist_path, folder, key):
    try:
        with open(checklist_path, 'r') as f:
            data = json.load(f)
    except:
        data = {}

    data[folder] = key_maps[chr(key)]
    with open(checklist_path, 'w') as f:
        json.dump(data, f)

    print(f"MARK {folder} AS {key_maps[chr(key)]}\n")


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


def check_case(path, case_data):
    ok_list = ['vinif', 'kc']
    return True, 'kc' # TODO delete this line
    try:
        folder_name = path.split('/')[-1]
        oke = case_data[folder_name] in ok_list
        if oke:
            return True, case_data[folder_name]
        else:
            return False, None
    except:
        return False, None


def read_check_list(json_path):
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            return data
    except:
        return {}


def get_list_folder(root, checklist_path):
    folder_paths = glob.glob(os.path.join(root, '*'))
    folder_paths = [os.path.abspath(path) for path in folder_paths \
                        if os.path.isdir(path)]

    case_data = read_cases_from_json()
    checklist_data = read_check_list(checklist_path)

    folder_list = []
    for path in folder_paths:
        ok, case_value = check_case(path, case_data)
        if ok:
            try:
                label = checklist_data[path]
                folder_list.append((path, case_value, label))
            except:
                folder_list.insert(0, (path, case_value, ''))

    return np.array(folder_list)


def check_global_json(json_path, name=''):
    if os.path.isfile(json_path):
        print(f"FOUND {name} JSON FROM {json_path}")
    else:
        print(f"CAN NOT FIND {name} JSON FROM {json_path}")
        print(f"CREATE NEW EMPTY {name} JSON\n")
        with open(json_path, 'w') as f:
            json.dump({}, f)


if __name__ == '__main__':
    args = parse_args()

    check_global_json(args.json, 'GLOBAL')
    check_global_json(args.checklist, 'CHECK_LIST')

    folder_list = get_list_folder(args.root, args.checklist)
    print(f"TOTAL: {len(folder_list)} folders")
    if len(folder_list) == 0: exit(0)

    folder_idx = -1
    while True:
        #os.system('clear')

        folder_idx = (folder_idx + 1) % len(folder_list)
        folder_path, case_value, folder_label = folder_list[folder_idx]

        print('*'*20, case_value, '*'*20)

        vis = VIS(folder_path, args.json, folder_label)

        # init cv2 window and functions
        window_grid = os.path.basename(folder_path)
        window_video = "full_video"
        window_button = "button"

        # init button
        cv2.namedWindow(window_button, cv2.WINDOW_AUTOSIZE)
        cv2.moveWindow(window_button, 0, 0)

        # init grid
        cv2.namedWindow(window_grid, cv2.WINDOW_AUTOSIZE)
        cv2.resizeWindow(window_grid, vis.win_width, vis.win_height)
        cv2.moveWindow(window_grid, 400, 0)
        cv2.createTrackbar('Scroll bar', window_grid, 0, 100, on_trackbar) 
        # init full video
        cv2.namedWindow(window_video)
        cv2.moveWindow(window_video, 1100, 0)

        cv2.setMouseCallback(window_grid, on_grid_click)
        cv2.setMouseCallback(window_button, on_button_click)


        while True:
            grid, full_video, img_button = vis.get_ui()

            cv2.imshow(window_button, img_button)
            cv2.imshow(window_grid, grid)
            cv2.imshow(window_video, full_video)

            key = cv2.waitKey(60)
            if key == ord("q"):
                cv2.destroyAllWindows()
                exit(0)
            elif key in list_keys:
                folder_list[folder_idx][2] = key_maps[chr(key)]
                vis.update_label(key_maps[chr(key)])
                save_check_list(args.checklist, folder_path, key)
            elif key == ord('u'):
                # undo
                folder_idx -= 1
                cv2.destroyAllWindows()
                break
            elif key == ord('x'):
                # done, go next
                cv2.destroyAllWindows()
                break
