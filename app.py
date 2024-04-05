import streamlit as st
import tempfile
from paddleocr import PPStructure
from langchain_community.llms.moonshot import Moonshot
import os
from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser
from langchain.schema.runnable import Runnable, RunnablePassthrough, RunnableConfig
import json
import re
from dotenv import load_dotenv
import cv2

@st.cache_resource()
def get_ocr_llm():
    load_dotenv()
    # 从环境变量中获取API密钥
    api_key = os.environ.get("MOONSHOT_API_KEY")
    if not api_key:
        raise ValueError("MOONSHOT_API_KEY not found in environment variables")

    # 初始化PaddleOCR
    return PPStructure(layout=False, show_log=True), Moonshot(model="moonshot-v1-8k") # type: ignore


ocr, llm = get_ocr_llm()
# or use a specific model
# Available models: https://platform.moonshot.cn/docs
# llm = Moonshot(model="moonshot-v1-128k")

def list_to_str(list):
    return ",".join(list)

# 实现一个函数，使用llm将html转换为json，入参为html字符串，返回json字符串，使用langchain的prompt，使用lcel
def html2json(html, main_fields, child_fields):
    prompt = PromptTemplate.from_template('''
        请将以下 >>> <<< 中的html表格转换为json格式，注意区分主表（main）信息和明细（children）信息。
        注意将主表信息按字段拆分。注意将明细的汇总信息放在主表中。
        如果主表信息缺少字段名称，请自行添加字段名称，如果没有明细信息，请删除children字段。
        按照字段的语义，将主表字段分别替换为{main_fields}，将明细字段分别替换为{child_fields}。
        如果主表或子表的字段不在替换字段中，请删除该字段。
        注意去除多余的空格，如果是数值类的字段，请将文本转换为数值类型。
        只返回json即可不用返回其他信息
        >>> {html} <<< 
        返回格式如下：
        {{
            "main": {{"key": "value"}},
            "children": [
               {{"key": "value"}},
            ]
        }}
    ''')
    format_prompt = prompt.format(html=html, main_fields=list_to_str(main_fields), child_fields=list_to_str(child_fields))
    runnable =  llm | JsonOutputParser()
    return runnable.invoke(format_prompt)

def convert_origin_to_hecom(origin, hecom):
    prompt = PromptTemplate.from_template('''
        请将以下原始字段与实际字段按照语义进行一一对应，输出json格式。
        原始字段：{origin}。实际字段：{hecom}。 
        返回格式如下：
        {{
            "实际字段": "原始字段",
        }}
    ''')
    runnable = (
        prompt
        | llm
        | JsonOutputParser()
    )
    return runnable.invoke({"origin":",".join(origin), "hecom":",".join(hecom)})

def recognize_table(uploaded_file):
    tfile = tempfile.NamedTemporaryFile(delete=False) 
    tfile.write(uploaded_file.read())
    # 读取图片
    img = cv2.imread(tfile.name) # type: ignore
    # 使用PaddleOCR进行表格识别
    result = ocr(img)
    return result[0]['res']['html']

def extract_field_names(json_data):
    main_fields = list(json_data['main'].keys())
    children_fields = set()
    for child in json_data['children']:
        for key in child.keys():
            children_fields.add(key)
    return main_fields, list(children_fields)   

st.title("表格识别测试")
with st.expander("如何使用"):
    st.markdown("""
    1. 输入红圈CRM+对象字段，用于模拟从服务器获取的要录入对象的字段。
    2. 上传表单图片，等待识别结果。
    3. 查看OCR识别结果，检查OCR识别准确性。
    4. 查看JSON结果，检查生成JSON的准确性。
    """)

st.subheader("红圈CRM+对象字段")
with st.container(border=True):
    main_input = st.text_input("请输入主表字段，用逗号、分号或空格分隔：")
    main_fields = re.split(',|;|，|；| ', main_input)
    if len(main_input) > 0:
        st.write("你输入的主表字段：")
        st.write(",".join(main_fields))
    st.divider()
    child_input = st.text_input("请输入子表字段，用逗号、分号或空格分隔：")
    child_fields = re.split(',|;|，|；| ', child_input)
    if len(child_input) > 0:
        st.write("你输入的子表字段：")
        st.write(",".join(child_fields))

st.subheader("上传表单图片")
uploaded_file = st.file_uploader("", type=['jpg', 'jpeg', 'png'])
st.info("支持的图片格式：jpg, jpeg, png")
if uploaded_file is not None:
    with st.container(border=True):
        with st.spinner('正在识别...'):
            html = recognize_table(uploaded_file)
            json_data = html2json(html, main_fields, child_fields)
            # main, children = extract_field_names(json_data)
            # hecom_main = convert_origin_to_hecom(main, main_fields)
            # hecom_children = convert_origin_to_hecom(children, child_fields)
        # st.write("主表字段映射：")
        # st.code(json.dumps(hecom_main,indent=2, ensure_ascii=False), language='json')
        # st.write("子表字段映射：")
        # st.code(json.dumps(hecom_children,indent=2, ensure_ascii=False), language='json')

        st.write("OCR识别结果：")
        st.markdown(html, unsafe_allow_html=True)
        st.write("JSON结果：")
        st.code(json.dumps(json_data,indent=2, ensure_ascii=False), language='json')
        
