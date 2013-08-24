# -*- coding: utf-8 -*-
"""
    Библиотека для работы с сервисом Uniteller

    :copyright: (c) 2013 by Pavel Lyashkov.
    :license: BSD, see LICENSE for more details.
"""
import hashlib
import string
import csv
from console import app
from grab import Grab
from lxml import etree


class UnitellerApi(object):
    CODE_SUCCESS = 'AS000'

    STATUS_COMPLETE = 'Paid'
    STATUS_AUTH = 'Authorized'
    STATUS_CANCELED = 'Canceled'

    SUCCESS_NO = 0
    SUCCESS_YES = 1
    SUCCESS_ALL = 2

    EMPTY_ORDER = dict(
        order_id='',
        amount='',
        mean_type='',
        money_type='',
        life_time='',
        customer_id='',
        card_id='',
        l_data='',
        paymen_type='',
    )

    def __init__(self, const):
        self.const = const
        self.grab = None
        self.order_id = None
        self.success = self.SUCCESS_ALL
        self.shop_id = self.const.SHOP_ID
        self.password = self.const.PASSWORD
        self.login = self.const.LOGIN
        self.prefix = self.const.TEST and self.const.TEST_PREFIX or self.const.DEFAULT_PREFIX

    def __repr__(self):
        return "%s" % self.const

    def get_url(self, method):
        return "%s%s/%s/" % (self.prefix, self.const.GENERAL_URL, method)

    def get_sing(self, order):
        result = [hashlib.md5(str(value)).hexdigest() for value in order]

        return string.upper(hashlib.md5(str('&'.join(result))).hexdigest())

    def get_reccurent_sing(self, order):
        """Обязательные данные - order_id, amount, parent_order_id"""
        data = (
            self.shop_id,
            order['order_id'],
            order['amount'],
            order['parent_order_id'],
            self.password
        )

        return self.get_sing(data)

    def get_payment_sing(self, order):
        full_order = dict(self.EMPTY_ORDER, **order)
        data = (
            self.shop_id,
            full_order['order_id'],
            full_order['amount'],
            full_order['mean_type'],
            full_order['money_type'],
            full_order['life_time'],
            full_order['customer_id'],
            full_order['card_id'],
            full_order['l_data'],
            full_order['paymen_type'],
            self.password
        )

        return self.get_sing(data)

    def set_request(self, url, data=None):
        return_data = False

        if not self.grab:
            self.grab = Grab()

        if data:
            self.grab.setup(post=data)

        try:
            self.grab.go(url)
        except Exception as e:
            app.logger.error(e)
        else:
            return_data = self.grab

        return return_data

    def get_payment_info(self):
        return_data = False

        keys = (
            'ordernumber',
            'response_code',
            'total',
            'currency',
            'date',
            'billnumber',
            'status',
            'cardnumber',
            'phone',
            'ipaddress',
        )
        data = dict(
            Shop_ID=self.shop_id,
            Login=self.login,
            Password=self.password,
            Format=4,
            Success=self.success
        )

        if self.order_id:
            data['ShopOrderNumber'] = self.order_id

        result = self.set_request(self.get_url('results'), data)

        if result:
            try:
                tree = etree.fromstring(result.response.body)
            except Exception as e:
                app.logger.error(e)
            else:
                event_nodes = tree.xpath(
                    '/unitellerresult/orders/order')

                return_data = {}
                for event_node in event_nodes:

                    data = {}
                    for key in keys:
                        data[key] = event_node.find(key).text

                    if 'ordernumber' in data:
                        return_data[data['ordernumber']] = data

        return return_data

    def reccurent_payment(self, order):
        """Обязательные данные - order_id, amount, parent_order_id"""
        return_data = False

        data = dict(
            Shop_IDP=self.shop_id,
            Order_IDP=order['order_id'],
            Subtotal_P=order['amount'],
            Parent_Order_IDP=order['parent_order_id'],
            Signature=self.get_reccurent_sing(order)
        )

        result = self.set_request(self.get_url('recurrent'), data)

        if result:
            data = result.response.body
            reader = csv.reader(data.split('\n'), delimiter=';')
            response_code = None
            for row in reader:
                if len(row) > 1:
                    response_code = row[1]
            return_data = response_code

        return return_data
