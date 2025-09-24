"""
Demo data for testing Q&A generation without database connection.
"""

DEMO_TABLES = {
    "Employees": [
        {"column_name": "EmployeeID", "data_type": "int", "is_nullable": False},
        {"column_name": "FirstName", "data_type": "varchar", "is_nullable": False},
        {"column_name": "LastName", "data_type": "varchar", "is_nullable": False},
        {"column_name": "DepartmentID", "data_type": "int", "is_nullable": True},
        {"column_name": "Salary", "data_type": "decimal", "is_nullable": True},
        {"column_name": "HireDate", "data_type": "datetime", "is_nullable": False},
    ],
    "Departments": [
        {"column_name": "DepartmentID", "data_type": "int", "is_nullable": False},
        {"column_name": "DepartmentName", "data_type": "varchar", "is_nullable": False},
        {"column_name": "ManagerID", "data_type": "int", "is_nullable": True},
        {"column_name": "Budget", "data_type": "decimal", "is_nullable": True},
    ],
    "Projects": [
        {"column_name": "ProjectID", "data_type": "int", "is_nullable": False},
        {"column_name": "ProjectName", "data_type": "varchar", "is_nullable": False},
        {"column_name": "DepartmentID", "data_type": "int", "is_nullable": False},
        {"column_name": "StartDate", "data_type": "datetime", "is_nullable": False},
        {"column_name": "EndDate", "data_type": "datetime", "is_nullable": True},
        {"column_name": "Budget", "data_type": "decimal", "is_nullable": True},
    ]
}

DEMO_RELATIONSHIPS = [
    {
        "fk_name": "FK_Employee_Department",
        "parent_table": "Employees",
        "parent_column": "DepartmentID",
        "referenced_table": "Departments",
        "referenced_column": "DepartmentID"
    },
    {
        "fk_name": "FK_Department_Manager",
        "parent_table": "Departments", 
        "parent_column": "ManagerID",
        "referenced_table": "Employees",
        "referenced_column": "EmployeeID"
    },
    {
        "fk_name": "FK_Project_Department",
        "parent_table": "Projects",
        "parent_column": "DepartmentID", 
        "referenced_table": "Departments",
        "referenced_column": "DepartmentID"
    }
]

DEMO_SAMPLE_DATA = {
    "Employees": [
        {"EmployeeID": 1, "FirstName": "John", "LastName": "Smith", "DepartmentID": 1, "Salary": 75000, "HireDate": "2020-01-15"},
        {"EmployeeID": 2, "FirstName": "Sarah", "LastName": "Johnson", "DepartmentID": 2, "Salary": 82000, "HireDate": "2019-03-22"},
        {"EmployeeID": 3, "FirstName": "Mike", "LastName": "Davis", "DepartmentID": 1, "Salary": 68000, "HireDate": "2021-06-10"},
    ],
    "Departments": [
        {"DepartmentID": 1, "DepartmentName": "Engineering", "ManagerID": 1, "Budget": 500000},
        {"DepartmentID": 2, "DepartmentName": "Marketing", "ManagerID": 2, "Budget": 300000},
        {"DepartmentID": 3, "DepartmentName": "Sales", "ManagerID": None, "Budget": 400000},
    ],
    "Projects": [
        {"ProjectID": 1, "ProjectName": "Website Redesign", "DepartmentID": 1, "StartDate": "2024-01-01", "EndDate": "2024-06-30", "Budget": 150000},
        {"ProjectID": 2, "ProjectName": "Marketing Campaign", "DepartmentID": 2, "StartDate": "2024-02-15", "EndDate": None, "Budget": 80000},
        {"ProjectID": 3, "ProjectName": "Product Launch", "DepartmentID": 1, "StartDate": "2024-03-01", "EndDate": "2024-12-31", "Budget": 200000},
    ]
}
