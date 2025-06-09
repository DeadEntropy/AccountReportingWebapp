# Salary
DEFAULT_PAYROLLS_1 = ["NAYA BIOSCIENCES PAYROLL", "CYTOVIA THERAPEUTICS", "NAYA ONCOLOGY", "TRINET HR CORPORATE PAYROLL"]
BASE_PAYROLL_1 = "NAYA_CYTOVIA"
DEFAULT_PAYROLLS_2 = ["UBS SALARY", "UBS BONUS"]
BASE_PAYROLL_2 = "UBS"
EXCLUDE_DEFAULT = []
BASE_SALARY_1 = 13250
USE_LEGACY_SALARY_CLASS = True

SALARY_CONFIG = {
    "NAYA_CYTOVIA": {
        "base_salary": 13250,
        "payrolls": [
            "NAYA BIOSCIENCES PAYROLL",
            "CYTOVIA THERAPEUTICS",
            "NAYA ONCOLOGY",
            "TRINET HR CORPORATE PAYROLL",
        ],
    },
    "UBS": {
        "base_salary": None,
        "payrolls": ["UBS SALARY", "UBS BONUS"],
    },
}

# Year DrowDropdowndown
YEARS = range(2016, 2026)

# Category Dropdown
DEFAULT_CATEGORY = "SubType: Grocery"
CATEGORY_MAP = {"MasterType": "FullType", "Type": "FullSubType", "SubType": "MemoMapped"}
THRESHOLD = 1000

# Reporting Currency
REF_CURRENCY = "USD"
