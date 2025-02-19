#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from src.api.get_json import config
from asyncio.log import logger
from urllib import response
import pytest
from jira import JIRA
from datetime import datetime as dt
import time
from src.api.log import log  # 封装日志引入
from src.api.feishu_robot_push import feishu_robot  # 飞书机器人引入
from src.api.feishu_sign import sign# 飞书签名
# 日志实例化
logger = log().logger()
# 读取配置文件
Config = config("../../config/config.json").get_config_from_json()
UserInfo = config("../../config/userInfo.json").get_config_from_json()
# jira初始化
jira = JIRA(auth=(Config["jira"]["username"], Config["jira"]
            ["password"]), options={'server': Config["jira"]["url"]})
# 飞书签名
from src.api.feishu_sign import sign
timestamp = str(round(time.time()))
secret = Config["feishu"]["secret"]
sign=sign(timestamp,secret).gen_sign()



@pytest.mark.skip
def test():
    # 查询问题，支持JQL语句
    open_issues = jira.search_issues(
        'status = 激活 AND creator in ("liyc") ORDER BY priority DESC, updated DESC', maxResults=-1)
    # 激活、已关闭、已解决
    # 注意：如果不加maxResults=-1参数，则实际总数大于50时只能查出50条数据。
    print("open_issues:", open_issues)
    print("open_issues:", len(open_issues))


@pytest.mark.test
def test_feishu_post():
    # 存放jira bug list
    result = []
    # 读取人员名单
    workers = UserInfo["userInfo"]
    # 初始化迭代
    i = 0
    k = 0
    # 遍历人员名单
    for worker in workers:
        # 注意：如果不加maxResults=-1参数，则实际总数大于50时只能查出50条数据。
        open_issues = jira.search_issues(
            'status = 激活 AND creator in ("'+worker["username"]+'") ORDER BY priority DESC, updated DESC', maxResults=-1)
        # 日志输出
        logger.info('【{}】{}'.format(worker["username"], open_issues))
        # 放入第一层数据
        result.append([
            {"username": worker["username"]},
            {"name": worker["name"]},
            {"open":[]}, # 激活状态bug list
            {"resolved":[]} # 已解决状态bug list
        ])
        """
            result的数据格式：
            [[{"username":"zhanggsan"},{"name":"张三"},{"open":[{"key":xxx,"id":xxx},{"key":xxx,"id":xxx}],"resolved":[{"key":xxx,"id":xxx},{"key":xxx,"id":xxx}]}],
            [{"username":"lisi"},{"name":"李四"},{"open":[{"key":xxx,"id":xxx},{"key":xxx,"id":xxx}],"resolved":[{"key":xxx,"id":xxx},{"key":xxx,"id":xxx}]}],
            [{"username":"wangwu"},{"name":"王五"},{"open":[{"key":xxx,"id":xxx},{"key":xxx,"id":xxx}],"resolved":[{"key":xxx,"id":xxx},{"key":xxx,"id":xxx}]}]]
        """
        # 放入第一层数据open节点中
        for index in range(len(open_issues)):
            print("result[{}]][2]".format(i),result[i][2])
            (result[i][2])['open'].append({
                "key": open_issues[index].key,
                "id": open_issues[index].id,
                "url": Config["jira"]["url_browse"]+open_issues[index].key,
            })
        resolved_issues = jira.search_issues('status = 已解决 AND creator in ("'+worker["username"]+'") ORDER BY priority DESC, updated DESC', maxResults=-1)
        # 日志输出
        logger.info('【{}】{}'.format(worker["username"], resolved_issues))
        # 放入第一层数据resolved节点中
        for index in range(len(resolved_issues)):
            print("result[{}][3]".format(i),result[i][3])
            (result[i][3])['resolved'].append({
                "key": resolved_issues[index].key,
                "id": resolved_issues[index].id,
                "url": Config["jira"]["url_browse"]+resolved_issues[index].key,
            })
        i += 1
    logger.info('result' + str(result))
    
    """
        result的数据格式：
        [[{"username":"zhanggsan"},{"name":"张三"},{"open":[{"key":xxx,"id":xxx},{"key":xxx,"id":xxx}],"resolved":[{"key":xxx,"id":xxx},{"key":xxx,"id":xxx}]}],
        [{"username":"lisi"},{"name":"李四"},{"open":[{"key":xxx,"id":xxx},{"key":xxx,"id":xxx}],"resolved":[{"key":xxx,"id":xxx},{"key":xxx,"id":xxx}]}],
        [{"username":"王五"},{"name":"王五"},{"open":[{"key":xxx,"id":xxx},{"key":xxx,"id":xxx}],"resolved":[{"key":xxx,"id":xxx},{"key":xxx,"id":xxx}]}]]
    """
    # 遍历result 依次调用飞书机器人发送结果
    i = 0
    for j in result:
        #
        # logger.info("j数据类型："+ str(type(j)))  # <class 'list'>
        # 姓名
        logger.info("姓名:" + j[1]['name'])
        logger.info("open bug：" + str(len(j[2]["open"])-1))
        logger.info("resolved bug:" + str(len(j[3]["resolved"])-1))
        
        message_body = {
            "timestamp": timestamp,
            "sign": sign,
            "msg_type": "post",  # 消息类型 包括：text、post、image、file、audio、media、sticker、interactive、share_chat、share_user等，类型定义请参考发送消息content说明:https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/im-v1/message/create_json
            "content":
            {
                "post":  {
                    "zh_cn": {
                        "title": "JIRA bug 日常提醒【{}】【{}】".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), j[1]['name']),
                        "content": [
                            [{
                                "tag": "text",
                                "text": "未处理：{}".format(len(j[2]["open"])-1),
                            },
                                {
                                "tag": "a",
                                "href": "https://jira.homeking365.com/browse/S5A-1924?filter=10818&jql=status = {} AND assignee in ({}) ORDER BY priority DESC, updated DESC".format("激活", j[0]['username']),
                                "text": "点击查看"
                            }],
                            [{
                                "tag": "text",
                                "text": "已解决：{}".format(len(j[3]["resolved"])-1),
                            },
                                {
                                "tag": "a",
                                "href": "https://jira.homeking365.com/browse/S5A-1924?filter=10818&jql=status = {} AND assignee in ({}) ORDER BY priority DESC, updated DESC".format("已解决", j[0]['username']),
                                "text": "点击查看"
                            }],
                            # [{
                            #     "tag": "text",
                            #     "text": "已关闭：{}".format(len(j)-1),
                            # },
                            #     {
                            #     "tag": "a",
                            #     "href": "https://jira.homeking365.com/browse/S5A-1924?filter=10818&jql=status = {} AND assignee in ({}) ORDER BY priority DESC, updated DESC".format("已关闭", j[0]['username']),
                            #     "text": "点击查看"
                            # }],
                            # [
                            #     {
                            #         "tag": "at",
                            #         "user_id": "all",
                            #         "user_name": " 所有人 "
                            #     }
                            # ],
                            # [{
                            #     "tag": "img",
                            #     "image_key": "img_7ea74629-9191-4176-998c-2e603c9c5e8g",
                            #     "width": 100,
                            #     "height": 100
                            # }]
                        ]
                    },
                }}
        }
        i += 1
        # 发送飞书机器人
        response_message = feishu_robot(
            Config["feishu"]["webhook"], message_body).push()
        logger.info(response_message)


@pytest.mark.skip
def test_feishu_text():
    # 飞书机器人群关键字
    key_word = "jira"
    # 发送内容
    message_body = {
        "msg_type": "text",
        "content": {"text": key_word + "你要发送的消息"}
    }
    # 发送飞书机器人
    response_message = feishu_robot(
        Config["feishu"]["webhook"], message_body).push()
    logger.info(response_message)
