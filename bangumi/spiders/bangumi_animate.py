# -*- coding: utf-8 -*-import re

import datetime
import re
import time
from collections import OrderedDict

from logbook import Logger
from scrapy import Selector, Request

from bangumi import db
from bangumi.Item.bangumi.animate import *
from bangumi.Item.bangumi.pic import *
from bangumi.spiders import SpiderDebug

logging = Logger("Animate Spider")


class BangumiAnimateSpider(scrapy.Spider):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # if not SpiderDebug:
        if False:
            self.collection = db['Id'] #db = connection['bangumi']
            id_list = [subject['bangumi_id'] for subject in self.collection.find({"bangumi_type": "animate"})]
            spided_id = [animate['bangumi_id'] for animate in db['Animate1'].find()]
            print(len(id_list),len(spided_id))
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            for animate_id in spided_id:
                if (animate_id != None):
                    id_list.remove(animate_id)

            self.start_urls = ['http://bangumi.tv/subject/%s' % subject_id for subject_id in
                               id_list]
        else:
            self.start_urls = ['https://bangumi.tv/subject/324']

    name = "bangumi_animate"
    allowed_domains = ["bangumi.tv"]
    start_urls = []

    # 获取番剧信息
    def parse(self, response):
        print(response.xpath('//title'))
        animate = AnimateItem()
        # Get animate bangumi_id
        animate['bangumi_id'] = get_field_value(
            response.selector.xpath('//*[@id="headerSubject"]/h1/a/@href').re('/subject/(\d+)'))
        if(animate['bangumi_id'] == None):
            animate['bangumi_id'] = str(response).strip().split('/')[-1][:-1]
            time.sleep(0.4)
        # Get animate name
        animate['name'] = get_field_value(response.selector.xpath('//*[@id="headerSubject"]/h1/a/text()').extract())
        # Get animate summary
        animate['summary'] = "".join(response.xpath('//*[@id="subject_summary"]/text()').extract()) if len(
            response.xpath('//*[@id="subject_summary"]/text()').extract()) != 0 else None
        # Get animate type
        animate['animate_type'] = get_field_value(response.xpath('//*[@id="headerSubject"]/h1/small/text()').extract())
        # Get animate cover
        animate['cover_prefix'] = 'animate'
        animate['cover_url'] = 'http:%s' % get_field_value(
            response.xpath('//*[@id="bangumiInfo"]/div/div/a/@href').extract())
        # Get animate info
        animate['score'] = float(response.xpath('//*[@class="number"]/text()').extract()[0])
        animate['rank'] = response.xpath('//*[@class="alarm"]/text()').extract()[0]
        animate['info'] = dict()
        for item in Selector(response=response).xpath('//*[@id="infobox"]/li'):
            animate_info_title = item.xpath('./span/text()').extract()[0][:-2]
            if animate_info_title == '放送开始':
                try:
                    animate['start_play'] = datetime.datetime.strptime(item.xpath('./text()').extract()[0], "%Y年%m月%d日")
                    continue
                except:
                    try:
                        animate['start_play'] = datetime.datetime.strptime(item.xpath('./text()').extract()[0],
                                                                           "%Y-%m-%d")
                        continue
                    except:
                        pass

            if animate_info_title == '中文名':
                try:
                    animate['chinese_name'] = get_field_value(item.xpath('./text()').extract())
                    continue
                except:
                    pass
            if animate_info_title == '话数':
                try:
                    animate['episode_count'] = int(get_field_value(item.xpath('./text()').extract()))
                    continue
                except:
                    pass
            animate['info'][animate_info_title] = list()
            li_content = (item.extract())
            # 处理获取信息
            if li_content.find('<a') == -1:
                # 去除多余信息
                li_content = re.sub('<span class="tip">(.*?)</span>', "", li_content)
                li_content = re.sub("<.*?>", "", li_content)

                if li_content.find("、") != -1:
                    value_text_set = li_content.split("、")
                    for i in value_text_set:
                        animate['info'][animate_info_title].append(i)

                else:
                    animate['info'][animate_info_title].append(li_content)
            else:
                for value in item.xpath('.//a/text()').extract():
                    animate['info'][animate_info_title].append(value)
        tag_field = response.xpath('//*[@class="subject_detail"]//div[@class="inner"]//span/text()').extract()
        # animate['tag'] = [tag.extract() for tag in tag_field]
        animate['tag'] = response.xpath('//*[@class="subject_tag_section"]//div[@class="inner"]//span/text()').extract()
        logging.debug(animate)
        request = scrapy.Request('http://bangumi.tv/subject/%s/persons' % animate['bangumi_id'],
                                 callback=self.parse_cast)
        request.meta['animate_data'] = animate
        # 获取番剧剧集信息
        return request

    def parse_cast(self, response):
        animate = response.meta['animate_data']
        cast_set_field = Selector(response).xpath('//*[@id="columnInSubjectA"]/div[@class = "light_odd clearit"]')
        animate['cast'] = list()
        for cast_item_field in cast_set_field:
            cast = AnimateCastItem()
            cast['bangumi_id'] = get_field_value(cast_item_field.xpath('.//h2/a').re('/person/(\d+)'))
            cast['japan_name'] = cast_item_field.xpath('.//h2/a/text()').extract()[0].replace(" / ", "")
            cast['chinese_name'] = get_field_value(cast_item_field.xpath('.//h2/a/span/text()').extract())
            cast['job'] = list()
            for job in cast_item_field.xpath('.//div[@class = "prsn_info"]//span[@class = "badge_job"]/text()'):
                cast['job'].append(job.extract())
            animate['cast'].append(cast)
        request = scrapy.Request('http://bangumi.tv/subject/%s/characters' % animate['bangumi_id'],
                                 callback=self.parse_character)
        request.meta['animate_data'] = animate
        return request

    def parse_character(self, response):
        animate = response.meta['animate_data']
        animate['character'] = list()
        character_field = Selector(response).xpath('//*[@id="columnInSubjectA"]')
        for character in character_field.xpath('.//div[@class="clearit"]'):
            character_item = AnimateCharacterItem()
            character_item['bangumi_id'] = get_field_value(character.re('<a href="/character/(\d+)" class="l">'))
            character_item['japan_name'] = get_field_value(character.xpath('./h2/a/text()').extract())
            try:
                character_item['chinese_name'] = get_field_value(character.xpath('./h2/span/text()').extract())[3:]
            except:
                character_item['chinese_name'] = None
            character_item['job'] = get_field_value(character.re('<span class="badge_job">(.*?)</span>'))
            character_item['info'] = dict()
            character_info = character.xpath('./div[@class = "crt_info"]').re('<span class="tip_j">(.*?)</span> (\S+)')
            for cur in range(0, len(character_info), 2):
                character_item['info'][character_info[cur]] = character_info[cur + 1]

            # cv information
            character_item['cv'] = list()
            for cv_list in character.xpath('.//div[@class = "actorBadge clearit"]/p'):
                cv = AnimateCharacterCVItem()
                cv['bangumi_id'] = cv_list.re('<a href="/person/(\d+)" class="l">')[0]
                cv['japan_name'] = get_field_value(cv_list.xpath('./a/text()').extract())
                cv['chinese_name'] = get_field_value(cv_list.xpath('./small/text()').extract())
                character_item['cv'].append(cv)
            animate['character'].append(character_item)

        request = scrapy.Request('http://bangumi.tv/subject/%s/ep' % animate['bangumi_id'],
                                 callback=self.parse_episode)
        request.meta['animate_data'] = animate
        return request

    def parse_episode(self, response):
        animate = response.meta['animate_data']
        ep_field = Selector(response).xpath('//*[@id="columnInSubjectA"]/div/ul')
        cat = ep_field.xpath('.//li/@class').extract()
        cat_pos = [i for i, a in enumerate(cat) if a == 'cat']
        category_list = OrderedDict()
        category_name = ""
        for li_cur, item_li in enumerate(ep_field.xpath('.//li')):
            if li_cur in cat_pos:
                category_name = item_li.xpath('.//text()').extract()[0]
                category_list[category_name] = []
                continue
            else:
                ep_number = item_li.xpath('.//h6/a/text()').re('(\d+)\..*?')[0]
                ep_japan = item_li.xpath('.//h6/a/text()').extract()[0]
                ep_date = item_li.xpath('.//small/text()').re('(\d+-\d+-\d+)')
                if len(ep_date) == 0:
                    ep_date = ""
                else:
                    ep_date = ep_date[0]
                    try:
                        ep_date = datetime.datetime.strptime(ep_date, "%Y-%m-%d")
                    except:
                        ep_date = datetime.datetime.strptime('1970-01-01', "%Y-%m-%d")
                ep_japan = re.sub('\d+\.(.*?)', "", ep_japan)

                ep_chinese = item_li.xpath('.//span[@class = "tip"]/text()')
                if len(ep_chinese) == 0:
                    ep_chinese = ""
                else:
                    ep_chinese = ep_chinese.extract()[0][3:]
                ep = AnimateEpisodeItem(
                    number=ep_number,
                    japan_name=ep_japan,
                    chinese_name=ep_chinese,
                    show_date=ep_date
                )
                category_list[category_name].append(ep)
        animate['episode'] = category_list
        request = scrapy.Request('http://bangumi.tv/subject/%s/comments' % animate['bangumi_id'],
                                 callback=self.parse_comment)
        request.meta['animate_data'] = animate
        return request

    def parse_comment(self, response):
        animate = response.meta['animate_data']
        pages = int(response.xpath('//*[@class="p_edge"]/text()').extract()[0].replace('\xa0','').split('/')[1][:-1])
        animate['comments'] = list()
        for i in range(1,pages+1):
            nexturl = 'http://bangumi.tv/subject/{}/comments?page={}'.format(animate['bangumi_id'],i)
            yield scrapy.Request(nexturl, callback = self.parse_comments, meta = response.meta)
            # request.meta['animate_data'] = animate
        return animate

    def parse_comments(self, response):
        animate = response.meta['animate_data']
        username = response.xpath('//*[@id="comment_box"]//a/text()').extract()
        score = response.xpath('//*[@id="comment_box"]//div/div/span').re('<span class="sstars(.*?) starsinfo')
        text = response.xpath('//p/text()').extract()
        z = zip(username,score,text)
        temp = [dict(username=a,score=b,text=c) for a,b,c in list(z)]
        animate['comments'].extend(temp)
        x = [dict(username=a,score=b,text=c) for a,b,c in list(z)]
        return animate

def get_field_value(selector, index=0):
    return selector[index] if len(selector) != 0 else None
