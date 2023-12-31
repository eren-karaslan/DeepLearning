# -*- coding: utf-8 -*-
"""LSTM.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/152bRNAx4qu1e8OQ_AnAeHMmSh_l8uaPl

"""


import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt

#Model değerlendirme ve veriyi scale etmek için kütüphaneler
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

#Model için kütüphaneler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense,LSTM,Dropout
from tensorflow.keras.callbacks import ModelCheckpoint,EarlyStopping

#Warningleri kapatmak için
import warnings
warnings.filterwarnings('ignore')


import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

from google.colab import drive
drive.mount('/content/drive',force_remount=True)

dir_path= '/content/drive/MyDrive/TSLA.csv'
print(dir_path)

df=pd.read_csv(dir_path)
df.head()

def check_df(dataframe,head=5):
  print("################################## Shape #########################")
  print(dataframe.shape)
  print("################################## Types #########################")
  print(dataframe.dtypes)
  print("################################## Head #########################")
  print(dataframe.head(head))
  print("################################## Tail #########################")
  print(dataframe.tail(head))
  print("################################## NA #########################")
  print(dataframe.isnull().sum())
  print("################################## Quantiles #########################")
  print(dataframe.quantile([0 , 0.05 , 0.50 , 0.95 , 0.99 , 1]).T)

check_df(df)



df['Date'] = pd.to_datetime(df['Date']) #converting to datetime

df.head()

tesla_df= df[["Date","Close"]] #Only use this 2 column

print("Minimum Tarih: ",tesla_df["Date"].min())
print("Maksimum Tarih: ",tesla_df["Date"].max())

tesla_df.index=tesla_df["Date"]

tesla_df

tesla_df.drop("Date", axis=1, inplace=True) #axis=1 column 0 row,inplace=True permanent deleting

tesla_df

result_df=tesla_df.copy() 

plt.figure(figsize=(12,6))
plt.plot(tesla_df['Close'],color='blue')
plt.ylabel('Stock Price')
plt.xlabel('Time')
plt.show()

tesla_df=tesla_df.values

tesla_df[0:5]

tesla_df=tesla_df.astype('float32')

def split_data(dataframe, test_size):
  pos = int(round(len(dataframe) * (1-test_size)))
  train = dataframe[:pos]
  test = dataframe[pos:]
  return train,test,pos

train,test,pos = split_data(tesla_df,0.20)

print(train.shape,test.shape)

scaler_train = MinMaxScaler(feature_range = (0,1))
train = scaler_train.fit_transform(train)
scaler_test = MinMaxScaler(feature_range = (0,1))
test = scaler_test.fit_transform(test)

def create_features(data,lookback):
  X,Y = [],[]
  for i in range(lookback,len(data)):
    X.append(data[i-lookback:i,0])
    Y.append(data[i,0])
  return np.array(X),np.array(Y)

lookback=20  #last 20 days

X_train,y_train = create_features(train,lookback)
X_test,y_test = create_features(test,lookback)

print(X_train.shape, y_train.shape, X_test.shape, y_test.shape)

X_train[0:5] #everyday read data of last 20 days

y_train[0:5] #closing price of days

#For LSTM data have to be 3 dimensions
X_train= np.reshape(X_train,(X_train.shape[0], 1 ,X_train.shape[1]))
X_test=  np.reshape(X_test,(X_test.shape[0], 1 ,X_test.shape[1]))
y_train= y_train.reshape(-1,1)
y_test=  y_test.reshape(-1,1)

print(X_train.shape,y_train.shape,X_test.shape,y_test.shape)


model=Sequential()

model.add(LSTM(units=50,
              activation='relu',
              input_shape=(X_train.shape[1], lookback)))
model.add(Dropout(0.2))
model.add(Dense(1)) #one cell for output,because we expect number

model.summary()


model.compile(loss='mean_squared_error' , optimizer='adam')

callbacks=[EarlyStopping(monitor='val_loss',patience=3,verbose=1,mode='min'),
           ModelCheckpoint(filepath='mymodel.h5',monitor='val_loss',mode='min',
                           save_best_only=True,save_weights_only=False,verbose=1)]

history=model.fit(x=X_train,
                  y=y_train,
                  epochs=100,
                  batch_size=20,
                  validation_data=(X_test,y_test),
                  callbacks=callbacks,
                  shuffle=False) #if shuffle is false data is not shuffling

plt.figure(figsize=(20,5))
plt.subplot(1,2,2)
plt.plot(history.history['loss'],label='Training Loss')
plt.plot(history.history['val_loss'],label='Validation Loss')
plt.legend(loc='upper right')
plt.xlabel('Epoch' ,fontsize=16)
plt.ylabel('Loss' ,fontsize=16)
plt.ylim([0,max(plt.ylim())])
plt.title('training and Validation Loss',fontsize=16)
plt.show()



loss = model.evaluate(X_test,y_test,batch_size=20)
print("\nTest loss: %.1f%%" % (100.0 * loss))

train_predict=model.predict(X_train)
test_predict=model.predict(X_test)

train_predict=scaler_train.inverse_transform(train_predict)
test_predict=scaler_test.inverse_transform(test_predict)  

y_train=scaler_train.inverse_transform(y_train) 
y_test=scaler_test.inverse_transform(y_test)

#Train verisetine ait RMSE değeri
train_rmse= np.sqrt(mean_squared_error(y_train,train_predict))

#Test verisetine ait RMSE değeri
test_rmse= np.sqrt(mean_squared_error(y_test,test_predict))

print(f"Train RMSE: {train_rmse}") 
print(f"Test RMSE: {test_rmse}")

train_prediction_df=result_df[lookback:pos]
train_prediction_df["Predicted"] = train_predict
train_prediction_df.head()
#first 19 values is same,because this code look last 20 days

test_prediction_df=result_df[pos+lookback:]
test_prediction_df["Predicted"] = test_predict
test_prediction_df.head()