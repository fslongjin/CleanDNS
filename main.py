from dns.resolver import Resolver

from utils import load_config, get_logger

# 获取配置文件
config = load_config()

dns_resolver = Resolver()
# 设置resolver的
dns_resolver.nameservers = config['Resolver']['nameservers']



