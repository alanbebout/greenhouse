import pandas
import numpy
import random
import matplotlib.pyplot
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn import neighbors
from sklearn import svm
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score, confusion_matrix,ConfusionMatrixDisplay,RocCurveDisplay
import pickle 

random.seed()

idx = 0
randTemps = []
randMoistures = []
labels = []

upperBoundTemp = 120
lowerBoundTemp = 30

def EvaluateClassifier(theModel,testData,testTrueCategories,modelDescriptor):
    predictedCategories = theModel.predict(testData)

    precision = precision_score(testTrueCategories,predictedCategories,average="weighted")
    recall = recall_score(testTrueCategories,predictedCategories,average="weighted")
    f1 = f1_score(testTrueCategories,predictedCategories,average="weighted")
    accuracy = accuracy_score(testTrueCategories,predictedCategories)
    confusionMatrix = confusion_matrix(testTrueCategories,predictedCategories)

    print(modelDescriptor + " -----------------------------------------")
    print(f"Precision: {precision:.2f}")
    print(f"Recall: {recall:.2f}")
    print(f"F1 Score: {f1:.2f}")
    print(f"Accuracy: {accuracy:.2f}")

    ConfusionMatrixDisplay.from_predictions(testTrueCategories,predictedCategories)
    matplotlib.pyplot.savefig(f"ConfusionMatrix_{modelDescriptor}.png")
    matplotlib.pyplot.show()

def ClassifyCondition(temp,moisture):

    #an oval of acceptability
    value1 = ((temp-70)**2)/80 + ((moisture-0.5)**2)*30
    value2 = temp < 70
    value3 = moisture < 0.5
    
    if value1 < 1:
        label = "SAFE"
    else:
        #cold and dry
        if value2 and value3:
            label = "ATACAMA"
        # cold and wet
        if value2 and (not value3):
            label = "KAMCHATKA"
        # hot and dry
        if (not value2) and value3:
            label = "SAHARA"
        # hot and wet
        if (not value2) and (not value3):
            label = "AMAZON"
        
    return label
    
trainingDataFile = open("TrainingDataFile.csv","w")
while idx < 10000:
    randTemp = random.randrange(lowerBoundTemp, upperBoundTemp, 1)
    randMoisture = random.randrange(0,1000,1) / 1000
    theLabel = ClassifyCondition(randTemp,randMoisture)
    randTemps.append(randTemp)
    randMoistures.append(randMoisture)
    labels.append(theLabel)
    trainingDataFile.write(str(randTemp)+ "," + str(randMoisture) + "," + str(theLabel) + "\n")
    idx = idx + 1

dataFrame = pandas.read_csv("TrainingDataFile.csv", names = ["temp","moisture","label"])

valueCols = ["temp","moisture"]
x = dataFrame[valueCols]
y = dataFrame["label"]

x_train, x_test, y_train, y_test = train_test_split(x,y,test_size=0.2,random_state = 8675309)
modelDescriptor = "KNearestNeighbors_3"
model = neighbors.KNeighborsClassifier(n_neighbors=3)
model.fit(x_train,y_train)
modelSaveFileName = "GREENHOUSE_"+modelDescriptor + ".sav"
pickle.dump(model,open(modelSaveFileName,'wb'))
EvaluateClassifier(model,x_test,y_test,modelDescriptor)



