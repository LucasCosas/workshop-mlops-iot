from azureml.core.compute import ComputeTarget, AmlCompute
from azureml.core.compute_target import ComputeTargetException
from azureml.core import Environment, Experiment, Workspace, Dataset
from azureml.core.conda_dependencies import CondaDependencies
from azureml.core.runconfig import RunConfiguration
from azureml.pipeline.core import PipelineData, Pipeline
from azureml.pipeline.steps import PythonScriptStep, EstimatorStep
from azureml.train.estimator import Estimator
from azureml.core.datastore import Datastore
from azureml.data.data_reference import DataReference
import os

cluster_name = "azuremlcluster"

# Get Azure machine learning workspace

ws = Workspace.get(
    name=os.environ.get("AMLWORKSPACE_NAME"),
    subscription_id=os.environ.get("SUBSCRIPTION_ID"), 
    resource_group=os.environ.get("RESOURCE_GROUP"),
)

# Get all variables from the pipelines library

datasetname = os.environ.get("AMLDATASET")
filename = os.environ.get("DATASETFILENAME")
env_name = os.environ.get("ENVNAME")
modelname = os.environ.get("MODELNAME")
pipelinename = os.environ.get("PIPELINENAME")
default_ds = ws.get_default_datastore()
account_name = os.environ.get("STORAGENAME")
container_name = os.environ.get("CONTAINERNAME")
account_key = os.environ.get("STORAGEKEY")
blob_datastore_name = os.environ.get("AMLDATASTORE")

# if dataset is not registered

if datasetname not in ws.datasets:
    
    #Set blobdatastore only if it doesn't exists already    
    try:
        blob_datastore = Datastore.get(ws, blob_datastore_name)
        print("Found Blob Datastore with name: %s" % blob_datastore_name)
    except:
        blob_datastore = Datastore.register_azure_blob_container(
        workspace=ws,
        datastore_name=blob_datastore_name,
        account_name=account_name, # Storage account name
        container_name=container_name, # Name of Azure blob container
        account_key=account_key) # Storage account key
        print("Registered blob datastore with name: %s" % blob_datastore_name)

    print(filename)
    csvrelative = '/' + filename
    # Update following line with your training dataset file
    csv_path = (blob_datastore, csvrelative)
    #csv_path = (blob_datastore, '/creditcard.csv')

    try:
        tab_ds = Dataset.Tabular.from_delimited_files(path=csv_path)
        #Update following line with the dataset name you'll register at AML
        tab_ds = tab_ds.register(workspace=ws, name=datasetname)
    except Exception as ex:
        print(ex)
else:
    print('Dataset already registered.')

experiment_folder = './model/scripts'

# Verify that cluster exists
try:
    pipeline_cluster = ComputeTarget(workspace=ws, name=cluster_name)
    print('Found existing cluster, use it.')
except ComputeTargetException:
    # If not, create it
    compute_config = AmlCompute.provisioning_configuration(vm_size='STANDARD_D2_V2',
                                                           max_nodes=4,
                                                           idle_seconds_before_scaledown=1800)
    pipeline_cluster = ComputeTarget.create(ws, cluster_name, compute_config)

pipeline_cluster.wait_for_completion(show_output=True)


# Create a Python environment for the experiment

model_env = Environment(env_name)
model_env.python.user_managed_dependencies = False # Let Azure ML manage dependencies
model_env.docker.enabled = True # Use a docker container

# Create a set of package dependencies
packages = CondaDependencies.create(conda_packages=['scikit-learn','pandas'],
                                             pip_packages=['azureml-sdk'])

# Add the dependencies to the environment
model_env.python.conda_dependencies = packages

# Register the environment (just in case you want to use it again)
model_env.register(workspace=ws)

registered_env = Environment.get(ws, env_name)

# Create a new runconfig object for the pipeline
pipeline_run_config = RunConfiguration()

# Use the compute you created above. 
pipeline_run_config.target = pipeline_cluster

# Assign the environment to the run configuration
pipeline_run_config.environment = registered_env

print ("Run configuration created.")


# Get the training dataset
train_ds = ws.datasets.get(datasetname)

# Create a PipelineData (temporary Data Reference) for the model folder
model_folder = PipelineData("model_folder", datastore=ws.get_default_datastore())
#pipeline_data = PipelineData('pipeline_data',  datastore=default_ds)

data_ref = DataReference(datastore=default_ds, data_reference_name = 'data_ref', path_on_datastore="config/")

estimator = Estimator(source_directory=experiment_folder,
                        compute_target = pipeline_cluster,
                        environment_definition=pipeline_run_config.environment,
                        entry_script='train.py')

# Step 1, run the estimator to train the model
train_step = EstimatorStep(name = "Train Model",
                           estimator=estimator,
                           estimator_entry_script_arguments=['--output_folder', model_folder, '--data_dir', data_ref],
                           inputs=[train_ds.as_named_input('train_ds'), data_ref],
                           outputs=[model_folder],
                           compute_target = pipeline_cluster,
                           allow_reuse = True)

# Step 2, run the model registration script
register_step = PythonScriptStep(name = "Register Model",
                                source_directory = experiment_folder,
                                script_name = "register.py",
                                arguments = ['--model_folder', model_folder, '--modelname', modelname],
                                inputs=[model_folder],
                                compute_target = pipeline_cluster,
                                runconfig = pipeline_run_config,
                                allow_reuse = True)

print("Pipeline steps defined")

# Construct the pipeline
pipeline_steps = [train_step, register_step]
pipeline = Pipeline(workspace = ws, steps=pipeline_steps)
print("Pipeline is built.")

# Create an experiment and run the pipeline
experiment = Experiment(workspace = ws, name = pipelinename)
pipeline_run = experiment.submit(pipeline, regenerate_outputs=True)
print("Pipeline submitted for execution.")

# RunDetails(pipeline_run).show()
pipeline_run.wait_for_completion()

published_pipeline = pipeline.publish(name=pipelinename,
                                      description="Trains " + modelname + " model",
                                      version="1.0")
rest_endpoint = published_pipeline.endpoint

print(rest_endpoint)