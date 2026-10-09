# E-commerce Delivery Risk Project

This project aims to implement an end-to-end pipeline for delivery risk prediction using the [Brazilian E-Commerce Olist dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) that is publicly available on Kaggle.

## Project Status

Project is in its experimental stage focusing on tuning the ML model used for classification.

## A little bit about the data

The project focuses on the Brazilian E-Commerce dataset acquired from Kaggle. It consists of a total of 9 separate .csv files.

The .csv files are downloaded, and validated in python. A benchmark manifest is created based on the datasets that also includes
a calculated SHA-256 along with the details of every file.

When there are no files or manifests available, the data is downloaded from Kaggle, validated and saved.

If a benchmark manifest already exists, the pipeline runs checks to ensure that the data that is being downloaded adheres to the existing manifest.
A new, temporary manifest is then saved and can be compared to the benchmark manifest through validation.

When data already exists, unless specified otherwise, a new download will not happen and the data will not be overwritten.

The files responsible for downloading and validating data as well as creating and saving the manifests have
a developed set of pytest test which can be run through a terminal.

## PostgreSQL and DBeaver

To handle multiple datasets with various data PostgreSQL is used. A container is created in Docker that hosts the
queries. The data handling files can be found in the sql direcotry of this project.

To be able to visualize the connections between the tables, a connection is made to DBeaver, however, it is used only
for screening/temporary queries and as mentioned before visualization. All data handling is managed through saved .sql files.

First three schemas are created: raw, staging, curated.

The raw schema contains the completely raw tables with the column name spelling and data types matching the ones in the .csv files.
After the raw tables are created, the project moves into its staging phase. The staging tables are created while already keeping in mind the correct
column name spelling, data types, and primary key and foreign key constraints along with the not null constraints. 
The staging tables are loaded with the data and are later used for profiling before the curated tables can be created.
The profiling queries can be found in the 001_profile_staging_data.sql file. The outcomes are described in further detail in the docs/sql_profiling_findings.md

The curated tables are created considering the fact that the ML used for classification will require some data like timestamps to be 
modified in a way that extracts the most important information.

In case of timestamps, hour of the day, day of the week, and month details are extracted. To ensure that every order
is represented by one row of data the multiple latitude and longitude coordinates belonging to one zip code prefix are aggregated by finding the median.
The reviews are currently excluded from both non-delivery and late-delivery pipelines since they include data acquired after the 
orders were delivered, and using it might cause data leakage.

## Models

Because the data contains items that were not delivered and canceled, as described in the problem definition section, I have decided to create to models:
non-delivery prediction and late-delivery prediction.

Two curated tables were created to accommodate the differences in data that needs to be used for each model.

Both datasets are highly imbalanced.

### Non-delivery model

