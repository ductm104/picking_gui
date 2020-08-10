import os
import re
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


def save_check_list(checklist_path, dr_name, folder, key, remove_last=False):
    try:
        with open(checklist_path, 'r') as f:
            data = json.load(f)
    except:
        data = {}
    try:
        folder_label_list = data[folder]
        if remove_last:
            folder_label_list.pop()
    except:
        folder_label_list = []

    folder_label_list.append([dr_name, key_maps[chr(key)]])
    data[folder] = folder_label_list
    with open(checklist_path, 'w') as f:
        json.dump(data, f)

    print(f"MARK {folder} AS {key_maps[chr(key)]}\n")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=str,
        help="path to dicom folder")
    parser.add_argument("--json_chamber", type=str,
        help="path to json chamber")
    parser.add_argument("--checklist", type=str,
        help="path to check list")
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
    return True, 'kc' # TODO del this line
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
                folder_list.insert(0, (path, case_value, []))

    return np.array(folder_list)


def check_global_json(json_path, name=''):
    if os.path.isfile(json_path):
        print(f"FOUND {name} JSON FROM {json_path}")
        os.system(f'cp {json_path} {json_path}.swp')
    else:
        print(f"CAN NOT FIND {name} JSON FROM {json_path}")
        print(f"CREATE NEW EMPTY {name} JSON\n")
        with open(json_path, 'w') as f:
            json.dump({}, f)


def get_dr_name():
    os.system("clear")
    print("*"*40)
    print("INPUT DOCTOR's NAME")
    while True:
        name = input()
        if re.match("^[a-zA-Z]*$", name):
            break
        else:
            print("Doctor's name must contain only '[a-z][A-Z]'")
    print("*"*40)

    return name


if __name__ == '__main__':
    dr_name = get_dr_name()
    args = parse_args()

    check_global_json(args.json_chamber, 'GLOBAL')
    check_global_json(args.checklist, 'CHECK_LIST')

    folder_list = get_list_folder(args.root, args.checklist)
    print(f"TOTAL: {len(folder_list)} folders")
    if len(folder_list) == 0: exit(0)

    folder_idx = -1
    track_list = {}
    for i in range(len(folder_list)):
        track_list[i] = False
    while True:
        folder_idx = (folder_idx + 1) % len(folder_list)
        folder_path, case_value, folder_label_list_tmp = folder_list[folder_idx]

        print('*'*20, case_value, '*'*20)

        cur_label = None
        folder_label_list = folder_label_list_tmp.copy()
        if track_list[folder_idx]:
            cur_label = folder_label_list.pop()[1]

        vis = VIS(dr_name, folder_path, args.json_chamber, folder_label_list, cur_label)

        # init cv2 window and functions
        window_grid = os.path.basename(folder_path)
        window_video = f"CASE-[{case_value.upper()}]-[{folder_idx+1}]/[{len(folder_list)}]"
        window_button = "button"

        # init button
        cv2.namedWindow(window_button, cv2.WINDOW_AUTOSIZE)
        cv2.moveWindow(window_button, 0, 0)

        # init grid
        cv2.namedWindow(window_grid, cv2.WINDOW_AUTOSIZE)
        cv2.resizeWindow(window_grid, vis.win_width, vis.win_height)
        cv2.moveWindow(window_grid, 400, 0)
        cv2.createTrackbar('Scroll bar', window_grid, 0, 100, on_trackbar) # init full video
        cv2.namedWindow(window_video)
        cv2.moveWindow(window_video, 1100, 0)

        cv2.setMouseCallback(window_grid, on_grid_click)
        cv2.setMouseCallback(window_button, on_button_click)

        while True:
            grid, full_video, img_button = vis.get_ui()

            cv2.imshow(window_button, img_button)
            cv2.imshow(window_grid, grid)
            cv2.imshow(window_video, full_video)

            key = cv2.waitKey(30)
            if key == ord("q"):
                cv2.destroyAllWindows()
                exit(0)
            elif key in list_keys:
                vis.update_label(key_maps[chr(key)])
                save_check_list(args.checklist, dr_name, folder_path,
                                key, track_list[folder_idx])
                folder_list[folder_idx][2] = read_check_list(args.checklist)[folder_path]
                track_list[folder_idx] = True
            elif key == ord('u'):
                # undo
                folder_idx -= 2
                cv2.destroyAllWindows()
                break
            elif key == ord('x'):
                # done, go next
                cv2.destroyAllWindows()
                break
