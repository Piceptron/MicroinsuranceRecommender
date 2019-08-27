# MyMicroinsurance Manager and Recommender app Backend

## Features
Parses and manages assets provided in the form of images, and
recommends optimal insurance for all your assets

## Deploying on AWS
Zip application.py, regressor.h5, requirements.txt, and StandardScaler to zip file
and upload zip file to Elastic Beanstalk.

## Endpoints
**/sendImage:** takes input image in base64 and sends it to AWS Rekognition
to understand what the image is and a category for the image,
then queries the MySQL database for a valuation of that type of product.
If the return product is similar looking to a receipt, will call
AWS Textract to parse out information from the receipt, and
collects the asset information including valuation from the parsed text.

**/addAsset:**
adds an asset to the database

**/getAllAssets:**
returns json containing list of all assets 
recorded in the database

**/getTop4Assets:**
returns json containing list of 4 most recent assets 
recorded in the database

**/getRecommendations:**
returns json containing list of all recommendations
for the user using his current assets recorded in the database.
Recommendations taken from Keras Neural Network currently trained with dummy data.

**/get4Recommendations:**
returns json containing list of top 4 most confident recommendations
for the user using his current assets recorded in the database.
Recommendations taken from Keras Neural Network currently trained with dummy data.

## Technology Stack
Endpoints hosted with Flask, MySQL database, predictions using Keras model.
