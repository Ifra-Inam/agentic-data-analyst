# AdventureWorks Database Documentation (Business-Oriented)

**Purpose of this document:** This explains the major business domains in the AdventureWorks database and how they relate conceptually, so the agent can navigate between domains correctly when answering cross-cutting questions. This is not a full technical schema reference — the agent can inspect the live database for exact column lists and types. Schema/table names are given in lowercase (`schema.table`), matching the standard AdventureWorks-for-Postgres port. The database has five schemas: `person`, `humanresources`, `production`, `purchasing`, `sales`.

---

## High-Level Conceptual Flow

```
Person / BusinessEntity (identity layer)
        │
        ├── Customer (Individual or Store) ──► Sales Order ──► Sales Order Detail ──► Product
        │                                            │                                    │
        │                                     Sales Territory                    Product Subcategory
        │                                            │                                    │
        │                                       Salesperson ◄── Employee          Product Category
        │
        ├── Vendor ──► Purchase Order ──► Purchase Order Detail ──► Product
        │
        └── Employee ──► Department (via history)
```

Nearly everything in AdventureWorks traces back to `person.businessentity`, which is the shared identity spine for people, stores, and vendors. Role-specific tables (`person.person`, `sales.store`, `purchasing.vendor`, `humanresources.employee`) attach details to a `businessentityid`.

---

## Domain: Sales

### Business purpose
Represents AdventureWorks' outbound transactions: customers (individuals or reseller stores) buying products, through either the online store or a sales representative.

### Important concepts
- **Sales Order** (`sales.salesorderheader`): one row per order, holding customer, salesperson, territory, dates, and monetary totals (subtotal, tax, freight).
- **Sales Order Detail** (`sales.salesorderdetail`): one row per product line within an order (product, quantity, unit price, discount).
- **Customer** (`sales.customer`): links a `personid` (individual) or `storeid` (reseller) to a `territoryid`.
- **Salesperson** (`sales.salesperson`): an employee assigned to manage a territory and/or store accounts.
- **Sales Territory** (`sales.salesterritory`): geographic sales region.
- **Sales Reason** (`sales.salesreason` + `sales.salesorderheadersalesreason`): why the customer bought (many-to-many with orders).
- **Special Offer** (`sales.specialoffer`, `sales.specialofferproduct`): promotions/discounts that can apply to an order line.

### How concepts relate
- One sales order (`salesorderheader`) has many sales order details (`salesorderdetail`), joined on `salesorderid`.
- Each sales order detail references exactly one product (`productid`).
- Each sales order references one customer (`customerid`), and typically one salesperson (`salespersonid`) and one territory (`territoryid`).
- A sales order can be linked to zero or more sales reasons via the cross-reference table.

### Common analytical questions
- "What are our total sales / revenue?"
- "Which products/categories sell best?"
- "Which customers are our biggest?"
- "Which territory or salesperson performs best?"
- "What's our average order value?"
- "Why do customers buy from us?" (sales reasons)

### Important ambiguities
- **"Revenue" is not a single stored field.** In this Postgres port, `salesorderdetail`'s per-line total (`unitprice * (1 - unitpricediscount) * orderqty`) and `salesorderheader`'s total-due figure (`subtotal + taxamt + freight`) are **not** stored, pre-computed columns — they must be calculated in the query. See `metric_definitions.md` for exact formulas.
- "Order" without qualification could mean a sales order or a purchase order — see `business_definitions.md`.
- A customer's territory (`sales.customer.territoryid`), an order's territory (`sales.salesorderheader.territoryid`), and a salesperson's territory (`sales.salesperson.territoryid`) are separate fields and can, in principle, disagree.

### Relevant database schemas/tables
`sales.salesorderheader`, `sales.salesorderdetail`, `sales.customer`, `sales.store`, `sales.salesperson`, `sales.salesterritory`, `sales.salesreason`, `sales.salesorderheadersalesreason`, `sales.specialoffer`, `sales.specialofferproduct`

---

## Domain: Products

### Business purpose
Describes what AdventureWorks makes and sells: the product catalog, its merchandising hierarchy (category/subcategory), the underlying design hierarchy (model), and current inventory levels.

### Important concepts
- **Product** (`production.product`): a specific sellable/buildable item — has a list price, standard cost, and physical attributes (color, size, weight).
- **Product Subcategory** (`production.productsubcategory`): merchandising grouping within a category.
- **Product Category** (`production.productcategory`): top-level merchandising grouping (e.g., Bikes, Components, Clothing, Accessories).
- **Product Model** (`production.productmodel`): the design/engineering grouping independent of size/color variants.
- **Inventory** (`production.productinventory`): quantity on hand per product per storage location.
- **Bill of Materials** (`production.billofmaterials`): which component products go into an assembled product.

### How concepts relate
- `production.product.productsubcategoryid` → `production.productsubcategory.productsubcategoryid` → `production.productsubcategory.productcategoryid` → `production.productcategory.productcategoryid`. Category is two joins away from Product.
- `production.product.productmodelid` → `production.productmodel.productmodelid`. Multiple product variants (sizes/colors) can share one model.
- `production.productinventory.productid` → `production.product.productid`, with one row per (product, location) pair.

### Common analytical questions
- "What are our best/top-selling products?"
- "How many products do we have per category?"
- "What's our current inventory for X?"
- "What's the price/cost/margin structure of our catalog?"

### Important ambiguities
- `productsubcategoryid` and `productmodelid` are nullable on `production.product` — some products (e.g. raw materials that aren't finished goods) may not roll up into a merchandising category or a model.
- "Best-selling" requires joining out to `sales.salesorderdetail` — this is a sales-domain question answered with product-domain dimensions, not a property stored on the product itself.
- List price (`listprice`) is the catalog price, not necessarily what was actually charged — actual transaction price is `sales.salesorderdetail.unitprice`, which can differ due to discounts or historical price changes.

### Relevant database schemas/tables
`production.product`, `production.productsubcategory`, `production.productcategory`, `production.productmodel`, `production.productinventory`, `production.location`, `production.billofmaterials`

---

## Domain: Customers

### Business purpose
Represents who AdventureWorks sells to. AdventureWorks sells through two channels: direct-to-consumer (individuals) and reseller (stores), each represented differently in the data.

### Important concepts
- **Business Entity** (`person.businessentity`): shared identity root.
- **Person** (`person.person`): individual person records, tagged with a `persontype` code (e.g. `IN` = individual customer, `SP` = salesperson, `EM` = employee).
- **Store** (`sales.store`): a reseller business, linked to a managing salesperson.
- **Customer** (`sales.customer`): the selling relationship — links either a person or a store (via `personid`/`storeid`) to a sales territory.

### How concepts relate
- `sales.customer.personid` → `person.person.businessentityid` for individual customers.
- `sales.customer.storeid` → `sales.store.businessentityid` for store/reseller customers.
- `sales.store.salespersonid` → `sales.salesperson.businessentityid` — each store has an assigned rep.

### Common analytical questions
- "Who are our biggest/top customers?"
- "How many individual vs. store customers do we have?"
- "Which customers are in which territory?"

### Important ambiguities
- A `sales.customer` row is exactly one of "individual" or "store" — never both. Queries that aggregate "customers" without distinguishing type will mix two structurally different kinds of buyer (consumers vs. resellers), which can be misleading for questions like "average revenue per customer."
- Individual customer names live in `person.person`; store names live in `sales.store.name`. There is no single denormalized "customer name" column — the correct join depends on which type of customer the row represents.

### Relevant database schemas/tables
`person.businessentity`, `person.person`, `sales.store`, `sales.customer`, `person.address`, `person.businessentityaddress`

---

## Domain: Purchasing

### Business purpose
Represents AdventureWorks' inbound transactions: buying raw materials and components from external vendors to support manufacturing.

### Important concepts
- **Vendor** (`purchasing.vendor`): an external supplier.
- **Purchase Order** (`purchasing.purchaseorderheader`): one row per procurement order, including the AdventureWorks employee who placed it, the vendor, dates, and monetary totals.
- **Purchase Order Detail** (`purchasing.purchaseorderdetail`): one row per product line within a purchase order.
- **Product-Vendor relationship** (`purchasing.productvendor`): which vendors supply which products, and at what standard price/lead time.

### How concepts relate
- `purchasing.purchaseorderheader.vendorid` → `purchasing.vendor.businessentityid`.
- `purchasing.purchaseorderdetail.purchaseorderid` → `purchasing.purchaseorderheader.purchaseorderid`.
- `purchasing.purchaseorderdetail.productid` → `production.product.productid`.

### Common analytical questions
- "How much do we spend on purchasing?"
- "Who are our vendors, and what do we buy from each?"
- "What are typical lead times/order quantities per vendor?"

### Important ambiguities
- Purchasing is structurally the mirror image of sales (header + detail, subtotal/tax/freight), but is **inbound spend**, not revenue — it should never be summed together with sales figures as if they were the same kind of monetary flow.
- As with sales, per-line and header total-due amounts are not stored as ready-made columns in this Postgres port and must be calculated — see `metric_definitions.md`.

### Relevant database schemas/tables
`purchasing.vendor`, `purchasing.purchaseorderheader`, `purchasing.purchaseorderdetail`, `purchasing.productvendor`, `purchasing.shipmethod`

---

## Domain: Human Resources

### Business purpose
Represents AdventureWorks' workforce: employees, their departments, and their organizational history. This is where salespeople originate as employees before being separately flagged as sales staff.

### Important concepts
- **Employee** (`humanresources.employee`): job title, hire date, salaried status, current employment flag.
- **Department** (`humanresources.department`): organizational unit (e.g. Engineering, Sales, Production).
- **Employee Department History** (`humanresources.employeedepartmenthistory`): time-bound record of which department(s) an employee has belonged to.
- **Shift** (`humanresources.shift`): work shift assignment.

### How concepts relate
- `humanresources.employee.businessentityid` → `person.person.businessentityid` for name/contact details.
- `humanresources.employeedepartmenthistory.businessentityid` → `humanresources.employee.businessentityid`; current department requires filtering to the row with `enddate IS NULL`.
- Salespeople are employees who additionally appear in `sales.salesperson` (same `businessentityid`).

### Common analytical questions
- "How many employees do we have?"
- "Which employees are salespeople?"
- "How are employees distributed across departments?"

### Important ambiguities
- "Employee count" should generally be scoped to `currentflag = true` unless historical headcount is explicitly requested — otherwise former employees are included.
- Department membership is historical, not a static field on the employee row; a naive employee-to-department join without filtering `employeedepartmenthistory` can double-count employees who changed departments.

### Relevant database schemas/tables
`humanresources.employee`, `humanresources.department`, `humanresources.employeedepartmenthistory`, `humanresources.employeepayhistory`, `humanresources.shift`, `person.person`

---

## Domain: Production (Manufacturing)

### Business purpose
Represents how AdventureWorks builds the products it sells: which products are manufactured in-house, what components they require, and the work orders that track production runs.

### Important concepts
- **Work Order** (`production.workorder`): a manufacturing run for a given product and quantity, with a scrapped-quantity field.
- **Bill of Materials** (`production.billofmaterials`): a recursive structure defining which component products (and quantities) make up an assembled product.
- **Scrap Reason** (`production.scrapreason`): why units were scrapped during production.
- **Transaction History** (`production.transactionhistory`): a log of inventory-affecting events, tagged by type — `W` (work order/manufacturing), `S` (sales), `P` (purchasing).

### How concepts relate
- `production.workorder.productid` → `production.product.productid`.
- `production.billofmaterials.productassemblyid` and `componentid` both reference `production.product.productid`, forming a self-referential parts hierarchy.
- `production.transactionhistory.transactiontype` distinguishes production movements from sales and purchasing movements within what is otherwise a shared transaction log.

### Common analytical questions
- "How many units did we manufacture / scrap?"
- "What components go into product X?"
- "What's our production throughput or lead time?"

### Important ambiguities
- Not all products are manufactured — `production.product.makeflag = false` indicates a product is purchased finished rather than built in-house; work orders and BOM data only apply to `makeflag = true` products.
- `production.transactionhistory` is a movement log, not a running balance; current on-hand quantity is read from `production.productinventory`, not derived by summing this history table unless explicitly reconciling movements.

### Relevant database schemas/tables
`production.workorder`, `production.workorderrouting`, `production.billofmaterials`, `production.scrapreason`, `production.transactionhistory`, `production.product`

---

## Cross-Domain Notes

- **Products connect Sales, Purchasing, and Production.** The same `production.product` table is referenced by `sales.salesorderdetail.productid`, `purchasing.purchaseorderdetail.productid`, and `production.workorder.productid` — this is the central join point for any "product performance across the business" question.
- **People connect Sales and HR.** A salesperson is simultaneously a `humanresources.employee` row and a `sales.salesperson` row sharing the same `businessentityid`.
- **Money is never a single global concept.** Sales revenue, purchasing spend, product cost, and product list price are all distinct monetary concepts stored in different places — see `metric_definitions.md` before summing or comparing any dollar figures across domains.
