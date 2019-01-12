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
from sqlalchemy import create_engine


class GmailToVKbot():
    def __init__(self,
                 vk_access_token,
                 vk_api_version,
                 gmail_client_secret,
                 gmail_service_account_key=None):
        self.vk_api_version = vk_api_version
        self.gmail_client_secret = gmail_client_secret
        self.gmail_service_account_key = gmail_service_account_key
        self.vk_access_token = vk_access_token
        self.vk_session = vk.Session(access_token=vk_access_token)
        self.vk_api = vk.API(self.vk_session, v=vk_api_version)

    def connect_to_VK_Long_Poll(self, group_id):
        print("Connection to vk.com")
        try:
            self.longPoll = self.vk_api.groups.getLongPollServer(
                group_id=group_id)  #
            self.server = self.longPoll['server']
            self.key = self.longPoll['key']
            self.ts = self.longPoll['ts']
        except Exception as e:
            print("\tFailed : +" + str(e) + "\r\n")
        else:
            print("\tSuccessfully \r\n")

    def create_vk_id_base(self):
        e = create_engine("sqlite:///vk_id.db")
        e.execute("""
                  create table vk_id (
                          peer_id integer primary key
                                     )
                  """)

    def add_to_vk_private_messages(self, peer_id):
        if not os.path.exists("vk_id.db"):
            self.create_vk_id_base()
        e = create_engine("sqlite:///vk_id.db")
        try:
            e.execute("""
                      INSERT INTO `vk_id`(`peer_id`) VALUES (""" +
                      str(peer_id) + """);
                      """)
        except Exception as e:
            print("\tFailed : +" + str(e) + "\r\n")

    def send_vk_private_messages(self, message):
        if os.path.exists("vk_id.db"):
            e = create_engine("sqlite:///vk_id.db")
            peer_id = e.execute("""
                      SELECT peer_id FROM vk_id;
                      """).fetchall()
            for p_id in peer_id:
                self.vk_api.messages.send(
                    peer_id=p_id[0], random_id='0', message=message)

    def connect_to_GMAIL(self, scopes):
        print("Connection to gmail.com")
        try:
            store = file.Storage('token.json')
            creds = store.get()
            if not creds or creds.invalid:
                flow = client.flow_from_clientsecrets('client_secret.json',
                                                      scopes)
                creds = tools.run_flow(flow, store)
            self.gmail_service = build(
                'gmail', 'v1', http=creds.authorize(Http()))
            '''
            Получаем email-адрес авторизованного пользователя
            '''

            self.gmail_user = self.gmail_service.users().getProfile(
                userId='me').execute()
            self.historyId = self.gmail_user['historyId']
            self.last_date = 0
        except Exception as e:
            print("\tFailed : +" + str(e) + "\r\n")
        else:
            print("\tSuccessfully")
            print("\t\t User:", self.gmail_user['emailAddress'], '\r\n')

    def get_last_message(self, user_id='me'):
        self.history = self.gmail_service.users().history().list(
            userId='me',
            historyTypes=['messageAdded'],
            startHistoryId=self.historyId).execute()
        print(self.history)
        try:
            history = self.history['history']
            for h in history:
                messages = h['messages']
                for msg in messages:
                    self.last_message = self.gmail_service.users().messages(
                    ).get(
                        userId='me', id=msg['id']).execute()
        except Exception as e:
            print("\tFailed : +" + str(e) + "\r\n")
            self.last_message = None
        self.historyId = self.history['historyId']
        print(self.last_message)

    def gmail_log_out(self, filename):
        print('Start logout')
        try:
            os.remove(filename)
        except:
            print('\tLogout failed')
            print('\t' + filename + 'is not exist!')
        else:
            print('\tLogout completed')

    def run(self):
        peer_id = None
        print('Bot is run')
        STOP = True
        SERVER = True

        while SERVER:
            try:
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
                print(self.longPoll['updates'])
                if self.longPoll['updates'] and len(
                        self.longPoll['updates']) != 0:
                    for update in self.longPoll['updates']:
                        '''
                        Событие message_new- входящее сообщение
                        '''
                        if update['type'] == 'message_new':
                            '''
                            Получаем id пользователя, отправившего сообщение боту
                            '''

                            peer_id = update['object']['peer_id']
                            '''
                            Помечаем сообщение как прочитанное
                            '''

                            if 'старт' in update['object']['text'].lower():
                                STOP = False
                                self.vk_api.messages.send(
                                    peer_id=peer_id,
                                    random_id='0',
                                    message='Бот запущен')
                            if 'стоп' in update['object']['text'].lower():
                                STOP = True
                                self.vk_api.messages.send(
                                    peer_id=peer_id,
                                    random_id='0',
                                    message='Бот остановлен')
                            '''
                            Остановка бота, выход из while True:
                            '''

                            if 'остановить' in update['object']['text'].lower(
                            ):
                                SERVER = False
                                self.vk_api.messages.send(
                                    peer_id=peer_id,
                                    random_id='0',
                                    message='Остановлено')
                            if 'выход' in update['object']['text'].lower():
                                self.gmail_log_out('token.json')
                                self.vk_api.messages.send(
                                    peer_id=peer_id,
                                    random_id='0',
                                    message='Завершено')

                            if 'отправляй мне в лс' in update['object'][
                                    'text'].lower():
                                self.add_to_vk_private_messages(peer_id)
                                self.vk_api.messages.send(
                                    peer_id=peer_id,
                                    random_id='0',
                                    message='Добавлено')
                '''
                Прослушивание gmail

                Письмо хранится в формате json (возможно list) в переменной self.last_message
                '''
                if peer_id is not None or not STOP:
                    self.get_last_message(user_id='me')
                    if self.last_message is not None:

                        subject = ""  # если письмо будет без темы, то
                        # эта строка просто останется пустой
                        # постепенно углубляемся в словарь для получения данных
                        main_headers = self.last_message['payload']
                        headers = main_headers['headers']

                        for item in headers:  # цикл по словарям
                            if item['name'] == 'From':  # ищем From - уникальное name с данными автора
                                author = "Автор: " + item[
                                    'value'] + "\n"  # строка с автором и почтой письма
                            if item['name'] == 'Subject':  # ищем Subject - уникальное name с темой
                                subject = "Тема: " + item[
                                    'value']  # формируем строку с темой письма

                        vk_message = "На почте новое письмо\n" + author + subject  # формируем строку для отправки в вк
                        self.vk_api.messages.send(
                            peer_id=VK_CHAT_ID,
                            random_id='0',
                            message=vk_message)
                        self.send_vk_private_messages(vk_message)
                self.ts = self.longPoll['ts']
            except Exception as e:
                print("\tFailed : +" + str(e) + "\r\n")
                SERVER = False


gmvkbot = GmailToVKbot(VK_API_ACCESS_TOKEN, VK_API_VERSION,
                       GMAIL_CLIENT_SECRET)
gmvkbot.connect_to_GMAIL(SCOPES)
gmvkbot.connect_to_VK_Long_Poll(GROUP_ID)
gmvkbot.run()