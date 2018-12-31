# -*- coding: utf-8 -*-
"""
Created on Tue Jan  1 00:04:29 2019

@author: Medvedev Denis
"""


import vk
from configuration import *
from requests import *
import os
import time


def main():
        session = vk.Session(access_token = VK_API_ACCESS_TOKEN)
        api = vk.API(session, v = VK_API_VERSION)
        
        
        '''
            Перед подключением к Long Poll серверу необходимо получить данные сессии (server, key, ts) методом groups.getLongPollServer. 
            getLongPollServer получает адрес для подключения к Long Poll серверу ВКонтакте;
        ''' 
        
        longPoll = api.groups.getLongPollServer(group_id = GROUP_ID) #
        server, key, ts = longPoll['server'], longPoll['key'], longPoll['ts']
        peer_id=None
        print('START')
        STOP=True
        while True:
            
            
            '''
            POST-запрос вида {$server}?act=a_check&key={$key}&ts={$ts}&wait=25 
            
            -key — секретный ключ сессии;
            -server — адрес сервера;
            -ts — номер последнего события, начиная с которого нужно получать данные;
            -wait — время ожидания (так как некоторые прокси-серверы обрывают соединение после 30 секунд, мы рекомендуем указывать wait=25). Максимальное значение — 90. 
            '''
            longPoll = post('%s'%server, data = {'act': 'a_check',
                                                 'key': key,
                                                 'ts': ts,
                                                 'wait': 25}).json()
        
            '''
            JSON-объект в ответе содержит два поля:
        
            ts (integer) — номер последнего события. Используйте его в следующем запросе.
            updates (array) — массив, элементы которого содержат представление новых событий.
            '''
            if longPoll['updates'] and len(longPoll['updates']) != 0:
                for update in longPoll['updates']:
                    
                    '''
                    Событие message_new- входящее сообщение
                    '''
                    if update['type'] == 'message_new':
                        
                        peer_id=update['object']['peer_id']
                        
                        '''
                        Помечаем сообщение как прочитанное
                        '''
                        api.messages.markAsRead(peer_id = update['object']['peer_id'])
                        
                        if update['object']['text']=='СТАРТ':
                            STOP=False
                        if update['object']['text']=='СТОП':
                            STOP=True
                        '''
                        Отправляем сообщение
                        '''
                        api.messages.send(peer_id = update['object']['peer_id'], message = 'С новым годом')
                        
            
            if peer_id is not None and not STOP :
                    time.sleep(1)
                    api.messages.send(peer_id =peer_id, message = 'С новым годом')
                
            ts = longPoll['ts']
main()