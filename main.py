

from utils import load_config, get_logger, init_logging
import remoteHTTPDNS_server
import localDNS_server




if __name__ == '__main__':
    # 获取配置文件
    config = load_config()

    # 启动local dns server
    if config['Common']['run_mode'] == 'L':
        localDNS_server.run(config)

