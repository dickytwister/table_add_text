import os
import time

import numpy as np
import json
import cv2
import requests
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup


def cv2ImgAddText(img, text, left, top, textColor=(0, 0, 255), textSize=5):
    if (isinstance(img, np.ndarray)):  # 判断是否OpenCV图片类型
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    # 创建一个可以在给定图像上绘图的对象
    draw = ImageDraw.Draw(img)
    # 字体的格式
    fontStyle = ImageFont.truetype(
        "simsun.ttc", textSize, encoding="utf-8")
    # 绘制文本
    draw.text((left, top), text, textColor, font=fontStyle)
    # 转换回OpenCV格式
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)

def draw_boxes_gil(data, img_file_path, box_output=True, text_view=False, text_output=False):
    """
    对给定的图片和坐标信息在图片上标框
    :param text_view: 是否显示识别内容
    """
    # image = cv2.imread(img_file_path, cv2.IMREAD_UNCHANGED)
    image = cv2.imdecode(np.fromfile(img_file_path, dtype=np.uint8), -1)
    h, w, c = image.shape
    # with open(response_file, 'r', encoding='utf-8') as f:
    #     data = json.load(f)
    boxes = data["text_content"]
    n = 0
    score = 0
    rec_score = 0
    text_list = []
    for box in boxes:
        coo = box[0]
        first_point = coo[0]
        last_point = coo[2]

        if box_output:
            # 在图片上绘制框
            cv2.rectangle(image, (max(0, int(first_point[0])), max(0, int(first_point[1]))), (min(w, int(last_point[0])), min(h, int(last_point[1]))), (0, 255, 0), 1)
            # 在图片上绘制识别结果
            text = box[1][0]
            score = float(box[1][1])
            score_str = "{:.4f}".format(score)

            if text_view:
                image = cv2ImgAddText(image, text, max(0, int(first_point[0])) - 10, max(0, int(first_point[1])) - 5, textColor=(255, 0, 0), textSize=13)

        if text_output:
            text = box[1][0]
            text_list.append(text)

        n += 1
        rec_score += score
    rec = rec_score / n


    return rec, image, text_list


def draw_boxes_hs(data, img_file_path, text_view=False):
    """
    对给定的图片和坐标信息在图片上标框
    :param text_view: 是否显示识别内容
    """
    # image = cv2.imread(img_file_path, cv2.IMREAD_UNCHANGED)
    image = cv2.imdecode(np.fromfile(img_file_path, dtype=np.uint8), -1)
    h, w, c = image.shape
    # with open(response_file, 'r', encoding='utf-8') as f:
    #     data = json.load(f)
    boxes = data["data"]["text_content"]
    n = 0
    rec_score = 0
    for box in boxes:
        coo_lefttop = box[0][0]
        coo_rightbottom = box[0][2]

        # 在图片上绘制框: cv2.rectangle（图片，长方形框左上角坐标, 长方形框右下角坐标， 字体颜色，字体粗细）
        cv2.rectangle(image, (max(0, int(coo_lefttop[0])), max(0, int(coo_lefttop[1]))), (min(w, int(coo_rightbottom[0])), min(h, int(coo_rightbottom[1]))), (0, 255, 0), 1)
        # 在图片上绘制识别结果
        text = box[1][0]
        score = float(box[1][1])
        score_str = "{:.2f}".format(score) + "_" + text

        if text_view:
            image = cv2ImgAddText(image, text, max(0, int(coo_lefttop[0])) - 10, max(0, int(coo_lefttop[1])) - 5, textColor=(255, 0, 0), textSize=13)
        n += 1
        rec_score += score
    rec = rec_score / n
    return rec, image


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


def draw_boxes_dmp(data, img_file_path, text_view=False):
    """
    对给定的图片和坐标信息在图片上标框
    :param text_view: 是否显示识别内容
    """
    # image = cv2.imread(img_file_path, cv2.IMREAD_UNCHANGED)
    image = cv2.imdecode(np.fromfile(img_file_path, dtype=np.uint8), -1)
    h, w, c = image.shape
    gtsoup = BeautifulSoup(data["data"], 'lxml')
    td_item = get_tag(gtsoup, 'td')
    p_item = get_tag(gtsoup, 'p')
    all_item = td_item + p_item

    n = 0
    rec_score = 0
    for item in all_item:
        coo_lefttop = [item[1][0], item[1][1]]
        coo_rightbottom = [item[1][2], item[1][3]]

        # 在图片上绘制框: cv2.rectangle（图片，长方形框左上角坐标, 长方形框右下角坐标， 字体颜色，字体粗细）
        cv2.rectangle(image, (max(0, int(coo_lefttop[0])), max(0, int(coo_lefttop[1]))), (min(w, int(coo_rightbottom[0])), min(h, int(coo_rightbottom[1]))), (0, 255, 0), 1)
        # 在图片上绘制识别结果
        text = item[0]
        # score = float(box[1][1])
        # score_str = "{:.2f}".format(score) + "_" + text

        if text_view:
            image = cv2ImgAddText(image, text, max(0, int(coo_lefttop[0])) - 10, max(0, int(coo_lefttop[1])) - 5, textColor=(255, 0, 0), textSize=13)
        n += 1
        # rec_score += score
    rec = rec_score / n
    return rec, image


if __name__ == '__main__':
    # img_dir = r'F:\data\Ant\ant_img2_dataset\ant_img2_tab_dataset\11-1xml\imgs'
    # img_dir = r'F:\data\Ant\蚂蚁清洗测试9-28_文本框标注\test\imgs'
    # img_dir = r'F:\data\wenzishibie_0822\debug'
    # img_dir = r'F:\data\Ant\测试集\ant_img2_tab_dataset\蚂蚁标注-测试集\蚂蚁-无线表'
    # img_dir = r'F:\data\违规\gilocr违规测试集\imgs'

    # img_dir = r'F:\data\gilocr_badcase微调\文字识别\业务侧badcase\第四批\第四批_现金表_倾斜校正'
    # save_dir = r'F:\data\gilocr_badcase微调\文字识别\业务侧badcase\第四批\第四批_现金表_DMPview'
    img_dir = r'F:\data\ESG港股\平台预标注\研报--测试\imgs'
    save_dir = r'F:\data\ESG港股\平台预标注\研报--测试\gl_view'
    # img_dir = r'F:\test_code\test'
    # save_dir = r'F:\test_code\test_view'  # 可视化保存路径不能有中文

    os.makedirs(save_dir, exist_ok=True)
    # url = 'http://10.3.12.8:9292/gilocr/trocr/parse_img'
    # javaocrpy_url = 'http://10.3.12.7:9292/predictions/ocr/v1'
    gilocr_url = "http://10.3.12.8:9292/gilocr/trocr/parse_img?key=text_extract&ocr_service=svtr"
    ydocr_url = 'http://10.3.12.8:9100/ocr/intermediate_result?ocr_engine=yd_ocr&ocr_detect=True'
    hsocr_url = "http://10.3.12.7:8866/hsnlp/ocr/parse_image?is_compose=on&text_pdf=on&rotate=on&char_position"
    # img_extract_dmp = "http://10.3.12.8:9230/ocr/gilocr/image_extract?key=dmp"
    img_extract_dmp = "http://10.106.24.12:9230/ocr/gilocr/image_extract?key=dmp"
    # 调取返回值
    file_list = os.listdir(img_dir)
    for file in file_list:
        name = file.split(".")[1]
        if name != "cach" and name != "txt":
            path = os.path.join(img_dir, file)
            with open(path, 'rb') as f:
                st_time = time.time()
                r = requests.post(url=img_extract_dmp, files={'file': f}, timeout=3000)
                # r = requests.post(url=ydocr_url, files={'image': f})
                if not r.status_code == 200:
                    print("调用失败...", path)
                else:
                    print("调用成功...", path)
                    time_all = time.time() - st_time
                    print("time:", time_all)
                    res = r.json()
                    try:
                        data = json.loads(r.content)
                        # _, image, text_list = draw_boxes_gil(data, path, box_output=False, text_view=False, text_output=True)
                        _, image = draw_boxes_dmp(data, path, text_view=True)
                        # name = "{:.4f}".format(score) + "_" + file
                        # save_file = os.path.join(save_dir, name)
                        save_file = os.path.join(save_dir, file)
                        save_txt_file = os.path.join(save_dir, "三大表文本收集.txt")

                        # 存图片
                        image_pil = Image.fromarray(image)
                        image_pil.save(save_file)
                        print("img saved\n")
                        # # 存txt
                        # with open(save_txt_file, "a", encoding='utf-8') as li:
                        #     for item in text_list:
                        #         if item:
                        #             li.write(item + "\n")
                        # print("txt saved\n")


                    except Exception as e:
                        print("JSONDecodeError:", str(e))

