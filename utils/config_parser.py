import configparser
import os


def load_config(path):
    """
    :param path: 配置文件的路径
    :return:
    """
    parser = configparser.ConfigParser()
    parser.read(path, encoding='utf8')

    ret = dict()
    for sec in parser.sections():
        ret[sec] = dict()
        for k, v in parser.items(sec):
            ret[sec][k] = v

    # 返回一个字典对象，包含读取的参数
    return ret


