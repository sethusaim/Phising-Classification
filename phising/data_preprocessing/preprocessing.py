import numpy as np
import pandas as pd
from phising.s3_bucket_operations.s3_operations import S3_Operation
from utils.logger import App_Logger
from utils.model_utils import Model_Utils
from utils.read_params import read_params


class Preprocessor:
    """
    Description :   This class shall  be used to clean and transform the data before training.
    Written by  :   iNeuron Intelligence
    
    Version     :   1.2
    Revisions   :   Moved to setup to cloud 
    """

    def __init__(self,log_file):
        self.log_writer = App_Logger()

        self.config = read_params()

        self.class_name = self.__class__.__name__

        self.log_file = log_file

        self.model_utils = Model_Utils()

        self.null_values_file = self.config["null_values_csv_file"]

        self.n_components = self.config["pca_model"]["n_components"]

        self.input_files_bucket = self.config["s3_bucket"]["input_files"]

        self.s3 = S3_Operation()

    def separate_label_feature(self, data, label_column_name):
        """
        Method Name :   separate_label_feature
        Description :   This method separates the features and a Label Coulmns.
        
        Output      :   Returns two separate dataframes, one containing features and the other containing labels .
        On Failure  :   Write an exception log and then raise an exception

        Version     :   1.2
        Written by  :   iNeuron Intelligence
        Revisions   :   moved setup to cloud
        """
        method_name = self.separate_label_feature.__name__

        self.log_writer.start_log("start",self.log_file,self.class_name,method_name)

        try:
            self.X = data.drop(labels=label_column_name, axis=1)

            self.Y = data[label_column_name]

            self.log_writer.log(
                self.log_file, f"Separated {label_column_name} from {data}",
            )

            self.log_writer.start_log("exit",self.log_file,self.class_name,method_name)

            return self.X, self.Y

        except Exception as e:
            self.log_writer.exception_log(e,self.log_file,self.class_name,method_name)

    def replace_invalid_values(self, data):
        """
        Method Name :   replace_invalid_values
        Description :   This method replaces invalid values i.e. 'na' with np.nan

        Output      :   Replaces the invalid values like "'na'" with np.nan, so that imputation can be done
        On Failure  :   Write an exception log and then raise an exception

        Version     :   1.2
        Written by  :   iNeuron Intelligence
        Revisions   :   moved setup to cloud
        """
        method_name = self.replace_invalid_values.__name__

        self.log_writer.start_log("start",self.log_file,self.class_name,method_name)

        try:
            data.replace(to_replace="'na'", value=np.nan, inplace=True)

            self.log_writer.log(self.log_file, "Replaced " "na" " with np.nan")

            self.log_writer.start_log("exit",self.log_file,self.class_name,method_name)

            return data

        except Exception as e:
            self.log_writer.exception_log(e,self.log_file,self.class_name,method_name)

    def is_null_present(self, data):
        """
        Method Name :   is_null_present
        Description :   This method checks whether there are null values present in the pandas Dataframe or not.
        
        Output      :   If null values are present in the dataframe, a csv file is created and then uploaded back to input files bucket
        On Failure  :   Write an exception log and then raise an exception
        
        Version     :   1.2
        Written by  :   iNeuron Intelligence
        Revisions   :   moved setup to cloud
        """
        method_name = self.is_null_present.__name__

        self.log_writer.start_log("start",self.log_file,self.class_name,method_name)

        try:
            null_present = False

            cols_with_missing_values = []

            cols = data.columns

            self.null_counts = data.isna().sum()

            self.log_writer.log(
                self.log_file, f"Null values count is : {self.null_counts}",
            )

            for i in range(len(self.null_counts)):
                if self.null_counts[i] > 0:
                    null_present = True

                    cols_with_missing_values.append(cols[i])

            self.log_writer.log(
                self.log_file, "created cols with missing values",
            )

            if null_present is True:
                self.log_writer.log(
                    self.log_file,
                    "null values were found the columns...preparing dataframe with null values",
                )

                self.null_df = pd.DataFrame()

                self.null_df["columns"] = data.columns

                self.null_df["missing values count"] = np.asarray(data.isna().sum())

                self.log_writer.log(
                    self.log_file, "Created dataframe with null values",
                )
                
                self.s3.upload_df_as_csv(self.null_df,self.null_values_file,self.null_values_file,self.input_files_bucket,self.log_file)

            else:
                self.log_writer.log(
                    self.log_file,
                    "No null values are present in cols. Skipped the creation of dataframe",
                )

            self.log_writer.start_log("exit",self.log_file,self.class_name,method_name)

            return null_present

        except Exception as e:
            self.log_writer.exception_log(e,self.log_file,self.class_name,method_name)

    def impute_missing_values(self, data):
        """
        Method Name :   impute_missing_values
        Description :   This method replaces all the missing values in the dataframe using mean values of the column.
        
        Output      :   A dataframe which has all the missing values are imputed.
        On Failure  :   Write an exception log and then raise an exception

        Version     :   1.2
        Written by  :   iNeuron Intelligence
        Revisions   :   moved setup to cloud
        """
        method_name = self.impute_missing_values.__name__

        self.log_writer.start_log("start",self.log_file,self.class_name,method_name)

        try:
            data = data[data.columns[data.isnull().mean() < 0.6]]

            data = data.apply(pd.to_numeric)

            for col in data.columns:
                data[col] = data[col].replace(np.NaN, data[col].mean())

            self.log_writer.start_log("exit",self.log_file,self.class_name,method_name)

            return data

        except Exception as e:
            self.log_writer.exception_log(e,self.log_file,self.class_name,method_name)
