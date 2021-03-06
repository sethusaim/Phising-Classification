from json import loads
from os import environ

from pandas import DataFrame
from pymongo import MongoClient
from utils.logger import App_Logger
from utils.read_params import read_params


class MongoDB_Operation:
    """
    Description :   This method is used for all mongodb operations
    Written by  :   iNeuron Intelligence
    
    Version     :   1.2
    Revisions   :   Moved to setup to cloud 
    """

    def __init__(self):
        self.config = read_params()

        self.class_name = self.__class__.__name__

        self.DB_URL = environ["MONGODB_URL"]

        self.client = MongoClient(self.DB_URL)

        self.log_writer = App_Logger()

    def get_database(self, db_name: str, log_file):
        """
        Method Name :   get_database
        Description :   This method gets database from MongoDB from the db_name

        Output      :   A database is created in MongoDB with name as db_name
        On Failure  :   Write an exception log and then raise an exception

        Version     :   1.2
        Revisions   :   moved setup to cloud
        """
        method_name = self.get_database.__name__

        self.log_writer.start_log("start", self.class_name, method_name, log_file)

        try:
            db = self.client[db_name]

            self.log_writer.log(f"Created {db_name} database in MongoDB", log_file)

            self.log_writer.start_log("exit", self.class_name, method_name, log_file)

            return db

        except Exception as e:
            self.log_writer.exception_log(e, self.class_name, method_name, log_file)

    def get_collection(self, database: str, collection_name: str, log_file):
        """
        Method Name :   get_collection
        Description :   This method gets collection from the particular database and collection name

        Output      :   A collection is returned from database with name as collection name
        On Failure  :   Write an exception log and then raise an exception

        Version     :   1.2
        Revisions   :   moved setup to cloud
        """
        method_name = self.get_collection.__name__

        self.log_writer.start_log("start", self.class_name, method_name, log_file)

        try:
            collection = database[collection_name]

            self.log_writer.log(
                f"Created {collection_name} collection in mongodb", log_file
            )

            self.log_writer.start_log("exit", self.class_name, method_name, log_file)

            return collection

        except Exception as e:
            self.log_writer.exception_log(e, self.class_name, method_name, log_file)

    def get_collection_as_dataframe(self, db_name: str, collection_name: str, log_file):
        """
        Method Name :   get_collection_as_dataframe
        Description :   This method is used for converting the selected collection to dataframe

        Output      :   A collection is returned from the selected db_name and collection_name
        On Failure  :   Write an exception log and then raise an exception

        Version     :   1.2
        Written by  :   iNeuron Intelligence
        Revisions   :   moved setup to cloud
        """
        method_name = self.get_collection_as_dataframe.__name__

        self.log_writer.start_log("start", self.class_name, method_name, log_file)

        try:
            database = self.get_database(db_name, log_file)

            collection = database.get_collection(name=collection_name)

            df = DataFrame(list(collection.find()))

            if "_id" in df.columns.to_list():
                df = df.drop(columns=["_id"], axis=1)

            self.log_writer.log("Converted collection to dataframe", log_file)

            self.log_writer.start_log("exit", self.class_name, method_name, log_file)

            return df

        except Exception as e:
            self.log_writer.exception_log(e, self.class_name, method_name, log_file)

    def insert_dataframe_as_record(
        self, data_frame, db_name: str, collection_name: str, log_file
    ):
        """
        Method Name :   insert_dataframe_as_record
        Description :   This method inserts the dataframe as record in database collection

        Output      :   The dataframe is inserted in database collection
        On Failure  :   Write an exception log and then raise an exception

        Version     :   1.2
        Revisions   :   moved setup to cloud
        """
        method_name = self.insert_dataframe_as_record.__name__

        self.log_writer.start_log("start", self.class_name, method_name, log_file)

        try:
            records = loads(data_frame.T.to_json()).values()

            self.log_writer.log(f"Converted dataframe to json records", log_file)

            database = self.get_database(db_name, log_file)

            collection = database.get_collection(collection_name)

            self.log_writer.log("Inserting records to MongoDB", log_file)

            collection.insert_many(records)

            self.log_writer.log("Inserted records to MongoDB", log_file)

            self.log_writer.start_log("exit", self.class_name, method_name, log_file)

        except Exception as e:
            self.log_writer.exception_log(e, self.class_name, method_name, log_file)
