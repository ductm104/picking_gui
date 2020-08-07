import cv2
import argparse
import os
import glob
import pydicom
import math
import itertools
import numpy as np
import shutil
import json
from PIL import Image


def read_and_save_first_frame(input_dir, filter_dir):
	for path in glob.glob(os.path.join(input_dir, '**'), recursive=True):
		path = os.path.abspath(path)
		print(path)
		if os.path.isdir(path): continue
		try:
			dataset = pydicom.dcmread(path)
			nFrame = int(dataset[0x0028,0x0008].value) 

			if nFrame >= 10:
				first_frame = dataset.pixel_array[0]
			else:
				first_frame = dataset.pixel_array[9]

			study_id = str(dataset[0x0020,0x000D].value)

			first_frame_path = os.path.join(filter_dir, study_id, f"{os.path.basename(path)}.jpg")
			os.makedirs(os.path.dirname(first_frame_path), exist_ok=True)
			cv2.imwrite(first_frame_path, first_frame)
			with open(os.path.join(os.path.dirname(first_frame_path), 'study.txt'), "a+") as fp:
				print(str(path) + "|"  + str(os.path.basename(first_frame_path)), file=fp)
			print("OK")

		except Exception as e:
			print(path, e)
			continue

def get_frame_10_img(input_file=""):
	# print("GET FRAME 10 DICOM: {}".format(input_file))
	try:
		dataset = pydicom.dcmread(input_file)

		dicom_images = dataset.pixel_array

		# print("input_file: {} SHAPE: {}".format(input_file, dicom_images.shape))

		if len(dicom_images.shape) == 3 and dicom_images.shape[2] != 3: 
		# (case/media/tuan/Data1/DATA_RAW/BVE_SIUID/1.2.840.113663.1500.1.467297889.1.1.20200626.93641.290/IM_0167 SHAPE: (768, 1024, 3))
			dicom_images = np.repeat(dicom_images[..., None], 3, axis=-1)

		first_frame = dicom_images
		if len(first_frame.shape) == 2:
				first_frame = np.repeat(first_frame[..., None], 3, axis=-1)

		# print("first_frame.shape: ", first_frame.shape, dicom_images.shape)
		# exit(0)

		try:
			nFrame = int(dataset[0x0028,0x0008].value)

			first_frame = dicom_images[min(9, nFrame - 1)]
			if nFrame >= 10:
				first_frame = dicom_images[min(9, nFrame - 1)]
			# print("nFrame: {}".format(nFrame))
			return first_frame

		except Exception as e:

			return first_frame

		# return 
		# if nFrame >= 10:
		# 	first_frame = dataset.pixel_array[9]
		# return first_frame

	except Exception as e:
		# print(e)
		# exit(0)
		return None

study_marks = {}

def load_study_from_file(filter_dir234):
	global study_marks
	mark_path = os.path.join(filter_dir234, "mark.json")
	if os.path.isfile(mark_path):
		with open(mark_path, 'r') as json_file:
			study_marks = json.load(json_file)

def mark_study_done(filter_dir234, study_id, value_check=True):
	study_marks[study_id] = value_check

	print("CASE: {} mark: {}".format(study_id, value_check))

	with open(os.path.join(filter_dir234, "mark.json"), 'w') as json_file:
		json.dump(study_marks, json_file)



def pick(filter_dir, filter_dir234, filter_dir_frame_10, margin=2, n_col=12):
	def onDoubleClick(event, x, y, flags, param):
		if event == cv2.EVENT_LBUTTONDBLCLK:
			x_i, y_i, n_i = get_x_i_y_i(x, y)
			print(x, y, x_i, y_i, n_i)
			if n_i < len(image_map):
				choose_image(x_i, y_i, n_i)

	def get_x_i_y_i(x, y):
		x_i = x // (img_w+margin)
		y_i = y // (img_h+margin)
		n_i = x_i+y_i*n_col
		return x_i, y_i, n_i

	def choose_image(x_i, y_i, n_i):
		nonlocal choose_n
		choose_n = n_i
		# print(f"choose_image {choose_n}")
		output = get_img_choice()
		x1, y1 = x_i*(img_w+margin)-margin//2, y_i*(img_h+margin)-margin//2
		x2, y2 = x1+(img_w+margin), y1+(img_h+margin)
		cv2.rectangle(output, (x1, y1), (x2, y2), (0,255,0), thickness=margin)
		cv2.imshow("matrix", output)

	def get_img_choice():
		img_choice = imgmatrix.copy()
		# print("choose_n: {}".format(choose_n))
		for n_i in range(len(image_map)):
			x_i = n_i % n_col
			y_i = n_i // n_col
			x1, y1 = x_i*(img_w+margin)+margin, y_i*(img_h+margin)+30
			if choose_chamber[n_i] > 0:
				cv2.putText(img_choice, f"{choose_chamber[n_i]}C", (x1,y1), cv2.FONT_HERSHEY_COMPLEX, 1, (0,255,255),thickness=3)

		if choose_n >= 0 and choose_n < len(image_map):
			x_i = choose_n % n_col
			y_i = choose_n // n_col
			x1, y1 = x_i*(img_w+margin)-margin//2, y_i*(img_h+margin)-margin//2
			x2, y2 = x1+(img_w+margin), y1+(img_h+margin)
			cv2.rectangle(img_choice, (x1, y1), (x2, y2), (0,255,0), thickness=margin)

		return img_choice

	load_study_from_file(filter_dir234)
	img_w, img_h = 150, 150
	number_accepted = 0
	
	study_id_history = []

	id_cnt =  len(study_marks)

	undo = False

	while True:
		id_cnt += 1
		# if (id_cnt % 100 == 0 or id_cnt > 1390):
		print("\n")
		print("process to #case: {}".format(id_cnt))
	
		# folder = pick_a_study_id(filter_dir)

		if undo == True:
			if len(study_id_history) > 0:
				# print("Before: {}".format(study_id_history))
				folder = study_id_history[-1]

				study_id_history = study_id_history[:-1]

				
				# print("After: {}".format(study_id_history))
				# print(study_marks)
				study_id = os.path.basename(folder)

				# print(study_marks[folder])
				if study_id in study_marks: 
					print("Undo folder: {} with label: {}".format(folder, study_marks[study_id]))
					del study_marks[study_id]


			else:
				folder = pick_a_folder(filter_dir)
			undo = False

		else:
			folder = pick_a_folder(filter_dir)
		
		if folder is None:
			exit(0)

		# folder = "/media/tuan/Data1/DATA_RAW/BVHNVX_SIUID/1.2.840.113619.2.394.3093.1586774779.4.1"
		study_id = os.path.basename(folder)

		print("Pick folder: {}".format(folder))
		
		# study_id_history.append(folder)


		image_map, choose_chamber = [], []
		
		choose_n = -1

		fn_frame_10_png = os.path.join(filter_dir_frame_10, study_id + ".jpeg")
		if os.path.isfile(fn_frame_10_png):

			print("FOUND FILE HERE: {}".format(fn_frame_10_png))

			imgmatrix = cv2.imread(fn_frame_10_png)
			
			# continue



		else:
		
			image_map, choose_chamber = get_dicom_map(folder, img_w, img_h)

			
			# choose_chamber = [0]*len(image_map)
			# print("choose_chamber: {}".format(choose_chamber))

			if len(image_map) == 0:
				print("LEN IMAGE_MAP : {} = 0".format(study_id))
				mark_study_done(filter_dir234, study_id, "no image found")
				continue
			if len(image_map) > 72:
				print("LEN IMAGE_MAP LARGE : {}".format(study_id))
				mark_study_done(filter_dir234, study_id, "#image so large")
				continue

			imgmatrix = make_grid([ x[1] for x in image_map], margin=margin, w=n_col)
			
			# print("DONE LOAD IMAGEMATRIX: {}".format(study_id))
			
			im = Image.fromarray(imgmatrix).save(fn_frame_10_png)

			print("DONE SAVE FILE IMG: {}".format(fn_frame_10_png))
			# exit(0)

			continue


		# pass

		cv2.destroyAllWindows()

		cv2.namedWindow(study_id)
		cv2.setMouseCallback(study_id, onDoubleClick)


		cv2.imshow(study_id, get_img_choice())

		
		

		while True:
			key = cv2.waitKey(1) & 0xFF

			# if key == ord('2'):
			# 	print(f"{choose_n} 2C")
			# 	if choose_n >= 0 and choose_n < len(image_map): choose_chamber[choose_n] = 2
			# 	cv2.imshow("matrix", get_img_choice())
			# elif key == ord('3'):
			# 	print(f"{choose_n} 3C")
			# 	if choose_n >= 0 and choose_n < len(image_map): choose_chamber[choose_n] = 3
			# 	cv2.imshow("matrix", get_img_choice())
			# elif key == ord('4'):
			# 	print(f"{choose_n} 4C")
			# 	if choose_n >= 0 and choose_n < len(image_map): choose_chamber[choose_n] = 4
			# 	cv2.imshow("matrix", get_img_choice())
			# elif key == ord('0') or key == 27:
			# 	print(f"{choose_n} 0C")
			# 	if choose_n >= 0 and choose_n < len(image_map): choose_chamber[choose_n] = 0
			# 	cv2.imshow("matrix", get_img_choice())

			if key == ord('q'):
				exit(0)
			
			elif key == ord('n'):
				print("SKIP FOLDER: {}".format(study_id))
				mark_study_done(filter_dir234, study_id, "skip")
				break
			
			elif key == ord('b'):
				mark_study_done(filter_dir234, study_id, "bad")
				study_id_history.append(folder)
				break

			elif key == ord('o'):
				mark_study_done(filter_dir234, study_id, "other")
				study_id_history.append(folder)
				break

			elif key == ord('k'):
				mark_study_done(filter_dir234, study_id, "kc")
				study_id_history.append(folder)
				break

			elif key == ord('v'):
				mark_study_done(filter_dir234, study_id, "vinif")
				study_id_history.append(folder)
				break
			elif key == ord('u'):
				# undo
				# print("before len: {}".format(len(study_id_history)))
				# if len(study_id_history) > 0:
				# 	study_id_history = study_id_history[:-1]
				# print("after len: {}".format(len(study_id_history)))
				id_cnt -= 1
				undo = True
				break




			# elif key == 13:
			# 	print("Accept", study_id)
			# 	mark_study_done(filter_dir234, study_id)


				# for choice, item in zip(choose_chamber, image_map):
				# 	if choice > 0:
				# 		print(choice, item[0], item[1])
				# 		dst_folder = os.path.join(filter_dir234, study_id)
				# 		os.makedirs(dst_folder, exist_ok=True)
				# 		shutil.copy(item[1], os.path.join(dst_folder, f"{os.path.basename(item[1])}-{choice}C"))
				# print("Done")
				# number_accepted += 1

				# print("number_accepted: {}\n".format(number_accepted))
				# break
			


			else:
				pass
		

def make_grid(imgs, margin=2, w = 5):
	img_h, img_w, img_c = imgs[0].shape

	m_x = int(margin)
	m_y = m_x
	h = math.ceil(len(imgs) / w)
	n = w*h

	imgmatrix = np.zeros((img_h * h + m_y * (h - 1),
						  img_w * w + m_x * (w - 1),
						  img_c),
						 np.uint8)

	imgmatrix.fill(255)    

	for x_i in range(w):
		for y_i in range(h):
			if y_i*w+x_i >= len(imgs): continue
			img = imgs[y_i*w+x_i]
			
			if len(img.shape) == 2:
				img = np.repeat(img[..., None], 3, axis=-1)	
			# print(y_i*w+x_i, img.shape, type(img))
			x = x_i * (img_w + m_x)
			y = y_i * (img_h + m_y)
			imgmatrix[y:y+img_h, x:x+img_w, :] = img

	return imgmatrix

def pick_a_folder(filter_dir):
	# return "/media/tuan/DATA/AI-Cardio/filter_data_234c/data/1.2.840.113619.2.239.94.1243243046.0.2"
	# 1.2.840.113619.2.185.355.1301540583.0.2 file to large
	# 1.2.840.113663.1500.1.467297889.1.1.20191014.104613.551 read file study.txt
	# 1.2.840.113619.2.239.94.1243243046.0.2
	# 1.2.840.113663.1500.1.420121243.1.1.20181003.151301.703
	
	for folder in glob.glob(os.path.join(filter_dir, "*")):
		if os.path.isdir(folder):
			study_id = os.path.basename(folder)
			if study_id not in study_marks:
				return os.path.abspath(folder)
	# return "/media/tuan/DATA/AI-Cardio/filter_data_234c/data/1.2.840.113663.1500.1.467297889.1.1.20191014.104613.551"

study_img_marks = {}
def pick_a_study_id(filter_dir):
	# return "/media/tuan/DATA/AI-Cardio/filter_data_234c/data/1.2.840.113619.2.239.94.1243243046.0.2"
	# 1.2.840.113619.2.185.355.1301540583.0.2 file to large
	# 1.2.840.113663.1500.1.467297889.1.1.20191014.104613.551 read file study.txt
	# 1.2.840.113619.2.239.94.1243243046.0.2
	# 1.2.840.113663.1500.1.420121243.1.1.20181003.151301.703
	# data = glob.glob(os.path.join(filter_dir, "*"))
	# print(len(data))
	# exit(0)
	for folder in glob.glob(os.path.join(filter_dir, "*")):
		if os.path.isdir(folder):
			study_id = os.path.basename(folder)
			if study_id not in study_img_marks:
				# print("study_id: {}".format(study_id))
				study_img_marks[study_id] = "DONE"
				return os.path.abspath(folder)
	return None

	# return "/media/tuan/DATA/AI-Cardio/filter_data_234c/data/1.2.840.113663.1500.1.467297889.1.1.20191014.104613.551"

def get_list_img(pre_select_folder="/media/tuan/DATA/AI-Cardio/filter_data_234c/dicom234"):
	dicoms = os.listdir(pre_select_folder)
	
	list_images = []

	for di in dicoms:
		# di = os.path.abspath(di)
		fn = os.path.join(pre_select_folder, di)
		# print("fn: {}".format(fn))
		if os.path.isfile(fn):
			frame_10 = get_frame_10_img(fn)

			if frame_10 is not None:
				list_images.append([frame_10, fn])

	return list_images

def get_dicom_map(pre_select_folder="/media/tuan/DATA/AI-Cardio/filter_data_234c/dicom234", img_w=150, img_h=150):
	# folder: from tuan_select data
	# get chamber from folder )
	# dicoms = os.listdir(pre_select_folder)

	# # print("get_dicom_map: {}".format(dicoms))
	# nChambers = {}

	# for di in dicoms:
	# 	# di = os.path.abspath(di)
	# 	if os.path.isfile(os.path.join(pre_select_folder, di)):
			
	# 		nChambers[str(di[:-3])] = int(di[-2])
	# 		print("TUAN FOLDER: ", di[:-3], di[-2], nChambers[str(di[:-3]) ])

			
	# # check data image from folder: data_folder = folder.replace("dicom234", "data")
	# folder = pre_select_folder.replace("dicom234", "data")

	# with open(os.path.join(folder, 'study.txt'), 'r') as f:
	# 	lines = f.readlines()

	# lines = [line[:-1] for line in lines]
	# image_map = []
	# chambers = []

	# for line in lines:
	# 	# print("ori line: {}".format(line))
	# 	# p = line.rindex("/")
	# 	line = line.split("|")

	# 	image_map.append([line[1], line[0]])

	# 	# print("str_right: {} space_count: {}".format(str_right, space_count))
	# # print("lines: {}".format(lines))
	# # tokens = [x.strip().split(' ') for x in lines]
	# # print("tokens: {}".format(tokens))
	# # image_map = [(x[1], x[0]) for x in tokens if len(x) == 2]
	# image_maps = []
	# list_images = {}

	# # print("image_map: {}".format(image_map))
	# for x in image_map:
	# 	if x[0] in list_images:
	# 		continue
	# 	list_images[x[0]] = True

	# 	img = cv2.imread(os.path.join(folder, x[0]))

	list_images = get_list_img(pre_select_folder)
	# print(len(list_images))
	
	image_maps = []
	chambers = []
	for (img, path) in list_images:

		# print
		# print(img.shape, path)
		if len(img.shape) == 3:
			h, w, c = img.shape
		else:
			h, w = img.shape
		# print(h, w, c)
		if h > 100 and w > 100:
			image_maps.append( (path, cv2.resize(img, (img_w, img_h) ) ) )
			# print(x[0], img.shape)
			# l1 = x[0]
			# l1 = l1[:-4]
			# # print("l1 in line: {}".format(l1))
			# if l1 in nChambers:
			# 	chambers.append(nChambers[l1])
			# else:

			chambers.append(0)


	image_map = image_maps
	# print("LEN IMAGE: {}".format(len(image_map)))
	# image_map = [(x[0], x[1], cv2.resize(cv2.imread(os.path.join(folder, x[0])), (img_w, img_h))) for x in image_map]
	return image_map, chambers

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	# parser.add_argument('--input_dir', type=str, default='/media/tuan/DATA/AI-Cardio/NEW_DATA_HITACHI_4T_2020_02_22')
	parser.add_argument('--filter_dir', type=str, default='/media/tuan/Data1/DATA_RAW/BVE_SIUID')
	parser.add_argument('--filter_dir234', type=str, default='/media/tuan/Data1/DATA_RAW/BVE_VERIFIED/FILTER')
	parser.add_argument('--filter_dir_frame_10', type=str, default='/media/tuan/Data1/DATA_RAW/BVE_VERIFIED/BVE_SIUID_FRAME_10_IMG')

	# # parser.add_argument('--job', type=str, default='read_and_save')
	args = parser.parse_args()

	# print(args)

	# # if args.job == 'read_and_save':
	# #     read_and_save_first_frame(args.input_dir, args.filter_dir)
	# # elif args.job == 'pick':
	pick(args.filter_dir, args.filter_dir234, args.filter_dir_frame_10)

	# get_dicom_map("/media/tuan/Data1/DATA_RAW/BVHNVX_SIUID/1.2.410.200010.1051923.6409.304447.2918990.2918990")
