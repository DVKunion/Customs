import base64
import json
import re
import time

import requests

import common.timer
from github.graphQL import GraphQL
from dockerfile_parse import DockerfileParser


class GithubCode:
    def __init__(self, token, date=""):
        self.url = 'https://api.github.com/search/code'
        self.headers = {'Authorization': f'Bearer {token}', "Accept": "application/vnd.github+json"}
        self.graphQL = GraphQL(token, date)
        self.codes = []

    @common.timer.calculate_execution_time
    def fetch_code_detail(self):
        self.graphQL.fetch_all_result()
        total_repos = len(self.graphQL.repos)
        print(self.graphQL.query_time, "total:", total_repos)
        for i in range(0, total_repos):
            repo = self.graphQL.repos[i]
            response = self.fetch_detail(repo)
            response_json = response.json()
            retry_cnt = 0
            while response.status_code != 200 and retry_cnt < 3:
                if "message" in response_json and "API rate limit" in response_json["message"]:
                    # 触发频率限制了，休息个50s左右
                    print(f"rete limit, now process: {i}/{total_repos}")
                    time.sleep(60)
                response = self.fetch_detail(repo)
                response_json = response.json()
                retry_cnt += 1
            if retry_cnt > 3:
                print("error fetch repo:", repo)
                continue
            total = response_json["total_count"]
            print(repo["nameWithOwner"], total)
            repo["details"] = []
            if total == 0:
                details = self.parse_default_result(repo)
                if "images" in details:
                    repo["details"].append(details)
                    print(f"{details['filename']}:{details['path']} - {details['url']}")
            else:
                repo["details"] = self.parse_result(response_json)
            self.codes.append(repo)

    def fetch_detail(self, repo):
        params = {'q': f'FROM repo:{repo["nameWithOwner"]} language:Dockerfile', "page": "1", "per_page": "100"}
        response = requests.get(self.url, headers=self.headers, params=params)
        return response

    def parse_result(self, response_json):
        result = []
        for item in response_json["items"]:
            res = dict()
            res['filename'] = item["name"]
            res['path'] = item["path"]
            url = item["url"]
            res['detail_url'] = url
            print(f"{res['filename']}:{res['path']} - {res['detail_url']}")
            # need get
            resp_detail = requests.get(url, headers=self.headers)
            if resp_detail.status_code == 200:
                resp_detail_json = resp_detail.json()
                res['images'] = parse(resp_detail_json)
                result.append(res)
            else:
                print(resp_detail.text)

        return result

    def parse_default_result(self, repo):
        # 当 search indexed 失败时候, 尝试从main分支的Dockerfile获取一下
        res = dict()
        res['filename'] = "Dockerfile"
        res['path'] = "Dockerfile"
        res['url'] = f"https://api.github.com/repos/{repo['nameWithOwner']}/contents/Dockerfile"
        # need get
        resp_detail = requests.get(res['url'], headers=self.headers)
        if resp_detail.status_code == 200:
            resp_detail_json = resp_detail.json()
            res['images'] = parse(resp_detail_json)
        return res

    def save_result(self):
        date_slice = self.graphQL.query_time.split("-")
        with open(f"dataset/{date_slice[0]}/{date_slice[1]}/github-{self.graphQL.query_time}.json", "w+") as file:
            file.write(json.dumps(self.codes))


def parse(resp_detail_json):
    image_list = []
    try:
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

                image_list.append(image)
    except:
        print("error parse")
        print(resp_detail_json)
    return image_list


def get_arg_value(arg_name, dockerfile):
    arg_pattern = rf'ARG\s+{arg_name}=([^\n\r]+)'
    arg_match = re.search(arg_pattern, dockerfile)

    if arg_match:
        return arg_match.group(1).strip().replace("\"", "").replace("'", "")
    else:
        return None
