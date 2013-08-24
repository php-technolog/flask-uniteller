# -*- coding: utf-8 -*-
"""
    Консольное приложение для тестирования и отладки

    :copyright: (c) 2013 by Pavel Lyashkov.
    :license: BSD, see LICENSE for more details.
"""

from flask.ext.script import Command

from console.configs.payment import UnitellerConfig
from libs.uniteller_api import UnitellerApi


class TestCommand(Command):

    def run(self):
        un = UnitellerApi(UnitellerConfig)

        print un.confirm_payment(99)
