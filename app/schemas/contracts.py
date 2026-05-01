from datetime import date
from typing import List
from dataclasses import dataclass

# Overview page contracts

# Data (month)
# - Total Income
# - Total Expenses
# - Balance

# Data (over time)
# - Total Income 
# - Total Expenses
# - Top Income (5)
# - Top Expenses (5)

@dataclass
class MonthlyTotal:
    month_reference: int
    year_reference: int
    amount: float
    type: str

@dataclass
class OverviewKPIs:
    month_reference: int
    year_reference: int
    total_income: float
    total_expenses: float
    total_balance: float

@dataclass
class CategoryBreakdown:
    name: str
    color: str
    type: str
    total_amount: float
    percentage: float
    

@dataclass
class OverviewPageData:
    kpis: OverviewKPIs
    monthly_data: List[MonthlyTotal]
    income_breakdown: List[CategoryBreakdown]
    expense_breakdown: List[CategoryBreakdown]


# Expenses page contracts

@dataclass
class ExpenseItem:
    transaction_date: date
    description: str
    category_name: str
    category_color: str
    amount: float


@dataclass
class ExpensesPageData:
    year_reference: int
    monthly_totals: List[MonthlyTotal]
    category_breakdown: List[CategoryBreakdown]
    top_items: List[ExpenseItem]


# Income page contracts

@dataclass
class IncomeItem:
    transaction_date: date
    description: str
    category_name: str
    category_color: str
    amount: float


@dataclass
class IncomePageData:
    year_reference: int
    monthly_totals: List[MonthlyTotal]
    category_breakdown: List[CategoryBreakdown]
    top_items: List[IncomeItem]


# Budget page contracts

@dataclass
class BudgetRow:
    category_name: str
    category_color: str
    budgeted: float
    spent: float
    percent_used: float
    status: str  # "under" | "over"


@dataclass
class BudgetPageData:
    month_reference: int
    year_reference: int
    rows: List[BudgetRow]
    total_budgeted: float
    total_spent: float