# MLOPS 

### Create resources

Go to portal.azure.com and create the following resources:

- Resource Group (which will contain our services)
- Azure Machine Learning workspace
- Storage Account and a container

### Data and Storage Account

Download the csv in the link below and upload into a new container in the previously created Storage Account

https://storagemlops.blob.core.windows.net/fraud/creditcard.csv?sp=r&st=2020-09-22T20:16:07Z&se=2023-02-01T04:16:07Z&spr=https&sv=2019-12-12&sr=b&sig=Ko6xp1yKEIGed7hgpdnHXTxNV1m7fByPE6S%2BLvSfK%2FQ%3D

Take note of the Storage Account name, container name and key

### Clone Repository & Create Environment Library  

Start in DevOps by creating a new blank project in Azure DevOps

https://dev.azure.com

Look for the repo's blade:

![repository](images/1repo.JPG)

Start cloning this repo in the Azure DevOps Repo blade.

> Import Repo https://github.com/LucasCosas/workshop-mlops-iot

Next step is creating a library variables to use in our pipelines:
![variables](images/2variables.JPG)

Create a variable library called "iotmodel" in the Pipelines blade with the following:

- RESOURCE_GROUP: "resource group name containing the Azure Machine Learning workspace (AML workspace)"
- AMLWORKSPACE_NAME: "AML workspace name"
- AMLDATASET: "The name of the training dataset registered at AML (or to be registered)"
- DATASETFILENAME: "The specific name of the file, e.g 'file.csv' "
- AMLDATASTORE: "The name of the Datastore do be registered in AML, e.g 'BlobDataStore' "
- ENVNAME: "The Environment name for the specific model registered at AML (or to be registered)"
- MODELNAME: "the name of the model you'll register in AML e.g 'iot_model' "
- PIPELINENAME: "Name of the pipeline we'll experiment in AML, e.g 'IoT-Pipeline' "
- STORAGENAME: "Name of the storage account created previously"
- CONTAINERNAME: "Name of the container which contains the dataset"
- STORAGEKEY: "Key from Storage Account"


### Create Connected Services

> You'll need two different connections. One for the Azure Subscription and the other for the Azure Machine Learning workspace:

Go to project settings on the left corner and look for Service Connections

![service connections](images/3serviceconnections.JPG)

1st:

- Create a new service connection for Azure Resource Manager, scope level "Subscription" specifing a manual Service Principal if you already have a Service Principal or an autommatic one if you have permissions to create one. Name it "MLOpsServiceConnection". You can leave the "Resource Group" blank or point to your Resource Group that contains the AML.

2nd:

- Create the second for Azure Resource Manager, manual/automatic and check Azure Machine Learning workspace. Name it "AzureMLServiceConnection". If manual chosen here, make sure to put the Service Principal as a contributor to the Resource Group where the AML workspace is. Also make sure to find the right Resource Group and AML workspace

### Create first Pipeline

Head to the pipelines blade and create your first build/training pipeline:

![pipelines](images/4pipelines.JPG)


Click new pipeline and chose Azure Repos Git and Existing Azure Pipelines YAML File
"/pipeline/azure-pipelines.yml"

Save the pipeline without running (there's an arrow right beside run, expand the checkbox and save)

Rename the pipeline to "iotmodel". One of the steps of the yml is to use the same variables library as the name of the pipeline, so renaming to "iotmodel" will force the pipeline to use that group of variables during the build/training.

![pipelines](images/5renamepipeline.JPG)

Run the pipeline.

While the pipeline is running you can continue the steps

### Training and Registering pipeline

The pipeline above will do a few things:

Register a datastore pointing to your BLOB 
Register a dataset
Train a model
Register the model at AML and create an Azure DevOps Artifact

### AML Extension

Install the following extension to your organization:
> https://marketplace.visualstudio.com/items?itemName=ms-air-aiagility.vss-services-azureml

## Continuos Deployment

Go to the Repo's blade and click on Releases. Click new Pipeline and Start with an Empty Job
Save this Release (you can save under "\") and go back to the "All Pipelines"

![release](images/6release.JPG)

Under "New", import a release pipeline from this repo /pipeline/Deploy Webservice.json

> https://github.com/LucasCosas/workshop-mlops-iot/blob/master/pipeline/Deploy%20Webservice.json

### Edit Tasks

Make sure to chose the Azure Pipelines Agent pools pointing to ubuntu:

> Click on the blue link at "1 Job, 3 tasks" from QA  - Deploy to ACI

For each:

> Agent Job > Agent Pool > Azure Pipelines and Specification > Ubuntu 20.04

![agent pool](images/7agentpool.JPG)

For each step of the pipeline, there's a need to change the Azure Resource Manager pointing to the MLOpsServiceConnection
> Do that for all the steps.

![task service connections](images/8taskconnection.JPG)


Between QA and PROD there's a Post-Deployment conditions.
> Click on the link and choose someone to be an approver. This will make sure that the model will only be deployed to production once approved propperly.

### Edit Artifacts

In the artifacts blade, you'll need two different artifacts:

1st:

Create an Artifact from AzureML Model Artifact type, chosing the Service Endpoint AzureMLServiceConnection and Model named iotmodel (o another model you own). Click on the lightning icon on top of the artifact and enable CD trigger

2nd:
Add another artifact for the Azure Repos, specifying the git repo you cloned.

### Edit Variables

In the Variables blade of the pipeline, change the values as they fit in your scenario. 

Please note that WORKING_DIR_PROD is your repo artifact created above e.g _REPOSITORY/config/

> ENDPOINT_NAME_PROD : Name of the endpoint you'll deploy in AML
> ENDPOINT_NAME_QA : Name of the endpoint you'll deploy in AML
> MODEL_NAME_QA : The exact name of the model you registered in the first pipeline
> MODEL_NAME_PROD : The name of the model you'll register for Production (that way we'll have different models and versions, for QA and Prod)
> RESOURCE_GROUP_PROD : Resource group from Production Workspace (sometimes different than QA)
> RESOURCE_GROUP_QA : Resource group from AML QA workspace
> WORKING_DIR_PROD :  _REPO/config/
> WORKING_DIR_QA :  _REPO/config/
> WORKSPACE_PROD : PROD AML workspace
> WORKSPACE_QA : QA AML workspace

### Edit the score.py file in the repository

Last step before running the CD is editing the file /config/score.py and /config/scoreprod.py. The inference python opens the model and receives new data to make inferences, so we need to change the name of the deployed ML model.

Go to the Repos blade again, locate the files and edit the line 14 of both files : 
> model_path = Model.get_model_path(model_name = 'iot_model')
> Replace the score.py with the MODEL_NAME_QA value and the scoreprod.py with the MODEL_NAME_PROD value

Finally, run the CD 

# Contents:

## Config:
   - Deploymentconfig for both ACI and AKS
   - Inference Config for Prod and QA
   - Myenv 
   - Score.py for both Prod and QA

## Model:
>Endpoint:
   - Inference_test.py
>Scripts:
   - Register.py
   - Setup.py
   - train.py

## Pipeline:
   - azure-pipelines.yml
   - Deploy Webservice.json