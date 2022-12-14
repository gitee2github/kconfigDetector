"""此文件用于生成配置项的父类或子类配置项
函数依赖于main.py生成的dep.json文件

这里的子类配置从作用角度出发
一切会对当前配置产生影响的配置项均认为是其父类配置项
反之则为子类
"""

import tools


def get_kid(config_dep, save):
    """获得指定配置项的子类配置项

    Args:
        config_dep (str): 待查询配置项名称
        save (str): 子类配置项集合输出文件
    """
    dep_data = tools.load_json(config_dep)
    jsondata = tools.make_dict(dep_data, True)
    print("{:<40}".format("[Prepare write ConfigPath]") + "file => " + save)
    tools.write_json(jsondata, save)


def get_father(config_dep, save):
    """获得指定配置项的父类配置项

    Args:
        config_dep (str): 待查询配置项名称
        save (str): 父类配置项集合输出文件
    """
    dep_data = tools.load_json(config_dep)
    jsondata = tools.make_dict(dep_data, False)
    print("{:<40}".format("[Prepare write ConfigPath]") + "file => " + save)
    tools.write_json(jsondata, save)


if __name__ == '__main__':
    config_dep = ""
    save = ""

    get_kid(config_dep, save + "_Kid.json")
    get_father(config_dep, save + "_Father.json")
