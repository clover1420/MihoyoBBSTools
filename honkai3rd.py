import time
import tools
import config
import random
import setting
from request import http
from loghelper import log
from error import CookieError


class Honkai3rd:
    def __init__(self) -> None:
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'DS': tools.get_ds(web=True, web_old=True),
            'Origin': 'https://webstatic.mihoyo.com',
            'x-rpc-app_version': setting.mihoyobbs_Version_old,
            'User-Agent': 'Mozilla/5.0 (Linux; Android 9; Unspecified Device) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Version/4.0 Chrome/39.0.0.0 Mobile Safari/537.36 miHoYoBBS/2.3.0',
            'x-rpc-client_type': setting.mihoyobbs_Client_type_web,
            'Referer': f'https://webstatic.mihoyo.com/bh3/event/euthenia/index.html?bbs_presentation_style=fullscreen'
                       f'&bbs_game_role_required=bh3_cn&bbs_auth_required=t'
                       f'rue&act_id={setting.honkai3rd_Act_id}&utm_source=bbs&utm_medium=mys&utm_campaign=icon',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,en-US;q=0.8',
            'X-Requested-With': 'com.mihoyo.hyperion',
            "Cookie": config.mihoyobbs_Cookies,
            'x-rpc-device_id': tools.get_device_id()
        }
        self.acc_List = self.get_account_list()
        self.sign_day = 0

    # 获取绑定的账号列表
    def get_account_list(self) -> list:
        log.info("正在获取米哈游账号绑定的崩坏3账号列表...")
        temp_list = []
        req = http.get(setting.honkai3rd_Account_info_url, headers=self.headers)
        data = req.json()
        if data["retcode"] != 0:
            log.warning("获取账号列表失败！")
            config.honkai3rd_Auto_sign = False
            config.save_config()
            raise CookieError("BBS Cookie Error")
        for i in data["data"]["list"]:
            temp_list.append([i["nickname"], i["game_uid"], i["region"]])
        log.info(f"已获取到{len(temp_list)}个崩坏3账号信息")
        return temp_list

    # 获取今天已经签到了的dict
    def get_today_item(self, raw_data: list):
        # 用range进行循环，当status等于0的时候上一个就是今天签到的dict
        for i in range(len(raw_data)):
            if raw_data[i]["status"] == 0:
                self.sign_day = i - 1
                return raw_data[i - 1]
            self.sign_day = i
            if raw_data[i]["status"] == 1:
                return raw_data[i]
            if i == int(len(raw_data) - 1) and raw_data[i]["status"] != 0:
                return raw_data[i]

    # 判断签到
    def is_sign(self, region: str, uid: str):
        req = http.get(setting.honkai3rd_Is_signurl.format(setting.honkai3rd_Act_id, region, uid), headers=self.headers)
        data = req.json()
        if data["retcode"] != 0:
            log.warning("获取账号签到信息失败！")
            print(req.text)
            exit(1)
        today_item = self.get_today_item(data["data"]["sign"]["list"])
        if today_item["status"] == 1:
            return True
        else:
            return False

    # 签到
    def sign_account(self):
        return_data = "崩坏3："
        if len(self.acc_List) != 0:
            for i in self.acc_List:
                log.info(f"正在为舰长{i[0]}进行签到...")
                time.sleep(random.randint(2, 8))
                is_data = self.is_sign(region=i[2], uid=i[1])
                if is_data:
                    time.sleep(random.randint(2, 8))
                    req = http.post(url=setting.honkai3rd_SignUrl, headers=self.headers,
                                    json={'act_id': setting.honkai3rd_Act_id, 'region': i[2], 'uid': i[1]})
                    data = req.json()
                    if data["retcode"] == 0:
                        today_item = self.get_today_item(data["data"]["list"])
                        log.info(f"舰长{i[0]}签到成功~\r\n今天获得的奖励是{tools.get_item(today_item)}")
                    elif data["retcode"] == -5003:
                        # 崩坏3应为奖励列表和签到信息在一起了，加上上面已经可以进行了一次判断，所以这里旧不重复再次执行判断来获取内容了
                        log.info(f"舰长{i[0]}今天已经签到过了~")
                    else:
                        log.warning("账号签到失败！")
                        print(req.text)
                else:
                    log.info(f"舰长{i[0]}今天已经签到过了~\r\n今天获得的奖励是{tools.get_item(today_item)}")
            if is_data["is_sign"] or data["retcode"] == 0 or data["retcode"] == -5003:
                return_data += f"\n{i[0]}已连续签到{self.sign_day}天\n今天获得的奖励是{tools.get_item(today_item)}"
            else:
                return_data += f"\n{i[0]}，本次签到失败"
        else:
            log.warning("账号没有绑定任何崩坏3账号！")
            return_data += "\n并没有绑定任何崩坏3账号"
        return return_data
