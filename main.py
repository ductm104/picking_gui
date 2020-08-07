import os
import glob
import argparse
import numpy
import cv2


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=str,
        help="path to dicom folder")
    #parser.add_argument("json", type=str,
        #help="path to json file")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    print(args.folder)

    print(glob.glob(os.path.join(args.folder, '*')))
