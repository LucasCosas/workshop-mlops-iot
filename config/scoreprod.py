from azureml.core.model import Model
import json
import pickle
import pandas as pd
import joblib



# Called when the service is loaded
def init():
    global model
    # Get the path to the deployed model file and load it
    model_path = Model.get_model_path(model_name = 'iot_model-production')
    
    model = joblib.load(model_path)
    

# Called when a request is received
def run(raw_data):
    # Get the input data as a numpy array
    data = json.loads(raw_data)['data']
    # Get a prediction from the model
    predictions = model.predict(data)    
    # Return the predictions as JSON
    return predictions.tolist()

