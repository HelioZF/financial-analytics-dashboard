

@dataclass
class User:
    id: int
    display_name: str
    username: str
    password_hash: str

@dataclass
class Transaction:
    id: int
    user_id: int
    amount: float
    category_id: int
    date: datetime
    description: str

@dataclass
class Category:
    id: int
    name: str
    type: str 
    color: str


@dataclass
class Budget:
    id: int
    user_id: int
    month: int
    year: int
    category_id: int
    amount: float

