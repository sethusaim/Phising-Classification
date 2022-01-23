from phising.mlflow_utils.mlflow_operations import Mlflow_Operations
from phising.s3_bucket_operations.s3_operations import S3_Operations
from utils.logger import App_Logger
from utils.read_params import read_params


class load_prod_model:
    """
    Description :   This class shall be used for loading the production model
    Written by  :   iNeuron Intelligence
    Version     :   1.0
    Revisions   :   None
    """

    def __init__(self, num_clusters):
        self.log_writer = App_Logger()

        self.config = read_params()

        self.class_name = self.__class__.__name__

        self.num_clusters = num_clusters

        self.model_bucket = self.config["s3_bucket"]["phising_model_bucket"]

        self.db_name = self.config["db_log"]["db_train_log"]

        self.load_prod_model_log = self.config["train_db_log"]["load_prod_model"]

        self.exp_name = self.config["mlflow_config"]["experiment_name"]

        self.remote_server_uri = self.config["mlflow_config"]["remote_server_uri"]

        self.s3_obj = S3_Operations()

        self.mlflow_op = Mlflow_Operations(
            db_name=self.db_name, collection_name=self.load_prod_model_log
        )

    def load_production_model(self):
        """
        Method Name :   load_production_model
        Description :   This method is responsible for moving the models from the trained models dir to
                        prod models dir and stag models dir based on the metrics of the cluster

        Version     :   1.2
        Revisions   :   moved setup to cloud
        """
        method_name = self.load_production_model.__name__

        self.log_writer.start_log(
            key="start",
            class_name=self.class_name,
            method_name=method_name,
            db_name=self.db_name,
            collection_name=self.load_prod_model_log,
        )

        try:
            self.mlflow_op.set_mlflow_tracking_uri(server_uri=self.remote_server_uri)

            exp = self.mlflow_op.get_experiment_from_mlflow(exp_name=self.exp_name)

            runs = self.mlflow_op.get_runs_from_mlflow(exp_id=exp.experiment_id)

            """
            Code Explaination: 
            num_clusters - Dynamically allocated based on the number of clusters created using elbow plot

            Here, we are trying to iterate over the number of clusters and then dynamically create the cols 
            where in the best model names can be found, and then copied to production or staging depending on
            the condition

            Eg- metrics.XGBoost1-best_score
            """
            reg_model_names = self.mlflow_op.get_mlflow_models()

            cols = [
                "metrics." + str(model) + "-best_score"
                for model in reg_model_names
                if model != "KMeans"
            ]

            self.log_writer.log(
                db_name=self.db_name,
                collection_name=self.load_prod_model_log,
                log_message="Created cols for all registered model",
            )

            runs_cols = runs[cols].max().sort_values(ascending=False)

            self.log_writer.log(
                db_name=self.db_name,
                collection_name=self.load_prod_model_log,
                log_message="Sorted the runs cols in descending order",
            )

            metrics_dict = runs_cols.to_dict()

            self.log_writer.log(
                db_name=self.db_name,
                collection_name=self.load_prod_model_log,
                log_message="Converted runs cols to dict",
            )

            """ 
            Eg-output: For 3 clusters, 
            
            [
                metrics.XGBoost0-best_score,
                metrics.XGBoost1-best_score,
                metrics.XGBoost2-best_score,
                metrics.RandomForest0-best_score,
                metrics.RandomForest1-best_score,
                metrics.RandomForest2-best_score
            ] 

            Eg- runs_dataframe: I am only showing for 3 cols,actual runs dataframe will be different
                                based on the number of clusters
                
                since for every run cluster values changes, rest two cols will be left as blank,
                so only we are taking the max value of each col, which is nothing but the value of the metric
                

run_number  metrics.XGBoost0-best_score metrics.RandomForest1-best_score metrics.XGBoost1-best_score
    0                   1                       0.5
    1                                                                                   1                 
    2                                                                           
            """

            """(metrics.RandomForest1-best_score,0.5),(metrics.XGBoost1-best_score,1)"""

            best_metrics_names = [
                max(
                    [
                        (file, metrics_dict[file])[0]
                        for file in metrics_dict
                        if str(i) in file
                    ]
                )
                for i in range(0, self.num_clusters)
            ]

            self.log_writer.log(
                db_name=self.db_name,
                collection_name=self.load_prod_model_log,
                log_message=f"Got top model names based on the metrics of clusters",
            )

            ## best_metrics will store the value of metrics, but we want the names of the models,
            ## so best_metrics.index will return the name of the metric as registered in mlflow

            ## Eg. metrics.XGBoost1-best_score

            ## top_mn_lst - will store the top 3 model names

            top_mn_lst = [mn.split(".")[1].split("-")[0] for mn in best_metrics_names]

            self.log_writer.log(
                db_name=self.db_name,
                collection_name=self.load_prod_model_log,
                log_message=f"Got the top model names",
            )

            results = self.mlflow_op.search_mlflow_models(order="DESC")

            ## results - This will store all the registered models in mlflow
            ## Here we are iterating through all the registered model and for every latest registered model
            ## we are checking if the model name is in the top 3 model list, if present we are putting that
            ## model into production or staging

            for res in results:
                for mv in res.latest_versions:
                    if mv.name in top_mn_lst:
                        self.mlflow_op.transition_mlflow_model(
                            model_version=mv.version,
                            stage="Production",
                            model_name=mv.name,
                            bucket=self.model_bucket,
                            db_name=self.db_name,
                            collection_name=self.load_prod_model_log,
                        )

                    ## In the registered models, even kmeans model is present, so during prediction,
                    ## this model also needs to be in present in production, the code logic is present below

                    elif mv.name == "KMeans":
                        self.mlflow_op.transition_mlflow_model(
                            model_version=mv.version,
                            stage="Production",
                            model_name=mv.name,
                            bucket=self.model_bucket,
                            db_name=self.db_name,
                            collection_name=self.load_prod_model_log,
                        )

                    else:
                        self.mlflow_op.transition_mlflow_model(
                            model_version=mv.version,
                            stage="Staging",
                            model_name=mv.name,
                            bucket=self.model_bucket,
                            db_name=self.db_name,
                            collection_name=self.load_prod_model_log,
                        )

            self.log_writer.log(
                db_name=self.db_name,
                collection_name=self.load_prod_model_log,
                log_message="Transitioning of models based on scores successfully done",
            )

        except Exception as e:
            self.log_writer.raise_exception_log(
                error=e,
                class_name=self.class_name,
                method_name=method_name,
                db_name=self.db_name,
                collection_name=self.load_prod_model_log,
            )