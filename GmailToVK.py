# -*- coding: utf-8 -*-
"""
Created on Tue Jan  1 00:04:29 2019

@author: Medvedev Denis
"""

import vk
from configuration import *
from requests import post
import time


class GmailToVKbot():
    def __init__(self, vk_access_token, vk_api_version):
        self.vk_api_version = vk_api_version
        self.vk_access_token = vk_access_token
        self.vk_session = vk.Session(access_token=vk_access_token)
        self.vk_api = vk.API(self.vk_session, v=vk_api_version)

    def connect_to_VK_Long_Poll(self, group_id):
        self.longPoll = self.vk_api.groups.getLongPollServer(
            group_id=group_id)  #
        self.server = self.longPoll['server']
        self.key = self.longPoll['key']
        self.ts = self.longPoll['ts']

    def run(self):
        peer_id = None
        print('START')
        STOP = True
        SERVER = True
        while SERVER:
            '''
            POST-запрос вида {$server}?act=a_check&key={$key}&ts={$ts}&wait=25

            -key — секретный ключ сессии;
            -server — адрес сервера;
            -ts — номер последнего события, начиная с которого нужно получать данные;
            -wait — время ожидания (так как некоторые прокси-серверы обрывают соединение после 30 секунд, мы рекомендуем указывать wait=25). Максимальное значение — 90.
            '''
            self.longPoll = post(
                '%s' % self.server,
                data={
                    'act': 'a_check',
                    'key': self.key,
                    'ts': self.ts,
                    'wait': 25
                }).json()
            '''
            JSON-объект в ответе содержит два поля:

            ts (integer) — номер последнего события. Используйте его в следующем запросе.
            updates (array) — массив, элементы которого содержат представление новых событий.
            '''
            if self.longPoll['updates'] and len(self.longPoll['updates']) != 0:
                for update in self.longPoll['updates']:
                    '''
                    Событие message_new- входящее сообщение
                    '''
                    if update['type'] == 'message_new':

                        peer_id = update['object']['peer_id']
                        '''
                        Помечаем сообщение как прочитанное
                        '''
                        self.vk_api.messages.markAsRead(
                            peer_id=update['object']['peer_id'])

                        if update['object']['text'] == 'СТАРТ':
                            STOP = False
                        if update['object']['text'] == 'СТОП':
                            STOP = True
                        if update['object']['text'] == 'Остановить':
                            SERVER = False
                        '''
                        Отправляем сообщение
                        '''
                        self.vk_api.messages.send(
                            peer_id=update['object']['peer_id'],
                            message='С новым годом')

            if peer_id is not None and not STOP:
                time.sleep(1)
                self.vk_api.messages.send(
                    peer_id=peer_id, message='С новым годом')

            self.ts = self.longPoll['ts']


gmvbot = GmailToVKbot(VK_API_ACCESS_TOKEN, VK_API_VERSION)
gmvbot.connect_to_VK_Long_Poll(GROUP_ID)
gmvbot.run()