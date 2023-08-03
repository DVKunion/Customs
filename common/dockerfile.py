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


def parse_reference(reference):
    try:
        # Split by ":" to get the image tag (version) and image name
        tag_split = reference.split(":")
        tag = tag_split[1] if len(tag_split) == 2 else "latest"

        # Split by "/" to get the image repository, organization, and image name
        image_parts = tag_split[0].split("/")

        if len(image_parts) == 1:
            # If there's only one part, assume it's the image name without organization
            repository = "docker.io"
            organization = "library"
            image_name = "library/" + image_parts[0]
        elif len(image_parts) == 2:
            # If there are two parts, assume the first part is the organization and the second part is the image name
            repository = "docker.io"
            organization = image_parts[0]
            image_name = image_parts[0] + "/" + image_parts[1]
        else:
            repository = image_parts[0]
            organization = image_parts[1]
            image_name = "/".join(image_parts[1:])

        res = {
            "repository": repository,
            "organization": organization,
            "image_name": image_name,
            "tag": tag
        }
        if res["repository"] == "":
            print("error repository: " + reference)
            return None
        return res
    except Exception as e:
        print("无法解析镜像reference信息：", str(e))
        return None


def get_arg_value(arg_name, dockerfile):
    arg_pattern = rf'ARG\s+{arg_name}=([^\n\r]+)'
    arg_match = re.search(arg_pattern, dockerfile)

    if arg_match:
        return arg_match.group(1).strip().replace("\"", "").replace("'", "")
    else:
        return None


if __name__ == "__main__":
    # Example usage:
    image_reference_1 = "docker.io/my_org/my_image"
    image_reference_2 = "nginx:latest"
    parsed_info_1 = parse_reference(image_reference_1)
    parsed_info_2 = parse_reference(image_reference_2)

    print(parsed_info_1)
    print(parsed_info_2)
