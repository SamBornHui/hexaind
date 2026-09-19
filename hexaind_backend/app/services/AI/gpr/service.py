import os
import sys
import json
from typing import List
import torch
import mlflow
import joblib
import logging
import textwrap
import datetime
import gpytorch
import numpy as np
import pandas as pd
from pathlib import Path
from pymongo import MongoClient
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler
from motor.motor_asyncio import AsyncIOMotorClient
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio


from .dao import GPRDao
from .schemas import GPRConfig, GPRResponse

from app.config.env_vars import environment as env
from app.services.notification.service import Notification
from app.services.AI.models.utils.model_utils import ModelUtils
from app.services.data.curation.data.source.model import DataSourceModel
from app.services.AI.gpr.gpr_models import (
    SingletaskGPModel,
    MultitaskGPModel,
    SingletaskGPModelLarge,
    MultitaskGPModelLarge,
)
from app.services.data.assets.datasets.schemas import (
    Dataset,
    MachineLearningModel,
    AccessMode,
)
from app.services.notification.schema import (
    NotificationModel,
    NotificationType,
    NotificationCategory,
    NotificationImportance,
)


logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


class GPRModelWrapper(mlflow.pyfunc.PythonModel):
    def __init__(self, likelihood, model, x_scaler, y_scaler):
        self.likelihood = likelihood
        self.model = model
        self.x_scaler = x_scaler
        self.y_scaler = y_scaler

    def predict(self, context, model_input):
        # Standardize the input data
        X_scaled = self.x_scaler.transform(model_input)

        # Convert to PyTorch tensor
        X_tensor = torch.from_numpy(X_scaled).float()

        # Ensure the model is in evaluation mode
        self.likelihood.eval()
        self.model.eval()

        # Ensure no gradients are computed during inference
        with torch.no_grad(), gpytorch.settings.fast_pred_var():
            output = self.likelihood(self.model(X_tensor))
            pred_mean = output.mean
            lower, upper = output.confidence_region()
            pred_mean = pred_mean.detach().numpy()
            lower = lower.detach().numpy()
            upper = upper.detach().numpy()
            if len(pred_mean.shape) == 1:
                pred_mean = pred_mean.reshape(-1, 1)
            if len(lower.shape) == 1:
                lower = lower.reshape(-1, 1)
            if len(upper.shape) == 1:
                upper = upper.reshape(-1, 1)

        pred_mean = self.y_scaler.inverse_transform(pred_mean)
        lower = self.y_scaler.inverse_transform(lower)
        upper = self.y_scaler.inverse_transform(upper)
        pred_std = (upper - lower) / 4

        return pred_mean, pred_std


class GPRService:
    def __init__(
        self,
        db_sync_client: MongoClient = None,
        db_async_client: AsyncIOMotorClient = None,
    ) -> None:
        logger.info("Initializing GPR Service")
        self.gpr_dao = GPRDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

    def send_notification(self, notification_obj):
        verified_notfication_obj = NotificationModel(**notification_obj)
        notification_service_obj = Notification(
            db_sync_client=self.gpr_dao.db_sync_client
        )
        notification_service_obj.create_notification_sync(verified_notfication_obj)

    def measure_performance(self, model, likelihood, X, y, output_dim=None):
        logger.info("Measuring performance")
        model.eval()
        likelihood.eval()
        with torch.no_grad(), gpytorch.settings.fast_pred_var():
            predictions = likelihood(model(X))
            mean = predictions.mean
            if output_dim is not None:  # Multi-output case
                mean = mean[:, output_dim]
                y = y[:, output_dim]
        mse = mean_squared_error(y.numpy(), mean.numpy())
        return mse

    def permutation_feature_importance(self, model, likelihood, X, y, feature_names):
        logger.info("Calculting permutation feature importance")
        if y.ndimension() == 1:  # Single-output case
            num_outputs = 1
            y = y.unsqueeze(1)
        else:  # Multi-output case
            num_outputs = y.shape[1]

        importances = np.zeros((X.shape[1], num_outputs))

        for output_dim in range(num_outputs):
            baseline_performance = self.measure_performance(
                model, likelihood, X, y, output_dim if num_outputs > 1 else None
            )

            for i in range(X.shape[1]):
                X_permuted = X.clone()
                X_permuted[:, i] = X[
                    torch.randperm(X.size(0)), i
                ]  # Shuffle the i-th column
                permuted_performance = self.measure_performance(
                    model,
                    likelihood,
                    X_permuted,
                    y,
                    output_dim if num_outputs > 1 else None,
                )
                importances[i, output_dim] = baseline_performance - permuted_performance

        importances /= importances.sum(axis=0)  # Normalize to sum to 1 for each output
        return importances

    def wrap_feature_names(self, feature_names, width=20):
        return [textwrap.fill(name, width=width) for name in feature_names]

    def plot_feature_importance(
        self,
        importances,
        feature_names,
        save_path,
        y_feature_name,
        beeswarm_plot_path: str,
    ):
        logger.info("Plotting feature importance")
        wrapped_feature_names = self.wrap_feature_names(feature_names)

        # Determine figure height based on the number of features
        figure_height = 8  # Default height
        figure_width = 10  # Default width
        dynamic_adjust = 0.5 * len(feature_names)
        wrapped_feature_names = np.array(wrapped_feature_names)
        order = np.argsort(importances)[::-1]
        if dynamic_adjust > figure_height:
            figure_height = dynamic_adjust
            figure_width = dynamic_adjust

        # Set figure size
        plt.figure(figsize=(figure_width, figure_height))

        bars = plt.barh(wrapped_feature_names[order], importances[order], color="teal")
        plt.xlabel("Feature Importance")
        plt.ylabel("Features")
        plt.title(f"Feature Importance for output {y_feature_name}")
        plt.gca().invert_yaxis()  # Highest importance at the top

        # Optional: Set alignment for better appearance
        for bar in bars:
            bar.set_edgecolor("none")  # Optional: Remove edge color to reduce clutter
            # width = bar.get_width()
        # Save the plot
        plt.savefig(save_path, bbox_inches="tight")
        plt.close()

        feature_importance_df = pd.DataFrame(
            {"Feature": wrapped_feature_names, "Importance": importances}
        )

        # 2. Interactive Beeswarm Plot (Plotly)
        fig = px.strip(
            feature_importance_df,
            y="Feature",
            x="Importance",
            title=f"Feature Importance Distribution (Beeswarm Plot) for GPR",
            template="plotly_white",
            stripmode="overlay",  # This is important for beeswarm-like effect
        )

        features = list(feature_importance_df["Feature"].unique())

        # Adding horizontal jitter to simulate a beeswarm plot (scatter effect)
        for i, feature in enumerate(features, start=1):
            feature_data = feature_importance_df[
                feature_importance_df["Feature"] == feature
            ]
            fig.add_trace(
                go.Scatter(
                    x=feature_data["Importance"],
                    y=feature_data["Feature"],
                    mode="markers",
                    marker=dict(
                        color=feature_data[
                            "Importance"
                        ],  # TODO test with different columns
                        colorscale="bluered",
                        showscale=i == len(features),
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
                )
            )

        # Updating layout for a cleaner appearance
        fig.update_layout(
            xaxis_title="SHAP value (impact on model output)",
            yaxis_title="Feature",
            height=600,
            width=900,
            xaxis=dict(zeroline=True, zerolinecolor="black", zerolinewidth=2),
            yaxis=dict(autorange="reversed"),
            margin=dict(l=0, r=0, t=25, b=0),
        )

        # Save the violin plot as an interactive HTML file
        pio.write_html(fig, file=beeswarm_plot_path, auto_open=False)

    def train_gpr(
        self,
        gpr_config: GPRConfig,
        data_path: Path,
        result_folders: str,
        project_id: str,
        wf_id: str,
        run_id: str,
        dataset_name: str,
        user_id: str,
        site_id: str,
        user_name: str,
        dataset_record: Dataset = None,
        widget_urn: str = None,
    ):
        try:
            logger.info("Starting GPR training")
            logger.info(f"GPR configuration {str(gpr_config)}")

            data = ModelUtils.read_data_for_training(
                dataset_record=dataset_record, data_path=data_path
            )

            logger.info(f"before dropping nan Data shape: {data.shape}")
            input_cols = gpr_config.input_cols
            output_cols = gpr_config.output_cols
            logger.info("Preprocessing for Regression")

            data = ModelUtils.check_and_drop_nan(data, input_cols + output_cols)
            data.reset_index(drop=True, inplace=True)
            encoded_data = ModelUtils.categorical_encoding(
                data[input_cols + output_cols]
            )
            train_data, test_data = ModelUtils.test_train_split(
                data=encoded_data, split_ratio=gpr_config.split_ratio
            )
            logger.info(f"Data shape: {data.shape}")
            if gpr_config.spectral_kernel == False:
                spectral_selected = gpr_config.spectral_kernel
                num_mixtures = 7
            else:
                spectral_selected = gpr_config.spectral_kernel.spectral_selected
                num_mixtures = gpr_config.spectral_kernel.num_mixtures

            inducing_info = dict()
            inducing_info["variational"] = gpr_config.variational
            if gpr_config.variational:
                num_latents = gpr_config.variational.num_latents
                num_inducing = gpr_config.variational.num_inducing
                inducing_info["variational"] = True
                inducing_info["num_inducing"] = num_inducing
            else:
                num_latents = 4
                num_inducing = 4

            kernel_selected = gpr_config.kernel_selected
            mean = gpr_config.mean
            max_train = gpr_config.max_train

            train_x = train_data.drop(output_cols, axis=1)
            train_y = train_data[output_cols]
            test_x = test_data.drop(output_cols, axis=1)
            test_y = test_data[output_cols]

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            x_cols = train_x.columns.to_list()
            y_cols = output_cols

            feature_names = train_x.columns.to_list()
            y_feature_names = train_y.columns.to_list()
            train_x = train_x.to_numpy().astype(float)
            test_x = test_x.to_numpy().astype(float)
            train_y = train_y.to_numpy().astype(float)
            test_y = test_y.to_numpy().astype(float)

            # Standardize inputs and outputs
            x_scaler = StandardScaler()
            train_x = x_scaler.fit_transform(train_x)
            test_x = x_scaler.transform(test_x)
            y_scaler = StandardScaler()
            train_y = y_scaler.fit_transform(train_y)
            test_y = y_scaler.transform(test_y)

            train_x = torch.from_numpy(train_x).float()
            test_x = torch.from_numpy(test_x).float()
            train_y = torch.from_numpy(train_y).float()
            test_y = torch.from_numpy(test_y).float()

            # Set up MLflow
            logger.info("Creating MLFLOW experiment")

            mlflow.set_tracking_uri(
                env.mlflow_tracking_uri
            )  # Set this to your MLflow server's URI

            experiment_name = f"GPR_{project_id}_{wf_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            mlflow.set_experiment(experiment_name)
            mlflow.set_tag("GPR version", "v1.0")
            mlflow.set_tag("Model type", "GPR")
            mlflow.set_tag("custom_run_id", run_id)

            notification_obj = {
                "message": "GPR Model training has started",
                "category_id": wf_id,
                "project_id": project_id,
                "notification_type": NotificationType.INFO,
                "importance": NotificationImportance.MEDIUM,
                "notification_category": NotificationCategory.MODEL,
            }
            logger.info("Starting MLFLOW experiment")
            with mlflow.start_run(nested=True) as run:
                model_name = f"gpr_model_{run.info.run_id}"
                model_path = os.path.join(result_folders, model_name)
                os.makedirs(model_path, exist_ok=True)
                scaler_x_path = os.path.join(model_path, "scaler_x.pkl")
                scaler_y_path = os.path.join(model_path, "scaler_y.pkl")
                summary_file = os.path.join(model_path, "summary.csv")
                ml_model = dict(
                    user_id=user_id,
                    project_id=project_id,
                    site_id=site_id,
                    wf_run_id=run_id,
                    description="GPR model description",
                    created_at=datetime.datetime.now(),
                    ml_model_file_path=model_path,
                    access_mode=AccessMode.INTERNAL,
                    tags=[],
                    user_name=user_name,
                    dataset_path=data_path,
                    widget_urn=widget_urn,
                )

                ml_model["ml_flow_detail"] = dict(
                    experiment_id=run.info.experiment_id,
                    experiment_name=experiment_name,
                    run_id=run.info.run_id,
                )

                self.send_notification(notification_obj=notification_obj)
                # mlflow.autolog()
                params_dict = gpr_config.model_dump()

                mlflow.log_params(params_dict)
                if train_y.shape[1] > 1:
                    likelihood = gpytorch.likelihoods.MultitaskGaussianLikelihood(
                        num_tasks=train_y.shape[1]
                    )
                else:
                    likelihood = gpytorch.likelihoods.GaussianLikelihood()
                covar_module = self.select_kernal(
                    train_x,
                    train_y,
                    max_train,
                    num_latents,
                    num_mixtures,
                    spectral_selected,
                    kernel_selected,
                )
                mean_module, num_latents_info = self.set_mean(
                    train_x, max_train, y_cols, mean, num_latents
                )
                model, gpr_model_type = self.choose_model(
                    train_x,
                    train_y,
                    max_train,
                    num_latents,
                    num_inducing,
                    covar_module,
                    mean_module,
                    likelihood,
                )
                additional_info = {"model_type": gpr_model_type}
                additional_info.update(num_latents_info)
                additional_info.update(inducing_info)

                learning_rate = 0.1  # starting learning rate
                training_iterations_max = (
                    gpr_config.training_iterations_max
                )  # max allowed number of training iterations
                model.train()
                likelihood.train()

                # Use the adam optimizer
                if train_x.shape[0] > max_train:
                    optimizer = torch.optim.Adam(
                        [
                            {"params": model.parameters()},
                            {"params": likelihood.parameters()},
                        ],
                        lr=learning_rate,
                    )  # Maybe learning rate is parameter
                    mll = gpytorch.mlls.VariationalELBO(
                        likelihood, model, num_data=train_y.size(0)
                    )
                else:
                    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
                    mll = gpytorch.mlls.ExactMarginalLogLikelihood(likelihood, model)

                # Create scheduler to reduce learning rate automatically
                scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, "min")

                # training loop
                prev_iter_loss = 10
                lr_new = learning_rate
                for _ in range(training_iterations_max):
                    optimizer.zero_grad()
                    output = model(train_x)
                    try:
                        loss = -mll(output, train_y)
                    except:
                        loss = prev_iter_loss
                        lr_new = lr_new / 10

                    if loss.dim() != 0:
                        loss = loss.mean()
                    loss.backward()
                    optimizer.step()
                    scheduler.step(loss)
                    # lr_new=scheduler.get_last_lr() -------------changed by ali due to error 'ReduceLROnPlateau' object has no attribute 'get_last_lr'
                    lr_new = optimizer.param_groups[0]["lr"]
                    # break loop if learning stagnates
                    # if lr_new[0]<1e-5: -------------changed by ali due to error 'ReduceLROnPlateau' object has no attribute 'get_last_lr'
                    prev_iter_loss = loss
                    if lr_new < 1e-5:
                        break

                # Set into eval mode
                model.eval()
                likelihood.eval()

                importances = self.permutation_feature_importance(
                    model, likelihood, test_x, test_y, feature_names
                )
                self.feature_imp_plot = list()
                self.feature_imp_plot_beeswarm = list()
                for ind, feature in enumerate(y_feature_names):
                    self.feature_imp_plot.append(
                        os.path.join(
                            model_path, f"GPR_{feature}_feature_imp_{timestamp}.png"
                        )
                    )
                    self.feature_imp_plot_beeswarm.append(
                        os.path.join(
                            model_path, f"GPR_{feature}_feature_imp_{timestamp}.html"
                        )
                    )
                    self.plot_feature_importance(
                        importances[:, ind],
                        feature_names,
                        self.feature_imp_plot[ind],
                        feature,
                        self.feature_imp_plot_beeswarm[ind],
                    )

                # Concatenate train_x and test_x along a new dimension
                tensor_cancate = False
                if gpr_config.split_ratio == 100 or gpr_config.split_ratio == 0:
                    all_data = train_x
                else:
                    all_data = torch.cat((train_x, test_x), dim=0)
                    tensor_cancate = True
                # Make predictions
                with torch.no_grad(), gpytorch.settings.fast_pred_var():
                    predictions = likelihood(model(all_data))
                    mean = predictions.mean
                    # sigma_s = predictions.variance.sqrt()
                    lower, upper = predictions.confidence_region()

                if tensor_cancate:
                    _, mean_test = torch.split(
                        mean, [train_x.size(0), test_x.size(0)], dim=0
                    )
                else:
                    mean_test = mean

                mean = mean.detach().numpy()
                mean_test = mean_test.detach().numpy()
                lower = lower.detach().numpy()
                upper = upper.detach().numpy()
                # sigma_s = sigma_s.detach().numpy()
                test_x = x_scaler.inverse_transform(test_x)
                if len(test_y.shape) == 1:
                    test_y = test_y.reshape(-1, 1)
                if len(mean.shape) == 1:
                    mean = mean.reshape(-1, 1)
                if len(mean_test.shape) == 1:
                    mean_test = mean_test.reshape(-1, 1)
                # if len(sigma_s.shape) == 1:
                #     sigma_s = sigma_s.reshape(-1, 1)
                if len(lower.shape) == 1:
                    lower = lower.reshape(-1, 1)
                if len(upper.shape) == 1:
                    upper = upper.reshape(-1, 1)

                # transform targets and predictions back to original space
                test_y = y_scaler.inverse_transform(test_y)
                mean = y_scaler.inverse_transform(mean)
                mean_test = y_scaler.inverse_transform(mean_test)
                lower = y_scaler.inverse_transform(lower)
                upper = y_scaler.inverse_transform(upper)
                # sigma_s = y_scaler.inverse_transform(sigma_s)
                sigma_s = (upper - lower) / 4

                model_det = dict(
                    testing_samples=test_data.shape[0],
                    training_samples=train_data.shape[0],
                    configs=gpr_config.model_dump(),
                    dataset_name=dataset_name,
                )
                if len(gpr_config.output_cols) > 1:
                    model_det["type"] = "MOGPR"
                    summary = ModelUtils.error_metrics_report(
                        y_test=test_y,
                        y_pred=mean_test,
                        multioutput="raw_values",
                        cols_name=y_feature_names,
                    )
                else:
                    model_det["type"] = "GPR"
                    summary = ModelUtils.error_metrics_report(
                        y_test=test_y, y_pred=mean_test
                    )

                for key, value in summary.items():
                    if isinstance(value, np.float32):
                        summary[key] = round(float(value), 3)

                model_obj = ml_model.copy()

                model_det["name"] = f"{model_det['type']}_{timestamp}"
                model_det["feature_imp_plot"] = self.feature_imp_plot
                model_det["feature_imp_plot_violen"] = self.feature_imp_plot_beeswarm
                model_det["metrics"] = summary
                model_det["additional_info"] = additional_info
                model_obj["model"] = model_det

                ml_model = MachineLearningModel(**model_obj)
                self.gpr_dao.insert_gpr_record_sync(ml_model.model_dump())
                mean = mean.transpose().tolist()
                sigma_s = sigma_s.transpose().tolist()
                train_ind = train_data.index.tolist()
                test_ind = test_data.index.tolist()
                all_ind = train_ind + test_ind
                if gpr_config.split_ratio == 100 or gpr_config.split_ratio == 0:
                    all_ind = train_ind

                summary["all_indices"] = json.dumps(all_ind)
                summary["train_indices"] = json.dumps(train_ind)
                summary["test_indices"] = json.dumps(test_ind)
                summary["model"] = model_det["type"]
                for idx, col_name in enumerate(gpr_config.output_cols):
                    # Convert the column data to a JSON string
                    predict_col = "predict_" + col_name
                    std_col = "std_" + col_name
                    summary[predict_col] = json.dumps(mean[idx])
                    summary[std_col] = json.dumps(sigma_s[idx])

                model_summary_df = pd.DataFrame([summary])
                joblib.dump(x_scaler, scaler_x_path)
                joblib.dump(y_scaler, scaler_y_path)
                # Save model and necessary information
                dict_out = dict()
                dict_out["model"] = model
                dict_out["x_scaler"] = x_scaler
                dict_out["y_scaler"] = y_scaler
                set1 = set(x_cols)
                set2 = set(gpr_config.input_cols)
                difference = list(set1.symmetric_difference(set2))
                if difference:
                    dict_out["cat_var_names"] = difference
                dict_out["x_vars"] = x_cols
                dict_out["y_vars"] = y_cols
                joblib.dump(
                    dict_out, filename=os.path.join(model_path, "gpr_model.joblib")
                )
                model_summary_df.to_csv(summary_file, index=False)

                mlflow.log_artifact(scaler_x_path, artifact_path="scaler_x")
                mlflow.log_artifact(scaler_y_path, artifact_path="scaler_y")
                wrapped_model = GPRModelWrapper(
                    likelihood=likelihood,
                    model=model,
                    x_scaler=x_scaler,
                    y_scaler=y_scaler,
                )
                mlflow.pyfunc.log_model(
                    artifact_path="model",
                    python_model=wrapped_model,
                    artifacts={"scaler_x": scaler_x_path, "scaler_y": scaler_y_path},
                )
                # mlflow.pytorch.log_model(model, "model")
                mlflow.log_artifact(summary_file)

                # Additionally, save and log the likelihood as part of the model artifacts
                torch.save(likelihood.state_dict(), "likelihood.pth")
                mlflow.log_artifact("likelihood.pth")
                artifact_final_path = os.path.join(result_folders, model_name)
                mlflow.artifacts.download_artifacts(run_id=run.info.run_id,dst_path=artifact_final_path)
                logger.info(f"Artifacts downloaded to: {artifact_final_path}")
            
            mlflow.end_run()
            logger.info(f"MLFLOW Experiment Completed")

            notification_obj["message"] = "Model GPR has been trained"
            self.send_notification(notification_obj=notification_obj)

            return GPRResponse(tabular_path=summary_file,models_path=os.path.join(artifact_final_path,"model"))

        except Exception as e:
            logger.error(f"Error in training GPR model: {str(e)}", exc_info=True)
            notification_obj = {
                "message": "GPR Model training has failed",
                "category_id": wf_id,
                "project_id": project_id,
                "notification_type": NotificationType.ERROR,
                "importance": NotificationImportance.HIGH,
                "notification_category": NotificationCategory.MODEL,
            }
            self.send_notification(notification_obj=notification_obj)
            return GPRResponse(exception_detail=str(e))

    def choose_model(
        self,
        train_x,
        train_y,
        max_train,
        num_latents,
        num_inducing,
        covar_module,
        mean_module,
        likelihood,
    ):
        gpr_model_type = None
        if train_y.shape[1] == 1:
            train_y = train_y.reshape(-1)
            if train_x.shape[0] > max_train:
                model = SingletaskGPModelLarge(
                    train_x, train_y, num_inducing, covar_module, mean_module
                )
                gpr_model_type = "SingletaskGPModelLarge"
            else:
                model = SingletaskGPModel(
                    train_x, train_y, likelihood, covar_module, mean_module
                )
                gpr_model_type = "SingletaskGPModel"
        else:
            if train_x.shape[0] > max_train:
                model = MultitaskGPModelLarge(
                    train_x,
                    train_y,
                    num_latents,
                    num_inducing,
                    covar_module,
                    mean_module,
                )
                gpr_model_type = "MultitaskGPModelLarge"
            else:
                model = MultitaskGPModel(
                    train_x, train_y, likelihood, num_latents, covar_module, mean_module
                )
                gpr_model_type = "MultitaskGPModel"
        return model, gpr_model_type

    def set_mean(self, train_x, max_train, y_cols, mean, num_latents):
        additonal_info = dict()
        if len(y_cols) > 1 and train_x.shape[0] > max_train:
            if mean == "zero":
                mean_module = gpytorch.means.ZeroMean(
                    batch_shape=torch.Size([num_latents])
                )
            elif mean == "constant":
                mean_module = gpytorch.means.ConstantMean(
                    batch_shape=torch.Size([num_latents])
                )
            elif mean == "linear":
                mean_module = gpytorch.means.LinearMean(
                    input_size=train_x.shape[1], batch_shape=torch.Size([num_latents])
                )
            additonal_info["num_latents"] = num_latents
        else:
            if mean == "zero":
                mean_module = gpytorch.means.ZeroMean()
            elif mean == "constant":
                mean_module = gpytorch.means.ConstantMean()
            elif mean == "linear":
                mean_module = gpytorch.means.LinearMean(input_size=train_x.shape[1])
        return mean_module, additonal_info

    def select_kernal(
        self,
        train_x,
        train_y,
        max_train,
        num_latents,
        num_mixtures,
        spectral_selected,
        kernel_selected,
    ):
        if train_y.shape[1] > 1 and train_x.shape[0] > max_train:
            if spectral_selected:
                spectral_kernel = gpytorch.kernels.SpectralMixtureKernel(
                    ard_num_dims=train_x.shape[1],
                    num_mixtures=num_mixtures,
                    batch_shape=torch.Size([num_latents]),
                )
            rbf_kernel = gpytorch.kernels.RBFKernel(
                batch_shape=torch.Size([num_latents])
            )
            ard_rbf_kernel = gpytorch.kernels.RBFKernel(
                ard_num_dims=train_x.shape[1], batch_shape=torch.Size([num_latents])
            )
            matern_kernel = gpytorch.kernels.MaternKernel(
                nu=2.5, batch_shape=torch.Size([num_latents])
            )
            ard_matern_kernel = gpytorch.kernels.MaternKernel(
                nu=2.5,
                ard_num_dims=train_x.shape[1],
                batch_shape=torch.Size([num_latents]),
            )
            linear_kernel = gpytorch.kernels.LinearKernel(
                batch_shape=torch.Size([num_latents])
            )
        else:
            if spectral_selected:
                spectral_kernel = gpytorch.kernels.SpectralMixtureKernel(
                    ard_num_dims=train_x.shape[1], num_mixtures=num_mixtures
                )
            rbf_kernel = gpytorch.kernels.RBFKernel()
            ard_rbf_kernel = gpytorch.kernels.RBFKernel(ard_num_dims=train_x.shape[1])
            matern_kernel = gpytorch.kernels.MaternKernel(nu=2.5)
            ard_matern_kernel = gpytorch.kernels.MaternKernel(
                nu=2.5, ard_num_dims=train_x.shape[1]
            )
            linear_kernel = gpytorch.kernels.LinearKernel()

        kernels_list = []

        kernel_options = [
            rbf_kernel,
            ard_rbf_kernel,
            matern_kernel,
            ard_matern_kernel,
            linear_kernel,
        ]

        # if spectral mixture kernel is selected, use only that. Otherwise, use the combination of RBF/Matern/Linear specified
        # by the user
        if spectral_selected == True:
            covar_module = spectral_kernel
        else:
            for i in range(len(kernel_selected)):
                if kernel_selected[i] == True:
                    kernels_list.append(kernel_options[i])
                    if len(kernels_list) == 1:
                        covar_module = kernel_options[i]
                    else:
                        covar_module += kernel_options[i]
            covar_module = gpytorch.kernels.ScaleKernel(covar_module)
        return covar_module
