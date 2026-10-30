# AdventureWorks Data & Analytical Conventions

**Purpose of this document:** AdventureWorks is a sample database, not a real company, so there are no genuine corporate policies to document. Instead, this document captures the data-model conventions and analytical assumptions an AI data analyst needs to interpret AdventureWorks data correctly and avoid silently wrong conclusions. Each rule is labeled:

- **Dataset-defined** — directly supported by the AdventureWorks data model/schema.
- **Analytical convention** — a recommended interpretation the agent should default to, absent other instruction.
- **Requires clarification** — genuinely ambiguous; the agent should ask the user rather than assume.

---

## How a Sale Is Represented

**Classification:** Dataset-defined

A sale is represented across two tables: `sales.salesorderheader` (one row per order — customer, dates, salesperson, territory, header-level monetary totals) and `sales.salesorderdetail` (one row per product line within that order — product, quantity, unit price, discount). Any question about "what was sold" (products, quantities, discounts) must join to `salesorderdetail`; questions purely about "when/who/how many orders" can often be answered from `salesorderheader` alone.

---

## Sales Revenue

**Classification:** Analytical convention

When a user asks for "sales revenue" or "total sales" without specifying a measure, use net line revenue after discount as the default and state that assumption:

- Net line revenue after discount: `unitprice * (1 - unitpricediscount) * orderqty`

Use gross line revenue (`unitprice * orderqty`) when the user explicitly asks for revenue before discounts. Gross and net line revenue must be calculated from the line-item fields rather than read from a stored line-total column. If the user explicitly asks for an order total including tax and freight, use the stored `salesorderheader.totaldue` (sum it directly at order grain; do not re-add `subtotal`, `taxamt`, and `freight`). Label it as including tax and freight, and not as the default revenue measure. The line-level `salesorderdetail.linetotal` is not present in the SQL dump. See `metric_definitions.md` for details.

---

## Individual vs. Store Customers

**Classification:** Dataset-defined

`sales.customer` represents two structurally different kinds of buyer: individual consumers (`personid` populated) and reseller stores (`storeid` populated). A single row is never both. Aggregate "customer" metrics (e.g. "average revenue per customer," "top customers") should state which population is being analyzed when the distinction is likely to matter, since blending consumer and reseller order sizes produces a misleading average.

---

## How Products Are Categorized

**Classification:** Dataset-defined

Products roll up to categories through two joins: Product → Subcategory → Category. `productsubcategoryid` is nullable on `production.product`, so a small number of products may not belong to any subcategory/category. Product Model is a separate, parallel hierarchy (design grouping, not merchandising grouping) and should not be conflated with Category or Subcategory.

---

## How Sales Territories Are Represented

**Classification:** Dataset-defined

Territory can be attached at three different points: the customer (`sales.customer.territoryid`), the salesperson (`sales.salesperson.territoryid`), and the order itself (`sales.salesorderheader.territoryid`). For "sales by territory" questions, use the order-level territory field, since it reflects the territory actually attributed to that specific transaction. Customer- or salesperson-level territory should only be used when the question is specifically about customer or salesperson attributes rather than transaction attribution.

---

## How Sales Reasons Are Associated with Orders

**Classification:** Dataset-defined

`sales.salesorderheadersalesreason` is a many-to-many cross-reference: an order can have zero, one, or several sales reasons. When aggregating "orders by reason," a single order may legitimately be counted under multiple reasons. This is expected behavior, not double-counting to be corrected — the agent should not attempt to force a one-reason-per-order allocation.

---

## How Employees/Salespeople Relate to Sales

**Classification:** Dataset-defined

A salesperson is an employee who additionally has a row in `sales.salesperson`, sharing the same `businessentityid` with `humanresources.employee`. Not all employees are salespeople; sales attribution on an order (`sales.salesorderheader.salespersonid`) only applies to orders that went through a rep, which is more common for store/reseller orders than for direct online consumer orders. `sales.salesperson.salesytd` / `saleslastyear` are stored summary figures reflecting a fixed point in the sample data's history and should not be treated as a live, continuously updating total — for any specific date range, aggregate `sales.salesorderheader` directly instead.

---

## Differences Between Sales and Purchasing

**Classification:** Dataset-defined

Sales (`sales.*`) represents AdventureWorks selling to customers (revenue, outbound). Purchasing (`purchasing.*`) represents AdventureWorks buying from vendors (spend, inbound). The two domains are structurally parallel (header + detail, with subtotal/tax/freight fields) but represent opposite economic flows and must never be summed together as a single "total transactions" or "total revenue" figure. A purchase order references the AdventureWorks `employeeid` who placed it, not a `salespersonid`.

---

## Stored and Absent Derived Monetary Fields

**Classification:** Dataset-defined

The checked SQL dump confirms that `sales.salesorderheader.totaldue` is present and represents `subtotal + taxamt + freight`. It is not the default revenue measure because it includes tax and freight. The following derived columns are absent from their table definitions in this dump: `sales.salesorderdetail.linetotal`, `purchasing.purchaseorderdetail.linetotal`, and `purchasing.purchaseorderheader.totaldue`. Calculate line totals from their component fields. Verify against the active database when it may differ from this dump; do not generalize column absence from one port to every AdventureWorks version.

---

## Inventory Is a Snapshot, Not a Time Series

**Classification:** Dataset-defined

`production.productinventory` stores current quantity on hand per product per location; it is not a historical ledger. `production.transactionhistory` records discrete inventory-affecting events (sales, purchases, work orders) but reconstructing historical inventory levels from it (rather than reading current snapshot values) is a more complex derived analysis and should be flagged to the user as such rather than presented as a simple lookup.

---

## Current vs. Historical Employees

**Classification:** Analytical convention

"How many employees do we have" should default to `humanresources.employee.currentflag = true` (active employees only) unless the user asks about historical or terminated staff. Department assignment should similarly default to the current row in `employeedepartmenthistory` (`enddate IS NULL`), not the full history, unless a historical view is requested.

---

## "Product Performance" Has No Single Definition

**Classification:** Requires clarification

Terms like "top-performing products," "best products," or "product performance" could mean revenue, units sold, profit margin (list price vs. standard cost), order frequency, or customer ratings (`production.productreview`). The agent should ask the user which metric they mean when it isn't specified and the choice would materially change the answer, rather than silently defaulting to one interpretation. See `metric_definitions.md` for the metrics available to choose from.

---

## Gross vs. Net Figures

**Classification:** Analytical convention

AdventureWorks does not define a single canonical "gross sales" or "net sales" figure. For an unspecified sales revenue question, default to net line revenue after discount and state that assumption; do not ask the user to choose. If using the order-level `totaldue`, state that it includes tax and freight and is not the default revenue measure. See `metric_definitions.md` for the component fields and formulas.

---

## Return / Refund Data

**Classification:** Requires clarification

[NOT DEFINED BY ADVENTUREWORKS] — the standard AdventureWorks OLTP dataset used for this Postgres port does not include a dedicated sales-return or refund transaction table. If a user asks about product returns, the agent should clarify what data they expect this to be based on (e.g. `production.transactionhistory` transaction types, or `production.scrapreason`/work-order scrap data, which represent manufacturing scrap, not customer returns) rather than assuming a returns table exists.
