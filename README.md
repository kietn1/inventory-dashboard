# Inventory Operations Dashboard | SAMSUNG SDS AMERICA

**Python · Streamlit · pandas · NumPy**

A dashboard that turns warehouse Excel reports into inventory risk alerts, stock coverage estimates, and order-level availability checks.

> **Add Screenshot 1 — Overview:** Show the warehouse selector, inventory risk KPIs, and a few Critical/Warning SKUs.

## Project Background

I built this dashboard while supporting Samsung SDS logistics operations to address shortages that were often reported too close to delivery dates.

Used daily since late May 2026, the application supports three warehouse formats—Newark, Carson, and Orlando—and helps teams identify inventory risks earlier and plan replenishment.

**This portfolio version uses simulated data. Each warehouse is analyzed separately.**

## Key Features

* **Inventory Risk Monitoring:** Prioritizes SKUs as Critical, Warning, Watch, or Healthy.
* **Stock Coverage Estimates:** Uses recent outbound activity to estimate how long inventory may last.
* **Order Validation:** Checks upcoming orders against stock, accounting for quantities already recorded to avoid double-counting.
* **Transaction Lookup and Audits:** Helps investigate inventory movements and reconcile report balances.
* **Excel Exports:** Provides reports for follow-up and team communication.

> **Add Screenshot 2 — SKU Detail:** Show one at-risk SKU with its ending balance, days remaining, forecast stockout date, and transaction history.

## How It Works

1. Upload the matching warehouse Excel report.
2. The application standardizes the data and checks source totals and balances.
3. It estimates inventory coverage using **Ending Balance ÷ Average Daily Usage**.
4. Users review risk alerts and enter upcoming orders to check for shortages.

The usage calculation uses up to 30 report activity dates rather than a fixed 30-calendar-day period. Stockout dates are estimates based on recent usage.

## How to Use the Sample Files

1. Select the warehouse matching the simulated Excel file.
2. Upload the file without changing its headers or layout.
3. Review **Overview**, then select a product in **SKU Detail**.
4. Open **Stock Check**, paste **DO #, SKU, and Qty**, and click **Run Stock Check**.
5. Review shortages and download the results as needed.

Stock Check deducts demand in the order entered, so multiple orders for the same SKU share a temporary remaining balance.

> **Add Screenshot 3 — Stock Check:** Show example orders with both “Enough” and “Shortage” results, including requested quantities and remaining stock.

## Operational Impact

In daily use, the dashboard helped identify potential shortages approximately **1–2 weeks ahead**, allowing earlier replenishment and reducing reliance on last-minute warehouse alerts.

This lead time reflects operational experience, not a guaranteed forecasting result or a finding from the simulated dataset.

## Current Limitations

* Data refreshes through uploaded reports, not a live WMS connection.
* Future inbound shipments and ETAs are not included in stock checks.
* Forecasts depend on source-data quality and recent demand patterns.
