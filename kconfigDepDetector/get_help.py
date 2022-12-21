"""此函数用于获取所有config配置项的help信息
函数逻辑是
  首先需要将涉及到的所有Kconfig文件整理到一个文件内（getAllFile.py）
  其次抽取config的信息, 生成json文件
  最后抽取config得help信息, 生成json文件
依次生成 tag_arch.Kconfig -> tag_arch_config.json -> tag_arch_help.json
建议使用默认文件名

此函数需要将所有Kconfig函数整理到一个文件内, 借助HandleKconfig函数完成
如果已经完成此操作, 可以注释32行, 直接运行33行, 调用parser函数
函数将直接使用默认的文件名tag + _ + arch + .Kconfig

在初筛所有Kconfig的过程中
过滤掉Documentation, scripts/kconfig
对于arch路径下的, 搜索指定架构目录下的所有Kconfig文件
"""
import tools


def get_help(SourcePath, SavePath):
    """获取内核配置项help信息

    Args:
        SourcePath (str): 内核源码路径
        SavePath (str): 输出结果路径
    """
    data = tools.load_json(SourcePath)
    ConfigPath = {}
    for item in data:
        ConfigPath[item] = []
        for ptr in data[item]:
            help = ptr['help'].replace('\n\t\t', '').replace('\t\t', '')
            ConfigPath[item].append(help)

    print("{:<40}".format("[Prepare write ConfigHelp]") + "file => " + SavePath)
    tools.write_json_file(ConfigPath, SavePath)


if __name__ == '__main__':
    target = ""
    save = ""
    get_help(target, save)
