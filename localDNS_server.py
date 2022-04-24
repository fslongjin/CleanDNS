import dns.message
import requests
from dns.resolver import Resolver
from dnslib import DNSRecord, RD, SOA, DNSHeader, RR, A, CNAME, QTYPE
import dns
import requests
import socket
from typing import cast

import multiprocessing.dummy
import threading
from queue import Queue
import datetime
import time

import random




from utils import get_logger, init_logging


init_logging('log_ldns.txt')
ldns_logger = get_logger()

dns_resolver = Resolver()

name_servers = []

# 本地dns缓存字典
local_dns_buffer_write_lock = threading.Lock()
local_dns_buffer = dict()

global_TTL = datetime.timedelta(seconds=10)
global_buffer_check_interval = 20
global_buffer_check_rate = 0.2

def resolve_record(domain, rdtype):
    """
    解析记录
    :param domain 目标域名
    :return:
    """
    domain = domain.lower().strip()
    buf_key = str(domain) + str(rdtype)
    try:
        if buf_key in local_dns_buffer.keys():
            if local_dns_buffer[buf_key][1] < datetime.datetime.now():
                # 缓存过期，尝试删除
                local_dns_buffer_write_lock.acquire()
                # 获取锁之后需要再次确认
                if buf_key in local_dns_buffer.keys():
                    if local_dns_buffer[buf_key][1] < datetime.datetime.now():
                        # 删除缓存
                        del local_dns_buffer[buf_key]
                        #ldns_logger.logger.info("Cache expired, successfully deleted: [{}]".format(buf_key))
                        ldns_logger.logger.info("Cache expired, successfully deleted: [{}]".format(buf_key))
                local_dns_buffer_write_lock.release()
            else:
                # 缓存已存在，直接返回
                return local_dns_buffer[buf_key][0]
    except Exception as e:
        local_dns_buffer_write_lock.release()
        ldns_logger.logger.error("Unknown Error: {}".format(str(e.args)))
        return None

    for ns in name_servers:
        try:
            with requests.sessions.Session() as sess:
                query = dns.message.make_query(domain, rdtype)
                r = dns.query.https(query, ns, session=sess, timeout=3)

                # 获取buffer写锁
                local_dns_buffer_write_lock.acquire()
                local_dns_buffer[buf_key] = (r, datetime.datetime.now() + global_TTL)
                ldns_logger.logger.info("Refreshed key={}  expired:{}".format(buf_key, str(local_dns_buffer[buf_key][1])))
                local_dns_buffer_write_lock.release()
                return r
        except Exception as e:
            local_dns_buffer_write_lock.release()
            ldns_logger.logger.error(str(e.args))

    return None


def dns_handler(udp_sock, msg, address):
    """
    dns解析处理程序
    :param udp_sock:
    :param msg:dns报文
    :param address:来源ip
    :return:
    """

    try:
        try:
            # 解析dns请求包
            #recv_request = DNSRecord.parse(msg)
            recv_request = dns.message.from_wire(msg)
        except Exception as e:
            ldns_logger.logger.error("Parse dns record failed from address {}, error message:{}".format(address, str(e.args)))
            return
        try:
            # 解析请求类型
            # qtype = QTYPE.get(recv_request.q.qtype)
            # print(recv_request.index)
            qtype = str(recv_request.question[0].rdtype)
        except Exception as e:
            ldns_logger.logger.error(
                "Get QTYPE failed from address {}, error message:{}".format(address, str(e.args)))
            return

        # 获取目标域名

        domain = str(recv_request.question[0].name)

        ldns_logger.logger.info("Resolving request from client [{}]: domain=[{}], qtype=[{}]".format(address, domain, qtype))

        # 进行解析
        response = resolve_record(domain, recv_request.question[0].rdtype)
        if response is None:
            response = dns.message.make_response(recv_request)

        response.id = recv_request.id

        response.question = [recv_request.question[0]]
        wire = response.to_wire(cast(dns.name.Name, response))
        udp_sock.sendto(wire, address)
        ldns_logger.logger.info("Successfully send response to client [{}], domain=[{}], qtype=[{}]".format(
                                address, domain, qtype))
        return

    except Exception as e:
        ldns_logger.logger.error("Failed to send response to client [{}], msg:[{}]".format(
            address, str(e.args)))


def regular_check_expired_keys():
    """
    定时清除过期key的线程
    :return:
    """

    while True:
        # 间隔一段时间再检查缓存
        time.sleep(global_buffer_check_interval)
        try:
            ldns_logger.logger.info("Start regular check expired keys... current total buffer size:[{} bytes]"
                                    .format(local_dns_buffer.__sizeof__()))
            # 计算要检查的keys的数量，每次检查20%
            num_to_check = int(global_buffer_check_rate*len(local_dns_buffer))

            keys = list(local_dns_buffer.keys())
            # 随机检查
            for i in range(num_to_check):
                buf_key = random.choice(keys)

                if buf_key in local_dns_buffer.keys():
                    # print(str(local_dns_buffer[buf_key][1]))
                    if local_dns_buffer[buf_key][1] < datetime.datetime.now():
                        # 缓存过期，尝试删除
                        local_dns_buffer_write_lock.acquire()
                        # 获取锁之后需要再次确认
                        if buf_key in local_dns_buffer.keys():
                            if local_dns_buffer[buf_key][1] < datetime.datetime.now():
                                # 删除缓存
                                del local_dns_buffer[buf_key]

                                ldns_logger.logger.info("Cache expired, successfully deleted: [{}]".format(buf_key))
                        local_dns_buffer_write_lock.release()

        except Exception as e:
            local_dns_buffer_write_lock.release()
            ldns_logger.logger.error("Fault in check expired keys. Message:{}".format(str(e.args)))


def run(config):

    # 设置resolver的nameservers
    global name_servers, global_TTL, global_buffer_check_interval, global_buffer_check_rate
    name_servers = [x.strip() for x in config['Resolver']['nameservers'].split(',')]
    dns_resolver.nameservers = name_servers
    # 初始化全局TTL
    if int(config['Common']['global_ttl']) <= 0:
        # 默认全局TTL为60秒
        global_TTL = datetime.timedelta(seconds=60)
    else:
        global_TTL = datetime.timedelta(seconds=int(config['Common']['global_ttl']))

    if float(config['Common']['buffer_check_rate']) <= 0 or  \
            float(config['Common']['buffer_check_rate']) > 1:
        global_buffer_check_rate = 0.2
    else:
        global_buffer_check_rate = float(config['Common']['buffer_check_rate'])

    if int(config['Common']['buffer_check_interval']) <= 0:
        # 默认检查间隔为30秒
        global_buffer_check_interval = 20
    else:
        global_buffer_check_interval = int(config['Common']['buffer_check_interval'])


    print('global ttl = {}'.format(str(global_TTL)))

    # 创建UDP监听
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        udp_sock.bind(('', int(config['Common']['local_dns_port'])))
        ldns_logger.logger.info("Successfully binded port {}".format(config['Common']['local_dns_port']))
    except Exception as e:
        ldns_logger.logger.error(str(e.args))

    if int(config['Common']['dns_workers']) <= 0:
        pool = multiprocessing.dummy.Pool(processes=8)
    else:
        pool = multiprocessing.dummy.Pool(processes=int(config['Common']['dns_workers']) + 1)

    pool.apply_async(regular_check_expired_keys, args=())

    while True:
        try:

            # 循环的从服务端口监听dns报文
            msg, addr = udp_sock.recvfrom(8192)
            ldns_logger.logger.info('received request')
            pool.apply_async(dns_handler, args=(udp_sock, msg, addr))

        except Exception as e:
            print(e.args)
