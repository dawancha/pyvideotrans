# -*- coding: utf-8 -*-
import re
from typing import Union, List

import requests
from requests import JSONDecodeError

from videotrans.configure import config
from videotrans.translator._base import BaseTrans
from videotrans.util import tools


class HuoShan(BaseTrans):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.proxies = {"http": "", "https": ""}
        self.prompt = tools.get_prompt(ainame='zijie',is_srt=self.is_srt).replace('{lang}', self.target_language)
        self.model_name=config.params["zijiehuoshan_model"] 
    def _item_task(self, data: Union[List[str], str]) -> str:
        message = [
            {'role': 'system',
             'content': "You are a professional, helpful translation engine that translates only the content in <source> and returns only the translation results" if config.defaulelang != 'zh' else '您是一个有帮助的翻译引擎，只翻译<source>中的内容，并只返回翻译结果'},
            {'role': 'user',
             'content': self.prompt.replace('[TEXT]',
                                            "\n".join([i.strip() for i in data]) if isinstance(data, list) else data)},
        ]
        config.logger.info(f"\n[字节火山引擎]发送请求数据:{message=}\n接入点名称:{config.params['zijiehuoshan_model']}")

        try:
            req = {
                "model": config.params['zijiehuoshan_model'],
                "messages": message
            }
            resp = requests.post("https://ark.cn-beijing.volces.com/api/v3/chat/completions",
                                 proxies=self.proxies, json=req, headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {config.params['zijiehuoshan_key']}"
                })
            if resp.status_code!=200:
                raise Exception(f'字节火山引擎请求失败: status_code={resp.status_code} {resp.reason}')
            config.logger.info(f'[字节火山引擎]响应:{resp.text=}')
            data = resp.json()
            if 'choices' not in data or len(data['choices']) < 1:
                raise Exception(f'字节火山翻译失败:{resp.text=}')
            result = data['choices'][0]['message']['content'].strip()
        except JSONDecodeError as e:
            raise Exception('字节火山翻译失败，返回数据不是有效json格式')
        else:
            return re.sub(r'\n{2,}', "\n", result)
