# E-commerce Delivery Risk Prediction: Experimental Protocol

**Protocol version:** - 0.1 (draft)

**Status:** Draft

**Project:** E-commerce delivery Risk Prediction

**Repository:** 'NNikoletta/DeliveryRiskPrediction'

## 1. Purpose

This file defines the experimental approach used to develop, compare, select, and evaluate the models and pipelines used in this project. Its purpose is to ensure that all experiments are reproducible, all the comparisons are fair, and there is no data leakage in the architecture.

All conducted experiments must follow this protocol.

## 2. Experimental principles

The following rules apply throughout this project:

1. All data must be downloaded and validated automatically without manual interference.
2. Downloaded data must be validated using multiple methods including an SHA-256 checksum.
3. The main tool for data handling must be and SQL based method. All data must not be stored in pandas dataframes but an SQL database.
4. All Machine Leaning methods must be implemented in python and connected with the dataset.
5. When conducting ML experiments, training, validation, and testing datasets have to be completely isolated with no overlapping entries to avoid data leakage.
6. Preprocessing must only be fitted on the training data.
7. Every experimental choice must be made through configuration rather than manual changes in the source code.
8. Every result must create a new result code ensuring that no output gets overwritten.
9. Results must be reported with enough metadata to identify the dataset and the data used for training, validation and testing. The data includes the source-code version, configuration, software environment, and random seeds.
10. Before starting the first ML experiments, an MLFlow connection must be made for easy tracking.
11. All experiments are conducted according to the [prediction contract](https://github.com/NNikoletta/EcommerceDeliveryRisk/docs/problem_definition.md#prediction-contract) which defines the boundaries between legal features and future information.