# **********************************************************************
# Copyright (c) 2022 Institute of Software, Chinese Academy of Sciences.
# kconfigDepDetector is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#         http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, 
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY
# OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
# **********************************************************************/
__all__ = ['preprocess.py', 'config_yacc.py', 'check.py']

import os

from .check import Checker
from .config_yacc import ParseKconfig
from .preprocess import preprocessing as inner_preprocessing
from .utils import load_Kconfig as inner_load_Kconfig
from .utils import load_json as inner_load_json
from .utils import write_json_file as inner_write_json_file
from .utils import get_word as inner_get_word
from .utils import dict_add_item as inner_dict_add_item


def preprocessing(root, target, file, display) -> None:
    """ 预处理，解决ply包需要在同路径下调度parser的问题
    参数：
        root: 内核源码路径
        target: 体系架构
        file: 预处理后生成.Kconfig文件
        display: 终端打印开关
    """
    inner_preprocessing(root, target, file, display)


def load_Kconfig(path) -> str:
    return inner_load_Kconfig(path)


def load_json(path):
    return inner_load_json(path)


def check_file_data(path) -> bool:
    """ 检查文件是否存在且文件内部是否有数据
    参数:
        path: 文件路径信息
    返回值: 布尔类型，文件检查结果
    """
    if os.path.exists(path) and os.path.isfile(path):
        with open(path, 'r') as file:
            data = file.read()
            if len(data) > 0:
                return True
            else:
                return False
    else:
        return False


def check_folder(root, tag, arch) -> str:
    """ 检查保存文件夹是否存在, 不存在则在当前目录下创建文件夹
    参数:
        root: 根路径
        tag: 当前Linux内核版本
        arch: 需要处理的指定架构
    返回值: 文件夹名称
    """
    if root[-1] == '/':
        folder_name = root + tag + '-' + arch
    else:
        folder_name = root + '/' + tag + '-' + arch
    if os.path.exists(folder_name):
        return folder_name + '/'
    else:
        os.mkdir(folder_name)
        return folder_name + '/'


def write_json(data, save_file) -> None:
    inner_write_json_file(data, save_file)


def parse(Kconfig, config, config_dep, display) -> None:
    """ 解析Kconfig
    参数:
        Kconfig: 预处理后的文件路径
        config: *_config.json文件路径
        config_dep: *_config_dep.json文件路径
        display: 是否显示终端信息，可加快识别速度
    返回值: None
    """
    ParseKconfig(Kconfig, config, config_dep, display)


def check(dep_path, config_path, file_path, save_file) -> None:
    """ 检查配置文件中的错误值
    参数：
        dep_path: Kconfig解析后生成的_dep.json文件
        config_path: Kconfig解析后生成的_config.json文件
        file_path: 待检查内核配置文件
        save_file: 输出检查结果_error.json文件，包含所有错误项，若无错误则文件不存在
    """
    Checker(dep_path, config_path, file_path, save_file)


def make_dict(dep_data, flag) -> dict:
    """ 查询配置项的子类、父类
    参数：
        dep_data: 待查询配置项
        flag: 布尔类型
            True 查询子类
            False 查询父类
    返回值：
        查询结果，子类 or 父类配置项json字符串
    """
    getFather = {}
    getKid = {}
    for name in dep_data:
        for detail in dep_data[name]:
            temp = inner_get_word(detail['rev_select']) + inner_get_word(detail['dep'])
            for item in temp:
                getFather = inner_dict_add_item(getFather, name, item)
                getKid = inner_dict_add_item(getKid, item, name)
    if flag:
        return getKid
    else:
        return getFather
