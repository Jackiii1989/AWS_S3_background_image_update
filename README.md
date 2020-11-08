# AWS_S3_background_image_update

## Description

It is a background-image-updater application that gets the image from AWS S3 and updates the background image.
In order to free the disk of the PC and still have a Diashow runnnig with the images you like.

## Instructions( or what to execute):

1. pip install -r requirements.txt
2. python create_credentials_file.py <aws_access_key_id> <aws_secret_access_key> (P.S. the AWS user to whom the credential belong should have S3 and billing function get_cost_usage() access.)
3. update the configuration.json in the fields '<' '>' to define the configuration. For instance, to define the bucket where it should pull the images
3. run AWS_S3_background_image_update.pyw to see if it is working.


You can see if the execution went fine by looking in the logger.log file. Inside
