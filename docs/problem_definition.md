# E-commerce Delivery Risk Prediction: Problem Definition

**Status:** Draft

**Project:** E-commerce delivery Risk Prediction

**Repository:** 'NNikoletta/EcommerceDeliveryRisk'

## Objective

The aim of this project is to create a pipeline that is able to completely automatically predict whether a placed order will arrive late.

Late is defined as "after promised delivery date".

## Prediction Contract

The prediction contract defines the boundary between legal features and future information to avoid data leakage.

**Prediction contract:** At the time an order is **approved** predict if it will arrive **after** the promised delivery date.

This ensures that everything becomes relative to the time of approval and all data is handled in a way that would not cause data leakage.

As a consequence of the prediction contract, only the orders that are placed and/or received before the examined entry can be used for learning. These entries are treated as historical data.

**Prediction unit:** The prediction unit must be the probability of an order arriving late with 0 marking the orders arriving on time, and 1 marking the orders that will be definitely late.
