import config_parser
import log

import os


def load_config(path=os.path.join(os.getcwd(), 'config.ini')):
    """
        :param path: 配置文件的路径
        :return:
    """
    return config_parser.load_config(path)


def init_logging(log_path='log.txt'):
    print('正在初始化日志服务...', end='')
    log.init_log(log_path)
    print('ok')


def get_logger():
    return log.get_logger()

