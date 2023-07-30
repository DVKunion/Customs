import base64
import json
import re
import sys
import time

import requests
from dockerfile_parse import DockerfileParser

# 替换成你的GitHub Personal Access Token
ACCESS_TOKEN = ''

result = []
while_repo_list = ["docker_repair"]


def calculate_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Function '{func.__name__}' executed in {execution_time:.6f} seconds.")
        return result

    return wrapper


@calculate_execution_time
def get_dockerfile_images():
    url = 'https://api.github.com/search/code'
    params = {'q': 'FROM language:Dockerfile', "page": "1", "per_page": "100"}
    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}', "Accept": "application/vnd.github+json"}

    response = requests.get(url, headers=headers, params=params)
    response_json = response.json()
    if response.status_code != 200:
        print(response.json())
    parse_result(response_json)
    total = response_json["total_count"]
    print(total)
    for page in range(2, 100):
        params["page"] = str(page)
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(response.json())
        response_json = response.json()
        parse_result(response_json)

    with open("result.json", "w+") as file:
        file.write(json.dumps(result))


def parse_result(response_json):
    for item in response_json["items"]:
        res = dict()
        res['filename'] = item["name"]
        res['path'] = item["path"]
        res['repo_name'] = item["repository"]["name"]
        if res['repo_name'] in while_repo_list:
            continue
        url = item["url"]
        res['detail_url'] = url
        print(f"{res['filename']}:{res['path']} - {res['detail_url']}")
        images = []
        # need get
        resp_detail = requests.get(url, headers=headers)
        resp_detail_json = resp_detail.json()
        contents_base64 = resp_detail_json["content"].replace("\n", "")
        decoded_bytes = base64.b64decode(contents_base64)
        decoded_string = decoded_bytes.decode('utf-8')
        dfp = DockerfileParser()
        dfp.content = decoded_string
        alias = dict()
        for line in dfp.structure:
            if line["instruction"] == "FROM":
                values = line["value"].split(" ")
                image = values[0]
                # find replace value:
                arg_pattern = r'\$\{(\w+)\}'
                arg_matches = re.findall(arg_pattern, image)
                for arg_name in arg_matches:
                    arg_value = get_arg_value(arg_name, decoded_string)
                    if arg_value:
                        image = image.replace(f'${{{arg_name}}}', arg_value)
                # transfer alias
                if image in alias:
                    image = alias[image]
                for v in values:
                    if v.lower() == "as":
                        alias[values[-1]] = image

                images.append(image)
        res['images'] = images
        result.append(res)


def get_arg_value(arg_name, dockerfile):
    arg_pattern = rf'ARG\s+{arg_name}=([^\n\r]+)'
    arg_match = re.search(arg_pattern, dockerfile)

    if arg_match:
        return arg_match.group(1).strip().replace("\"", "").replace("'", "")
    else:
        return None


if __name__ == '__main__':
    args = sys.argv[1:]
    ACCESS_TOKEN = args[0]
    if ACCESS_TOKEN == "":
        print("empty token")
        sys.exit()
    get_dockerfile_images()
