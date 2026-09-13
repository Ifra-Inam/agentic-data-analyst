# AdventureWorks Metric Definitions

**Purpose of this document:** This is a metric dictionary for the AdventureWorks data analyst agent. Every metric below has been checked against the actual AdventureWorks-for-Postgres schema, including which computed columns exist as stored fields versus which must be calculated. **Important schema note:** the original SQL Server AdventureWorks includes several computed columns (`linetotal`, `totaldue`, `salesordernumber`) that are dropped during setup in the standard Postgres port and are therefore NOT available as stored columns — every formula below reflects this.

---

# Sales Revenue

## Definition

A monetary measure of the value of goods sold to customers. There are multiple valid definitions depending on whether discounts, tax, and freight are included — see Ambiguity below.

## Calculation

- **Net line revenue** (recommended default): `sales.salesorderdetail.unitprice * (1 - sales.salesorderdetail.unitpricediscount) * sales.salesorderdetail.orderqty`
- **Gross line revenue** (before discount): `sales.salesorderdetail.unitprice * sales.salesorderdetail.orderqty`
- **Order total including tax/freight**: `sales.salesorderheader.subtotal + sales.salesorderheader.taxamt + sales.salesorderheader.freight`, where `subtotal` should itself equal the sum of net line revenue for that order's lines.

## Relevant Data

- `sales.salesorderdetail`
- `sales.salesorderheader`

## Important Columns

- `salesorderdetail.unitprice` — actual transaction price per unit
- `salesorderdetail.unitpricediscount` — fractional discount (e.g. 0.10 = 10% off), 0 if none
- `salesorderdetail.orderqty` — units on that line
- `salesorderheader.subtotal`, `taxamt`, `freight` — header-level totals (subtotal is a stored value, not a computed column, but should reconcile to the sum of line totals)

## Aggregation

SUM at the line level for product/category/period breakdowns. Do not aggregate `unitprice` by itself (it's a per-unit rate, not a total) — always multiply by `orderqty` first.

## Common Dimensions

- Customer
- Product
- Product Category / Subcategory
- Sales Territory
- Salesperson
- Date (orderdate, duedate, shipdate)
- Online vs. rep-assisted (`onlineorderflag`)

## Common User Questions

- What were our total sales / revenue?
- What products/categories generated the most revenue?
- Which territory had the highest sales?
- What's our revenue trend over time?

## Caveats

- `linetotal` and `totaldue` are computed columns in the original SQL Server schema but are **dropped** in the standard Postgres port — they do not exist as queryable columns and must be calculated as shown above.
- Joining `salesorderheader` to `salesorderdetail` and then also referencing `salesorderheader.subtotal` in the same aggregation risks double-counting if not handled carefully (the header subtotal already represents the sum across all of that order's lines). When computing revenue at the product or category level, use only `salesorderdetail`, not the header total.
- `unitprice` reflects the actual price charged, which may differ from `production.product.listprice` due to discounts or historical price changes — do not substitute list price for actual transaction price.

## Ambiguity

If a user says "revenue" without specifying gross vs. net vs. total-with-tax-and-freight, the agent should default to net line revenue (post-discount, pre-tax/freight) as the most standard commercial definition, and note the assumption in the answer, per `company_policies.md`.

---

# Order Count

## Definition

A count of distinct sales transactions (orders), not order lines or units.

## Calculation

`COUNT(DISTINCT salesorderid)` from `sales.salesorderheader`

## Relevant Data

- `sales.salesorderheader`

## Important Columns

- `salesorderid` (primary key)
- `orderdate` for period filtering
- `status` for order status filtering (if only completed/shipped orders should count)

## Aggregation

COUNT DISTINCT on `salesorderid`.

## Common Dimensions

- Customer, Territory, Salesperson, Date, Online vs. rep-assisted

## Common User Questions

- How many orders did we have last quarter?
- How many orders per customer/territory?

## Caveats

- If counting from a query joined to `salesorderdetail` (e.g. to also filter by product), use `COUNT(DISTINCT salesorderid)`, not `COUNT(*)`, since an order with multiple lines will otherwise be counted multiple times.
- `status` is a coded field (dataset-defined values such as pending/shipped/cancelled per the original schema); clarify with the user if "orders" should include cancelled orders.

## Ambiguity

"Order count" is unambiguous as a concept, but should be clarified against order status if the user's intent is specifically about completed/fulfilled sales versus all order attempts.

---

# Sales Quantity (Units Sold)

## Definition

The total number of product units sold.

## Calculation

`SUM(sales.salesorderdetail.orderqty)`

## Relevant Data

- `sales.salesorderdetail`

## Important Columns

- `orderqty`
- `productid` for product-level breakdowns

## Aggregation

SUM.

## Common Dimensions

- Product, Product Category/Subcategory, Customer, Territory, Date

## Common User Questions

- How many units of X did we sell?
- What are our top-selling products by volume?

## Caveats

- Units sold is a volume metric and is not the same as revenue — a high-volume, low-price product can outrank a high-revenue product on this metric alone. State which one is being reported when answering "best-selling."

## Ambiguity

None significant — "quantity"/"units sold" maps cleanly to `orderqty`.

---

# Average Order Value

## Definition

The average revenue per sales order.

## Calculation

`Total net revenue / COUNT(DISTINCT salesorderid)`, where total net revenue is the SUM of net line revenue (see Sales Revenue above) over the relevant order set.

## Relevant Data

- `sales.salesorderdetail`
- `sales.salesorderheader`

## Important Columns

- `salesorderdetail.unitprice`, `unitpricediscount`, `orderqty`
- `salesorderheader.salesorderid`

## Aggregation

SUM revenue, then divide by a distinct COUNT of orders — not a simple AVG of line amounts, since orders have varying numbers of lines.

## Common Dimensions

- Customer type (individual vs. store), Territory, Date, Online vs. rep-assisted

## Common User Questions

- What's our average order value?
- Do store customers order more per transaction than individual customers?

## Caveats

- Computing this as `AVG(unitprice * orderqty)` at the line level is incorrect — it would average per-line amounts, not per-order totals. Aggregate to the order level first, then average.
- Individual (consumer) and store (reseller) orders likely differ substantially in typical size; consider segmenting by customer type per `business_definitions.md` rather than blending them, especially since AdventureWorks' resellers place bulk/wholesale-style orders.

## Ambiguity

Same gross/net/total-with-tax question as Sales Revenue applies here — clarify or default to net revenue.

---

# Revenue by Customer

## Definition

Total net revenue attributable to each customer.

## Calculation

`SUM(unitprice * (1 - unitpricediscount) * orderqty)` from `sales.salesorderdetail`, joined to `sales.salesorderheader` on `salesorderid`, grouped by `salesorderheader.customerid`.

## Relevant Data

- `sales.salesorderdetail`, `sales.salesorderheader`, `sales.customer`

## Important Columns

- `salesorderheader.customerid`
- `salesorderdetail.unitprice`, `unitpricediscount`, `orderqty`

## Aggregation

SUM, grouped by customer.

## Common Dimensions

- Individual vs. store customer, Territory, Date

## Common User Questions

- Which customers generate the most revenue?
- Who are our biggest customers?

## Caveats

- `sales.customer` rows represent either an individual (`personid`) or a store (`storeid`) — resolve the display name via the appropriate join (`person.person` or `sales.store.name`) depending on which is populated.
- Store/reseller customers will typically dominate a simple revenue ranking, since they buy in bulk; if the user wants "biggest individual customers" specifically, filter to `personid IS NOT NULL`.

## Ambiguity

None beyond the general revenue definition question above.

---

# Revenue by Product

## Definition

Total net revenue attributable to each product.

## Calculation

`SUM(unitprice * (1 - unitpricediscount) * orderqty)` from `sales.salesorderdetail`, grouped by `productid`.

## Relevant Data

- `sales.salesorderdetail`, `production.product`

## Important Columns

- `salesorderdetail.productid`, `unitprice`, `unitpricediscount`, `orderqty`
- `production.product.name` for display

## Aggregation

SUM, grouped by product.

## Common Dimensions

- Product Category/Subcategory, Territory, Date

## Common User Questions

- What are our best-selling / top-performing products?
- What are our top-selling bikes?

## Caveats

- "Top-selling bikes" requires filtering to the Bikes category via the Product → Subcategory → Category join, not a text match on product name.
- Distinguish "best by revenue" from "best by units sold" (see Sales Quantity) — these can rank differently.

## Ambiguity

"Best/top-performing" is inherently ambiguous between revenue, units, and margin — clarify per `company_policies.md` if not specified.

---

# Revenue by Category

## Definition

Total net revenue attributable to each product category.

## Calculation

`SUM(unitprice * (1 - unitpricediscount) * orderqty)` from `sales.salesorderdetail`, joined through `production.product.productsubcategoryid` → `production.productsubcategory.productcategoryid` → `production.productcategory`, grouped by category.

## Relevant Data

- `sales.salesorderdetail`, `production.product`, `production.productsubcategory`, `production.productcategory`

## Important Columns

- `salesorderdetail.productid`, `unitprice`, `unitpricediscount`, `orderqty`
- `product.productsubcategoryid`, `productsubcategory.productcategoryid`

## Aggregation

SUM, grouped by category (via two-level join).

## Common Dimensions

- Territory, Date, Subcategory (drill-down)

## Common User Questions

- Which product category generates the most revenue?
- How is revenue distributed across categories?

## Caveats

- Products with a NULL `productsubcategoryid` will not join to any category and should either be excluded or reported separately as "uncategorized," not silently dropped without mention.

## Ambiguity

None beyond the general revenue definition question.

---

# Revenue by Territory

## Definition

Total net revenue attributable to each sales territory.

## Calculation

`SUM(unitprice * (1 - unitpricediscount) * orderqty)` from `sales.salesorderdetail` joined to `sales.salesorderheader`, grouped by `salesorderheader.territoryid`.

## Relevant Data

- `sales.salesorderdetail`, `sales.salesorderheader`, `sales.salesterritory`

## Important Columns

- `salesorderheader.territoryid`
- `salesterritory.name`

## Aggregation

SUM, grouped by territory.

## Common Dimensions

- Date, Product Category

## Common User Questions

- Which sales territory performs best?
- How do territories compare?

## Caveats

- Use `salesorderheader.territoryid` (the territory recorded on the transaction), not `sales.customer.territoryid` or `sales.salesperson.territoryid`, for transaction-level territory attribution — see `company_policies.md`.
- `sales.salesterritory` also has stored `salesytd`/`saleslastyear` summary columns; these reflect a fixed snapshot in the sample data and should not be used in place of a fresh aggregation for a user-specified date range.

## Ambiguity

None beyond the general revenue definition question.

---

# Units Sold

See "Sales Quantity" above — same metric, alternate name.

---

# Average Selling Price

## Definition

The average actual transaction price per unit for a product (or set of products), as opposed to list price.

## Calculation

`SUM(unitprice * (1 - unitpricediscount) * orderqty) / SUM(orderqty)` — a quantity-weighted average, not a simple average of `unitprice` values across rows.

## Relevant Data

- `sales.salesorderdetail`

## Important Columns

- `unitprice`, `unitpricediscount`, `orderqty`

## Aggregation

Weighted average as shown above (SUM of revenue divided by SUM of quantity), not `AVG(unitprice)`.

## Common Dimensions

- Product, Category, Date

## Common User Questions

- What's the average price we actually sell product X for?
- How does average selling price compare to list price?

## Caveats

- A plain `AVG(unitprice)` treats every order line equally regardless of quantity, which distorts the result when line quantities vary — always weight by `orderqty`.
- Compare against `production.product.listprice` explicitly if the user wants to see discount impact; do not assume `unitprice` and `listprice` are the same.

## Ambiguity

None significant.

---

# Discount Amount

## Definition

The dollar value of discount applied to a sales order line, derived from the discount fraction.

## Calculation

`unitprice * unitpricediscount * orderqty`

## Relevant Data

- `sales.salesorderdetail`
- `sales.specialoffer` (for the promotional context behind a discount, via `specialofferid`)

## Important Columns

- `salesorderdetail.unitprice`, `unitpricediscount`, `orderqty`, `specialofferid`
- `sales.specialoffer.discountpct`, `description`, `type`, `category`

## Aggregation

SUM for total discount given over a period/product/category.

## Common Dimensions

- Product, Special Offer/Promotion, Date

## Common User Questions

- How much did we discount in total?
- Which promotions drove the most discounting?

## Caveats

- `unitpricediscount` is a fraction (e.g. 0.15), not a dollar amount — it must be multiplied by price and quantity to get a dollar figure.
- `sales.specialofferproduct` defines which offers were eligible for which products; the discount actually taken on a line is recorded via `specialofferid`/`unitpricediscount` on `salesorderdetail` itself.

## Ambiguity

None significant.

---

# Tax Amount

## Definition

Sales tax charged on an order.

## Calculation

Stored directly: `sales.salesorderheader.taxamt`

## Relevant Data

- `sales.salesorderheader`

## Important Columns

- `taxamt`

## Aggregation

SUM for totals over a period/territory.

## Common Dimensions

- Territory, Date

## Common User Questions

- How much sales tax have we collected?

## Caveats

- This is an order-level (header) field, not derivable from `salesorderdetail` — do not attempt to compute tax from line data.
- Purchasing has an analogous field, `purchasing.purchaseorderheader.taxamt` — do not conflate the two when the question is specifically about sales.

## Ambiguity

None.

---

# Freight

## Definition

Shipping cost charged on an order.

## Calculation

Stored directly: `sales.salesorderheader.freight` (for sales) or `purchasing.purchaseorderheader.freight` (for purchasing).

## Relevant Data

- `sales.salesorderheader`
- `purchasing.purchaseorderheader`

## Important Columns

- `freight`

## Aggregation

SUM for totals.

## Common Dimensions

- Territory, Date, Ship Method (`purchasing.shipmethod` / referenced `shipmethodid`)

## Common User Questions

- What are our total freight/shipping costs?

## Caveats

- Confirm whether the user means sales-side freight (charged to customers) or purchasing-side freight (paid to receive materials) — these are opposite economic directions.

## Ambiguity

"Freight" alone is ambiguous between sales and purchasing contexts — clarify if not specified.

---

# Gross Sales / Net Sales

## Definition

- **Gross sales**: line revenue before discount — `unitprice * orderqty`, summed.
- **Net sales**: line revenue after discount — `unitprice * (1 - unitpricediscount) * orderqty`, summed. This is the recommended default for "sales" or "revenue" per `company_policies.md`.

AdventureWorks does not define a single canonical "net sales" figure that also nets out returns, since there is no returns/refund table in this dataset (see Caveats).

## Calculation

See above; the difference between gross and net sales equals total Discount Amount (see above).

## Relevant Data

- `sales.salesorderdetail`

## Important Columns

- `unitprice`, `unitpricediscount`, `orderqty`

## Aggregation

SUM.

## Common Dimensions

- Product, Category, Territory, Date

## Common User Questions

- What's the difference between gross and net sales?
- How much did discounts cost us?

## Caveats

- [NOT DEFINED BY ADVENTUREWORKS] There is no stored returns/refund table in this dataset, so "net of returns" cannot be computed; only "net of discount" is supported. If a user asks for sales "net of returns," clarify that this cannot be derived from the available data.

## Ambiguity

Confirm which sense of "net" (net of discount vs. net of returns) the user means, since only the former is computable here.

---

# Purchase Amount (Purchasing Spend)

## Definition

The total amount spent purchasing materials/components from vendors.

## Calculation

- **Net line spend**: `purchasing.purchaseorderdetail.unitprice * orderqty` (there is no discount field on purchase order lines in this schema)
- **Order total including tax/freight**: `purchasing.purchaseorderheader.subtotal + taxamt + freight`

## Relevant Data

- `purchasing.purchaseorderdetail`
- `purchasing.purchaseorderheader`

## Important Columns

- `purchaseorderdetail.unitprice`, `orderqty`
- `purchaseorderheader.subtotal`, `taxamt`, `freight`, `vendorid`

## Aggregation

SUM.

## Common Dimensions

- Vendor, Product, Date

## Common User Questions

- How much do we spend on purchasing?
- Which vendors do we spend the most with?

## Caveats

- `purchaseorderdetail.linetotal` and `purchaseorderheader.totaldue` are computed columns in the original SQL Server schema but are **dropped** in the standard Postgres port — calculate explicitly as shown above rather than referencing these column names.
- This is inbound spend, structurally similar to Sales Revenue but economically the opposite direction — never combine with sales revenue in the same total.

## Ambiguity

Clarify whether the user wants spend including tax/freight or just the goods cost (subtotal-equivalent), consistent with the same ambiguity noted under Sales Revenue.

---

# Inventory Quantity

## Definition

The quantity of a product currently on hand, optionally broken down by storage location.

## Calculation

`SUM(production.productinventory.quantity)` grouped by `productid` (across all locations), or left ungrouped by location for a per-location view.

## Relevant Data

- `production.productinventory`
- `production.location`

## Important Columns

- `productinventory.productid`, `locationid`, `quantity`

## Aggregation

SUM across locations for a total per product; no aggregation needed for a single-location view.

## Common Dimensions

- Product, Location

## Common User Questions

- How much inventory do we have of product X?
- Which locations hold the most stock?

## Caveats

- This is a current-state snapshot, not a time series — there is no historical daily/weekly inventory-level table in this dataset. Trend questions about inventory over time are not directly supported; `production.transactionhistory` can show movement events but reconstructing historical balances from it is a materially more complex derived calculation and should be flagged as such.

## Ambiguity

None significant, aside from the snapshot-vs-history caveat above.

---

# Employee Count

## Definition

A headcount of AdventureWorks employees.

## Calculation

`COUNT(*)` from `humanresources.employee`, filtered to `currentflag = true` for active headcount (recommended default per `company_policies.md`).

## Relevant Data

- `humanresources.employee`

## Important Columns

- `businessentityid`, `currentflag`

## Aggregation

COUNT.

## Common Dimensions

- Department (via `humanresources.employeedepartmenthistory`, current row only), Salaried vs. hourly (`salariedflag`), Gender, Job Title

## Common User Questions

- How many employees do we have?
- Which employees are salespeople?
- How many employees per department?

## Caveats

- "Which employees are salespeople" requires joining `humanresources.employee` to `sales.salesperson` on `businessentityid` — a salesperson is not a distinct table of names, but an additional role attached to certain employees.
- Department breakdowns require joining to `employeedepartmenthistory` and filtering to `enddate IS NULL` for current assignment; otherwise employees who changed departments will be counted multiple times.

## Ambiguity

Clarify current vs. all-time headcount if not specified; default to current (`currentflag = true`) per `company_policies.md`.

---

# Product Return Quantity

## Definition

[NOT DEFINED BY ADVENTUREWORKS] — this metric is not supported by the standard AdventureWorks OLTP dataset. There is no sales-return, refund, or RMA (return merchandise authorization) table in this schema.

## Calculation

Not available. Do not approximate this using scrap data (`production.scrapreason`/`production.workorder.scrappedqty`), which represents manufacturing scrap during production, not customer returns of sold goods.

## Relevant Data

None available for this specific metric.

## Common User Questions

- How many products were returned?
- What's our return rate?

## Caveats

If a user asks for this metric, the agent should state plainly that AdventureWorks does not include return/refund transaction data, rather than substituting a loosely related field (like scrap quantity) without flagging the substitution clearly.

## Ambiguity

[REQUIRES BUSINESS CLARIFICATION] — if the user has a custom or extended version of the database with return data, ask them to identify the relevant table before proceeding.
