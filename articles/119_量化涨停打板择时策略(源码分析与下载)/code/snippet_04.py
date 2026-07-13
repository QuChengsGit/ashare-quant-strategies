import os：文件/路径操作（生成/写入配置与池文件）。

import sys：保留系统参数等（虽未显式使用，但与 Notebook 兼容场景常用）。

import json：读写涨停价字典 JSON 文件。

import time：主循环中微睡眠，降低 CPU 占用。

import random：生成股票池、行情、价格/队列的随机化模拟。

import threading：账户更新时加锁，保障并发安全。

import argparse：命令行参数解析，兼容 parse_known_args。

import configparser：读写 ini 配置（qmt_path、账号、每笔金额）。

from datetime import datetime, timedelta：时间戳、窗口推进与比较。

from collections import deque, defaultdict：高效队列缓存与默认字典（持仓/均价/缓存）。
