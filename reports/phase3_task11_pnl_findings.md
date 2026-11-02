# Phase 3 — Task 11: Profit and Loss Analysis

## Method
- Source: fact_ledger and dim_account.
- Revenue = credit minus debit.
- Expense = debit minus credit.
- Only detail accounts are included. Group/parent accounts are excluded to avoid double counting.
- Expense category and vendor analysis uses fact_expense amount excluding GST.
- Expense bills are analysed separately and are not added again to ledger P&L.

## Official headline reconciliation

| Period | Revenue (INR) | Expenses (INR) | Profit (INR) |
|---|---:|---:|---:|
| FY 2025-26 | 790160535.00 | 655004422.46 | 135156112.54 |
| Apr-Sep 2026 official | 470769517.00 | 381242041.96 | 89527475.04 |

FY 2025-26 revenue, expenses and profit match the README exactly.

Apr-Sep 2026 revenue matches the official reference exactly.
Actual ledger expenses are INR 381260491.96 and actual ledger
profit is INR 89509025.04. The difference from the official
reference is INR 18450.

## June 2026 payroll reconciliation exception

A department-level reconciliation was performed between fact_payroll
and fact_ledger for June 2026.

- Payroll earned fixed pay and account 5001 (Salaries & Wages)
  match in 10 of 11 departments.
- D01 earned fixed pay is INR 19873074.18.
- D01 account 5001 ledger debit is INR 19891524.18.
- The resulting unexplained excess ledger posting is INR 18450.
- Payroll employer cost agrees with reference_summary_dept_month
  for all departments.
- Account 5002 (Overtime Expense) reconciles to payroll overtime.
- Account 5003 (Incentives & Bonus) reconciles to payroll variable pay.

The INR 18450 difference explains the Apr-Sep 2026 P&L expense
variance. Its underlying cause remains unresolved and requires
Finance review. No source data has been adjusted.

## Three business findings

1. Revenue increased 11.1% from March to April 2026, but expenses
   increased 20.7%. Net profit decreased 26.0%, and profit margin
   declined from 20.60% to 13.72%.

2. Incentives and Bonus increased by INR 9467647.06, Salaries and Wages
   increased by INR 3630082.51, and Insurance increased by INR 2120000.
   Incentives were the largest positive expense driver.

3. Professional Fees contains a manual INR 1800000 credit journal
   (MJ-0002) dated 1 April 2026. After an INR 448840 expense debit,
   the category shows negative net expense of INR 1351160.
   Finance should confirm the purpose and supporting evidence for
   this journal.

## Expense analysis
- Expense bills analysed: 501.
- Amount excluding GST: INR 168245930.
- Category and vendor rankings are based on expense bills, not added to ledger P&L.

## Dashboard requirements
- Monthly revenue, expenses, net profit and profit margin.
- Expense category analysis.
- Top 10 vendors by expense excluding GST.
- Month selector.
- Reconciliation note for the June 2026 D01 INR 18450 salary exception.
