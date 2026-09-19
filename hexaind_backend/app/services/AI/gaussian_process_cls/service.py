# Original code with MLflow integration
import matplotlib
matplotlib.use('Agg')
from app.services.data.curation.data.source.model import DataSourceModel
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from matplotlib import pyplot as plt
from pathlib import Path
import pandas as pd
import json
import joblib
import mlflow
import os
import torch
import datetime
import numpy as np
from torch.utils.data import DataLoader, TensorDataset
import gpytorch
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, accuracy_score, classification_report
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import logging
import sys

from .dao import GPCDao 
from .schemas import GPCConfig, GPCResponse
from .gpc_helpers import standardize_inputs, construct_likelihood, construct_kernel, construct_mean_function, construct_model, resample

from app.services.AI.models.service import categorical_encoding
from app.services.AI.models.utils.model_utils import ModelUtils
from app.services.data.assets.datasets.schemas import Dataset, MachineLearningModel, AccessMode
from app.services.notification.service import Notification
from app.services.notification.schema import (
    NotificationModel,
    NotificationType,
    NotificationCategory,
    NotificationImportance)

from app.config.env_vars import environment as env

logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

class GPCPrediction(mlflow.pyfunc.PythonModel):
    def __init__(self, model, x_scaler, class_names):
        self.model = model
        self.x_scaler = x_scaler
        self.class_names = class_names

    def predict(self, context, model_input):
        # Standardize the input data
        X_scaled = self.x_scaler.transform(model_input)
        
        # Convert to PyTorch tensor
        X_tensor = torch.from_numpy(X_scaled).float()
        
        # Ensure the model is in evaluation mode
        self.model.eval()
        
        # Ensure no gradients are computed during inference
        with torch.no_grad():
            # Get the predictive distribution
            predictive_distribution = self.model(X_tensor)
            
            # Extract mean predictions (logits)
            mean_predictions = predictive_distribution.mean
            
            # Get the predicted class indices (argmax of the mean predictions along the class dimension)
            predicted_class_indices = mean_predictions.argmax(dim=0)
        
        # Convert class indices to class names
        predicted_class_names = [self.class_names[idx] for idx in predicted_class_indices.numpy()]
        
        return predicted_class_names
    
class GPCService:
    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None: # type: ignore
        logger.info("Initializing GPCService")
        self.gpc_dao = GPCDao(db_sync_client=db_sync_client, db_async_client=db_async_client)


    def send_notification(self, notification_obj):
        verified_notfication_obj = NotificationModel(**notification_obj)
        notification_service_obj = Notification(db_sync_client=self.gpc_dao.db_sync_client)
        notification_service_obj.create_notification_sync(verified_notfication_obj)

    def flatten_dict(self, d, parent_key='', sep='.'):
        logger.info("Flattening dictionary")

        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def batch_size_variational_training(self, train_x, train_y, likelihood, model, ml_config):
        # Set batch size for variational training
        logger.info("Doing batch size variational training")

        learning_rate = ml_config.lr_init
        training_iterations_max = ml_config.num_epochs
        batch_size = ml_config.batch_size
        patience = ml_config.patience
        max_train = ml_config.max_train
        if train_x.shape[0] > max_train:
            mll = gpytorch.mlls.VariationalELBO(likelihood, model, num_data=train_y.size(0))
            optimizer = torch.optim.Adam([
                {'params': model.parameters()},
                {'params': likelihood.parameters()},
            ], lr=learning_rate) # Maybe learning rate is parameter
            
            train_dataset = TensorDataset(train_x, train_y)   
            train_loader = DataLoader(dataset=train_dataset, batch_size=batch_size, drop_last=False, shuffle=True)
        
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=patience)    #Create scheduler to reduce learning rate automatically
            
            loss_list = []
            for i in range(training_iterations_max):
                batch_losses = []
                for x_batch, y_batch in train_loader:
                    optimizer.zero_grad()
                    output = model(x_batch)
                    loss = -mll(output, y_batch)
                    loss.backward()
                    optimizer.step()
                    batch_losses.append(loss.cpu().detach())
                    
                scheduler.step(loss)
                loss_mean = np.mean(batch_losses)
                lr_new = optimizer.param_groups[0]['lr']
                if i % 10 == 0:
                    print('Epoch %d/%d - Loss: %.5f - lr: %.5f' % (i + 1, training_iterations_max, loss_mean, lr_new))
                    loss_list.append(loss_mean)
                    
                #break loop if learning stagnates
                if lr_new < ml_config.lr_end:
                    break     
                
        else:
            optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
            mll = gpytorch.mlls.ExactMarginalLogLikelihood(likelihood, model)
            
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=10)

            for i in range(training_iterations_max):
                optimizer.zero_grad()
                output = model(train_x)
                loss = -mll(output, likelihood.transformed_targets).sum()
                loss.backward()
                optimizer.step()
                scheduler.step(loss)
                lr_new = optimizer.param_groups[0]['lr']
                if i % 10 == 0:
                    # print('Iter %d/%d - Loss: %.5f - lr: %.5f' % (i + 1, training_iterations_max, loss.item(), scheduler.get_last_lr()[0]))
                    print('Iter %d/%d - Loss: %.5f - lr: %.5f' % (i + 1, training_iterations_max, loss.item(), lr_new))
                test = {}
                test[0] = scheduler
                
                #break loop if learning stagnates
                if lr_new < ml_config.lr_end:
                    break

    def calculate_probabilities(self, model, total_rows, test_x, max_train):
        logger.info("calculating  probabilities")

        model.eval()
        if total_rows > max_train:
            f_preds = model(test_x)
            pred_samples = f_preds.sample(sample_shape=torch.Size((1000,)))
            probabilities = (pred_samples / pred_samples.sum(-1, keepdim=True)).mean(0)
            preds = f_preds.mean.detach().numpy()
            
        else:
            with gpytorch.settings.fast_pred_var(), torch.no_grad():
                test_dist = model(test_x)
            
                pred_means = test_dist.loc
            
            pred_means = pred_means.detach().numpy()
            pred_samples = test_dist.sample(torch.Size((1000,))).exp()
            probabilities = (pred_samples / pred_samples.sum(-2, keepdim=True)).mean(0)#.reshape(train_x.shape[0],num_classes)
            probabilities = torch.swapaxes(probabilities, 0, 1)

        return probabilities
    
    def plot_confusion_matrix(self, model, total_rows, max_train, conf_mat_file, uniques, test_x, y, codes):
        logger.info("plot confusion matrix")

        probabilities = self.calculate_probabilities(model, total_rows, test_x, max_train)
        probabilities = probabilities.detach().numpy()
        pred_labels = uniques[np.argmax(probabilities,axis=1)]
        conf_mat = confusion_matrix(codes, np.argmax(probabilities,axis=1))
        disp = ConfusionMatrixDisplay(confusion_matrix=conf_mat,display_labels=uniques)
        disp.plot().figure_.savefig(conf_mat_file + '.png')
        # disp.figure_.savefig(conf_mat_file+'.png')
        report = classification_report(y, pred_labels, output_dict=True)
        return report

    def evaluate_model_accuracy(self, model, total_rows, test_x, test_y, max_train):
        probabilities = self.calculate_probabilities(model, total_rows, test_x, max_train)
        accuracy = accuracy_score(test_y, np.argmax(probabilities, axis=1))
        return accuracy


    def calculate_permutation_importance(self, model, total_rows, test_x, test_y, feature_names, max_train):
        logger.info("calculating permutation importance")

        base_accuracy = self.evaluate_model_accuracy(model, total_rows, test_x, test_y, max_train)
        feature_importances = np.zeros(len(feature_names))
        
        for i in range(len(feature_names)):
            test_x_permuted = test_x.clone()
            permuted_col = test_x_permuted[:, i][torch.randperm(test_x_permuted.size(0))]
            test_x_permuted[:, i] = permuted_col
            permuted_accuracy = self.evaluate_model_accuracy(model, total_rows, test_x_permuted, test_y, max_train)
            feature_importances[i] = base_accuracy - permuted_accuracy
        
        # Normalize the feature importances
        feature_importances = feature_importances / np.sum(feature_importances)
        return feature_importances

    def plot_feature_importance(self, model, feature_names, output_path, total_rows, test_x, test_y, max_train, beeswarm_plot_path: str):
        try:
            logger.info("Plotting feature importance graph")
            # Check if the model has a kernel with lengthscales
            if hasattr(model.covar_module, 'base_kernel'):
                
                # Extract the learned lengthscales
                lengthscales = model.covar_module.base_kernel.lengthscale.detach().numpy().flatten()

                # Feature importance is the inverse of the lengthscale
                ## Compute the inverse of the lengthscales
                feature_importance = 1 / lengthscales
                
                # Normalize to get feature importance
                feature_importance /= feature_importance.sum()  # Normalize
                ### getting feature importance base on input features
                feature_importance = feature_importance[:len(feature_names)]
                
            else:
                ##### calculating feature importance data for Non-ARD kernel
                feature_importance = self.calculate_permutation_importance(model, total_rows, test_x, test_y, feature_names, max_train)
            
            feature_names = np.array(feature_names)
            order = np.argsort(feature_importance)
            
            # Plot feature importance
            plt.figure(figsize=(10, 6))
            plt.barh(feature_names[order], feature_importance[order], color="teal")
            plt.xlabel('Feature Importance')
            plt.ylabel('Features')
            plt.title('Feature Importance')
            plt.savefig(output_path)
            plt.close()

            feature_importance_df = pd.DataFrame({
                "Feature": feature_names,
                "Importance": feature_importance
            })

            # 2. Interactive Beeswarm Plot (Plotly)
            fig = px.strip(
                feature_importance_df, 
                y="Feature", 
                x="Importance", 
                title=f"Feature Importance Distribution (Beeswarm Plot) for {model}",
                template="plotly_white", 
                stripmode='overlay',  # This is important for beeswarm-like effect
            )

            features = list(feature_importance_df["Feature"].unique())

            # Adding horizontal jitter to simulate a beeswarm plot (scatter effect)
            for i, feature in enumerate(features, start=1):
                feature_data = feature_importance_df[feature_importance_df['Feature'] == feature]
                fig.add_trace(go.Scatter(
                    x=feature_data['Importance'],
                    y=feature_data['Feature'],
                    mode='markers',
                    marker=dict(
                        color=feature_data['Importance'], # TODO test with different columns
                        colorscale='bluered',
                        showscale=i==len(features),
                        colorbar=dict(
                            thickness=7,
                            tickvals=[0, 1],  # Positions for "Low" and "High" labels
                            ticktext=["Low", "High"],  # Labels for color scale
                        ),
                        size=6,
                        cmin=0,
                        cmax=1,
                    ),
                    name=feature,
                    showlegend=False,
                ))

            # Updating layout for a cleaner appearance
            fig.update_layout(
                xaxis_title="SHAP value (impact on model output)",
                yaxis_title="Feature",
                height=600,
                width=900,
                xaxis=dict(
                    zeroline=True,
                    zerolinecolor="black",
                    zerolinewidth=2
                ),
                # yaxis=dict(
                #     autorange="reversed"
                # ),
                margin=dict(l=0, r=0, t=25, b=0)
            )

            # Save the violin plot as an interactive HTML file
            pio.write_html(fig, file=beeswarm_plot_path, auto_open=False)

            return 1
        except:
            print("Model does not have lengthscales in its kernel to determine feature importance.")
            print('Continue without feature importance plot')
            return 0
    
    
    def train_gpc(self, ml_config: GPCConfig, data_path: Path, result_folders: Path, project_id: str, wf_id: str, run_id: str, dataset_name: str, user_id: str, site_id: str, user_name: str, dataset_record: Dataset = None, widget_urn: str = None) -> GPCResponse:
        try:
            logger.info("Starting Auto_ML training")
            logger.info(f"Auto_ML configuration {str(ml_config)}")
              
            # Verify data path and load data using pandas
            if not data_path.exists():
                raise FileNotFoundError(f"Data file not found at path: {data_path}")
            
            dff = ModelUtils.read_data_for_training(dataset_record=dataset_record,data_path=data_path)
            
            if dff.empty:
                raise ValueError("Loaded data is empty")
            all_cols  = ml_config.input_cols
            all_cols.append(ml_config.output_col)
            
            logger.info("Preprocessing for GPC")

            dff = ModelUtils.check_and_drop_nan(dff, all_cols)
            if dff.shape[0] > ml_config.max_train:
                notification_obj = {"message":"Dataset is larger than the maximum allowed size for GPC",
                    'category_id':wf_id,
                    'project_id':project_id,
                    'notification_type':NotificationType.ERROR,
                    'importance':NotificationImportance.HIGH,
                    'notification_category':NotificationCategory.MODEL}
                
                self.send_notification(notification_obj=notification_obj)
                return GPCResponse(exception_detail=notification_obj['message'])

                
            # Duplicate versions from prior implementation
            sampler_type = ml_config.sampler_type #type of sampling used in case of target imbalance
            max_train = ml_config.max_train #number of training rows after which variational strategy is automatically used
            num_inducing = ml_config.num_inducing #number of inducing points. Only used if variational==True (i.e., perform variational inference) Display option only if more than max_tran samples
            spectral_selected = False
            num_mixtures = 0
            if ml_config.spectral_kernel_setting:
                spectral_selected = ml_config.spectral_kernel_setting.spectral_kernel #whether spectral mixture kernel is selected
                num_mixtures = ml_config.spectral_kernel_setting.num_mixtures #to be specified by user, only if spectral kernel is selected

            kernel_selected = ml_config.covariance_function.covariance_function_selection #index 0 = rbf, index 1 = ARD rbf, index 2 = matern, index 3 = ARD matern, index 4 = linear. #True = on, False = off
            mean = ml_config.mean
            num_latents = ml_config.num_latents #number of latent GPs. Only used if variational==True (i.e., perform variational inference) Should be only used if multi-output
            
            X = dff.drop(columns=[ml_config.output_col])
            y = dff[ml_config.output_col]
            num_classes = len(set(y))
            x_cols = ml_config.input_cols

            ## sampleng strategy
            X_res, y_res = resample(X, y, sampler_type)

            
            X = categorical_encoding(X)
            X_res = categorical_encoding(X_res)
            
            x_cols = X.columns.to_list()
            codes, uniques = pd.factorize(y, sort=True)
            codes_res, _ = pd.factorize(y_res, sort=True)
            if X.shape[0]>max_train:
                y = pd.get_dummies(y)
                y_res = pd.get_dummies(y_res)
                y = y.to_numpy().astype(float)
                y_res = y_res.to_numpy().astype(float)
                test_y = torch.from_numpy(y)
                train_y = torch.from_numpy(y_res).double()

            else:
                test_y = torch.from_numpy(codes)
                train_y = torch.from_numpy(codes_res).double()
            
            X = X.to_numpy().astype(float)
            X_res = X_res.to_numpy().astype(float)

            x_scaler, test_x = standardize_inputs(X)
            train_x = x_scaler.transform(X_res)
            train_x = torch.from_numpy(train_x).float()

            self.all_indices = [i for i in range(dff.shape[0])]
            
            self.result_folders =  result_folders
            
            logger.info("Creating MLFLOW experiment")

            # Set up MLflow
            mlflow.set_tracking_uri(env.mlflow_tracking_uri)  # Set this to your MLflow server's URI
            experiment_name = f"GPC_{project_id}_{wf_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            mlflow.set_experiment(experiment_name)
            mlflow.set_tag("GPC version", "v1.0")
            mlflow.set_tag("Model type", "GPC")
            mlflow.set_tag('custom_run_id', run_id)
            flat_params_dict = self.flatten_dict(ml_config.model_dump())
            notification_obj = {"message":"GPC Model training has started",
                                'category_id':wf_id,
                                'project_id':project_id,
                                'notification_type':NotificationType.INFO,
                                'importance':NotificationImportance.MEDIUM,
                                'notification_category':NotificationCategory.MODEL}
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.ml_model = dict(user_id=user_id, project_id=project_id, site_id=site_id, wf_run_id=run_id, description='GPC model description', created_at=datetime.datetime.now(),
                                            ml_model_file_path=None, access_mode=AccessMode.INTERNAL, tags=[], user_name=user_name, dataset_path=str(data_path), widget_urn=widget_urn)
            self.model_detail = dict(type='GPC', name=f"{ml_config.output_col}_GPC_{timestamp}", testing_samples=0, training_samples=dff.shape[0], configs=ml_config.model_dump(), dataset_name=dataset_name)
            logger.info("Starting MLFLOW experiment")

            with mlflow.start_run(nested=True) as run:
                model_name = f"GPC_model_{run.info.run_id}"
                model_path = os.path.join(result_folders, model_name)
                os.makedirs(model_path, exist_ok=True)
                conf_mat_file = os.path.join(model_path, 'GPC_confusion_matrix')
                scaler_path = os.path.join(model_path, 'scaler.pkl')
                class_names_path = os.path.join(model_path, 'class_names.json')

                self.ml_model['ml_model_file_path'] = model_path
                self.feature_imp_plot = os.path.join(self.ml_model['ml_model_file_path'] , "GPC_feature_imp.png")
                self.feature_imp_plot_beeswarm = os.path.join(self.ml_model['ml_model_file_path'] , "GPC_feature_imp_beeswarm.html")
            
                self.summary_file = os.path.join(model_path, 'summary.csv')
                self.ml_model['ml_flow_detail'] = dict(experiment_id=run.info.experiment_id, experiment_name=experiment_name, run_id=run.info.run_id)
                self.send_notification(notification_obj=notification_obj)
                mlflow.log_params(flat_params_dict)
                # mlflow.autolog()
                
                ###############################################################################
                # Set up model
                covar_module = construct_kernel(train_x, train_y, max_train, kernel_selected, num_classes,
                                                num_mixtures=num_mixtures, spectral_selected=spectral_selected)
                train_y = train_y.int()
                likelihood = construct_likelihood(train_y, max_train)
                mean_module = construct_mean_function(train_x, train_y, mean, num_classes, max_train, num_latents=num_latents)
                model = construct_model(train_x, train_y, covar_module, mean_module, likelihood, max_train,
                                        num_latents=num_latents, num_inducing=num_inducing)
                ###############################################################################
                
                # Training loop
                model.train()
                likelihood.train()
                self.batch_size_variational_training(train_x, train_y, likelihood, model, ml_config)
                
                # Post-processing
                # Set into eval mode
                model.eval()
                likelihood.eval()

                model_metrics = self.plot_confusion_matrix(model, train_x.shape[0], max_train, conf_mat_file, uniques, test_x, y, codes)
                if self.plot_feature_importance(model, x_cols, self.feature_imp_plot, train_x.shape[0], test_x, test_y, max_train, self.feature_imp_plot_beeswarm):
                    self.model_detail['feature_imp_plot'] = self.feature_imp_plot
                    self.model_detail['feature_imp_plot_violen'] = self.feature_imp_plot_beeswarm
                    mlflow.log_artifact(self.feature_imp_plot)
                    mlflow.log_artifact(self.feature_imp_plot_beeswarm)
                else:
                    self.model_detail['feature_imp_plot'] = None
                    self.model_detail['feature_imp_plot_violen'] = None
                
                self.model_detail['metrics'] = model_metrics
                self.model_detail['visualizations'] = [conf_mat_file + '.png']
                self.ml_model['model'] = self.model_detail
                ml_model = MachineLearningModel(**self.ml_model)
                self.gpc_dao.insert_record_sync(ml_model.model_dump())
                # Convert the dictionary to a DataFrame
                df = pd.DataFrame(model_metrics).transpose()
                df.to_csv(self.summary_file, index=True)
                
                # Log and the scaler and class names as artifacts
                joblib.dump(x_scaler, scaler_path)
                #Save model and necessary information
                dict_out = dict()
                dict_out['model'] = model
                dict_out['x_scaler'] = x_scaler
                set1 = set(x_cols)
                set2 = set(ml_config.input_cols)
                difference = list(set1.symmetric_difference(set2))
                if difference:
                    dict_out['cat_var_names'] = difference
                dict_out['x_vars'] = ml_config.input_cols
                dict_out['y_vars'] = ml_config.output_col
                joblib.dump(dict_out,filename=os.path.join(model_path, 'gpc.joblib'))
                
                with open(class_names_path, "w") as f:
                    json.dump(uniques.to_list(), f)
                mlflow.log_artifact(scaler_path, artifact_path="scaler")
                mlflow.log_artifact(class_names_path, artifact_path="class_names")
                # Log the model using PyFunc
                gpc_model = GPCPrediction(model=model, x_scaler=x_scaler, class_names=uniques.to_list())
                mlflow.pyfunc.log_model(
                    artifact_path="model",
                    python_model=gpc_model,
                    artifacts={
                        "scaler": scaler_path,
                        "class_names": class_names_path
                    }
                )
                mlflow.log_artifact(self.summary_file)
                artifact_final_path = os.path.join(result_folders, model_name)
                mlflow.artifacts.download_artifacts(run_id=run.info.run_id,dst_path=artifact_final_path)
                logger.info(f"Artifacts downloaded to: {artifact_final_path}")
            
            

            mlflow.end_run()
            logger.info(f"MLFLOW Experiment Completed")


            notification_obj['message'] = "Model GPC has been trained"
            self.send_notification(notification_obj=notification_obj)

            return GPCResponse(tabular_path=self.summary_file,models_path=os.path.join(artifact_final_path,"model"))

        
        except Exception as e:
            logger.error("GPC training failed", exc_info=True)

            notification_obj = {"message":"GPC Model training has failed",
                                'category_id':wf_id,
                                'project_id':project_id,
                                'notification_type':NotificationType.ERROR,
                                'importance':NotificationImportance.HIGH,
                                'notification_category':NotificationCategory.MODEL}
            
            self.send_notification(notification_obj=notification_obj)
            return GPCResponse(exception_detail=str(e))
