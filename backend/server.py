# coding: utf-8

# imports
from flask import Flask, request
import base64
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from json import dumps
from flask import jsonify
from query_signup import *
from query_signin import *
from flask_cors import CORS, cross_origin
from database_functions import *
import time
import shutil
from utilities.download import *
from utilities.utils import *
from utilities.upload import upload as upload_db
from utilities.upload import uploadFile
from utilities.delete_file import delete_file
from api_utils import *
from flask import send_file
import os

app = Flask(__name__)
cors = CORS(app)
api = Api(app)


# Api to check if user exists
# Exposed API to check if user exists
# Route /check_user/<username
# Returns true if user exists, false if user does not exists
class CheckUser(Resource):
    def get(self, username):
        signup = SignUp(username)
        return jsonify(signup.check_user())


# Api to Add a user
# Route /add_user/<username>/<password>
class AddUser(Resource):
    def post(self):
        json_data = request.get_json(force=True)
        username = json_data['username']
        password = json_data['password']
        signup = SignUp(username, password)
        return jsonify(signup.add_user())


api.add_resource(CheckUser, '/check_user/<username>')
api.add_resource(AddUser, '/add_user/<username>/')


# API to check a username is available for signup
@app.route('/checkUser', methods=['POST'])
@cross_origin()
def checkUser():
    signup = SignUp(request.json['username'])
    username = request.json['username']
    password = request.json['password']
    x = jsonify(
        {'username': request.json['username'], 'password': request.json['password'], 'available': signup.check_user()})
    return x


# Api to register a new user
@app.route('/registerUser', methods=['POST'])
@cross_origin()
def registerUser():
    username = request.json['username']
    password = request.json['password']
    signup = SignUp(username, password)
    registered = signup.add_user_after_authentication()
    token = False
    if registered:
        token = str(generate_token())
        db = connection()
        presentTime = str(time.time())
        insert_into_token_table(db, username, presentTime, token)
    x = jsonify({'username': request.json['username'], 'password': request.json['password'],
                 'registered': registered, 'token': token})
    return x


def check_validity_token(username, token):
    """
    Function to check validity of a token
    :param username: Username
    :param token: Token
    :return: Validity of a token
    """
    db = connection()
    date_time = get_datetime_token(db, username, token)
    present_time = time.time()
    timeout = 3600  # seconds (1 hour)
    return float(present_time) - float(date_time) < timeout


# API to check the validity of a token for a particular username (<timeout)
@app.route('/checkValidity', methods=['POST'])
@cross_origin()
def checkValid():
    username = request.json['username']
    token = request.json['token']
    valid = check_validity_token(username, token)
    x = jsonify({'valid': valid})
    return x


# API to signin a user after authentication
@app.route('/signin', methods=['POST'])
@cross_origin()
def signInUser():
    username = request.json['username']
    password = request.json['password']
    signin = SignIn(username, password)
    if signin.check_user():
        valid = signin.check_password()
    else:
        valid = "User does not exist"
    if valid == "User successfully authenticated":
        token = str(generate_token())
        db = connection()
        presentTime = str(time.time())
        insert_into_token_table(db, username, presentTime, token)
    else:
        token = False
    return jsonify({'valid': valid, 'token': token, 'username': username})


# API to add a new transaction
# Legacy version - Uploading a bill, hence the name
# Later version - Adding a new transaction
@app.route('/uploadBill', methods=['POST'])
@cross_origin()
def upload():
    if 'image' in request.files:
        # Image has to be uploaded
        file = request.files['image']
        file_name = file.filename
        file.seek(0, os.SEEK_END)
        file_size = file.tell()/(10**6) # file_size in mb
        file_extension = file_name.split('.')[-1]
        original_file_name = file_name
        present_time = str(time.time())
        file_name = present_time + '.' + file_extension
        mapped_file_name = file_name
        # adding image mapping for cross referencing later
        insert_into_image_mapping_table(connection(), request.form['username'], original_file_name, mapped_file_name)

        # adding entry to image size table
        insert_into_image_size_table(connection(), mapped_file_name, file_size)

        # uploading the file to dropbox
        uploadFile(file, mapped_file_name)
    else:
        # Image not a part of the transaction
        mapped_file_name = str(False)
    user_name = request.form['username']
    title = request.form['Name']
    date_time = request.form['Date']
    description = request.form['Description']
    amount = request.form['Amount']
    category = request.form['category']
    # adding the transaction record
    insert_into_image_table(connection(), user_name, title, date_time, amount, description, mapped_file_name, category)

    # refresh the token, needs to be added to other API Calls
    refresh_token(connection(), request.form['username'])

    return jsonify({'uploadStatus': True})


# API to return the most recent transactions
@app.route('/getRecentTransactions', methods=['POST'])
@cross_origin()
def recentTransactions():
    """
    Api to get the recent transactions of a particular user.
    :return: 5 transactions for now. #TODO need to make it more dynamic and generalized later on.
    """
    user_name = request.json['username']
    refresh_token(connection(), user_name)
    try:
        limit_transactions = request.json['limit']
    except KeyError:
        limit_transactions = 100  # limit of the transaction to be retrieved
    try:
        transactions = query_recent_transaction(connection(), user_name, limit_transactions)
        if not transactions:
            return jsonify({False})
        return build_json_recent_transactions(transactions, user_name)
    except:
        return jsonify(False)


# API to return an image in b'64 format for preview(large view/downloading)
@app.route('/previewImage', methods=['POST'])
@cross_origin()
def previewImage():
    """
    API to preview the image for a particular transaction
    """
    user_name = request.json['username']
    mapped_image_name = request.json['mapped_name']
    original_image_name = request.json['original_name']
    refresh_token(connection(), user_name)
    try:
        # downloading the image to cacheable region
        user_name = str('.' + user_name)
        file = os.path.join(os.getcwd(), "temp", user_name, mapped_image_name)
        if not os.path.exists(file):
            download_file(user_name, mapped_image_name, original_image_name)
        with open(file, "rb") as f:
            Image_data = f.read()
            encoded_string = base64.b64encode(Image_data)
        return jsonify({'Image': str(encoded_string.decode('utf-8'))})
    except:
        return jsonify(False)


# API to signal that a particular user signed out
# Used to delete his data, also updating the db to remote
@app.route('/signout', methods=['DELETE'])
@cross_origin()
def signout():
    """
    API when user signs out. Delete all his transaction Data
    """
    upload_db() # upload the dropbox server to the latest code (automation)
    user_name = request.json['username']
    user_data_path = os.path.join(os.getcwd(), "temp", "." + user_name)
    if os.path.exists(user_data_path):
        shutil.rmtree(user_data_path)
    return jsonify(True)


# API to delete a particular transaction based on uid
@app.route('/deleteTransaction', methods=['DELETE'])
@cross_origin()
def deleteTransaction():
    """
    API to delete a particular transaction
    """
    user_name = request.json['username']
    uid = request.json['uid']
    refresh_token(connection(), user_name)
    mapped_name = request.json['mapped_name']
    try:

        message = delete_from_image_table(connection(), uid, user_name)
        delete_file(mapped_name)    # deleting that image from dropbox
        return jsonify(message)
    except:
        return jsonify("Deleting the transaction failed.")


# API to edit a particular transaction based on uid
@app.route('/editTransaction', methods=['POST'])
@cross_origin()
def edit_transaction():
    if 'image' in request.files:
        # Image has to be uploaded
        file = request.files['image']
        file_name = file.filename
        file_extension = file_name.split('.')[-1]
        original_file_name = file_name
        present_time = str(time.time())
        file_name = present_time + '.' + file_extension
        mapped_file_name = file_name
        # adding image mapping for cross referencing later
        insert_into_image_mapping_table(connection(), request.form['username'], original_file_name, mapped_file_name)

        # adding entry to image size table
        insert_into_image_size_table(connection(), mapped_file_name, file_size)

        # uploading the file to dropbox
        uploadFile(file, mapped_file_name)
    else:
        # Image not a part of the transaction
        mapped_file_name = str(False)
    user_name = request.form['username']
    uid = request.form['uid']
    title = request.form['Name']
    date_time = request.form['Date']
    description = request.form['Description']
    amount = request.form['Amount']
    category = request.form['category']
    # adding the transaction record
    edit_transactions_image_table(connection(), uid, user_name, title, date_time, amount, description,
                                  mapped_file_name, category)
    # refresh the token, needs to be added to other API Calls
    refresh_token(connection(), request.form['username'])

    return jsonify({'editStatus': True})


# API to get usage details for a particular user
@app.route('/usage', methods=['POST'])
@cross_origin()
def user_space_usage():
    """
    API for usage details
    """
    user_name = request.json['username']
    refresh_token(connection(), user_name)
    size = space_usage(connection(), user_name)
    total_quota = get_total_size()
    return jsonify({'TotalQuota': total_quota, 'UsedQuota': size})


if __name__ == '__main__':
    download()
    app.run(port=5000, debug=True)

# TODO Migrate APIs