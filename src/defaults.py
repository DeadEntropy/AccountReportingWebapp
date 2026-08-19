from datetime import datetime

# Salary
DEFAULT_PAYROLLS_1 = ["NAYA BIOSCIENCES PAYROLL", "CYTOVIA THERAPEUTICS", "NAYA ONCOLOGY", "TRINET HR CORPORATE PAYROLL"]
BASE_PAYROLL_1 = "NAYA_CYTOVIA"
DEFAULT_PAYROLLS_2 = ["UBS SALARY", "UBS BONUS"]
BASE_PAYROLL_2 = "UBS"
EXCLUDE_DEFAULT = []
BASE_SALARY_1 = 13250
USE_LEGACY_SALARY_CLASS = False

SALARY_CONFIG = {
    "NAYA_CYTOVIA": {
        "base_salary": None,
        "payrolls": [
            "NAYA BIOSCIENCES PAYROLL",
            "CYTOVIA THERAPEUTICS",
            "NAYA ONCOLOGY",
            "TRINET HR CORPORATE PAYROLL",
        ],
    },
    "MEDICUS_PHARMA": {
        "base_salary": None,
        "payrolls": ["MEDICUS PHARMA"],
    },
    "UBS": {
        "base_salary": None,
        "payrolls": ["UBS SALARY", "UBS BONUS"],
    },
}

# Year Dropdown. The upper bound follows the clock: app.py defaults the dropdown to the current
# year, and a hardcoded end would leave that default outside the options once the year rolled over.
YEARS = range(2016, datetime.today().year + 1)

# Category Dropdown
DEFAULT_CATEGORY = "SubType: Grocery"
CATEGORY_MAP = {"MasterType": "FullType", "Type": "FullSubType", "SubType": "MemoMapped"}
THRESHOLD = 1000

# Reporting Currency
REF_CURRENCY = "USD"

# Income Types
INCOME_TYPES = ['Capital Earnings', 'Capital Gain', 'Salary' ,'Exceptional Income' , 'Tax']
