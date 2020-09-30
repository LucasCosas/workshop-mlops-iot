from azureml.core import Run
import argparse
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification
from sklearn.metrics import roc_auc_score, f1_score
import shutil
import os

# Get parameters
parser = argparse.ArgumentParser()
parser.add_argument('--output_folder', type=str, dest='output_folder', default="model", help='output folder')
parser.add_argument('--data_dir', dest='data_dir')
args = parser.parse_args()
output_folder = args.output_folder
data_dir = args.data_dir #.data_dir 


# Get the experiment run context
run = Run.get_context()

# load the data (passed as an input dataset)
print("Loadng Data...")

# ----------------------------------------------------------------------------------------------------------------------------
# Training Model Logic Below

# Retrieves the dataset passes by the setup pipeline

iot_df = run.input_datasets['train_ds'].to_pandas_dataframe()

print(iot_df)

# Separate features and labels
X, y = iot_df.drop(['sensor_status', 'sensor_id', 'EventProcessedUtcTime', 'PartitionId', 'EventEnqueuedUtcTime'],axis=1).values, iot_df['sensor_status'].values

# Split data into training set and test set
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.30, random_state=42)
print(iot_df.head())

# Train a decision tree model
model = RandomForestClassifier(n_estimators=2,random_state=42)
model.fit(X_train, y_train)

print('Training a decision tree model')

# calculate accuracy
y_hat = model.predict(X_test)
acc = np.average(y_hat == y_test)
print('Accuracy:', acc)
run.log('Accuracy', np.float(acc))

#calculate F1-score
f1score = f1_score(y_test, y_hat, average='weighted')
print('F1-score: ', f1score)
run.log('F1-score', f1score)


# -------------------------------------------------------------------------------------------------------------------------------------
# Save the trained model

os.makedirs(output_folder, exist_ok=True)
output_path = output_folder + "/model.pkl"
joblib.dump(value=model, filename=output_path)

run.complete()