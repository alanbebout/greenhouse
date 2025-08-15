from fastapi import FastAPI
import time
import platform
import serial
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn import neighbors
from sklearn import svm
import pickle 
import sys
import statistics

app = FastAPI()

@app.get("/prediction")
def recieve_data(data):

    pathToModel = "/Users/alanbebout/Desktop/SU25FinalExam/GREENHOUSE_KNearestNeighbors_3.sav"
    theModel = pickle.load(open(pathToModel,'rb'))

    print(data)
    dataToks = data.split(',')
    print(dataToks)
    data = []
    for tok in dataToks:
        print(tok)
        data.append(float(tok))

    print(data)
    y_pred = theModel.predict([data])
    print(y_pred)

    prediction: str=str(y_pred)
    return {"prediction": f"{prediction}"}