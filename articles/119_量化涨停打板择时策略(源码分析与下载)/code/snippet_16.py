# sim_limit_up_strategy.py
# -*- coding: utf-8 -*-
"""
打板策略
- 行情：一字→炸板→回封，含买一封单与被吃速度（用于模拟封单消化速度）
- 策略：09:30–10:00 触板 + 回封/动量过滤 + 队列合理性；限价(涨停价)排队，超时撤单
- 兼容 Notebook：忽略未知参数（如 ipykernel 注入的 -f kernel.json）
"""
import os
import sys
import json
import time
import random
import threading
import argparse
import configparser
from datetime import datetime, timedelta
from collections import deque, defaultdict
