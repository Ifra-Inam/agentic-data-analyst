# AdventureWorks Business Definitions

**Purpose of this document:** This is a business glossary for the AdventureWorks Cycles data analyst agent. It defines what business terms *mean* so that the agent can correctly map a natural-language question to the right tables, columns, and filters. It does not replace schema inspection — the agent should still query the live database for structure. This document exists to resolve ambiguity in what the user is actually asking for.

Schema note: AdventureWorks is organized into five PostgreSQL schemas: `sales`, `production`, `purchasing`, `humanresources`, and `person`. Table and column names below are given in lowercase, matching the standard AdventureWorks-for-Postgres port.

---

## Business Entity

**Definition:**
The root identity concept in AdventureWorks. Every person, store, and vendor in the database is first registered as a row in `person.businessentity`, which exists only to generate a shared primary key (`businessentityid`). Specific details are then attached in a role-specific table (`person.person`, `sales.store`, `purchasing.vendor`, `humanresources.employee`, `sales.salesperson`).

**Related concepts:** Customer, Employee, Salesperson, Store, Vendor, Person

**Relevant AdventureWorks data:**
- `person.businessentity` (businessentityid)
- `person.person` (businessentityid, persontype)

**Common user terminology:**
entity, party, record, "who is this"

**Important distinction:**
A `businessentityid` on its own does not tell you what *kind* of entity it is. The `persontype` column on `person.person` disambiguates: `IN` = individual customer, `SP` = sales person, `EM` = employee, `VC` = vendor contact, `SC` = store contact, `GC` = general contact. The agent should not assume a businessentityid refers to a customer without checking which role table(s) it appears in.

---

## Customer

**Definition:**
An entity that has placed, or can place, sales orders with AdventureWorks. Customers come in two forms: **individual consumers** who buy directly (typically online), and **stores** (resellers) who buy through a sales representative for resale.

**Related concepts:** Individual customer, Store/customer account, Sales order, Sales territory

**Relevant AdventureWorks data:**
- `sales.customer` (customerid, personid, storeid, territoryid, accountnumber)
- `person.person` (for individual customers, via personid)
- `sales.store` (for store/reseller customers, via storeid)

**Common user terminology:**
customer, client, buyer, account, "who's buying"

**Important distinction:**
`sales.customer` is a single row per selling relationship, not per person. Exactly one of `personid` or `storeid` is populated per row:
- `personid` populated, `storeid` NULL → an **individual customer** (consumer).
- `storeid` populated → a **store/reseller customer**; `personid` may also be populated but represents the store's primary contact, not the buyer of record.
"Customer" in a user's question is ambiguous between these two types unless they say "individual customers" or "store/reseller customers" — see `company_policies.md` for the recommended handling.

---

## Individual Customer

**Definition:**
A person who buys AdventureWorks products directly as a consumer, typically through the online store.

**Related concepts:** Customer, Person, Sales order (OnlineOrderFlag)

**Relevant AdventureWorks data:**
- `sales.customer` where `personid` is not null
- `person.person` (persontype = 'IN')
- `sales.salesorderheader.onlineorderflag` — TRUE generally corresponds to consumer/online orders

**Common user terminology:**
individual, consumer, retail customer, online customer, "regular customer"

**Important distinction:**
Individual customers are not the same population as "store" customers, and generally do not have an assigned sales territory salesperson driving the sale — their orders are typically self-service/online. [REQUIRES BUSINESS CLARIFICATION] whether "individual customer" should always be cross-checked against `onlineorderflag`, since the two concepts are related but not formally the same field.

---

## Store / Customer Account (Reseller)

**Definition:**
A retail or wholesale business entity that purchases AdventureWorks products for resale, rather than for personal consumption. Stores are served by AdventureWorks sales representatives.

**Related concepts:** Customer, Salesperson, Business Entity

**Relevant AdventureWorks data:**
- `sales.store` (businessentityid, name, salespersonid, demographics)
- `sales.customer` where `storeid` is not null

**Common user terminology:**
store, reseller, retailer, wholesale account, "our accounts", dealer

**Important distinction:**
Do not confuse a "store" (a reseller/customer of AdventureWorks) with AdventureWorks' own retail channel — AdventureWorks Cycles does not operate its own physical retail stores in this dataset; `sales.store` rows represent independent third-party resellers. Each store can be linked to a specific `salespersonid` who manages that account.

---

## Sales Order

**Definition:**
A single customer transaction/order header — represents the commercial "who, when, and how much" of one order, but not the individual line items.

**Related concepts:** Sales order line, Customer, Salesperson, Sales territory, Sales reason

**Relevant AdventureWorks data:**
- `sales.salesorderheader` (salesorderid, orderdate, duedate, shipdate, customerid, salespersonid, territoryid, subtotal, taxamt, freight, onlineorderflag, status)

**Common user terminology:**
order, sale, transaction, purchase, "an order"

**Important distinction:**
"Order" is ambiguous between a **sales order** (a customer buying from AdventureWorks, in `sales.*`) and a **purchase order** (AdventureWorks buying from a vendor, in `purchasing.*`). If the user's question involves customers, revenue, or products sold, they mean a sales order. If it involves vendors or restocking, they mean a purchase order. See "Purchase Order" below.

---

## Sales Order Line (Sales Order Detail)

**Definition:**
An individual product line within a sales order — one row per distinct product/quantity/price combination on an order. A single sales order typically has multiple sales order lines.

**Related concepts:** Sales order, Product, Special offer

**Relevant AdventureWorks data:**
- `sales.salesorderdetail` (salesorderid, salesorderdetailid, productid, orderqty, unitprice, unitpricediscount, specialofferid)

**Common user terminology:**
order line, order item, line item, "products in the order"

**Important distinction:**
Revenue, quantity, and discount figures live at the **line level**, not the header level. `sales.salesorderheader.subtotal` is a header-level total but is not itself a stored, verified column in every AdventureWorks port (see `metric_definitions.md` for exact calculation guidance) — analytically, product-level and category-level revenue must be computed by aggregating `sales.salesorderdetail`, not by dividing the header subtotal.

---

## Product

**Definition:**
An individual sellable/manufacturable item, such as a specific bicycle, component, or accessory.

**Related concepts:** Product model, Product subcategory, Product category, Inventory, Manufacturing

**Relevant AdventureWorks data:**
- `production.product` (productid, name, productnumber, listprice, standardcost, color, size, productsubcategoryid, productmodelid, makeflag, finishedgoodsflag)

**Common user terminology:**
product, item, SKU, "what we sell"

**Important distinction:**
"Product" (a specific sellable variant, e.g. a particular size/color of bike) is distinct from "Product Model" (the underlying design shared across variants, see below). A question like "how many bikes do we sell" may mean distinct products, distinct models, or total units — clarify if ambiguous.

---

## Product Category

**Definition:**
The top-level grouping of products, e.g. Bikes, Components, Clothing, Accessories.

**Related concepts:** Product subcategory, Product

**Relevant AdventureWorks data:**
- `production.productcategory` (productcategoryid, name)
- linked to products via `production.productsubcategory.productcategoryid` → `production.product.productsubcategoryid`

**Common user terminology:**
category, product line (informal), department, "what kind of product"

**Important distinction:**
Category is two joins away from `production.product` (Product → Subcategory → Category). A product's `productsubcategoryid` can be NULL for non-merchandise items (e.g. raw materials), meaning such products won't roll up to any category.

---

## Product Subcategory

**Definition:**
A finer grouping within a category, e.g. within "Bikes": Mountain Bikes, Road Bikes, Touring Bikes.

**Related concepts:** Product category, Product

**Relevant AdventureWorks data:**
- `production.productsubcategory` (productsubcategoryid, productcategoryid, name)

**Common user terminology:**
subcategory, type of product, "kind of bike"

**Important distinction:**
Do not confuse subcategory (a merchandising grouping) with Product Model (an engineering/design grouping, see below) — a subcategory contains many models, and a model belongs to exactly one subcategory.

---

## Product Model

**Definition:**
The base design of a product, independent of specific size/color variants. For example, "Mountain-100" is a model; the specific red, 42cm version sold is a Product.

**Related concepts:** Product, Product subcategory

**Relevant AdventureWorks data:**
- `production.productmodel` (productmodelid, name, catalogdescription, instructions)
- `production.product.productmodelid`

**Common user terminology:**
model, product line (informal), design

**Important distinction:**
Counting "products" vs "models" gives different numbers — many `production.product` rows (different sizes/colors) can share one `productmodelid`. If a user asks "how many bike models do we have" vs "how many bike products do we have," these require different `COUNT(DISTINCT ...)` targets.

---

## Salesperson

**Definition:**
An AdventureWorks employee responsible for managing customer relationships (primarily store/reseller accounts) and driving sales within an assigned territory.

**Related concepts:** Employee, Sales territory, Store, Sales order

**Relevant AdventureWorks data:**
- `sales.salesperson` (businessentityid, territoryid, salesquota, bonus, commissionpct, salesytd, saleslastyear)
- `humanresources.employee` (businessentityid, jobtitle) — a salesperson is also an employee
- `sales.salesorderheader.salespersonid`

**Common user terminology:**
salesperson, sales rep, rep, account manager

**Important distinction:**
Not every employee is a salesperson — only employees who also have a row in `sales.salesperson` are salespeople. `sales.salesperson.salesytd` and `salesLastyear` are stored, pre-aggregated figures; they should be treated as summary/reporting fields, and any custom time-period analysis should instead aggregate `sales.salesorderheader`/`sales.salesorderdetail` directly rather than relying on these fields, since the stored totals reflect a fixed historical cutoff in the sample data.

---

## Sales Territory

**Definition:**
A geographic sales region (e.g. Northwest, Southwest, Canada, France, Germany, Australia, United Kingdom) used to organize salespeople, customers, and reporting.

**Related concepts:** Salesperson, Customer, Sales order

**Relevant AdventureWorks data:**
- `sales.salesterritory` (territoryid, name, countryregioncode, "group", salesytd, saleslastyear, costytd, costlastyear)
- `sales.salesorderheader.territoryid`
- `sales.customer.territoryid`
- `sales.salesperson.territoryid`

**Common user terminology:**
territory, region, market, country/area

**Important distinction:**
Territory can be attached at the order level, the customer level, or the salesperson level — these are not always identical (e.g. a customer's territory and the territory recorded on a specific order could diverge if data changed over time). For "sales by territory," `sales.salesorderheader.territoryid` is the most direct field for a specific order's territory attribution.

---

## Sales Reason

**Definition:**
A coded explanation of *why* a customer made a purchase (e.g. price, quality, promotion, marketing, review, other), associated with sales orders on a many-to-many basis.

**Related concepts:** Sales order

**Relevant AdventureWorks data:**
- `sales.salesreason` (salesreasonid, name, reasontype)
- `sales.salesorderheadersalesreason` (salesorderid, salesreasonid) — cross-reference table

**Common user terminology:**
reason for purchase, why customers buy, motivation, purchase driver

**Important distinction:**
An order can have zero, one, or multiple sales reasons attached. Aggregating "orders by reason" therefore means an order may be counted under more than one reason — this is not a mutually exclusive breakdown and double-counting across reasons is expected and correct, not an error.

---

## Vendor

**Definition:**
An external supplier from whom AdventureWorks purchases raw materials or components used in manufacturing.

**Related concepts:** Purchase order, Product

**Relevant AdventureWorks data:**
- `purchasing.vendor` (businessentityid, accountnumber, name, creditrating, preferredvendorstatus, activeflag)
- `purchasing.productvendor` (productid, businessentityid, standardprice, minorderqty, maxorderqty)

**Common user terminology:**
vendor, supplier, "who we buy from"

**Important distinction:**
Vendors supply AdventureWorks; they are not customers. A single product can have multiple approved vendors via `purchasing.productvendor`.

---

## Purchase Order

**Definition:**
An order placed by AdventureWorks to a vendor to procure materials/components — the inbound counterpart to a (outbound) sales order.

**Related concepts:** Vendor, Sales order (contrast), Employee (who placed the order)

**Relevant AdventureWorks data:**
- `purchasing.purchaseorderheader` (purchaseorderid, employeeid, vendorid, shipmethodid, orderdate, shipdate, subtotal, taxamt, freight, status)
- `purchasing.purchaseorderdetail` (purchaseorderid, purchaseorderdetailid, productid, orderqty, unitprice, receiveqty, rejectedqty)

**Common user terminology:**
purchase order, PO, restock order, procurement order

**Important distinction:**
See "Sales Order" above — "order" without qualification is ambiguous. Purchase orders reference an `employeeid` (the AdventureWorks employee who issued the order), not a `salespersonid`, since this is an internal procurement action, not a sale.

---

## Inventory

**Definition:**
The quantity of a given product currently on hand at a specific storage location.

**Related concepts:** Product, Production/Manufacturing

**Relevant AdventureWorks data:**
- `production.productinventory` (productid, locationid, shelf, bin, quantity)
- `production.location` (locationid, name, costrate, availability)

**Common user terminology:**
inventory, stock, stock level, on-hand quantity, "how much do we have"

**Important distinction:**
Inventory quantity is stored per product **per location** — a product's total on-hand quantity requires summing `quantity` across all `locationid` rows for that product. Inventory is a point-in-time stored snapshot in this dataset, not a time series; there is no continuous inventory history table for on-hand stock levels (`production.transactionhistory` records movement events, not running balances).

---

## Employee

**Definition:**
A person employed by AdventureWorks, in any role (manufacturing, sales, management, engineering, etc.).

**Related concepts:** Department, Salesperson, Business Entity

**Relevant AdventureWorks data:**
- `humanresources.employee` (businessentityid, jobtitle, hiredate, birthdate, gender, maritalstatus, salariedflag, currentflag)
- `person.person` (name fields, via businessentityid)

**Common user terminology:**
employee, staff, worker, headcount

**Important distinction:**
`humanresources.employee.currentflag` distinguishes currently active employees from historical/terminated ones — "how many employees do we have" should generally filter to `currentflag = true` unless the user asks about all employees ever recorded, historically. Not all employees are salespeople (see Salesperson above).

---

## Department

**Definition:**
An organizational unit that employees belong to (e.g. Engineering, Sales, Production, Marketing, Quality Assurance).

**Related concepts:** Employee

**Relevant AdventureWorks data:**
- `humanresources.department` (departmentid, name, groupname)
- `humanresources.employeedepartmenthistory` (businessentityid, departmentid, startdate, enddate)

**Common user terminology:**
department, team, group, division

**Important distinction:**
Department membership is historical/time-bound via `employeedepartmenthistory` (an employee can have moved between departments). Current department requires filtering to the history row with `enddate IS NULL` (or the most recent `startdate`).

---

## Production

**Definition:**
The set of internal processes and records related to manufacturing AdventureWorks' own products, as distinct from buying (purchasing) or selling (sales).

**Related concepts:** Manufacturing, Product, Vendor (contrast), Customer (contrast)

**Relevant AdventureWorks data:**
- `production.workorder` (workorderid, productid, orderqty, scrappedqty, startdate, enddate, duedate)
- `production.billofmaterials` (productassemblyid, componentid, perassemblyqty)
- `production.transactionhistory` (transactiontype: W = WorkOrder/manufacturing, S = Sales, P = Purchasing)

**Common user terminology:**
production, manufacturing, factory, assembly, "what we make"

**Important distinction:**
Production concerns internally manufactured goods (`makeflag = true` on `production.product`); not all products are manufactured in-house — some are purchased finished from vendors (`makeflag = false`).

---

## Manufacturing

**Definition:**
Synonym used interchangeably with "Production" in this dataset — see Production above. Refers specifically to the process of building products from components (Bill of Materials) via Work Orders.

**Related concepts:** Production, Bill of Materials, Work Order

**Relevant AdventureWorks data:**
- `production.workorder`, `production.workorderrouting`, `production.billofmaterials`

**Common user terminology:**
manufacturing, assembly, build, "how we make it"

**Important distinction:**
None beyond what's noted under Production.

---

## Reseller / Store

See "Store / Customer Account (Reseller)" above — these terms refer to the same concept.
