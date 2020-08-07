import glob
import os
import random
import json


list_files = {}

FOLDERS = [
	"/media/tuan/Data1/DATA_RAW/BVE_SIUID",
	"/media/tuan/Data1/DATA_RAW/BVHNVX_SIUID",
	"/media/tuan/Data1/GERMAN_DATA_NMCT/GERMAN_SIUID"
]

def get_list_cases(input_dir="/media/tuan/Data1/DATA_FOR_DUCTM/data"):
	folders = [os.path.join(input_dir, f) for f in os.listdir(input_dir)]
	return folders

LABERS = ["2C", "3C", "4C", "PTS_S", "PTS_L", "None"]

def gen_json_chamber(input_dir):

	global list_files
	files = []
	chambers = {}

	for path in glob.glob(os.path.join(input_dir, '**'), recursive=True):
		path = os.path.abspath(path)
		# print(path)
		if os.path.isdir(path) or ".json" in path or ".txt" in path: continue

		files.append(path)
		chambers[path] = LABERS[random.randint(0, len(LABERS) - 1)]


	bn = os.path.basename(input_dir)
	file_json = os.path.join(input_dir, bn + ".json")
	with open(file_json, 'w') as fw:
		json.dump(chambers, fw)

	# print(len(files))


cases = get_list_cases()

print(cases)
for idx, case in enumerate(cases):
	print("PROCESS TO #{} case: {}".format(idx, case))
	gen_json_chamber(case)

# gen_json_chamber(input_dir="/media/tuan/Data1/DATA_FOR_DUCTM/data")



	# 	try:
	# 		dataset = pydicom.dcmread(path)
	# 		# first_frame = dataset.pixel_array[0]
	# 		study_id = str(dataset[0x0020,0x000D].value)

	# 		dicom_des_path = os.path.join(filter_dir, study_id, f"{os.path.basename(path)}")            
	# 		# study_id_json[study_id] = input_dir

	# 		if study_id not in study_id_json:
	# 			study_id_json[study_id] = [path]
	# 		else:
	# 			study_id_json[study_id].append(path)

	# 		os.makedirs(os.path.dirname(dicom_des_path), exist_ok=True)
	# 		shutil.copy(path, dicom_des_path)
	# 		# print("DONE COPY: {}".format(dicom_des_path))
	# 		# cv2.imwrite(first_frame_path, first_frame)
	# 		with open(os.path.join(os.path.dirname(dicom_des_path), 'study.txt'), "a+") as fp:
	# 			print(str(path) + "|" + str(os.path.basename(dicom_des_path)), file=fp)
				
	# 		print("OK COPY: {}".format(dicom_des_path))

	# 	except Exception as e:
	# 		print("ERROR: ", path, e)
	# 		continue

	# # file_json = os.path.abspath(os.path.dirname(__file__)) + "/new_data_" + get_current_time() + ".json"
	
	# file_json = os.path.abspath(os.path.dirname(__file__)) + "/json_data/" + f"{os.path.basename(filter_dir)}" + "_siuid.json"
	# # print()
	# # print(file_json)
	
	# with open(file_json, "w") as f:
	# 	json.dump(study_id_json, f)