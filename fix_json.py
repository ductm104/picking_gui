import json
import os
import glob
import sys


json_file = sys.argv[1]
print(json_file)


with open(json_file, 'r') as f:
    data = json.load(f)


prefix = '/data.local/data/DICOM_DATA/BVE/'
subfix = '/media/tuan/Data1/DATA_RAW/BVE_SIUID/'

new_data = {}
for key, value in data.items():
    key = key.replace(prefix, subfix)
    new_data[key] = value

print(len(new_data))
with open(json_file+'.fix', 'w') as f:
    json.dump(new_data, f)
