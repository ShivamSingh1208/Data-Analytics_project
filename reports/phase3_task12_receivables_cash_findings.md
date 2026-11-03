# Phase 3 — Task 12: Receivables and Cash Movement

## Receivables ageing
At the reporting cutoff, the ageing mart contains 62 issued open invoices
with a balance of INR 139394278.00. The mart reconciles exactly to issued
open invoices in fact_invoice.

Ageing buckets:
- Not yet due: 49 invoices, INR 112283412.
- 1–30 days: 10 invoices, INR 22133626.
- 61–90 days: 1 invoice, INR 1940982.
- 90+ days: 2 invoices, INR 3036258.

One additional invoice, INV/2026-27/0217, is DRAFT with a balance of
INR 1028724. It is correctly excluded from issued open receivables.

## Cash movement
The monthly cash movement view covers April 2025 to September 2026.
Cash inflows are sourced from invoice payments; cash outflows are sourced
from paid expenses. Both cash-in and cash-out reconcile exactly to their
source records in all 18 months.

Across the period:
- Cash in: INR 1419349558.00.
- Cash out: INR 185831316.70.
- Net cash movement: INR 1233518241.30.

Cash movement is a receipts-and-paid-expenses view, not a substitute
for accrual-basis profit and loss.

## Dashboard
Dashboard: Receivables & Cash Dashboard.
Charts: open receivables by ageing bucket, monthly cash in/out/net
movement, and client average days to pay.
