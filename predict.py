from keras.models import load_model
from sklearn.externals import joblib

scaler_filename = "minMaxScaler"
model = load_model('regressor.h5')

scaler = joblib.load(scaler_filename)

names = ["Pc","Laptop","Rug","Wristwatch","Door","Headphones","Chair","Keyboard","Wood","Shoe","Clothing","Mouse","Bottle"]

db = getDB()
cursor = db.cursor()
query = "Select name from assets t1 join valuation t2 where t1.name = t2.name groupby name"
cursor.execute(query)
resultList = cursor.fetchall()[0]
resultList = [x for x in resultList]
x_val = []
for name in names:
    if name in resultList:
        x_val.append(1)
    else:
        x_val.append(0)
logging.error(x_val)
x_val = [x_val]
x_val = scaler.transform(x_val)
predictions = model.predict(x_val)