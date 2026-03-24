from dataclasses import dataclass, field
import uuid


@dataclass
class User:
    id: str
    auth0_id: str
    email: str
    username: str
    created_at: str
    is_admin: int = 0
    is_active: int = 1
    mfa_enabled: int = 0
    password_hash: str = ""
    totp_secret: str = ""


@dataclass
class BudgetRecord:
    id: str
    name: str
    is_shared: int  # 0 = personal, 1 = shared
    created_at: str


@dataclass
class Account:
    id: str
    name: str
    account_type: str
    institution: str
    balance: float
    budget_id: str = ""


@dataclass
class Transaction:
    date: str
    payee: str
    amount: float
    memo: str
    category_id: str
    account_id: str = ""
    plaid_transaction_id: str = ""
    budget_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Category:
    name: str
    budgeted: float
    activity: float
    available: float
    target_amount: float = 0.0
    target_type: str = ""
    target_date: str = ""
    budget_id: str = ""
    group_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Payee:
    id: str
    name: str
    budget_id: str = ""


@dataclass
class CategoryGroup:
    id: str
    name: str
    position: int = 0
    budget_id: str = ""


@dataclass
class RecurringTransaction:
    id: str
    payee: str
    amount: float
    memo: str
    category_id: str
    account_id: str
    frequency: str       # 'weekly', 'biweekly', 'monthly', 'yearly'
    next_date: str       # YYYY-MM-DD
    budget_id: str = ""
    is_active: int = 1


@dataclass
class Rule:
    id: str
    rule_type: str       # 'payee' or 'amount'
    match_field: str     # 'payee_name' or 'amount'
    match_type: str      # 'exact', 'contains', 'starts_with', 'greater_than', 'less_than', 'between'
    match_value: str
    action_type: str     # 'set_category', 'set_memo', 'set_account', 'flag'
    action_value: str
    budget_id: str = ""
    created_at: str = ""
