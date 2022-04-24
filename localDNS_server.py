import dns.message
import requests
from dns.resolver import Resolver
from dnslib import DNSRecord, RD, SOA, DNSHeader, RR, A, CNAME, QTYPE
import dns
import requests
import socket
from typing import cast

import multiprocessing.dummy
from queue import Queue

task_q = Queue()


from utils import get_logger, init_logging

init_logging('log_ldns.txt')
ldns_logger = get_logger()

dns_resolver = Resolver()

name_servers = []

def make_reply_for_A_record(received_record, ip_address, ttl=60):
    recv_data = A(received_record)


def resolve_A_record(domain):
    """
    解析A记录
    :param domain 目标域名
    :return:
    """
    domain = domain.lower().strip()

    for ns in name_servers:
        try:
            with requests.sessions.Session() as sess:
                query = dns.message.make_query(domain, dns.rdatatype.A)
                r = dns.query.https(query, ns, session=sess)
                for answer in r.answer:
                    print(answer)

                return r
        except Exception as e:
            ldns_logger.logger.error(str(e.args))
            print(e.args)


def resolve_record(domain, rdtype):
    """
    解析A记录
    :param domain 目标域名
    :return:
    """
    domain = domain.lower().strip()

    for ns in name_servers:
        try:
            with requests.sessions.Session() as sess:
                query = dns.message.make_query(domain, rdtype)
                r = dns.query.https(query, ns, session=sess)
                return r
        except Exception as e:
            ldns_logger.logger.error(str(e.args))
            print(e.args)

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
        qtype = 'A'
    except Exception as e:
        ldns_logger.logger.error(
            "Get QTYPE failed from address {}, error message:{}".format(address, str(e.args)))
        return

    # 获取目标域名
    #domain = str(recv_request.q.qname).strip('.')
    domain = str(recv_request.question[0].name)

    ldns_logger.logger.info("Resolving request from client [{}]: domain=[{}], qtype=[{}]".format(address, domain, qtype))

    #if qtype == 'A':
    #response = dns.message.make_response(resolve_A_record(domain))
    # response.flags |= dns.flags.AA
    response = resolve_record(domain, recv_request.question[0].rdtype)
    if response is None:
        response = dns.message.make_response(recv_request)

    #response = resolve_A_record(domain)
    response.id = recv_request.id

    response.question = [recv_request.question[0]]
    wire = response.to_wire(cast(dns.name.Name, response))
    udp_sock.sendto(wire, address)
    ldns_logger.logger.info("Successfully send response to client [{}], domain=[{}], qtype=[{}]".format(
                            address, domain, qtype))
    return

    ldns_logger.logger.info("Failed to send response to client [{}], domain=[{}], qtype=[{}]".format(
        address, domain, qtype))


def run(config):
    # 设置resolver的nameservers
    global name_servers
    name_servers = [x.strip() for x in config['Resolver']['nameservers'].split(',')]
    dns_resolver.nameservers = name_servers

    # 创建UDP监听
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        udp_sock.bind(('', int(config['Common']['local_dns_port'])))
        ldns_logger.logger.info("Successfully binded port {}".format(config['Common']['local_dns_port']))
    except Exception as e:
        ldns_logger.logger.error(str(e.args))

    pool = multiprocessing.dummy.Pool(processes=16)

    while True:
        try:

            # 循环的从服务端口监听dns报文
            msg, addr = udp_sock.recvfrom(8192)
            print('received')
            pool.apply_async(dns_handler, args=(udp_sock, msg, addr))

        except Exception as e:
            print(e.args)
