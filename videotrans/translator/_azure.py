# -*- coding: utf-8 -*-
import re
from typing import Union, List

import httpx,requests
from openai import AzureOpenAI, APIConnectionError

from videotrans.configure import config
from videotrans.translator._base import BaseTrans
from videotrans.util import tools


class AzureGPT(BaseTrans):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prompt = tools.get_prompt(ainame='azure',is_srt=self.is_srt).replace('{lang}', self.target_language)
        self._check_proxy()
        self.model_name=config.params["azure_model"]
        
    def _check_proxy(self):
        try:
            c=httpx.Client(proxies=None)
            c.get(config.params["azure_api"])
        except Exception as e:
            pro = self._set_proxy(type='set')
            if pro:
                self.proxies = {"https://": pro, "http://": pro}        

    def _item_task(self, data: Union[List[str], str]) -> str:
        model = AzureOpenAI(
            api_key=config.params["azure_key"],
            api_version=config.params['azure_version'],
            azure_endpoint=config.params["azure_api"],
            http_client=httpx.Client(proxies=self.proxies)
        )
        message = [
            {'role': 'system',
             'content': "You are a professional, helpful translation engine that translates only the content in <source> and returns only the translation results" if config.defaulelang != 'zh' else '您是一个有帮助的翻译引擎，只翻译<source>中的内容，并只返回翻译结果'},
            {'role': 'user',
             'content': self.prompt.replace('[TEXT]',
                                            "\n".join([i.strip() for i in data]) if isinstance(data, list) else data)},
        ]

        config.logger.info(f"\n[AzureGPT]请求数据:{message=}")
        try:
            response = model.chat.completions.create(
                model=config.params["azure_model"],
                messages=message
            )
        except APIConnectionError:
            raise requests.ConnectionError('Network connection failed')
        config.logger.info(f'[AzureGPT]返回响应:{response=}')

        if response.choices:
            result = response.choices[0].message.content.strip()
        else:
            config.logger.error(f'[AzureGPT]请求失败:{response=}')
            raise Exception(f"no choices:{response=}")
        result = result.replace('##', '').strip().replace('&#39;', '"').replace('&quot;', "'")
        return re.sub(r'\n{2,}', "\n", result)
