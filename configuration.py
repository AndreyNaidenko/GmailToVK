import json

VK_API_ACCESS_TOKEN = '**'
GROUP_ID = '**'
VK_API_VERSION = '5.92'
GMAIL_CLIENT_SECRET = 'client_secret.json'
GMAIL_SERVICE_ACCOUNT_KEY = '**.json'
VK_CHAT_ID = "2000000001"
KEYBOARD = {
    'one_time':
    False,
    'buttons': [[{
        'action': {
            'type': 'text',
            'payload': json.dumps({
                'buttons': '1'
            }),
            'label': 'Кнопка 1',
        },
        'color': 'negative'
    },
                 {
                     'action': {
                         'type': 'text',
                         'payload': json.dumps({
                             'buttons': '2'
                         }),
                         'label': 'Кнопка 2',
                     },
                     'color': 'primary'
                 }]]
}
