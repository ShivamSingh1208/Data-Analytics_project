CREATE TABLE IF NOT EXISTS dw.phase2_payroll_reference (
    month DATE PRIMARY KEY,
    employees_paid INTEGER,
    payroll_gross_pay NUMERIC(18,2),
    payroll_net_pay NUMERIC(18,2),
    payroll_employer_cost NUMERIC(18,2),
    ledger_salary_related_expense NUMERIC(18,2),
    ledger_revenue NUMERIC(18,2),
    ledger_total_expense NUMERIC(18,2),
    ledger_net_profit NUMERIC(18,2),
    bank_closing_balance NUMERIC(18,2),
    receivables_closing_balance NUMERIC(18,2),
    payroll_vs_ledger_difference NUMERIC(18,2)
);
