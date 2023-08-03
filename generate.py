import datetime
import os
import json

import requests

import common.dockerfile

image_count = dict()

repository_set = set()
repositories = []
image_set = set()
images = []


def generate_top_images_calc():
    print("image_count:", len(image_count))
    sorted_keys_by_value = sorted(image_count, key=lambda x: image_count[x])
    sorted_keys_by_value.reverse()
    # print("image_set: ", sorted_keys_by_value)
    res_dict = []
    for i in range(0, 50):
        res_dict.append({
            "image": sorted_keys_by_value[i],
            "count": image_count[sorted_keys_by_value[i]],
        })
    max_count = 0
    max_name = ""
    for image in image_count:
        if image_count[image] > max_count:
            max_count = image_count[image]
            max_name = image

    print("max images:", max_name)
    print("max images total:", max_count)

    with open("templates/top_50_images.json", "r+") as f:
        template = f.read()
        render = template.replace('$time', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) \
            .replace('"$data"', json.dumps(res_dict))
        r = requests.post("https://mtigd2.laf.run/transfer_svg", headers={
            "Content-Type": "application/json; charset=UTF-8",
        }, data=render)
        if r.status_code != 200:
            print(r.status_code, r.text)
            return
        with open('assets/top_50_images.svg', 'w+') as s:
            s.write(r.text)


def format_image():
    print(len(image_set))
    sorted_dict_array = sorted(images, key=lambda x: x['count'])
    sorted_dict_array.reverse()
    for i in range(0, 100):
        print(sorted_dict_array[i])


def load_json():
    repo_cnt = 0
    repo_be = 0
    max_star = 0
    for root, dirs, files in os.walk("dataset"):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                with open(file_path, "r") as f:
                    try:
                        data = json.load(f)
                        for repo in data:
                            repo_cnt += 1
                            if repo["stargazerCount"] > 10:
                                if repo["stargazerCount"] > max_star:
                                    max_star = repo["stargazerCount"]
                                repo_be += 1
                            image_tmp_key = dict()
                            for detail in repo["details"]:
                                # 增加逻辑：如果在同一个仓库出现多次，那么算做1次
                                for image in detail["images"]:
                                    if image in image_tmp_key:
                                        continue
                                    refer_dict = common.dockerfile.parse_reference(image)
                                    if refer_dict is None:
                                        continue
                                    if refer_dict["repository"] in repository_set:
                                        for r in repositories:
                                            if r["name"] == refer_dict["repository"]:
                                                r["count"] += 1
                                    else:
                                        repository_set.add(refer_dict["repository"])
                                        repositories.append({
                                            "name": refer_dict["repository"],
                                            "count": 1,
                                        })
                                    if refer_dict["image_name"] in image_set:
                                        for r in images:
                                            if r["name"] == refer_dict["image_name"]:
                                                r["tags"].add(refer_dict["tag"])
                                                r["count"] += 1
                                    else:
                                        image_set.add(refer_dict["image_name"])
                                        obj = {
                                            "name": refer_dict["image_name"],
                                            "count": 1,
                                            "tags": set()
                                        }
                                        obj["tags"].add(refer_dict["tag"])
                                        images.append(obj)
                                    image_tmp_key[image] = 0
                                    if image in image_count:
                                        image_count[image] += 1
                                    else:
                                        image_count[image] = 1
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON in {file}")
    print("repo count: ", repo_cnt)
    print("repo be: ", repo_be)
    print("max star: ", max_star)


if __name__ == '__main__':
    load_json()
    # format_image()
    generate_top_images_calc()
