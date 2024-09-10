from datetime import datetime
from flask import render_template, request
from run import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
from datetime import datetime
from flask import render_template, request
from run import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response

import requests
from lxml import html
import lxml.etree as etree

@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return render_template('index.html')


@app.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if 'action' not in params:
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']

    # 执行自增操作
    if action == 'inc':
        counter = query_counterbyid(1)
        if counter is None:
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
        else:
            counter.id = 1
            counter.count += 1
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
        return make_succ_response(counter.count)

    # 执行清0操作
    elif action == 'clear':
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response('action参数错误')


@app.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    counter = Counters.query.filter(Counters.id == 1).first()
    return make_succ_response(0) if counter is None else make_succ_response(counter.count)

def extract_info(tree, xpath, get_html=False):
    elements = tree.xpath(xpath)
    if elements:
        if get_html:
            return etree.tostring(elements[0], encoding='unicode', method='html')
        elif isinstance(elements[0], str):
            return elements[0].strip()
        elif isinstance(elements[0], html.HtmlElement):
            return ' '.join(elements[0].xpath('.//text()')).strip()
        else:
            return str(elements[0]).strip()
    return ''

@app.route('/api/searchibsn/<isbn>', methods=['GET'])
def search_isbn(isbn):
    url = f'https://book.douban.com/isbn/{isbn}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        tree = html.fromstring(response.content)

        book_info = {
            "书名":  extract_info(tree,'//h1/span[@property="v:itemreviewed"]/text()'),
            "作者":  extract_info(tree,"//span[@class='pl'][contains(text(),'作者')]/following-sibling::*[1][not(self::br)]//text()"),
            "出版社":  extract_info(tree,"//span[@class='pl'][contains(text(),'出版社')]/following-sibling::*[1][not(self::br)]//text()"),
            "出品方":  extract_info(tree,"//span[@class='pl'][contains(text(),'出品方')]/following-sibling::*[1][not(self::br)]//text()"),
            "副标题":  extract_info(tree,"(//span[@class='pl'][contains(text(),'副标题')]/following-sibling::text())[1]"),
            "原作名":  extract_info(tree,"(//span[@class='pl'][contains(text(),'原作名')]/following-sibling::text())[1]"),
            "译者":  extract_info(tree,"//span[@class='pl'][contains(text(),'译者')]/following-sibling::*[1][not(self::br)]//text()"),
            "出版年":  extract_info(tree,"(//span[@class='pl'][contains(text(),'出版年')]/following-sibling::text())[1]"),
            "页数":  extract_info(tree,"(//span[@class='pl'][contains(text(),'页数')]/following-sibling::text())[1]"),
            "定价":  extract_info(tree,"(//span[@class='pl'][contains(text(),'定价')]/following-sibling::text())[1]"),
            "装帧":  extract_info(tree,"(//span[@class='pl'][contains(text(),'装帧')]/following-sibling::text())[1]"),
            "丛书":  extract_info(tree,"//span[@class='pl'][contains(text(),'丛书')]/following-sibling::*[1][not(self::br)]//text()"),
            "主图":  extract_info(tree,"//div[@id='mainpic']/a[@class='nbg']/img/@src"),
            "作者简介":  extract_info(tree,"//h2/span[text()='作者简介']/../following-sibling::div[1]//div[@class='intro']"),
            "图书简介": extract_info(tree, "//span[@class='all hidden']//div[@class='intro']", get_html=True)
        }

        return make_succ_response(book_info)

    except requests.RequestException as e:
        return make_err_response(f"Error fetching book data: {str(e)}")
