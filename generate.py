import os
import json

image_count = dict()


def read_json_files(directory):
    repo_cnt = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                with open(file_path, "r") as f:
                    try:
                        data = json.load(f)
                        for repo in data:
                            repo_cnt += 1
                            for detail in repo["details"]:
                                for image in detail["images"]:
                                    if image in image_count:
                                        image_count[image] += 1
                                    else:
                                        image_count[image] = 1
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON in {file}")
    print("repo count: ", repo_cnt)


# 调用函数并指定当前目录（使用.）或者替换为指定目录的路径
read_json_files(".")
print("image_count:", len(image_count))
sorted_keys_by_value = sorted(image_count, key=lambda x: image_count[x])
print("image_set: ", sorted_keys_by_value)
max_count = 0
max_name = ""
for image in image_count:
    if image_count[image] > max_count:
        max_count = image_count[image]
        max_name = image

print("max images:", max_name)
print("max images total:", max_count)
