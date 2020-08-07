import cv2
import time
import math

import numpy as np

from utils import *
from button import Button


class VIS:
    def __init__(self, dataset):
        self.dataset = dataset
        self.imgs_data = dataset['imgs_data']
        self.labels = dataset['labels']
        self.file_paths = dataset['file_paths']
        self.n_files = len(self.file_paths)

        self.block_size = 150
        self.nrows = 5
        self.margin = 3

        self.button = Button()
        self.__init_thumbnails()
        self.__init_grid(self.thumbnails, self.labels)
        self.__reset()

    def __init_thumbnails(self):
        self.thumbnails = np.array([get_thumbnail(img) \
            for img in self.dataset['imgs_data']])

    def __init_grid(self, imgs, labels, nrows=5, block_size=150, margin=3):
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
                img = cv2.putText(img, f'{i_block}|[{self.imgs_data[i_block].shape[0]}]:{label}', (0, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                # calc image position
                x = col * (block_size + margin)
                y = row * (block_size + margin)
                img_matrix[y:y+block_size, x:x+block_size] = img

        self.img_matrix = img_matrix
        self.grid = img_matrix

    def get_ui(self):
        if self.is_video_running:
            self.__update_video()
        return self.grid, self.full_video, self.button.get_ui()

    def on_button_click(self, x, y):
        if self.is_video_running:
            value = self.button.on_mouse(x, y)
            self.labels[self.video_index] = value

    def on_grid_click(self, x, y):
        x_i = x // (self.block_size + self.margin)  # col
        y_i = y // (self.block_size + self.margin)  # row
        n_i = y_i + x_i*self.nrows
        if n_i < self.n_files:
            print("SELECTING CASE ID:", n_i)
            self.__update(x_i, y_i, n_i)
        else:
            self.__reset()
            print("NONE")

    def __reset(self):
        self.button.reset()
        self.grid = self.img_matrix.copy()
        self.is_video_running = False
        self.full_video = np.zeros((512, 512, 3), dtype=np.uint8)
        cv2.putText(self.full_video, "HELLO!!!", (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 1)

    def __draw_rectangle(self, row, col):
        stride = self.block_size + self.margin
        x1, y1 = col*(stride), row*(stride)
        x2, y2 = x1+self.block_size, y1+self.block_size
        #print(x1, y1, x2, y2)
        self.grid = self.img_matrix.copy()
        cv2.rectangle(self.grid, (x1, y1), (x2, y2),
                      (0, 255, 0), thickness=self.margin)

    def __update(self, col, row, i_block):
        self.__draw_rectangle(row, col)
        self.__run_video(row, col, i_block)
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

        grid = self.grid.copy()
        frame = self.imgs_data[self.video_index][self.frame_index].copy()
        self.full_video = frame
        frame = self.__pre_process(frame)

        stride = self.block_size + self.margin
        x, y = self.video_col*stride, self.video_row*stride
        grid[y:y+self.block_size, x:x+self.block_size] = frame
        self.grid = grid


    def __pre_process(self, frame):
        frame = cv2.resize(frame, (self.block_size, self.block_size))
        label = self.labels[self.video_index]
        cv2.putText(frame, label, (0, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (0, 0, 255), 1)
        return frame


if __name__ == '__main__':
    print("HELLO")

    imgs = np.ones((10, 150, 150, 3), dtype=np.uint8)
    grid = init_grid(imgs)

    cv2.imshow('a', grid)
    cv2.waitKey(0)
