from ast import literal_eval
from yaml import safe_load


# function to get the pending groups for a particular username
def get_group_title(db_connection, group_id):
    cursor = db_connection.execute('''SELECT title FROM GROUPS where ID = "{group_id}"  
    '''.format(group_id=group_id))
    for row in cursor:
        if row:
            return row[0]
    return False


# function to get the pending groups for a particular username
def get_pending_groups(db_connection, username):
    cursor = db_connection.execute('''SELECT group_id FROM PENDING_REQUESTS where username = "{username}" 
    AND status = "pending"
    '''.format(username=username))
    groups = []
    for row in cursor:
        if row:
            group_id = row[0]
            title = get_group_title(db_connection, group_id)
            groups.append([group_id, title])
    db_connection.commit()
    return groups if groups else "False"


# function to check if user has particular status in a group
'''
accepted
rejected
removed
pending
exited
'''


def get_status_for_group(db_connection, group_id, username, status):
    cursor = db_connection.execute('''SELECT group_id FROM PENDING_REQUESTS where username = "{username}" 
    AND status = "{status}" and group_id="{group_id}"
    '''.format(username=username, status=status, group_id=group_id))
    for row in cursor:
        if row:
            return True
    return False


# function to get the current users of the group
def get_group_current_users(db_connection, group_id):
    cursor = db_connection.execute('''SELECT users FROM GROUPS where ID = "{group_id}"  
    '''.format(group_id=group_id))
    for row in cursor:
        if row:
            return row[0]
    return False


# function to get the pending groups for a particular username
def get_groups_user(db_connection, username, status):
    cursor = db_connection.execute('''SELECT group_id FROM PENDING_REQUESTS where username="{username}" and status="{status}"
    '''.format(username=username, status=status))
    groups = []
    for row in cursor:
        if row:
            groups.append(row[0])
    db_connection.commit()
    return groups


# function to get all the group information for a particular group
def get_group_info(db_connection, group_id):
    cursor = db_connection.execute('''SELECT ID,group_admin,users,title,description, bill_ids, creation_time FROM 
    GROUPS where ID = "{group_id}"  
        '''.format(group_id=group_id))
    for row in cursor:
        if row:
            list_users = literal_eval(row[2])
            list_bills = literal_eval(row[5])
            group_info = {'group_id': row[0], 'group_admin': row[1],
                          'users': list_users, 'title': row[3], 'description': row[4],
                          'bills': list_bills, 'creation_time': row[6]}
            return group_info
    return False


# function to get the bill_ids for a group_id
def get_groups_bills(db_connection, group_id):
    cursor = db_connection.execute('''SELECT bill_ids FROM GROUPS where ID="{group_id}" 
    '''.format(group_id=group_id))
    for row in cursor:
        if row:
            return row[0]
    db_connection.commit()
    return False


# function to get data of a bill
def get_bill_data(db_connection, bill_id):
    cursor = db_connection.execute('''SELECT ID,uploader,title,datetime,amount,description,image_name,category,share,
    payer,group_id FROM GROUP_BILLS where ID="{bill_id}" 
        '''.format(bill_id=bill_id))
    for row in cursor:
        if row:
            share = safe_load(row[8])
            bill_info = {'bill_id': row[0], 'uploader': row[1],
                         'title': row[2], 'datetime': row[3], 'amount': row[4],
                         'description': row[5], 'image_name': row[6],
                         'category': row[7], 'share': share,
                         'payer': row[9], 'group_id': row[10]}
            return bill_info
    db_connection.commit()
    return False


# function to get bill name
def get_bill_name(db_connection, bill_id):
    cursor = db_connection.execute('''SELECT title FROM GROUP_BILLS where ID="{bill_id}" 
        '''.format(bill_id=bill_id))
    for row in cursor:
        if row:
            return row[0]
    db_connection.commit()
    return False