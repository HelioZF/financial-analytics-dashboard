
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