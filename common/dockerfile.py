import base64
import re

from dockerfile_parse import DockerfileParser


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
