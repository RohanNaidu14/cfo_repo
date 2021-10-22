import mysql.connector


def get_connection(input_host, input_port, input_username, input_password, input_database):
    '''
        PROVIDING DB ACCESS
    '''

    mydb = mysql.connector.connect(
    host = input_host,
    port = input_port,
    user = input_username,
    passwd = input_password,
    database = input_database,
    )

    return mydb


def check_connection(input_db):
    '''
        CHECKS IF DB IS CONNECTED
    '''

    if input_db.is_connected() == True:
        return 'db connected'
    else:
        return 'db disconnected'