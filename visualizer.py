import cv2
import json
import time
import math

import numpy as np

from utils import *
from button import Button


class VIS:
    def __init__(self, dr_name, folder_path, json_root, folder_label_list, cur_label=None):
        self.folder_label_list = folder_label_list
        self.folder_label = None
        self.dr_name = dr_name

        json_data, json_local_path = get_json_path(folder_path, json_root)
        self.dataset = read_folder(folder_path, json_data)

        self.imgs_data = self.dataset['imgs_data']
        self.labels = self.dataset['labels']
        self.file_paths = self.dataset['file_paths']

        self.n_files = len(self.file_paths)
        self.json_root = json_root
        self.json_path = json_local_path
        self.offset = 0

        self.block_size = 150
        self.ncols = 4
        self.nrows = 5
        self.margin = 3
        self.win_height = self.nrows * (self.block_size+self.margin)
        self.max_width = self.ncols * (self.block_size+self.margin)

        self.button = Button()
        self.__init_thumbnails()
        self.__init_grid()
        self.__reset()

        if cur_label is not None:
            self.update_label(cur_label)

    def __update_json_local(self):
        try:
            with open(self.json_path, 'r') as f:
                data = json.load(f)
        except:
            data = {}

        for path, label in zip(self.file_paths, self.labels):
            data[path] = label

        with open(self.json_path, 'w') as f:
            json.dump(data, f)

        self.__update_json_root()

    def __update_json_root(self):
        try:
            with open(self.json_root, 'r') as f:
                data = json.load(f)
        except:
            data = {}

        for path, label in zip(self.file_paths, self.labels):
            data[path] = label

        with open(self.json_root, 'w') as f:
            json.dump(data, f)
        #print('JSON ROOT UPDATED')

    def __get_thumbnail(self, images):
        if images.shape[0] > 10:
            return images[10, ...]
        return images[-1, ...]

    def __init_thumbnails(self):
        self.thumbnails = np.array([self.__get_thumbnail(img) \
            for img in self.dataset['imgs_data']])

    def __init_grid(self):
        nrows, block_size, margin = self.nrows, self.block_size, self.margin
        imgs, labels = self.thumbnails, self.labels

        ncols = math.ceil(len(imgs) / nrows)
        n_blocks = ncols * nrows

        img_matrix = np.ones((block_size*nrows + margin*(nrows-1),
                             block_size*ncols + margin*(ncols-1),
                             3), np.uint8) * 255

        n_imgs = imgs.shape[0]
        for col in range(ncols):
            for row in range(nrows):
                i_block = col * nrows + row #row*ncols + col
                if i_block >= n_imgs:
                    continue

                # get image at index i
                img = imgs[i_block]
                label = labels[i_block]
                img = cv2.resize(img, (block_size, block_size))
                img = cv2.putText(img, f'{self.imgs_data[i_block].shape[0]}-{label}', (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (37, 200, 37), 2)

                # calc image position
                x = col * (block_size + margin)
                y = row * (block_size + margin)
                img_matrix[y:y+block_size, x:x+block_size] = img

        self.img_matrix = img_matrix
        self.grid = img_matrix.copy()
        self.win_width = img_matrix.shape[1]

    def on_trackbar(self, val):
        self.offset = min(int(val/100*self.win_width), self.win_width-self.max_width)
        self.offset = max(self.offset, 0)

    def get_ui(self):
        if self.is_video_running:
            self.__update_video()

        grid = self.grid[:, self.offset:self.offset+self.max_width]
        return grid, self.full_video, self.button.get_ui()

    def on_button_click(self, x, y):
        if self.is_video_running:
            value = self.button.on_mouse(x, y)
            self.labels[self.video_index] = value
            self.__init_grid()
            self.__update_json_local()

    def on_grid_click(self, x, y):
        x_i = (self.offset+x) // (self.block_size + self.margin)  # col
        y_i = y // (self.block_size + self.margin)  # row
        n_i = y_i + x_i*self.nrows
        if n_i < self.n_files:
            print("SELECTING CASE ID:", n_i)
            self.__update(x_i, y_i, n_i)
        else:
            self.__reset()
            print("SELECT NONE")

    def update_label(self, label):
        self.folder_label = label
        self.full_video = self.full_video_tmp.copy()
        self.__pre_process_frame(self.full_video)
        #cv2.putText(self.full_video, self.folder_label,
                    #(200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    #(0, 0, 200), 3)
        print('FOLDER DIAGNOSIS:', self.folder_label)

    def __reset(self):
        self.button.reset()
        self.grid = self.img_matrix.copy()
        self.is_video_running = False
        self.full_video_tmp = np.zeros((720, 512, 3), dtype=np.uint8)
        self.__pre_process_frame(self.full_video_tmp)
        self.full_video = self.full_video_tmp.copy()
        #cv2.putText(self.full_video, self.folder_label, (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 1)

    def __draw_rectangle(self, row, col):
        stride = self.block_size + self.margin
        x1, y1 = col*(stride), row*(stride)
        x2, y2 = x1+self.block_size, y1+self.block_size
        #print(x1, y1, x2, y2)
        self.grid = self.img_matrix.copy()
        cv2.rectangle(self.grid, (x1, y1), (x2, y2),
                      (0, 255, 0), thickness=self.margin)

    def __update(self, col, row, i_block):
        self.__run_video(row, col, i_block)
        self.__draw_rectangle(row, col)
        self.button.on_change(self.labels[i_block])

    def __run_video(self, row, col, i_block):
        # run whole video
        self.is_video_running = True
        self.video_index = i_block
        self.frame_index = -1
        self.video_row = row
        self.video_col = col

        self.__update_video()

    def __update_video(self):
        self.frame_index += 1
        if self.frame_index >= self.imgs_data[self.video_index].shape[0]:
            self.frame_index = 0

        frame = self.imgs_data[self.video_index][self.frame_index]
        self.full_video_tmp = frame.copy()
        self.full_video = self.__pre_process_frame(frame.copy())
        frame = self.__pre_process(frame.copy())

        stride = self.block_size + self.margin
        x, y = self.video_col*stride, self.video_row*stride
        self.grid[y:y+self.block_size, x:x+self.block_size] = frame

    def __pre_process_frame(self, full_frame):
        for i in range(len(self.folder_label_list)):
            label = ': '.join(self.folder_label_list[i])
            cv2.putText(full_frame, label, (30, 100+i*50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 200), 3)

        if self.folder_label:
            label = self.dr_name + ': ' + self.folder_label
            cv2.putText(full_frame, label, (30, 100+len(self.folder_label_list)*50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 200), 3)
        return full_frame

    def __pre_process(self, frame):
        frame = cv2.resize(frame, (self.block_size, self.block_size))
        label = self.labels[self.video_index]
        cv2.putText(frame, label, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (0, 0, 200), 2)
        return frame


if __name__ == '__main__':
    print("HELLO")

    imgs = np.ones((10, 150, 150, 3), dtype=np.uint8)
    grid = init_grid(imgs)

    cv2.imshow('a', grid)
    cv2.waitKey(0)
