# E-commerce Delivery Risk Prediction: Problem Definition

**Status:** Draft

**Project:** E-commerce delivery Risk Prediction

**Repository:** 'NNikoletta/DeliveryRiskPrediction'

## Objective

The aim of this project is to create a pipeline that is able to completely automatically predict whether a placed order will arrive late.

Late is defines as "after promised delivery date".

## Prediction Contract

The prediction contract defines the boundary between legal features and future information to avoid data leakage.

**Prediction contract:** At the time an order is **approved** predict if it will arrive **after** the promised delivery date.

This ensures that everything that happens after the approval like carrier hand-off time, and delivery time among others are handled in a way that would not cause data leakage.

As a consequence of the prediction contract, only the data acquired (orders placed) before the examined entry can be used for learning. These entries are treated as historical data.