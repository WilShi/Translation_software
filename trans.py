#! -*- coding: utf-8 -*-

from datetime import datetime
import html
import random
import re
from sys import argv
import time
import requests
import json

from io import StringIO
from concurrent import futures
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import process_pdf
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams


from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkcore.auth.credentials import AccessKeyCredential
from aliyunsdkcore.auth.credentials import StsTokenCredential
from aliyunsdkalimt.request.v20181012.TranslateRequest import TranslateRequest



# need install "pdfminer3k"

class lang():
    def __init__(self, dic={}, translateFrom='google') -> None:
        self.dic = dic if dic else {}
        self.translateFrom = translateFrom


    def check_zh(self, word):

        xx = u"([\u4e00-\u9fff]+)"
        pattern = re.compile(xx)
        results = pattern.findall(word)

        enxx = u"([a-zA-Z0-9.\(\)\[\]\_\-]+)"
        enpattern = re.compile(enxx)
        ens = enpattern.findall(word)
        
        if results and not ens:
            return True
        if ens and not results:
            return False
        else:
            zh = ''.join(results)
            return False if len(ens) > len(zh) else True


    def translate(self, word, from_='zh', to_='en'):

        from_ = 'zh' if self.check_zh(word) else 'en'
        to_ = 'en' if from_ == 'zh' else 'zh'

        if word in self.dic:
            wd = {from_: word, to_: self.dic[word][2], "key": "{}_".format(self.tag) + self.dic[word][2].replace(' ', '_')}
            return wd
        
        if self.translateFrom == "google":
            gfrom_ = 'zh-CN' if from_ == 'zh' else from_
            to_ = 'zh-CN' if to_ == 'zh' else to_

            # 使用Google翻译翻译单词
            translateApi = "http://translate.google.cn/m?q=%s&tl=%s&sl=%s" % (word, to_, gfrom_)
            try:
                info = requests.get(translateApi)
            except Exception as error:
                time.sleep(1)
                info = requests.get(translateApi)
            data = info.text
            expr = r'(?s)class="(?:t0|result-container)">(.*?)<'
            result = re.findall(expr, data)

            res = html.unescape(result[0])

            
        elif self.translateFrom == "deepl":
            proxies = {
                'https': 'http://127.0.0.1:41091'
            }

            word = '"' + word + '"'
            u_sentence = word.encode("unicode_escape").decode()
            data = '{"\
                jsonrpc":"2.0",\
                "method": "LMT_handle_jobs",\
                "params":\
                    {"jobs":[\
                        {"kind":"default",\
                        "raw_en_sentence":' + word + ',\
                        "raw_en_context_before":[],\
                        "raw_en_context_after":[],\
                        "preferred_num_beams":4,\
                        "quality":"fast"}\
                        ],\
                    "lang":{"user_preferred_langs":["EN","ZH"],\
                            "source_lang_computed":"ZH",\
                            "target_lang":"EN"\
                            },\
                    "priority": 1,\
                    "commonJobParams":{},\
                    "timestamp":' + str(int(time.time() * 10000)) + \
                    '},\
                "id":' + str(random.randint(1, 100000000)) + '}'

            r = requests.post('https://www2.deepl.com/jsonrpc',
                            headers={'content-type': 'application/json'},
                            data=data.encode(),
                            proxies=proxies)

            print(r.status_code)
            if r.status_code != 200:
                print(r.text)
                res = False
            else:
                res =  r.json()['result']['translations'][0]['beams'][0]['postprocessed_sentence']

        return res


    
    def ip_proxy(self):
        ip_pool = [
            '119.98.44.192:8118',
            '111.198.219.151:8118',
            '101.86.86.101:8118',
            '111.155.124.78:8123'
        ]

        ip = ip_pool[random.randrange(0,4)]
        proxy_ip = 'http://'+ip
        proxies = {'http':proxy_ip}
        return proxies

    # 解析pdf文件
    def read_from_pdf(self, file_path):
        with open(file_path, 'rb') as file:
            resource_manager = PDFResourceManager()
            return_str = StringIO()
            lap_params = LAParams()
            device = TextConverter(
                resource_manager, return_str, laparams=lap_params)
            process_pdf(resource_manager, device, file)
            device.close()
            content = return_str.getvalue()
            return_str.close()
            return content

    # 将输入的data返回成为段落组成的列表
    def clean_data(self, data):
        data = data.replace('\n\n', '$#$')
        data = data.replace('\n', ' ')
        return data.split('$#$')

    def trans_doc(self, path, outpath):
        if ".pdf" in path:
            words = self.read_from_pdf(path)
            words_list = self.clean_data(words)

            with futures.ThreadPoolExecutor(4) as excuter:
                zh_txt = excuter.map(self.translate, words_list)
            # zh_txt = [translate(txt) for txt in data_list]
            zh_txt = list(zh_txt)
            article = '\n\n'.join(zh_txt)

            print(article)
            # print(article)
            # with open(outpath, 'w', encoding='utf-8') as f:
            #     f.write(article)



class Translate():

    def __init__(self) -> None:

        """使用了阿里云的翻译接口，QPS为50次/秒。请务必控制使用频率，避免接口被封！！！！！！"""
        self.credentials = AccessKeyCredential('LTAI5t7Qdn7tm4Ky4CFMryuD', 'AMlzEjLGkQygr21uzUkHQeTOE50K6s')# 狗哥的阿里云密钥
        # use STS Token
        # credentials = StsTokenCredential('<your-access-key-id>', '<your-access-key-secret>', '<your-sts-token>')
        self.client = AcsClient(region_id='cn-hangzhou', credential=self.credentials)

        pass


    def translate_cn_en(self, word, showOutput=True) -> str:

        """使用了阿里云的翻译接口，QPS为50次/秒。请务必控制使用频率，避免接口被封！！！！！！"""
        # credentials = AccessKeyCredential('LTAI5t7Qdn7tm4Ky4CFMryuD', 'AMlzEjLGkQygr21uzUkHQeTOE50K6s')# 狗哥的
        # # use STS Token
        # # credentials = StsTokenCredential('<your-access-key-id>', '<your-access-key-secret>', '<your-sts-token>')
        # client = AcsClient(region_id='cn-hangzhou', credential=credentials)

        request = TranslateRequest()
        request.set_accept_format('json')

        request.set_FormatType("text")
        request.set_TargetLanguage("en")
        request.set_SourceLanguage("zh")
        request.set_SourceText(word)
        request.set_Scene("communication")

        response = self.client.do_action_with_exception(request)
        response_data = json.loads( str(response, encoding='utf-8') )

        # print(response_data)

        if response_data['Code'] != '200': return ''
        
        en_word = response_data['Data']['Translated']

        if showOutput:
            # print(f"** 成功将 {word} 翻译成: {en_word} **")
            self.out_message(word, en_word)

        return en_word


    def translate(self, word, sl='en', tl='zh', showOutput=True) -> str:
        request = TranslateRequest()
        request.set_accept_format('json')

        request.set_FormatType("text")
        request.set_TargetLanguage(tl)
        request.set_SourceLanguage(sl)
        request.set_SourceText(word)
        request.set_Scene("communication")

        response = self.client.do_action_with_exception(request)
        response_data = json.loads( str(response, encoding='utf-8') )

        # print(response_data)

        if response_data['Code'] != '200': return ''
        
        tran_word = response_data['Data']['Translated']

        if showOutput:
            # print(f"** 成功将 {word} 翻译成: {en_word} **")
            self.out_message(word, tran_word)

        return tran_word


    def autoLang(self, word):
        lc = lang()

        sl = 'zh' if lc.check_zh(word) else 'en'
        tl = 'en' if sl == 'zh' else 'zh'

        return self.translate(word, sl, tl, showOutput=False)


    def out_message(self, word, tran):
        print( f"\n{word} ｜===>| {tran}\n" )
    




if __name__ == "__main__":


    # res = lang(translateFrom='google').translate(argv[1])
    # print(res)

    lang(translateFrom='google').trans_doc(argv[1], '')

