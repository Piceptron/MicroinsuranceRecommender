from flask import Flask, request, jsonify, make_response
import MySQLdb
import boto3
import re
import logging
import base64
from keras.models import load_model
from sklearn.externals import joblib
import numpy as np
import tensorflow as tf

scaler_filename = "StandardScaler"
model = load_model('regressor.h5')
scaler = joblib.load(scaler_filename)
graph = tf.get_default_graph()

def extractReceipt(data):
    # logging.error(data)
    cost = re.compile("^[0-9]+\.[0-9]+$")
    date = re.compile(
        "^([0-9]|[0-9][0-9])/[0-9][0-9]/([0-9][0-9][0-9][0-9]|[0-9][0-9])$")
    nextname = False
    getName = True
    response = {}
    for x in data["Blocks"]:
        if (x["BlockType"] != "PAGE" and x["BlockType"] != "KEY_VALUE_SET"):
            if (getName):
                if (cost.match(x["Text"]) and nextname == False):
                    response["value"]=int(float(x["Text"]))
                    nextname = True
                elif (nextname):
                    response["name"]=x["Text"]
                    getName = False
            elif (date.match(x["Text"])):
                if (len(x["Text"]) == 8):
                    response["purchaseDate"] = ("20" + x["Text"][6:8] + "-" + x["Text"][0:2] + "-" + x["Text"][3:5])
                elif (len(x["Text"]) == 7):
                    response["purchaseDate"]= ("20" + x["Text"][5:7] + "-" + "0" + x["Text"][0:1] + "-" + x["Text"][2:4])
                elif (len(x["Text"]) == 10):
                    response["purchaseDate"]=(x["Text"][6:10] + "-" +
                                  x["Text"][0:2] + "-" + x["Text"][3:5])
                elif (len(x["Text"]) == 9):
                    response["purchaseDate"]=(x["Text"][5:9] + "-" + "0" +
                                  x["Text"][0:1] + "-" + x["Text"][2:4])
                break
    return (response)


def getDB():
    return MySQLdb.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, passwd=DB_PASS, db=DB_NAME)

# def getDB():
#   return MySQLdb.connect(unix_socket='/cloudsql/' + INSTANCE_NAME, db=DB_NAME, user=DB_USER, passwd=DB_PASS, charset='utf8')


def testing():
    content = request.json
    return content


def testDB():
    logging.basicConfig(filename='/opt/python/log/my.log', level=logging.DEBUG)
    logging.error('This is an error messagessss')
    db = getDB()
    cursor = db.cursor()
    cursor.execute("Select * from test")
    return {"name": cursor.fetchall()[1][0]}


def sendReceipt(image_binary, confidence):
    client = boto3.client('textract',
                          aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY,
                          region_name="us-east-2")
    response = client.analyze_document(
        Document={'Bytes': image_binary}, FeatureTypes=['FORMS'])
    output = {
        "name": "",
        "confidence": confidence,
        "description": "",
        "value": 0,
        "purchaseDate": ""
    }
    extracted = extractReceipt(response)
    for key, value in extracted.items():
        output[key]=value
    # we dont currently parse category yet
    output["category"] = output["name"]
    logging.error(output)
    return output


def sendImage():
    # print('in sendImage start print')
    logging.basicConfig(filename='/opt/python/log/my.log', level=logging.DEBUG)
    logging.error('in sendImage start')
    content = request.json
    # logging.error("cont: ", str(content))
    # print(str(content))
    image_binary = base64.b64decode(content)
    # print(image_binary)
    client = boto3.client('rekognition',
                          aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY,
                          region_name="us-east-2")
    
    response = client.detect_labels(
        Image={'Bytes': image_binary}, MaxLabels=10)
    logging.error(response)
    labels = response['Labels']
    receipt = [x for x in labels if x["Name"] in ["Text", "Paper"]]
    receiptCount = len(receipt)
    # recognize text or paper means it should be a receipt, since people dont insure text or paper
    if receiptCount != 0:
        # highest is more likely guess
        confidence = max(receipt, key=lambda x: x["Confidence"])["Confidence"]
        obj = sendReceipt(image_binary, confidence)
        logging.error(obj)
        return make_response(jsonify(obj))

    maxConfidence = max(labels, key=lambda x: x["Confidence"])["Confidence"]
    # list of objects most confident about
    mostLikelyList = [x for x in labels if x["Confidence"] == maxConfidence]
    maxParents = len(
        max(mostLikelyList, key=lambda x: len(x["Parents"]))["Parents"])
    # Take the first product if there are many
    likelyProduct = [x for x in mostLikelyList if len(
        x["Parents"]) == maxParents][0]
    parents = [x["Name"] for x in likelyProduct["Parents"]]
    # should have a parent found if it has parents
    likelyParent = [x for x in mostLikelyList if len(
        x["Parents"]) == 0 and x['Name'] in parents]
    if not likelyParent:
        likelyParent = likelyProduct
    else:
        likelyParent = likelyParent[0]

    db = getDB()
    cursor = db.cursor()
    cursor.execute("Select * from valuation where name = \'" +
                   likelyProduct["Name"] + "\'")

    logging.error(response)
    results = cursor.fetchall()
    if len(results) > 0:
        logging.error(results)
        logging.error(results[0][1])
        results = int(results[0][1])
    else:
        results = 0
    product = {
        "name": likelyProduct["Name"],
        "confidence": likelyProduct["Confidence"],
        "category": likelyParent["Name"],
        "description": "",
        "value": results,
        "purchaseDate": ""
    }
    return make_response(jsonify(product))


def addAsset():
    content = request.json
    db = getDB()
    cursor = db.cursor()
    query = ("Insert into assets (name, category, description, `value`, purchaseDate, `binary`) values (\'%s\', \'%s\', \'%s\', \'%s\', \'%s\', \'%s\')"
       % (content["name"], content["category"], content["description"], content["value"], content["purchaseDate"], content["binary"]))
    print(query)
    cursor.execute(query)
    db.commit()
    return "success"

def getAllAssets():
    names = ["id", "name", "category", "description",
             "value", "purchaseDate", "binary"]
    db = getDB()
    cursor = db.cursor()
    query = "Select `" + "`, `".join(names) + "` from assets"
    cursor.execute(query)
    assets = []
    print(query)
    for row in cursor.fetchall():
        asset = {}
        for i in range(len(names)):
            asset[names[i]] = row[i]
        assets.append(asset)
    return make_response(jsonify({"assets": assets}))


def getTop4Assets():
    names = ["id", "name", "category", "description",
             "value", "purchaseDate", "binary"]
    db = getDB()
    cursor = db.cursor()
    query = "Select `" + "`, `".join(names) + "` from assets order by id desc limit 4"
    cursor.execute(query)
    assets = []
    print(query)
    for row in cursor.fetchall():
        asset = {}
        for i in range(len(names)):
            asset[names[i]] = row[i]
        assets.append(asset)
    return make_response(jsonify({"assets": assets}))

#limit = -1
def getRecommendations(limit = -1):
    global model
    global scaler
    # logging.basicConfig(filename='/opt/python/log/my.log', level=logging.DEBUG)
    # scaler_filename = "s3://elasticbeanstalk-us-east-2-670621294440/Model/StandardScaler"
    # logging.error("hello")
    # model = load_model('s3://elasticbeanstalk-us-east-2-670621294440/Model/regressor.h5')
    # logging.error("hello")
    print("hi")
    # logging.error("hello")
    names = ["Pc","Laptop","Rug","Wristwatch","Door","Headphones","Chair","Keyboard","Wood","Shoe","Clothing","Mouse","Bottle"]
    # logging.error("hello")
    db = getDB()
    cursor = db.cursor()
    query = "Select t1.name from assets t1 join valuation t2 where t1.name = t2.name group by name"
    cursor.execute(query)
    resultList = cursor.fetchall()
    # ignore first entry which is table name
    # logging.error(resultList)
    resultList = [x[0] for x in resultList]
    x_val = []
    for name in names:
        if name in resultList:
            x_val.append(1)
        else:
            x_val.append(0)
    # logging.error(x_val)
    x_val = [x_val]
    x_val = scaler.transform(x_val)
    print(x_val)
    with graph.as_default():
        predictions = model.predict(np.array(x_val))
        predictions = predictions[0] 
    tempList = []
    for i in range(len(predictions)):
        tempList.append([i,predictions[i]])
    tempList = sorted(tempList, key=lambda x: x[1], reverse=True)
    print(tempList)
    out = [names[x[0]] for x in tempList]
    # query = "Select * from policy t1 join valuation t2 where t1.name = t2.name group by name"
    # cursor.execute(query)
    names = ["name", "premium", "description"]
    query = "Select `" + "`, `".join(names) + "` from policy where name in (\'"+ "\', \'".join(out)+"\')"
    print(query)
    cursor.execute(query)
    policies = []
    print(query)
    for row in cursor.fetchall():
        asset = {}
        for i in range(len(names)):
            asset[names[i]] = row[i]
        policies.append(asset)
    if limit == -1:
        return make_response(jsonify({"policies": policies}))
    return make_response(jsonify({"policies": policies[:limit]}))


application = Flask(__name__)

application.add_url_rule('/', "index", view_func=testDB)

application.add_url_rule(
    '/sendImage', view_func=sendImage, methods=['POST', ])

application.add_url_rule(
    '/addAsset', view_func=addAsset, methods=['POST', ])

application.add_url_rule('/post', view_func=testing, methods=['POST', ])

application.add_url_rule(
    '/getAllAssets', view_func=getAllAssets)

application.add_url_rule(
    '/getTop4Assets', view_func=getTop4Assets)

application.add_url_rule(
    '/getRecommendations', view_func=getRecommendations)

application.add_url_rule(
    '/get4Recommendations', view_func=lambda: getRecommendations(4))

if __name__ == "__main__":
    application.debug = True
    application.run(debug=True)
