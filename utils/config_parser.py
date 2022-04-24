import configparser
import os


def load_config(path):
    """
    :param path: 配置文件的路径
    :return:
    """
    parser = configparser.ConfigParser()
    parser.read(path, encoding='utf8')

    assert len(parser.sections()) == 3

    # 获取整型参数，按照key-value的形式保存
    _conf_ints = [(key, int(value)) for key, value in parser.items('ints')]

    # 获取浮点型参数，按照key-value的形式保存
    _conf_floats = [(key, float(value)) for key, value in parser.items('floats')]

    # 获取字符型参数，按照key-value的形式保存
    _conf_strings = [(key, str(value)) for key, value in parser.items('strings')]

    # 返回一个字典对象，包含读取的参数
    return dict(_conf_ints + _conf_floats + _conf_strings)


