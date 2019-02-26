import json

VK_API_ACCESS_TOKEN = '66fe530320e2c886339af523069ee5c07a57c12ba61f78435914fed8149c2c379eddd674367ec6a0481f4'
GROUP_ID = '169376229'
VK_API_VERSION = '5.92'
GMAIL_CLIENT_SECRET = 'client_id.json'
GMAIL_SERVICE_ACCOUNT_KEY = '**.json'


class Configs():
    def __init__(self):
        self.VK_CHAT_ID = "1"  #default
        self.ADD_KEYBOARD = {
            'one_time':
            True,
            'buttons': [[{
                'action': {
                    'type': 'text',
                    'payload': json.dumps({
                        'buttons': '1'
                    }),
                    'label': 'Добавить рассылку в ЛС',
                },
                'color': 'positive'
            }]]
        }
        self.DELETE_KEYBOARD = {
            'one_time':
            True,
            'buttons': [[{
                'action': {
                    'type': 'text',
                    'payload': json.dumps({
                        'buttons': '2'
                    }),
                    'label': 'Удалить из рассылки',
                },
                'color': 'negative'
            }]]
        }

    def setChatID(self, chat_id):
        '''[summary]
            
            Arguments:
                chat_id {[type]} -- [description]
            '''
        self.VK_CHAT_ID = str(chat_id)

    def getChatID(self):
        '''[summary]
            
            Returns:
                [type] -- [description]
            '''

        return '200000000' + self.VK_CHAT_ID

    def getKeyBoard(self, type):
        if Type == "add":
            return self.ADD_KEYBOARD
        if Type == 'delete':
            return self.DELETE_KEYBOARD
