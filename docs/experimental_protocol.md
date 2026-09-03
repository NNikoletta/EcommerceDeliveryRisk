# E-commerce Delivery Risk Prediction: Experimental Protocol

**Protocol version:** - 0.2 (draft)

**Status:** Draft

**Project:** E-commerce delivery Risk Prediction

**Repository:** 'NNikoletta/EcommerceDeliveryRisk'

## 1. Purpose

This file defines the experimental approach used to develop, compare, select, and evaluate the models and pipelines used in this project. Its purpose is to ensure that all experiments are reproducible, all the comparisons are fair, and there is no data leakage in the architecture.

All conducted experiments must follow this protocol.

## 2. Experimental principles

The following rules apply throughout this project:

1. All data must be downloaded and validated automatically without manual interference.
2. Downloaded data must be validated using multiple methods including an SHA-256 checksum.
3. The persistent source of truth and transformation must be PostgreSQL. All data must not be stored in Pandas dataframes but an SQL database, however, handling the data in Pandas and NumPy at the final model-training is reasonable.
4. All Machine Learning methods must be implemented in python and connected with the dataset.
5. When conducting ML experiments, training, validation, and testing datasets have to be completely isolated with no overlapping entries to avoid data leakage.
6. Preprocessing must only be fitted on the training data.
7. Every experimental choice must be made through configuration rather than manual changes in the source code.
8. Every result must create a new result code ensuring that no output gets overwritten.
9. Results must be reported with enough metadata to identify the dataset and the data used for training, validation and testing. The data includes the source-code version, configuration, software environment, and random seeds.
10. Before starting the first ML experiments, an MLFlow connection must be made for easy tracking.
11. All experiments are conducted according to the [prediction contract](./problem_definition.md) which defines the boundaries between legal features and future information.
12. All predictions must fall in the range defined by the [prediction unit](./problem_definition.md); the prediction unit can be converted to \[%\] to represent chance instead of probability.