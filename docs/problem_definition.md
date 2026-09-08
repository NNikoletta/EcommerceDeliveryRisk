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

**Prediction unit:** The prediction unit must be one order, identified by order_id

**Model output:** The probability of an order arriving late with 0 marking the orders arriving on time, and 1 marking the orders that will be definitely late.

**Target labels:**
* 0: order arrives on time
* 1: order arrives late

**Target formula:** order_delivered_customer_date > order_estimated_delivery_date: an order can be considered late if it arrived after the estimated delivery date.

**Canceled, unavailable, lost/never-delivered orders:** Orders from these categories will be completely excluded from the training pipeline since their presence may distort the delivery timeline. Orders may get canceled due to a client changing their mind, due to fraud, or due to lack of stock, among others.
Orders may get lost in transit, or have the wrong shipping address, which is one of the many causes of items not being delivered. These orders need to be taken out of the main training pool, but they may be used for a separate risk prediction.

**Train/Validate/Test split:** The splitting of the data must happen in a chronological manner with the oldest, historical, entries being the main building blocks of the training dataset.
The validation dataset will be created from Mid Data, and the test split will be based on the Most Recent Data. The dataset contains orders placed between 2016 and 2018. The dataset will undergo the preprocessing stages to ensure any undelivered, canceled, lost packages are not included, and then will be split into train/validate/test in an 80/10/10 ratio in chronological order.

