from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# --------------------
# User table
# --------------------
class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    conversations = db.relationship("Conversation", backref="user", lazy=True)

    def to_dict(self):
        return {"id": self.id, "username": self.username}


# --------------------
# Conversation table
# --------------------
class Conversation(db.Model):
    __tablename__ = "conversation"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship("Message", backref="conversation", lazy=True)


# --------------------
# Message table
# --------------------
class Message(db.Model):
    __tablename__ = "message"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversation.id"))
    sender = db.Column(db.String(50))
    text = db.Column(db.Text)
    meta = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# --------------------
# Employees table
# --------------------
class Employee(db.Model):
    __tablename__ = "employees"

    employee_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    hire_date = db.Column(db.Date, nullable=False)
    job_title = db.Column(db.String(100))
    department = db.Column(db.String(100))
    salary = db.Column(db.Numeric(10, 2))
    manager_id = db.Column(db.Integer, db.ForeignKey("employees.employee_id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    manager = db.relationship("Employee", remote_side=[employee_id], backref="subordinates")
    addresses = db.relationship("EmployeeAddress", backref="employee", cascade="all, delete-orphan")
    projects = db.relationship("EmployeeProject", backref="employee", cascade="all, delete-orphan")


# --------------------
# Employee Addresses
# --------------------
class EmployeeAddress(db.Model):
    __tablename__ = "employee_addresses"

    address_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.employee_id"), nullable=False)
    address_type = db.Column(db.Enum("Home", "Office", "Other"), default="Home")
    street = db.Column(db.String(150))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100))


# --------------------
# Employee Projects
# --------------------
class EmployeeProject(db.Model):
    __tablename__ = "employee_projects"

    project_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.employee_id"), nullable=False)
    project_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
