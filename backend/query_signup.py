from database_functions import *


class SignUp:

    # Initializing the connection
    def __init__(self, username, password=None):
        self.db = connection()
        self.user = username
        self.password = password

    # check if user exists
    def check_user(self):
        return user_exists(self.db, self.user)

    # adding password to the SignUp Object
    def add_password(self, password):
        self.password = password

    # check if password is not empty
    def check_password(self):
        return self.password

    # add a user into user table
    def add_user(self):
        if not self.check_user() and self.check_password():
            insert_into_user_table(self.db, self.user, self.password)
            return True
        return False

    def add_user_after_authentication(self):
        insert_into_user_table(self.db, self.user, self.password)
