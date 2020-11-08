import pickle


def example():
    Credentials_data = {
        "aws_access_key_id": "<write the key here>",
        "aws_secret_access_key": '<write the key here>'
    }
    credentials = open('credentials', 'wb')
    #  usage:pickle.dump(<source>, <destination>)
    pickle.dump(Credentials_data, credentials)
    credentials.close()
    credentials = open('credentials', 'rb')
    #  print(credentials.read())
    db = pickle.load(credentials)
    for keys in db:
        print(keys, '=>', db[keys])
    credentials.close()


if __name__ == '__main__':
    example()
