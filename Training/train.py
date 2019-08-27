from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import RMSprop
from sklearn.preprocessing import StandardScaler
from sklearn.externals import joblib
import pandas as pd
import numpy as np

scaler_filename = "StandardScaler"

x_train = pd.read_csv('x.csv')
y_train = pd.read_csv('y.csv')

# feature scale
scaler = StandardScaler()
training_set_scaled = scaler.fit_transform(x_train)
joblib.dump(scaler, scaler_filename)

x_train, y_train = np.array(x_train), np.array(y_train)

classifier = Sequential()
classifier.add(Dense(7, input_dim=13, activation='relu'))
classifier.add(Dense(7, activation='relu'))
classifier.add(Dense(13, activation='softmax'))
classifier.compile(loss='categorical_crossentropy', optimizer=RMSprop(lr=0.001), metrics=['accuracy'])
classifier.fit(x_train,y_train,epochs=30,batch_size=16,validation_split=0.1)

classifier.save('regressor.h5')