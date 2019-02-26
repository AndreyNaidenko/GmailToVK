 # -*- coding: utf-8 -*-
from configuration import *
from scopes import *
from requests import post
import json
import time
import os
import vk
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import urllib.parse as urlparse


class BotGmailToVk():
    def __init__(self,
                 vk_access_token,
                 vk_api_version,
                 gmail_client_secret,
                 gmail_service_account_key=None):
        """Функция инициализации.

        Arguments:
            vk_access_token {str} -- Токен сообщества vk.com
            vk_api_version {str} -- Используемая версия api vk.com
            gmail_client_secret {str} -- Путь к токену приложения gmail

        Keyword Arguments:
            gmail_service_account_key {[type]} -- [description] (default: {None})
        """

        self.vk_api_version = vk_api_version
        self.gmail_client_secret = gmail_client_secret
        self.gmail_service_account_key = gmail_service_account_key
        self.vk_access_token = vk_access_token
        self.vk_session = vk.Session(access_token=vk_access_token)
        self.vk_api = vk.API(self.vk_session, v=vk_api_version)

    def connect_to_vk_long_poll(self, group_id):
        """Подключение к long poll серверу vk.

        Arguments:
            group_id {str} -- Id группы используемой для рассылки
        """

        try:
            self.longPoll = self.vk_api.groups.getLongPollServer(
                group_id=group_id)
            self.server = self.longPoll['server']
            self.key = self.longPoll['key']
            self.ts = self.longPoll['ts']
        except Exception as e:
            print("Error with connect to vk longPoll: " + str(e))

    def connection_to_postgre(self):
        url = urlparse.urlparse(os.environ['DATABASE_URL'])
        self.dbname = url.path[1:]
        user = url.username
        password = url.password
        host = url.hostname
        port = url.port

        conn = psycopg2.connect(
            dbname=self.dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        return conn, cursor

    def create_vk_id_table(self):
        """Создание базы postgesql, хранящей id пользователей vk.com."""

        conn, cursor = self.connection_to_postgre()
        try:
            cursor.execute("create table vk_id (user_id integer primary key)")
        except Exception as e:
            print("Error with CREATE TABLE: " + str(e))
        cursor.close()
        conn.close()

    def add_to_vk_private_messages(self, user_id):
        """Добавление id пользователя в базу.

        Arguments:
            user_id {integer} -- Id пользователя
        """

        conn, cursor = self.connection_to_postgre()
        try:
            cursor.execute("INSERT INTO vk_id (user_id) VALUES (" +
                           str(user_id) + ");")
        except Exception as e:
            print("Error with command INSERT INTO: " + str(e))
        cursor.close()
        conn.close()

    def delete_from_vk_private_messages(self, user_id):
        """Удаление id пользователя из базы

        Arguments:
            user_id {integer} -- id пользователя
        """

        conn, cursor = self.connection_to_postgre()
        try:
            cursor.execute("DELETE FROM vk_id WHERE user_id = " +
                           str(user_id) + ";")
        except Exception as e:
            print("Error with command DELETE FROM: " + str(e))
        cursor.close()
        conn.close()

    def send_vk_private_messages(self, message):
        """Рассылка сообщений пользователям из базы.

        Arguments:
            message {str} -- Сообщение которое будет отправлено пользователям
        """

        conn, cursor = self.connection_to_postgre()
        try:
            cursor.execute("SELECT user_id FROM vk_id;")
            users = cursor.fetchall()
        except Exception as e:
            print("Error with command SELECT: " + str(e))
        for user in users:
            self.vk_api.messages.send(
                peer_id=user[0], random_id='0', message=message)
        cursor.close()
        conn.close()

    def send_keyboard(self, user_id, peer_id):
        """
        Отправляет клавиатуру в vk.com

        Arguments:
            user_id {integer} -- id пользователя
        """

        conn, cursor = self.connection_to_postgre()
        try:
            cursor.execute("SELECT user_id FROM vk_id;")
            users = cursor.fetchall()
        except Exception as e:
            print("Error with command SELECT: " + str(e))
        check = False
        # Проверяем есть ли пользователь в базе
        for user in users:
            if str(user[0]) == str(user_id):
                check = True
        # Если да, то отправляем ему кнопку "Удалить из рассылки"
        # Если нет, то отправляем ему кнопку "Добавить рассылку в ЛС"
        if check:
            KEYBOARD = DELETE_KEYBOARD
        else:
            KEYBOARD = ADD_KEYBOARD

        keyboard = json.dumps(KEYBOARD, ensure_ascii=False).encode('utf-8')
        keyboard = str(keyboard.decode('utf-8'))
        # Проверяем откуда пришло сообщение ЛС или беседа
        self.vk_api.messages.send(
            peer_id=user_id, message="Клавиатура", random_id='0', keyboard=keyboard)
        cursor.close()
        conn.close()

    def connect_to_gmail(self, scopes):
        """Подключение к gmail.

        Arguments:
            scopes {list} -- Области доступа
        """

        try:
            store = file.Storage('token.json')
            creds = store.get()
            if not creds or creds.invalid:
                flow = client.flow_from_clientsecrets('client_id.json',
                                                      scopes)
                creds = tools.run_flow(flow, store)
            self.gmail_service = build(
                'gmail', 'v1', http=creds.authorize(Http()))

            # получаем email-адрес авторизованного пользователя
            self.gmail_user = self.gmail_service.users().getProfile(
                userId='me').execute()
            self.historyId = self.gmail_user['historyId']
            self.last_date = 0
        except Exception as e:
            print("Error with connection to gmail: " + str(e))
        else:
            print("E-mail:", self.gmail_user['emailAddress'])

    def get_last_message(self, user_id='me'):
        """Получение последнего сообщения в gmail.com.

        Keyword Arguments:
            user_id {str} -- Id в gmail (default:{'me'})
        """
        try:
            self.history = self.gmail_service.users().history().list(
                userId='me',
                historyTypes=['messageAdded'],
                startHistoryId=self.historyId).execute()

            history = self.history['history']
            for h in history:
                messages = h['messages']
                for message in messages:
                    self.last_message = self.gmail_service.users().messages(
                    ).get(
                        userId='me', id=message['id']).execute()
            self.historyId = self.history['historyId']
        except Exception as e:
            print("Error with get last message: " + str(e))
            self.last_message = None

    def gmail_log_out(self, filename):
        """Выход из аккаунта gmail.com.

        Arguments:
            filename {str} -- Путь к файлу в котором хранится
        токен
        """

        try:
            os.remove(filename)
        except:
            print('\tLogout failed')
            print('\t' + filename + 'is not exist!')
        else:
            print('\tLogout completed')

    def send_message_to_vk(self):
        '''Отправка сообщения в vk'''

        subject = ""  # если письмо будет без темы, то
        # эта строка просто останется пустой
        # постепенно углубляемся в словарь для получения данных
        main_headers = self.last_message['payload']
        headers = main_headers['headers']

        for header in headers:  # цикл по словарям
            if header['name'] == 'From':  # ищем From - уникальное name с данными автора
                author = "Автор: " + header[
                    'value'] + "\n"  # строка с автором и почтой письма
            if header['name'] == 'Subject':  # ищем Subject - уникальное name с темой
                subject = "Тема: " + header[
                    'value']  # формируем строку с темой письма

        vk_message = "На почте новое письмо\n" + author + \
            subject  # формируем строку для отправки в вк
        if "INBOX" in self.last_message[
                'labelIds']:  # если в ответе на запрос есть метка "INBOX"
            self.vk_api.messages.send(
                peer_id=VK_CHAT_ID, random_id='0',
                message=vk_message)  # отправляем в вк
            self.send_vk_private_messages(vk_message)

    def run(self):
        """Основная функция."""

        peer_id = None
        STOP = False
        SERVER = True
        while SERVER:

            # POST-запрос вида {$server}?act=a_check&key={$key}&ts={$ts}&wait=25
            # -key — секретный ключ сессии;
            # -server — адрес сервера;
            # -ts — номер последнего события, начиная с которого нужно получать данные;
            # -wait — время ожидания (так как некоторые прокси-серверы обрывают соединение после 30 секунд, мы рекомендуем указывать wait=25). Максимальное значение — 90.
            try:
                self.longPoll = post(
                    '%s' % self.server,
                    data={
                        'act': 'a_check',
                        'key': self.key,
                        'ts': self.ts,
                        'wait': 25
                    }).json()

                # JSON-объект в ответе содержит два поля:
                # ts (integer) — номер последнего события. Используйте его в следующем запросе.
                # updates (array) — массив, элементы которого содержат представление новых событий.
            except Exception as e:
                print("Error with longPoll post: " + str(e))
                SERVER = False
            try:
                if self.longPoll['updates'] and len(
                        self.longPoll['updates']) != 0:
                    for update in self.longPoll['updates']:
                        # Событие message_new- входящее сообщение
                        if update['type'] == 'message_new':
                            # Получаем id пользователя, отправившего сообщение боту
                            peer_id = update['object']['peer_id']
                            from_id = update['object']['from_id']                            
                            if 'уведомлять меня лично' in update['object'][
                                    'text'].lower():
                                self.add_to_vk_private_messages(
                                    update['object']['from_id'])
                                self.vk_api.messages.send(
                                    peer_id=update['object']['from_id'],
                                    random_id='0',
                                    message='Добавлено')
                            if 'прекратить личные уведомления' in update['object'][
                                    'text'].lower():
                                self.delete_from_vk_private_messages(
                                    update['object']['from_id'])
                                self.vk_api.messages.send(
                                    peer_id=update['object']['from_id'],
                                    random_id='0',
                                    message='Удалено')
                            if 'рассылка' in update['object']['text'].lower():
                                self.send_keyboard(from_id, peer_id)
            except Exception as e:
                print("Error in run: " + str(e))
                SERVER = False
            try:
                if not STOP:
                    self.get_last_message(user_id='me')
                    print(self.last_message)
                    if self.last_message:
                        self.send_message_to_vk()
                self.ts = self.longPoll['ts']
            except Exception as e:
                print("Error with send message to vk: " + str(e))
                SERVER = False


gmvkbot = BotGmailToVk(VK_API_ACCESS_TOKEN, VK_API_VERSION,
                       GMAIL_CLIENT_SECRET)
gmvkbot.connect_to_gmail(SCOPES)
gmvkbot.connect_to_vk_long_poll(GROUP_ID)
gmvkbot.run()
