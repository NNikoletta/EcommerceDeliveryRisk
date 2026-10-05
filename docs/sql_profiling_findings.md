# SQL Profiling findings

**Status:** Draft

**Project:** E-commerce delivery Risk Prediction

**Repository:** 'NNikoletta/EcommerceDeliveryRisk'

This file intends to document the findings of the SQL profiling done during the data preparation process.

The source .sql file can be found in the src/ecommercedeliveryrisk/sql/profiling/001_profile_staging_data.sql path.

## SQL queries and their results

### 1. Order eligibility and status check

The first check performed intends to inspect how many and what order statuses exist. It also shows how many orders within each status where approved, and how many were eventually delivered.

The results of the first query are the following:

| order_status | order_count_by_status | approved_order_count | delivered_order_count |
|--------------|-----------------------|----------------------|-----------------------|
| delivered    | 96478                 | 96464                | 96470                 |
| shipped      | 1107                  | 1107                 | 0                     |
| canceled     | 625                   | 484                  | 6                     |
| unavailable  | 609                   | 609                  | 0                     |
| invoiced     | 314                   | 314                  | 0                     |
| processing   | 301                   | 301                  | 0                     |
| created      | 5                     | 0                    | 0                     |
| approved     | 2                     | 2                    | 0                     |

### 2. Defining modeling populations

The second query is checking how many orders were not approved, how many were truly delivered, how many were canceled or unavailable, and how many are unresolved.


| outcome_group           | order_count |
|-------------------------|-------------|
| censored_unresolved     | 1732        |
| confirmed_non_delivery  | 1093        |
| delivered_observed      | 96456       |
| ineligible_not_approved | 160         |

From the table above one can see the number of eligible entries for the conditional late-delivery model in the delivery_observed column and
the number of positive examples for the non-delivery model in the confirmed_non_delivery column. It also shows the entries that fall outside the prediction population in the ineligible_not_approved column, as well as the 
entries that cannot be labeled as non-delivered in the censored_unresolved attribute.

### 3. Late-delivery target

This query is working with approved entries that have an estimated delivery date and were also delivered.
If the delivery date falls after the estimated delivery, the order is considered to be late and receives the appropriate label: 1.
The table below shows the results of this check and features the number of orders belonging to each label. As one can see the dataset the future ML model will be working with is quite imbalanced
with an approximately 8.114% of the total data belonging to the target class.

| late_delivery_label | order_count |
|---------------------|-------------|
| 0                   | 88630       |
| 1                   | 7826        |


### 4. Timeline checks

This check aims to filter out any inconsistencies in the timeline of the orders. Orders need to be purchased, approved, sent to carrier, and delivered. An estimated delivery date should also be 
generated before the items are delivered. The table below shows if there are any orders that have conflicting timestamps.
One can see that no order was approved or delivered before the purchase timestamp. However, there are orders that were forwarded to the carrier before their status became approved.
There are also multiple orders that were delivered to the customer before they seem to have been delivered to the carrier, and there are also multiple orders that
were delivered without an estimated delivery date being available.

| check_name                             | invalid_row_count |
|----------------------------------------|-------------------|
| carrier_before_approval                | 1359              |
| customer_delivery_before_carrier       | 23                |
| estimated_delivery_before_purchase     | 0                 |
| approval_before_purchase               | 0                 |
| delivered_status_without_delivery_date | 8                 |

The first two cases depicted in the table above will remain in the modeling pool, since the orders were delivered to the carrier or to the customer.
The first to cases indicate a possible glitch in the system that tracks the package, but beside this mic up there seems to be no other indications that the package is
not inside the delivery pipeline. However, the last case (delivered_status_without_deliver_date) will be excluded from both models.

### 5. One-to-many connections

This query targets three tables with one-to-many connections to the orders table through the order_id.
To be able to create the main dataset the future ML will be working with, certain JOIN function/aggregations will need to be performed.
If they are not done considering these connections, multiple duplicate rows might be created or one order might be connected to multiple rows.
To see if this might occur, this query checks how many orders have multiple records, in the order_items, order_payments, and order_review tables.
The results are shown in the table below.

| source_table   | represented_orders | orders_with_multiple_records | maximum_records_per_order |
|----------------|--------------------|------------------------------|---------------------------|
| order_reviews  | 98673              | 547                          | 3                         |
| order_payments | 99440              | 2961                         | 29                        |
| order_items    | 98666              | 9803                         | 21                        |


### 6. Numeric checks

The query functions as a diagnostic check that screens the numeric values for invalid variables.
It checks if all numeric values that are connected to a real life measurement, or price are within the required range.
The following table shows that all the values were verified which allows for a constraint to be added to the tables.

| check_name                    | invalid_row_count |
|-------------------------------|-------------------|
| negative_freight_value        | 0                 |
| negative_item_price           | 0                 |
| invalid_review_score          | 0                 |
| negative_payment_value        | 0                 |
| negative_payment_installments | 0                 |

### 7. Geolocation checks

To see if there are any aggregations needed before joining the geolocation table to the customers and sellers tables, a check is performed to see how many zip codes have multiple different types of details belonging to them.
The table below shows that there are several zip codes that can span over multiple cities, states, locations.

| unique_zip_code_prefixes | zip_code_prefixes_with_multiple_records | zip_code_prefixes_with_multiple_cities | zip_code_prefixes_with_multiple_states | maximum_locations_per_zip |
|--------------------------|-----------------------------------------|----------------------------------------|----------------------------------------|---------------------------|
| 19015                    | 17972                                   | 8555                                   | 8                                      | 1146                      |

## Decisions

* Order items will be aggregated before a join can be performed to orders.
* Payments will be aggregated before a join can be performed to orders.
* Reviews will not be used as current-order features because they occur after prediction time. They may only contribute to point-in-time historical features when the review was created before the examined order’s approval time.
* Geolocation details will be aggregated to ZIP-prefix levels.
* Timeline anomalies need to be handled as described earlier.