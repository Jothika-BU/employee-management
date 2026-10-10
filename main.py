
import os
import mysql.connector
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field

load_dotenv()

app = FastAPI()

class EmployeeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    department: str = Field(min_length=1, max_length=50)
    salary: float = Field(gt=0)


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


@app.get("/")
def home():
    return {"message": "Employee API is running"}


@app.get("/test-db")
def test_database():
    connection = None

    try:
        connection = get_connection()
        return {"message": "MySQL connected successfully"}

    except mysql.connector.Error:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed. Check configuration."
        )

    finally:
        if connection and connection.is_connected():
            connection.close()

@app.get("/employees")
def get_employees():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, name, email, department, salary FROM employees"
        )
        employees = cursor.fetchall()

        return {"employees": employees}

    except mysql.connector.Error:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve employee records."
        )

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.post("/employees", status_code=201)
def create_employee(employee: EmployeeCreate):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO employees (name, email, department, salary)
            VALUES (%s, %s, %s, %s)
        """

        values = (
            employee.name,
            employee.email,
            employee.department,
            employee.salary
        )

        cursor.execute(query, values)
        connection.commit()

        return {
            "message": "Employee created successfully",
            "id": cursor.lastrowid,
            "name": employee.name,
            "email": employee.email,
            "department": employee.department,
            "salary": employee.salary
        }

    except mysql.connector.IntegrityError:
        if connection and connection.is_connected():
            connection.rollback()

        raise HTTPException(
            status_code=409,
            detail="An employee with this email may already exist."
        )

    except mysql.connector.Error:
        if connection and connection.is_connected():
            connection.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to save employee record."
        )

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()