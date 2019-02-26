import uuid
import psycopg2


class Admins():
    def __init__(self):
        '''[summary]
        '''

        self.current_token = '123'
        self.admins = []

    def add_new_admin(self, id):
        self.admins.append(id)

    def set_new_token(self):
        self.current_token = uuid.uuid4()

    def get_token(self):
        return str(self.current_token)
