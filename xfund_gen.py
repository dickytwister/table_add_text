import json
import os
from PIL import Image
import cv2
import numpy as np
import requests
from bs4 import BeautifulSoup

def read_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def write_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def pil_to_cv2(pil_image):
    """将 PIL 图像转换为 OpenCV 格式"""
    open_cv_image = np.array(pil_image)
    # 将 RGB 转换为 BGR
    return cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)

def get_tag(gtsoup, tagname):
    tag_item = []
    for item in gtsoup.find_all(tagname):
        try:
            box = [int(float(item.attrs['x'])),
                   int(float(item.attrs['y'])),
                   int(float(item.attrs['x'])) + int(float(item.attrs['w'])),
                   int(float(item.attrs['y'])) + int(float(item.attrs['h']))]
            text = str(item.string)
            if text == "None":
                text = "NULL"
            tag_item.append([text, box])
        except:
            continue
    return tag_item

def get_text(pil_img, x1, y1, x2, y2):
    """
    传入PNG图片数组，调用文字识别接口，返回识别的文本内容
    :param pil_img: PIL Image对象
    :param x1, y1, x2, y2: 裁剪区域的坐标
    :return: 识别的文本内容
    """
    # 设置文字识别接口URL
    img_extract_dmp = "http://10.106.24.12:9230/ocr/gilocr/image_extract?key=dmp"

    # 将 PIL 图像转换为 NumPy 数组进行裁剪
    img_np = np.array(pil_img)
    cropped_img = img_np[y1:y2, x1:x2]

    # 将裁剪后的图像从 NumPy 数组转换为 PIL Image，再转换为 OpenCV 格式
    cv2_img = pil_to_cv2(Image.fromarray(cropped_img))

    # 将OpenCV图像转换为PNG格式字节流
    _, img_encoded = cv2.imencode('.png', cv2_img)
    img_bytes = img_encoded.tobytes()

    # 调用文字识别接口
    try:
        response = requests.post(url=img_extract_dmp, files={'file': ('image.png', img_bytes, 'image/png')}, timeout=3000)

        # 判断请求是否成功
        if response.status_code != 200:
            print("调用失败...")
            return None

        # 解析返回的JSON数据
        data = response.json()
        gtsoup = BeautifulSoup(data["data"], 'lxml')
        text_items = get_tag(gtsoup, 'td') + get_tag(gtsoup, 'p')

        # 提取识别的文本内容
        text_list = [item[0] for item in text_items]
        return '\n'.join(text_list)

    except Exception as e:
        print("请求或解析出错:", str(e))
        return None

def xfund_generator(studio_json_path, img_folder, xfund_json_path):
    skip_list = [
        "table",
        "wireless",
        "formula",
        "image",
        "head_image",
        "foot_image",
        "有线表",
        "缺线表",
        "独立公式",
        "行内内嵌公式",
        "图片",
        "图表",
        "分子结构图",
        "页脚图片",
        "页眉图片"
    ]  # 需要跳过的标签
    studio_json = read_json(studio_json_path)
    # 创建一个空的xfund_json
    xfund_json = {
        "documents": []
    }
    # 遍历studio_json中的每张图片
    for image_json in studio_json:
        image_name = image_json["file_upload"].split('.')[0].split('-')[1]
        image_path = os.path.join(img_folder, image_name + '.png')
        with Image.open(image_path) as img:
            # 获取图片的宽高
            width, height = img.width, img.height
            # 创建一个空的xfund_image
            xfund_image = {}
            xfund_image["id"] = image_name
            xfund_image["document"] = []
            for res in image_json["annotations"][0]["result"]:
                if res["value"]["rectanglelabels"][0] in skip_list:
                    continue
                else:
                    x1 = round(0.01 * width * res["value"]["x"])
                    y1 = round(0.01 * height * res["value"]["y"])
                    x2 = round(0.01 * width * (res["value"]["x"] + res["value"]["width"]))
                    y2 = round(0.01 * height * (res["value"]["y"] + res["value"]["height"]))
                    text = get_text(img, x1, y1, x2, y2)
                    xfund_image["document"].append(
                        {
                            "id": res["id"],
                            "text": text,
                            "label": res["value"]["rectanglelabels"][0],
                            "box": [
                                x1,
                                y1,
                                x2,
                                y2
                            ]
                        }
                    )
            xfund_image["img"] = {
                "fname": image_name + '.png',
                "width": width,
                "height": height
            }

            xfund_json["documents"].append(xfund_image)

    write_json(xfund_json_path, xfund_json)

if __name__ == '__main__':
    studio_json_path = './json/project-43-at-2024-07-02-06-14-290eed43.json'
    img_folder = './img'
    xfund_json_path = './xfund示例/out_xfund.json'

    xfund_generator(studio_json_path, img_folder, xfund_json_path)
