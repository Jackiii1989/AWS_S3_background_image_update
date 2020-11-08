import boto3
import pickle
import os
import ctypes
import json
import logging
import datetime

FILE_PATH = os.path.abspath(__file__)
BASE_DIR = os.path.dirname(FILE_PATH)

logging.basicConfig(filename="logger.log",
                    filemode='a',
                    format='%(asctime)s %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)


class background_image_update:
    def __init__(self, json_conf_path: str = "configuration.json"):
        self.logger = logging.getLogger('Back-Img-log')
        self.current_month = datetime.datetime.now().month  # for resetting the count at each start of the month
        self.check_and_load_json__conf_file(json_conf_path)
        ##  get the credentials in abs path
        credentials_file_path = self.json_conf_parameters['credentials_file_path']
        abs_credentials_path = os.path.join(BASE_DIR, credentials_file_path)
        self.load_credentials_data(abs_credentials_path)

    def load_credentials_data(self, abs_credentials_path: str):
        try:
            with open(abs_credentials_path, 'rb') as cred_file:
                self.cred = pickle.load(cred_file)
        except Exception as e:
            self.logger.error("Can not read the credentials file. Exception: ", e)
            exit(-1)

    def check_and_load_json__conf_file(self, json_conf_path: str):
        abs_json_conf_path = os.path.join(BASE_DIR, json_conf_path)
        if not os.path.exists(json_conf_path):
            self.logger.error("Json Configuration file is missing. Please add it!")
            exit(-1)
        self.abs_json_conf_path = abs_json_conf_path
        try:
            with open(self.abs_json_conf_path, 'r') as jsonData:
                self.json_conf_parameters = json.load(jsonData)
        except Exception as e:
            logging.error("Can not read the configuration.json file.Exception:", e)

    def start(self):
        s3 = boto3.client('s3',
                          aws_access_key_id=self.cred['aws_access_key_id'],
                          aws_secret_access_key=self.cred['aws_secret_access_key'],
                          region_name='eu-central-1')
        ## load the needed parameters
        temporary_image_name = self.json_conf_parameters['temporary_image_name']
        bucket_to_download = self.json_conf_parameters['bucket_to_download']
        index_number_of_the_images_in_AWS = self.json_conf_parameters['index_number_of_the_images_in_AWS']
        ## get the number of elements(jpg) in the cloud and check if the counter did not exceed the max value
        Meta_data_combined_with_data = s3.list_objects(Bucket=bucket_to_download)
        list_leng = len(Meta_data_combined_with_data['Contents'])
        if index_number_of_the_images_in_AWS == list_leng:
            index_number_of_the_images_in_AWS = 1
        ## check if we are in the next month and reset the execution counter
        if self.current_month != self.json_conf_parameters['number_of_month']:
            self.json_conf_parameters['number_of_execution'] = 1
            self.json_conf_parameters['number_of_month'] = self.current_month
        ## get the object name, download the image and save as defined in 'temporary_image_name'
        Object_name = Meta_data_combined_with_data['Contents'][index_number_of_the_images_in_AWS]['Key']
        s3.download_file(bucket_to_download, Object_name, temporary_image_name)
        # increment the counter for the next time in json configuration file
        self.json_conf_parameters['index_number_of_the_images_in_AWS'] = index_number_of_the_images_in_AWS + 1
        ## get the full path and update the background image
        abs_temp_image_path = os.path.join(BASE_DIR, temporary_image_name)
        self.get_billing_information()
        self.__update_windows_background_image(abs_temp_image_path)
        self.json_conf_parameters['number_of_execution'] += 1  # increment the number of execution
        self.__update_json_configuration_file()

    def __update_json_configuration_file(self):
        with open(self.abs_json_conf_path, 'w') as f:
            json.dump(self.json_conf_parameters, f)

    def __update_windows_background_image(self, abs_image_path: str):
        SPI_SETDESKWALLPAPER = 20  # code for setting the desk image
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, abs_image_path, 0)
        # more info: http://timgolden.me.uk/pywin32-docs/win32gui__SystemParametersInfo_meth.html
        self.logger.info(f"image updated! Number of execution/s:"
                         f"'{self.json_conf_parameters['number_of_execution']}' "
                         f"and the costs for today:{self.str_amount} {self.str_currency}")

    def get_billing_information(self):
        billing = boto3.client('ce',
                               aws_access_key_id=self.cred['aws_access_key_id'],
                               aws_secret_access_key=self.cred['aws_secret_access_key'],
                               )
        ## get the date range from where the report will be generated
        str_first_day_of_month = str(datetime.datetime.today().replace(day=1).strftime('%Y-%m-%d'))
        str_today = str(datetime.date.today())
        # str_yesterday = str(datetime.date.today() - datetime.timedelta(days=1))
        ## execute the call for getting the billing information
        try:
            r = billing.get_cost_and_usage(
                TimePeriod={
                    'Start': str_first_day_of_month,
                    'End': str_today
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost']
            )
            # extract the date from the response
            for data in r['ResultsByTime']:
                self.str_amount = data['Total']['UnblendedCost']['Amount']
                self.str_currency = data['Total']['UnblendedCost']['Unit']
        except Exception as e:
            self.logger.error("Error in the billing API. Exception:", e)
            exit(-1)


if __name__ == '__main__':
    obj = background_image_update()
    obj.start()
