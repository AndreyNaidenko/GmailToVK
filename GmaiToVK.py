
# A very simple Flask Hello World app for you to get started with...

from flask import Flask,request,json
import vk
import time
import random
import threading
app = Flask(__name__)

def get_message():
    if random.randint(0,10)%2==0:
        return True
    return False

@app.route('/')
def hello_world():

    return 'r'

@app.route('/', methods=['POST'])
def processing():
    data = json.loads(request.data)
    if 'type' not in data.keys():
        return 'not vk'
    if data['type'] == 'confirmation':
        return '**'
    
    '''
    Обработка входящих
    '''
    if data['type']== 'message_new':
        session = vk.Session()
        api = vk.API(session, v=5.84)
        peer_id = data['object']['peer_id']
        api.messages.send(access_token='**', peer_id=(peer_id), message='Вам письмо')
        return 'ok'

def Listener():
    session = vk.Session()
    api = vk.API(session, v=5.84)

    '''
    Тут должна быть авторизация GMAIL
    '''
    peer_id = '**'
    while True:
        if get_message()==True:
            api.messages.send(access_token='**', peer_id=(peer_id), message='Вам письмо')
        time.sleep(1)

t = threading.Thread(target=Listener,
                         name="Listener",
                         args=(),
                         daemon=True)
t.start()