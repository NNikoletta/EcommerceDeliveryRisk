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
An order is only able to contribute outcome-based features if its outcome was known before the examined order's approval time.

Every order that reached the approved status is eligible for prediction at order_approved_at. Only information available at the time of approval can affect the eligibility, and it cannot depend on the order's eventual delivery status.

Delivery outcomes will be divided into two groups. A non-delivery model will be created to predict whether an approved order
will be canceled, become unavailable, or remain undelivered. A separate late-delivery model will predict if an order will arrive after its promised delivery date, conditional on the order eventually being delivered.

Historical canceled, unavailable, and never-delivered orders will be included when training the non-delivery model but excluded from the conditional late-delivery model because they do not have an observable delivery date.

### Shared characteristics of the two models

**Prediction unit:** The prediction unit must be one order, identified by order_id

**Canceled, unavailable, lost/never-delivered orders:** Orders from these categories will be excluded from the conditional late-delivery model but retained for training the non-delivery model. Their presence may distort the delivery timeline. Orders may get canceled due to a client changing their mind, due to fraud, or due to lack of stock, among others.
Orders may get lost in transit, or have the wrong shipping address, which is one of the many causes of items not being delivered. These orders need to be taken out of the main training pool, but they will be used for a separate non-delivery risk prediction.

**Train/Validate/Test split:** The splitting of the data must happen in a chronological manner with the oldest, historical, entries being the main building blocks of the training dataset.
The validation dataset will be created from Mid Data, and the test split will be based on the Most Recent Data. The dataset contains orders placed between 2016 and 2018. The two models will use separate modeling populations. The non-delivery model will include eligible historical approved orders with observable outcomes. The conditional late-delivery model will include only orders that were eventually delivered.
Both datasets will follow the earlier described chronological split based on approval time.

### Late-delivery model

**Model output:** The model outputs the estimated probability that an eligible order will arrive late.

**Target labels:**
* 0: order arrives on time
* 1: order arrives late

**Target formula:** order_delivered_customer_date > order_estimated_delivery_date: an order can be considered late if it arrived after the estimated delivery date.

### Non-delivery model

**Model output:** The model outputs the estimated probability that an order will not be delivered.

**Target labels:**
* 0: order will eventually be delivered
* 1: order will be canceled, is unavailable, or otherwise confirmed as non-delivered


Orders whose outcome is still unresolved at the dataset cutoff will not automatically be labeled as non-delivered; they will be treated as censored and excluded unless a sufficient observation window can establish the outcome.