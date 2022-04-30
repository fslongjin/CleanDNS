# CleanDNS

一个干净不受本地污染的轻量级DNS服务器

## 它有什么用？

    在现实网络环境中，可能存在着DNS篡改、劫持的现象，导致我们的网页请求被重定向到不正确的网址。有时候dns污染还会导致网站打不开、访问速度慢的现象。在这种环境下，直接在电脑/手机上设置DNS服务器并不一定有用，因为，您的解析请求很可能根本无法到达公共DNS服务器（被LocalDNS劫持了）。

    CleanDNS则是一个轻量级的本地DNS服务器，它能够绕开被污染的解析链路，直达国内的公共DNS，为本地的网络设备提供干净的LocalDNS服务。

## 原理

CleanDNS使用了DoH来访问公共DNS服务器，DoH是基于Https的dns请求方式，而不是使用传统的DNS递归解析。因此Local DNS服务器无法污染CleanDNS向公共DNS服务器发起的请求。从而实现了绕开LocalDNS的目的。

## 特性

- 轻量化，只需安装少数的库即可运行

- 响应迅速

- 具有基本的dns缓存及清理策略

- 支持自定义设置公共DNS（默认使用DNSPod）

## 如何使用？

首先，修改config.ini，将其中的local_dns_port设置为53

然后，在系统设置中将dns服务器设置为127.0.0.1

接着根据系统的区别，执行以下命令：

### Windows

```
git clone https://github.com/fslongjin/CleanDNS
cd CleanDNS
pip install -r requirements.txt
python main.py
```

### Linux

```
git clone https://github.com/fslongjin/CleanDNS
cd CleanDNS
pip install -r requirements.txt
sudo su root
python main.py
```

## 免责声明

本项目在开放源代码许可证的基础上进行开源，为防止项目被滥用，特此提出额外的免责声明：

**本项目仅可用于连接国内的公共DNS，以实现防劫持的功能。本项目不可被滥用作其他用途，否则一切后果与本项目无关！**
