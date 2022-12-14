"""
基础函数

    主要包含json文件读写
    字符串中配置项名称解析
    json字符串拼接
    
"""

import json
import re

import tools.check_lex as check_lex


class EmployeeEncoder(json.JSONEncoder):
    """辅助自定义类结构写入json文件"""
    def default(self, o):
        return o.__dict__


def load_Kconfig(path):
    """
    读取Kconfig文件, 并处理非UTF-8字符
    参数:
        path: 文件路径信息
    返回值: 文件数据
    Raises: 出现未处理的utf-8字符
    """
    with open(path, 'r') as file:
        data = file.read()
        data = data.replace(u'\xa0', ' ')
    return data


def load_json(path):
    """ 读取json文件
    参数:
        path: 文件路径
    返回值: json数据
    """
    with open(path, 'r') as file:
        data = json.load(file)
    return data


def write_json_file(data, save_file):
    """ 借助EmployeeEncoder类将数据写入json文件内
    参数:
        data: 自定义类数据
        save_file: 保存路径
    返回值: None
    """
    print("{:<40}".format("[Write json]"))
    jsonDate = json.dumps(data, indent=4, cls=EmployeeEncoder)
    with open(save_file, 'w') as file:
        file.write(jsonDate)


def get_word(line):
    """ 获得输入字符串中的配置项名称

    参数:
        line (str): 输入字符串

    返回值:
        list: 配置项名称列表
    """
    
    result = []

    check_lex.lexer.input(line)
    while True:
        tok = check_lex.lexer.token()
        if not tok:
            break
        if tok.type == 'WORD':
            if re.fullmatch('[0-9]+', tok.value) or tok.value[0:2] == '0x':
                pass
            if re.fullmatch('[A-Z0-9_x]+', tok.value):
                if tok.value not in result:
                    result.append(tok.value)
    return result


def dict_add_item(save, left, right):
    """ 规定字典中增加内容
        save = {left:[right]}

    参数:
        save (dict): 待增加内容的字典
        left: key
        right: value

    返回值:
        dict: 增加内容后的save
    """
    
    if save.get(left, None):
        if right not in save[left]:
            save[left].append(right)
    else:
        save[left] = [right]
    return save

