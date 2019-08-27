import boto3
from PIL import Image
import io
import base64
import requests
import json
import sys
import re


def extractReceipt(data):
    cost = re.compile("^[0-9]+\.[0-9]+$")
    date = re.compile(
        "^[0-9][0-9]/[0-9][0-9]/([0-9][0-9][0-9][0-9]|[0-9][0-9])$")
    nextname = False
    getName = True
    myList = []
    for x in data["Blocks"]:
        if (x["BlockType"] != "PAGE" and x["BlockType"] != "KEY_VALUE_SET"):
            if (getName):
                if (cost.match(x["Text"]) and nextname == False):
                    myList.append(x["Text"])
                    nextname = True
                elif (nextname):
                    myList.append(x["Text"])
                    getName = False
            elif (date.match(x["Text"])):
                if (len(x["Text"]) == 8):
                    myList.append(
                        "20" + x["Text"][6:8] + "-" + x["Text"][0:2] + "-" + x["Text"][3:5])
                elif (len(x["Text"]) == 10):
                    myList.append(x["Text"][6:10] + "-" +
                                  x["Text"][0:2] + "-" + x["Text"][3:5])
                break
    return (myList)

if __name__ == "__main__":
    # imgdata = base64.b64decode(imgstring)
    # filename = 'some_image.jpg' 
    # with open(filename, 'wb') as f:
    #     f.write(imgdata)

    client = boto3.client('rekognition',
                          aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY,
                          region_name="us-east-2")

    image_path = 'a.jpg'
    image = Image.open(image_path)

    stream = io.BytesIO()
    image.save(stream, format="JPEG")
    image_binary = stream.getvalue()

    # with open(image_path, 'rb') as imageFile:
    #     data = base64.b64encode(imageFile.read()).decode()
    # print(data)
    # r = requests.post('http://localhost:5000/sendImage', json={"binary": data})

    # print(json.loads(r.text))

    response = client.detect_labels(
        Image={'Bytes': image_binary}, MaxLabels=10)
    labels = response['Labels']
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
        x["Parents"]) == 0 and x['Name'] in parents][0]

    print(likelyProduct)
    print(likelyParent)
    # client.close()
    client=boto3.client('textract',
    aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY,
    region_name="us-east-2")

    image_path='b.jpg'
    image = Image.open(image_path)

    stream = io.BytesIO()
    image.save(stream,format="JPEG")
    image_binary = stream.getvalue()

    response = client.analyze_document(Document={'Bytes': image_binary}, FeatureTypes=['FORMS'])
    print(extractReceipt(response))
