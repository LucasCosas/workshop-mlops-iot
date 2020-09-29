import argparse
import joblib
from azureml.core import Workspace, Model, Run

# Get parameters
parser = argparse.ArgumentParser()
parser.add_argument('--model_folder', type=str, dest='model_folder', default="model", help='model location')
parser.add_argument('--modelname', type=str, dest='modelname', default="modelname", help='model name')
args = parser.parse_args()
model_folder = args.model_folder
model_name = args.modelname

# Get the experiment run context
run = Run.get_context()

Model.register(workspace=run.experiment.workspace,
               model_path = model_folder,
               model_name = model_name)

run.complete()