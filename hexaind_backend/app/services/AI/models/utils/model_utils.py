# import plotly.graph_objs as go
import sys
import os
import json
import logging
from datetime import datetime, timezone
from typing import Union, List, Dict
import numpy as np
import pandas as pd
import shap
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import mlflow
from fastai.tabular.all import TabularLearner
from autogluon.tabular import TabularPredictor
from autogluon.core.metrics import make_scorer
from scipy.stats import gaussian_kde
from sklearn.metrics import classification_report, ConfusionMatrixDisplay
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    median_absolute_error,
    mean_absolute_percentage_error,
)
from app.services.data.curation.data.source.model import DataSourceModel
from app.services.data.assets.datasets.schemas import MachineLearningModel, Dataset
from pathlib import Path

from ..dao import ModelDao
from ..service import error_metrics_report


logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


class FastAIModelWrapper:
    def __init__(self, learner, feature_names):
        self.learner = learner
        self.feature_names = feature_names

    def predict(self, X):
        # Check if input is a numpy array and convert it to a pandas DataFrame
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X, columns=self.feature_names)

        # Convert input to the format expected by FastAI model
        dl = self.learner.dls.test_dl(X)
        # Get predictions as numpy array
        preds, _ = self.learner.get_preds(dl=dl)
        return preds.numpy()


class ModelUtils:

    @staticmethod
    def double_check_encoding_cols(X: pd.DataFrame, Y: pd.DataFrame) -> pd.DataFrame:
        difference = list(set(X.columns) - set(Y.columns))
        print(f"Columns in X but not in Y: {difference}")
        if difference:
            new_columns = {col: False for col in difference}
            Y = pd.concat([Y, pd.DataFrame(new_columns, index=Y.index)], axis=1)

            # for col in difference:
            #     Y[col] = False
        return Y

    @staticmethod
    def categorical_encoding(X: pd.DataFrame) -> pd.DataFrame:
        # Categorical variable encoding if categorical variables exist
        cat_var_names = X.select_dtypes(
            ["object", "category", "string"]
        ).columns.to_list()
        if len(cat_var_names) > 0:
            X = pd.get_dummies(X, columns=cat_var_names)  # One hot categorical encoding

        return X

    @staticmethod
    def test_train_split(
        data: pd.DataFrame, split_ratio: float = 80.0
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        logger.info("Splitting data into train and test sets")
        train_data = data.sample(frac=split_ratio / 100, random_state=42)
        test_data = data.drop(train_data.index)
        if test_data.empty:
            logger.debug("Test data is empty. using train data as test data")
            test_data = train_data.copy()
        if train_data.empty:
            logger.debug("Train data is empty. using test data as train data")
            train_data = test_data.copy()
        return train_data, test_data

    @staticmethod
    def error_metrics_report(
        y_test: Union[pd.Series, np.ndarray, List[List]],
        y_pred: Union[pd.Series, np.ndarray, List[List]],
        multioutput: str = "uniform_average",
        cols_name: List[str] = [],
    ) -> Dict:

        # Convert inputs to numpy arrays if they aren't already
        y_test = np.array(y_test)
        y_pred = np.array(y_pred)

        # Calculate metrics
        mae = mean_absolute_error(y_test, y_pred, multioutput=multioutput)
        mse = mean_squared_error(y_test, y_pred, multioutput=multioutput)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, y_pred, multioutput=multioutput)
        mape = (
            mean_absolute_percentage_error(y_test, y_pred, multioutput=multioutput)
            * 100
        )
        medae = median_absolute_error(y_test, y_pred, multioutput=multioutput)

        # Initialize metrics report
        metrics_report = {}

        if multioutput == "raw_values" and cols_name:
            metrics_report = {
                "Mean Absolute Error (MAE)": dict(zip(cols_name, mae.tolist())),
                "Mean Squared Error (MSE)": dict(zip(cols_name, mse.tolist())),
                "Root Mean Squared Error (RMSE)": dict(zip(cols_name, rmse.tolist())),
                "R2 Score": dict(zip(cols_name, r2.tolist())),
                "Mean Absolute Percentage Error (MAPE)": dict(
                    zip(cols_name, mape.tolist())
                ),
                "Median Absolute Error (MedAE)": dict(zip(cols_name, medae.tolist())),
            }
        else:
            metrics_report = {
                "Mean Absolute Error (MAE)": mae,
                "Mean Squared Error (MSE)": mse,
                "Root Mean Squared Error (RMSE)": rmse,
                "R2 Score": r2,
                "Mean Absolute Percentage Error (MAPE)": mape,
                "Median Absolute Error (MedAE)": medae,
            }

        return metrics_report

    @staticmethod
    def check_and_drop_nan(df, cols):
        """Checks for NaN values in a DataFrame and drops rows containing them.

        Args:
            df: The DataFrame to check.

        Returns:
            The DataFrame with NaN values removed.
        """
        logger.info("Checking and dropping NaN values")
        df = df[cols].dropna()
        return df

    @staticmethod
    def flatten_dict(d, parent_key="", sep="."):
        logger.info("Flattening dictionary")
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(ModelUtils.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    # https://github.com/shap/shap/issues/632#issuecomment-508086613
    def shap_importance(shap_values, X):
        """Return a dataframe containing the features sorted by shap importance
        Parameters
        ----------
        shap_values : The shap values returned by the shap explainer
        X : pd.Dataframe
            training set/test set/the whole dataset ... (without the label)

        Returns
        -------
        pd.Dataframe
            A dataframe containing the features sorted by shap importance
        """
        vals = np.abs(shap_values.values).mean(0)
        feature_importance = pd.DataFrame(
            list(zip(X.columns, vals)),
            columns=["column_name", "feature_importance_vals"],
        )
        feature_importance.sort_values(
            by=["feature_importance_vals"], ascending=False, inplace=True
        )
        return feature_importance

    # return the shap feature importance of the model. Change introduced as part of SPOC-1150

    @staticmethod
    def shap_summary_plot_interactive(
        shap_values,
        features=None,
        feature_names=None,
        max_display=20,
        axis_color="#333333",
        model=None,
        violin_file_path=str,
    ):

        cdict1 = {
            "red": (
                (0.0, 0.11764705882352941, 0.11764705882352941),
                (1.0, 0.9607843137254902, 0.9607843137254902),
            ),
            "green": (
                (0.0, 0.5333333333333333, 0.5333333333333333),
                (1.0, 0.15294117647058825, 0.15294117647058825),
            ),
            "blue": (
                (0.0, 0.8980392156862745, 0.8980392156862745),
                (1.0, 0.3411764705882353, 0.3411764705882353),
            ),
            "alpha": ((0.0, 1, 1), (0.5, 1, 1), (1.0, 1, 1)),
        }

        # Create the red-to-blue colormap
        red_blue = LinearSegmentedColormap("RedBlueDarker", cdict1)

        # Conversion of matplotlib colormap to Plotly-compatible colorscale
        def matplotlib_to_plotly(cmap, pl_entries=255):
            h = 1.0 / (pl_entries - 1)
            pl_colorscale = []

            for k in range(pl_entries):
                r, g, b, _ = cmap(k * h)
                pl_colorscale.append(
                    [k * h, f"rgb({int(r * 255)}, {int(g * 255)}, {int(b * 255)})"]
                )

            return pl_colorscale

        # Use the converted colormap
        red_blue = matplotlib_to_plotly(red_blue, 255)

        if isinstance(features, pd.DataFrame):  # Check if features is a dataframe
            if feature_names is None:
                feature_names = features.columns
            features = features.values

        if max_display is None:
            max_display = 20

        # Summarize the SHAP values for each feature
        feature_importance = np.sum(
            np.abs(shap_values), axis=0
        )  # Calculate feature importance
        feature_order = np.argsort(feature_importance)[-max_display:][
            ::-1
        ]  # Sort features in descending order

        shap_values_noisy = shap_values + np.random.normal(0, 1e-6, shap_values.shape)

        # Prepare data for the Plotly summary plot
        traces = []
        for rank, feature_idx in enumerate(feature_order):
            shap_value = shap_values_noisy[:, feature_idx]
            feature_value = (
                features[:, feature_idx]
                if features is not None
                else np.zeros(len(shap_value))
            )

            # Calculate the density using Gaussian KDE
            kde = gaussian_kde(shap_value)
            density = kde(shap_value)
            density = (density - density.min()) / (density.max() - density.min())

            # Add jitter to the y-axis to simulate the spread of beeswarm plots
            jitter = (np.random.rand(len(shap_value)) - 0.25) * 0.25

            # Create a scatter trace for each feature
            trace = go.Scatter(
                y=np.full(shap_value.shape, rank)
                + jitter
                * density,  # Add density and jitter to the y-axis for visual spread
                x=shap_value,
                mode="markers",
                marker=dict(
                    size=7,
                    color=feature_value,
                    colorscale=red_blue,
                    showscale=(
                        True if rank == 0 else False
                    ),  # Only show colorbar for the first feature
                    colorbar=(
                        dict(
                            title="Feature value",
                            thickness=5,
                            len=1,
                            lenmode="fraction",
                            x=1.1,
                            xanchor="left",
                            y=0.5,
                            yanchor="middle",
                            tickvals=[
                                feature_value.min(),
                                feature_value.max(),
                            ],  # Set tick positions at the minimum and maximum values
                            ticktext=[
                                "Low",
                                "High",
                            ],  # Display "Low" and "High" labels at these positions
                            ticks="",  # Remove tick marks
                        )
                        if rank == 0
                        else None
                    ),
                ),
                name=(
                    feature_names[feature_idx]
                    if feature_names is not None
                    else f"Feature {feature_idx}"
                ),
                text=[
                    f"Feature: {feature_names[feature_idx] if feature_names is not None else f'Feature {feature_idx}'}<br>Value: {val}<br>SHAP Value: {shap_val}"
                    for val, shap_val in zip(feature_value, shap_value)
                ],
                hoverinfo="text",
            )
            traces.append(trace)

        # Create the layout
        layout = go.Layout(
            title=f"Feature Importance (BeeSwarm Plot) for {model}",
            xaxis=dict(
                title="SHAP value (impact on model output)",
                showline=True,
                zeroline=True,
                zerolinecolor="black",  # Make the zero line more visible
                zerolinewidth=1.0,
            ),
            yaxis=dict(
                title="Feature",
                tickvals=list(range(len(feature_order))),
                ticktext=[
                    feature_names[i] if feature_names is not None else f"Feature {i}"
                    for i in feature_order
                ],  # Set feature labels along y-axis
                autorange="reversed",
                showline=False,
            ),
            height=600,
            width=1000,
            hovermode="closest",
            showlegend=False,
            plot_bgcolor="rgba(240,240,240,0.95)",
            margin=dict(
                l=100, r=50, b=50, t=50
            ),  # Adjust left margin for y-axis labels
        )

        # Create the figure
        plotly_fig = go.Figure(data=traces, layout=layout)

        pio.write_html(plotly_fig, file=violin_file_path, auto_open=False)
        logger.info(f"Beeswarm Plot plot saved to {violin_file_path}")

    @staticmethod
    def plot_feature_importance(
        predictor,
        save_path,
        violin_save_path,
        test_data,
        model,
        train_data,
        return_best_model_shap_importance=False,
    ):
        logger.info(f"Plotting feature importance for model: {model}")

        # 1. Bar Plot for Feature Importance
        feature_importance_df = predictor.feature_importance(test_data, model=model)
        feature_importance_df = feature_importance_df.reset_index()

        required_columns = ["index", "importance"]
        if (
            "stddev" in feature_importance_df.columns
            and "p_value" in feature_importance_df.columns
        ):
            required_columns = ["index", "importance", "stddev", "p_value"]

        feature_importance_df = feature_importance_df[required_columns]
        feature_importance_df.columns = ["Feature", "Importance"] + required_columns[2:]

        feature_importance_df["Importance"] = np.abs(
            feature_importance_df["Importance"]
        )
        feature_importance_df = feature_importance_df.sort_values(
            by="Importance", ascending=False
        ).head(20)

        fig = px.bar(
            feature_importance_df,
            x="Importance",
            y="Feature",
            orientation="h",  # Horizontal bar plot
            title=f"Feature Importance (Bar Plot) for {model}",
            labels={"Importance": "Feature Importance", "Feature": "Features"},
        )
        # Invert the y-axis to have the most important feature at the top
        fig.update_layout(
            yaxis=dict(
                title="Features",
                automargin=True,  # Automatically adjust margins for proper alignment
                tickmode="array",  # Use array to ensure proper label alignment
                categoryorder="total descending",  # Sort features by importance in descending order
                autorange="reversed",
                tickvals=list(
                    range(len(feature_importance_df))
                ),  # Explicitly set tick positions
                ticktext=feature_importance_df[
                    "Feature"
                ].tolist(),  # Ensure tick labels match the features
            ),
            xaxis=dict(
                title="Feature Importance",
                showline=True,
                zeroline=True,
                zerolinecolor="black",
                zerolinewidth=1,
            ),
            title_x=0.5,  # Center title
            margin=dict(
                l=200, r=50, b=50, t=50
            ),  # Increased left margin for better alignment
            plot_bgcolor="rgba(240, 240, 240, 0.95)",  # Light background for better contrast
        )

        # Invert y-axis to have the most important feature at the top
        fig.write_html(save_path)

        logger.info(f"Feature importance bar plot saved to {save_path}")

        # 2. SHAP Beeswarm Plot (SHAP)
        best_model = predictor._trainer.load_model(model).model

        logger.info(
            f"BestModel: {best_model}, Type: {type(best_model)}, Model: {model}"
        )

        feature_names_test = test_data.columns
        feature_names_train = train_data.columns
        logger.info(f"Test Features: {feature_names_test}, {test_data.shape}")
        logger.info(f"Train Features: {feature_names_train}, {train_data.shape}")

        if hasattr(best_model, "feature_name"):
            # trained_features = best_model.feature_name()
            trained_features = (
                predictor.features()
            )  # use this to get the feature names. Changes introduced as part of SPOC-1198
            logger.info(f"Trained features: {trained_features}")

            if len(trained_features) != test_data.shape[1]:
                logger.warning(
                    f"Test data has {test_data.shape[1]} features but model was trained with {len(trained_features)} features."
                )

                missing_cols = [
                    col for col in trained_features if col not in test_data.columns
                ]
                extra_cols = [
                    col for col in test_data.columns if col not in trained_features
                ]

                if missing_cols:
                    logger.error(f"Missing columns in test data: {missing_cols}")
                if extra_cols:
                    logger.error(f"Extra columns in test data: {extra_cols}")

                test_data = test_data.reindex(columns=trained_features, fill_value=0)
                logger.info(f"Aligned test data to match training features")

        tree_model_identifiers = [
            "lightgbm",
            "LGBM",
            "catboost",
            "CAT BOOST",
            "randomforest",
            "Random Forest",
            "extratrees",
            "Extra Trees",
        ]  # 'xgboost', 'XG BOOST',
        kernel_model_identifiers = [
            "svm",
            "SVM",
            "knearestneighbor",
            "K Nearest Neighbor",
        ]  #'linearregression', 'Linear Regression'

        try:
            logger.info(f"type of model: {str(type(best_model)).lower()}")
            is_neural_network = (
                "neuralnetwork"
                in str(type(predictor._trainer.load_model(model).model)).lower()
                or "NeuralNet" in model
            )

            if is_neural_network:
                logger.info("Skipping plotting for neural network model")
                return

            if isinstance(best_model, TabularLearner):
                logger.info("Using FastAI TabularLearner model")
                best_model = FastAIModelWrapper(best_model, feature_names_test)
                explainer = shap.KernelExplainer(best_model.predict, test_data)

            elif any(
                tree_model in str(type(best_model)).lower() or tree_model in model
                for tree_model in tree_model_identifiers
            ):
                logger.info("Using TreeExplainer for Tree-based model")
                explainer = shap.TreeExplainer(best_model)

            elif any(
                kernel_model in str(type(best_model)).lower() or kernel_model in model
                for kernel_model in kernel_model_identifiers
            ):
                logger.info(
                    "Using KernelExplainer for Kernel-based models (SVM, KNN, Linear Regression)"
                )
                explainer = shap.KernelExplainer(best_model.predict, test_data)

            # elif 'neuralnetwork' in str(type(best_model)).lower() or 'Neural Network' in model:
            #     logger.info("Using DeepExplainer for Neural Networks")
            #     explainer = shap.DeepExplainer(best_model, test_data)

            else:
                logger.info(f"Using general SHAP Explainer for {best_model} model")
                explainer = shap.Explainer(best_model, test_data)

            shap_values = explainer(test_data)

            # SHAP Beeswarm Plot
            logger.info("Plotting SHAP beeswarm plot")
            ModelUtils.shap_summary_plot_interactive(
                shap_values.values,
                features=test_data,
                feature_names=feature_names_test,
                model=model,
                violin_file_path=violin_save_path,
            )

            logger.info(f"SHAP beeswarm plot saved to {violin_save_path}")

            if predictor.model_best == model and return_best_model_shap_importance:
                return ModelUtils.shap_importance(shap_values, test_data)

        except Exception as e:
            logger.error(f"Error plotting SHAP values: {e}")

    @staticmethod
    def prediction_and_indices_columns(
        data,
        test_data,
        train_data,
        predictor,
        label,
        model_name,
        summary,
        train_indices,
        test_indices,
        all_indices,
    ):
        logger.info(f"Generating predictions for model: {model_name}")
        y_pred_test_all = predictor.predict(
            test_data.drop(columns=[label]), model=model_name
        ).tolist()
        y_pred_train_all = predictor.predict(
            train_data.drop(columns=[label]), model=model_name
        ).tolist()
        y_pred_all = (
            y_pred_train_all + y_pred_test_all
        )  # predictor.predict(data.drop(columns=[label]), model=model_name)

        test_column_name = f"test_predict_{label}"
        train_column_name = f"train_predict_{label}"
        column_name = f"predict_{label}"

        summary.loc[summary["model"] == model_name, train_column_name] = json.dumps(
            y_pred_train_all
        )
        summary.loc[summary["model"] == model_name, test_column_name] = json.dumps(
            y_pred_test_all
        )
        summary.loc[summary["model"] == model_name, column_name] = json.dumps(
            y_pred_all
        )

        summary.loc[summary["model"] == model_name, "train_indices"] = json.dumps(
            train_indices
        )
        summary.loc[summary["model"] == model_name, "test_indices"] = json.dumps(
            test_indices
        )
        summary.loc[summary["model"] == model_name, "all_indices"] = json.dumps(
            all_indices
        )

    @staticmethod
    def plot_class_wise_distribution(data, label, title_name, save_path):
        logger.info(f"Plotting class-wise distribution for {title_name}")
        plt.figure(figsize=(10, 8))
        data[label].value_counts().plot(kind="barh", figsize=(10, 8), color="teal")
        plt.xlabel("Count")
        plt.ylabel(label)
        plt.title(f"Class-wise distribution of {title_name} Set")
        plt.gca().invert_yaxis()
        plt.savefig(save_path)
        plt.close()

    @staticmethod
    def plot_confusion_matrix(conf_mat, conf_mat_file):
        logger.info("Plotting confusion matrix")
        conf_mat_array = np.array(conf_mat)
        uniques = list(conf_mat.columns)
        disp = ConfusionMatrixDisplay(
            confusion_matrix=conf_mat_array, display_labels=uniques
        )
        disp.plot().figure_.savefig(conf_mat_file)

    # return the shap feature importance of the best model. Change introduced as part of SPOC-1150
    @staticmethod
    def log_individual_model_metrics(
        predictor,
        data,
        test_data,
        train_data,
        label,
        problem_type,
        model_detail,
        extra_metrics,
        train_indices,
        test_indices,
        all_indices,
        model_dao,
        ml_model,
        return_best_model_shap_importance=False,
    ):
        logger.info("Logging individual model metrics")
        leaderboard = predictor.leaderboard(test_data, extra_metrics=extra_metrics)
        leaderboard["score_test"] = -leaderboard["score_test"]
        leaderboard["score_val"] = -leaderboard["score_val"]
        model_names = leaderboard["model"].tolist()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        summary_file = os.path.join(ml_model["ml_model_file_path"], "summary.csv")
        best_shap_importance = None
        for model_name in model_names:
            model_obj = ml_model.copy()
            model_det = model_detail.copy()
            model_det["type"] = f"{model_name}"
            model_det["ml_sub_type"] = "autogluon"
            model_det["name"] = f"{label}_{model_det['type']}_{timestamp}"
            m_name = model_name.replace("/", "_")
            feature_imp_plot = os.path.join(
                ml_model["ml_model_file_path"], f"{m_name}_feature_imp.html"
            )
            feature_imp_violen_plot = None
            if not "NeuralNet" in m_name:
                feature_imp_violen_plot = os.path.join(
                    ml_model["ml_model_file_path"], f"{m_name}_violen_feature_imp.html"
                )
            shap_importance = ModelUtils.plot_feature_importance(
                predictor,
                feature_imp_plot,
                feature_imp_violen_plot,
                test_data,
                model_name,
                train_data,
                return_best_model_shap_importance=return_best_model_shap_importance,
            )
            if predictor.model_best == model_name:
                best_shap_importance = shap_importance
            model_metrics = predictor.evaluate(
                test_data,
                model=model_name,
                detailed_report=True,
                auxiliary_metrics=True,
            )

            if problem_type == "classification":
                y_pred = predictor.predict(data=test_data, model=model_name)
                report = classification_report(
                    test_data[label], y_pred, output_dict=True
                )
                model_det["metrics"] = report
                conf_plot = os.path.join(
                    ml_model["ml_model_file_path"], f"{m_name}_confusion_matrix.png"
                )
                ModelUtils.plot_confusion_matrix(
                    model_metrics["confusion_matrix"], conf_plot
                )
                mlflow.log_artifact(conf_plot)

                model_det["visualizations"] = [conf_plot]
                dist_sets = {"Train": train_data, "Test": test_data}
                for dist in dist_sets:
                    dist_path = os.path.join(
                        ml_model["ml_model_file_path"],
                        f"{m_name}_{dist}_class_distribution.png",
                    )
                    ModelUtils.plot_class_wise_distribution(
                        dist_sets[dist], label, dist, dist_path
                    )
                    mlflow.log_artifact(dist_path)
                    model_det["visualizations"].append(dist_path)

            else:
                y_pred = predictor.predict(data=test_data, model=model_name)
                y_test = test_data[label]
                model_metrics = error_metrics_report(y_pred=y_pred, y_test=y_test)
                model_det["metrics"] = model_metrics

            model_det["feature_imp_plot"] = feature_imp_plot
            model_det["feature_imp_plot_violen"] = feature_imp_violen_plot
            model_obj["model"] = model_det
            ml_model_obj = MachineLearningModel(**model_obj)
            model_dao.insert_record_sync(ml_model_obj.model_dump())

            mlflow.log_artifact(feature_imp_plot)
            ModelUtils.prediction_and_indices_columns(
                data,
                test_data,
                train_data,
                predictor,
                label,
                model_name,
                leaderboard,
                train_indices,
                test_indices,
                all_indices,
            )

        leaderboard.to_csv(summary_file)
        if return_best_model_shap_importance:
            return best_shap_importance

    @staticmethod
    def update_hyperparameters_for_gpu(hyperparameters, use_gpu=False):
        logger.info("Updating hyperparameters for GPU if available")
        if "XGB" in hyperparameters:
            hyperparameters["XGB"]["tree_method"] = "gpu_hist" if use_gpu else "hist"

        if "GBM" in hyperparameters:
            hyperparameters["GBM"]["device_type"] = "gpu" if use_gpu else "cpu"

        if "CAT" in hyperparameters:
            hyperparameters["CAT"]["task_type"] = "GPU" if use_gpu else "CPU"

        if "FASTAI" in hyperparameters:
            hyperparameters["FASTAI"]["num_gpus"] = 1 if use_gpu else 0

        return hyperparameters

    @staticmethod
    def rmse(y_true, y_pred):
        """
        rmse function is used by the define_scorer function
        """
        return np.sqrt(mean_squared_error(y_true, y_pred))

    @staticmethod
    def define_scorer(eval_metric_chosen):
        """
        define_scorer function enables score definitions for each of the three evaluation metrics.
        """
        scorer = None
        if eval_metric_chosen == "root_mean_squared_error":
            # Root Mean Squared Error (RMSE)
            scorer = make_scorer(
                name="root_mean_squared_error",
                score_func=ModelUtils.rmse,
                optimum=0,
                greater_is_better=False,
                needs_proba=False,
            )

        elif eval_metric_chosen == "mean_squared_error":
            # Mean Squared Error (MSE)
            scorer = make_scorer(
                name="mean_squared_error",
                score_func=mean_squared_error,
                optimum=0,
                greater_is_better=False,
                needs_proba=False,
            )

        elif eval_metric_chosen == "mean_absolute_error":
            # Mean Absolute Error (MAE)
            scorer = make_scorer(
                name="mean_absolute_error",
                score_func=mean_absolute_error,
                optimum=0,
                greater_is_better=False,
                needs_proba=False,
            )
        elif eval_metric_chosen == "mean_absolute_percentage_error":
            # Mean Absolute Percentage Error (MAPE)
            scorer = make_scorer(
                name="Mean Absolute Percentage Error",
                score_func=mean_absolute_percentage_error,
                optimum=0,
                greater_is_better=False,
                needs_proba=False,
            )

        return scorer

    @staticmethod
    def train_and_log_models(
        data,
        train_data,
        test_data,
        hyperparameters,
        eval_metric,
        label,
        model_path,
        hyperparameter_tune_kwargs,
        problem_type,
        model_detail,
        extra_metrics,
        db_sync_client,
        ml_model_obj,
        return_best_model_shap_importance=False,
    ):

        model_dao = ModelDao(db_sync_client=db_sync_client)
        train_indices = train_data.index.tolist()
        test_indices = test_data.index.tolist()
        all_indices = train_indices + test_indices
        if (
            model_detail["configs"]["split_ratio"] == 100
            or model_detail["configs"]["split_ratio"] == 0
        ):
            logger.info("Split ratio is 100 or 0. ")
            all_indices = train_indices
        eval_metric = ModelUtils.define_scorer(eval_metric)
        logger.info("Training and logging models")
        sub_problem_type = "regression"
        if problem_type == "classification":
            if len(data[label].unique()) > 2:
                sub_problem_type = "multiclass"
            else:
                sub_problem_type = "binary"

        predictor = TabularPredictor(
            label=label,
            problem_type=sub_problem_type,
            path=model_path,
            eval_metric=eval_metric,
        ).fit(
            train_data=train_data,
            hyperparameters=hyperparameters,
            hyperparameter_tune_kwargs=hyperparameter_tune_kwargs,
            fit_weighted_ensemble=False,
            fit_full_last_level_weighted_ensemble=False,
        )
        shap_importance = ModelUtils.log_individual_model_metrics(
            predictor,
            data,
            test_data,
            train_data,
            label,
            problem_type,
            model_detail,
            extra_metrics,
            train_indices,
            test_indices,
            all_indices,
            model_dao,
            ml_model_obj,
            return_best_model_shap_importance,
        )
        if return_best_model_shap_importance:
            return predictor, shap_importance

        return predictor

    @staticmethod
    def read_data_for_training(
        dataset_record: Dataset, data_path: Path
    ) -> pd.DataFrame:
        if dataset_record:
            data = DataSourceModel.from_dataset(dataset_record).dataframe
            data = data.compute()
        else:
            data = pd.read_csv(data_path)

        return data
