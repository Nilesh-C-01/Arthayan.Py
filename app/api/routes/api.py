from fastapi import APIRouter, Request, Form, Depends, status, Response, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, extract
from app.models.database import get_db
from app.models.domain import User, Transaction
import csv
import io
import json
import jwt
from collections import defaultdict
from datetime import datetime, timedelta

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

SECRET_KEY = "arthayan_super_secret_enterprise_key"
ALGORITHM = "HS256"

def get_current_user(request: Request):
    """Dependency to extract and verify the JWT token."""
    token = request.cookies.get("access_token")
    if not token: return None
    try: return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except: return None

@router.on_event("startup")
def seed_data():
    db = next(get_db())
    if not db.query(User).first():
        db.add_all([
            User(username="admin", password="password", role="Admin"),
            User(username="analyst", password="password", role="Analyst"),
            User(username="viewer", password="password", role="Viewer")
        ])
        db.commit()

@router.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    error = request.query_params.get("error")
    msg = request.query_params.get("msg")
    return templates.TemplateResponse(request=request, name="login.html", context={"error": error, "msg": msg})

@router.post("/login")
def login(expected_role: str = Form(...), username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username, User.password == password).first()
    if not user or user.role != expected_role:
        return RedirectResponse(url="/?error=Authentication+Failed+or+Unauthorized+Portal", status_code=status.HTTP_302_FOUND)
    
    expire = datetime.utcnow() + timedelta(hours=24)
    token = jwt.encode({"sub": user.username, "role": user.role, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
    
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=token, httponly=True, secure=True)
    return response

@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    error = request.query_params.get("error")
    return templates.TemplateResponse(request=request, name="signup.html", context={"error": error})

@router.post("/signup")
def register_user(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        if existing_user.password == password:
            return RedirectResponse(url="/?msg=Account+already+exists.+Please+Log+In.", status_code=status.HTTP_302_FOUND)
        else:
            return RedirectResponse(url="/signup?error=Username+already+taken.", status_code=status.HTTP_302_FOUND)
    
    db.add(User(username=username, password=password, role="Viewer"))
    db.commit()
    return RedirectResponse(url="/?msg=Registration+Successful!+Please+Log+In.", status_code=status.HTTP_302_FOUND)

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response

# --- NEW: SECURE PASSWORD CHANGE ENDPOINT ---
@router.post("/change_password")
def change_password(
    request: Request, current_password: str = Form(...), new_password: str = Form(...), db: Session = Depends(get_db)
):
    user_data = get_current_user(request)
    if not user_data: 
        return Response(json.dumps({"success": False, "msg": "Unauthorized"}), status_code=401)
    
    user = db.query(User).filter(User.username == user_data.get("sub")).first()
    if not user or user.password != current_password:
        return Response(json.dumps({"success": False, "msg": "Incorrect current password"}), status_code=400)
    
    user.password = new_password
    db.commit()
    return Response(json.dumps({"success": True, "msg": "Password updated successfully"}), status_code=200)

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request, db: Session = Depends(get_db),
    search: str = Query(None), filter_type: str = Query(None), filter_category: str = Query(None), filter_date: str = Query(None)
):
    user_data = get_current_user(request)
    if not user_data: return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

    role = user_data.get("role")
    username = user_data.get("sub")
    
    query = db.query(Transaction)
    if role == "Viewer": query = query.filter(Transaction.owner == username)
    all_viewers = [u.username for u in db.query(User).filter(User.role == "Viewer").all()] if role == "Admin" else []

    if search: query = query.filter(or_(Transaction.description.ilike(f"%{search}%"), Transaction.category.ilike(f"%{search}%")))
    if filter_type: query = query.filter(Transaction.type == filter_type)
    if filter_category: query = query.filter(Transaction.category.ilike(f"%{filter_category}%"))
    if filter_date: 
        try:
            target_year, target_month = map(int, filter_date.split('-'))
            query = query.filter(extract('year', Transaction.date) == target_year, extract('month', Transaction.date) == target_month)
        except Exception: pass

    transactions = query.order_by(Transaction.date.desc()).all()
    
    total_income = sum(t.amount for t in transactions if t.type == "Income")
    total_expense = sum(t.amount for t in transactions if t.type == "Expense")
    balance = total_income - total_expense

    expense_categories = defaultdict(float); income_categories = defaultdict(float)
    timeline = defaultdict(float); monthly_totals = defaultdict(float)

    now = datetime.utcnow()
    last_month = now.month - 1 if now.month > 1 else 12
    last_month_year = now.year if now.month > 1 else now.year - 1
    
    curr_mo_exp = sum(t.amount for t in transactions if t.type == "Expense" and t.date.month == now.month and t.date.year == now.year)
    last_mo_exp = sum(t.amount for t in transactions if t.type == "Expense" and t.date.month == last_month and t.date.year == last_month_year)
    mom_variance = ((curr_mo_exp - last_mo_exp) / last_mo_exp * 100) if last_mo_exp > 0 else 0

    user_expenses = defaultdict(float); user_incomes = defaultdict(float)
    day_sums = defaultdict(float)
    cat_counts = defaultdict(int); cat_sums = defaultdict(float)
    total_exp_count = 0; total_exp_sum = 0

    for t in transactions:
        date_str = t.date.strftime('%Y-%m-%d'); month_str = t.date.strftime('%b %Y')
        if t.type == "Expense":
            expense_categories[t.category] += t.amount; timeline[date_str] -= t.amount; monthly_totals[month_str] -= t.amount
            user_expenses[t.owner] += t.amount; day_sums[t.date.weekday()] += t.amount; cat_counts[t.category] += 1
            cat_sums[t.category] += t.amount; total_exp_count += 1; total_exp_sum += t.amount
        else:
            income_categories[t.category] += t.amount; timeline[date_str] += t.amount; monthly_totals[month_str] += t.amount
            user_incomes[t.owner] += t.amount

    top_spenders = [{"user": k, "amount": v} for k, v in sorted(user_expenses.items(), key=lambda x: x[1], reverse=True)[:5]]
    top_earners = [{"user": k, "amount": v} for k, v in sorted(user_incomes.items(), key=lambda x: x[1], reverse=True)[:5]]
    atv_list = [{"category": k, "atv": cat_sums[k]/cat_counts[k]} for k in cat_sums]
    sorted_atv = sorted(atv_list, key=lambda x: x["atv"], reverse=True)[:5]
    day_heatmap = [day_sums.get(i, 0) for i in range(7)]

    global_avg = total_exp_sum / total_exp_count if total_exp_count > 0 else 0
    anomaly_threshold = global_avg * 3 if global_avg > 0 else float('inf')
    anomalies = [t for t in transactions if t.type == "Expense" and t.amount > anomaly_threshold]

    sorted_timeline = sorted(timeline.items())

    return templates.TemplateResponse(request=request, name="dashboard.html", context={
        "role": role, "username": username, "transactions": transactions, "all_viewers": all_viewers,
        "total_income": total_income, "total_expense": total_expense, "balance": balance,
        "mom_variance": mom_variance, "abs_mom_variance": abs(mom_variance),
        "curr_mo_exp": curr_mo_exp, "last_mo_exp": last_mo_exp,
        "top_spenders": top_spenders, "top_earners": top_earners,
        "sorted_atv": sorted_atv, "day_heatmap": json.dumps(day_heatmap),
        "anomalies": anomalies, "global_avg": global_avg, "anomaly_threshold": anomaly_threshold,
        "chart_labels": json.dumps(list(expense_categories.keys())), "chart_data": json.dumps(list(expense_categories.values())),
        "expense_cat_labels": json.dumps(list(expense_categories.keys())), "expense_cat_data": json.dumps(list(expense_categories.values())),
        "income_cat_labels": json.dumps(list(income_categories.keys())), "income_cat_data": json.dumps(list(income_categories.values())),
        "timeline_labels": json.dumps([item[0] for item in sorted_timeline]), "timeline_data": json.dumps([item[1] for item in sorted_timeline]),
        "monthly_labels": json.dumps(list(monthly_totals.keys())), "monthly_data": json.dumps(list(monthly_totals.values())),
        "search": search or "", "filter_type": filter_type or "", "filter_category": filter_category or "", "filter_date": filter_date or ""
    })

@router.post("/transaction")
def create_transaction(request: Request, amount: float = Form(...), type: str = Form(...), category: str = Form(...), description: str = Form(""), date: str = Form(None), db: Session = Depends(get_db)):
    user_data = get_current_user(request)
    if not user_data or user_data.get("role") == "Analyst": return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    tx_date = datetime.strptime(date, '%Y-%m-%d') if date else datetime.utcnow()
    db.add(Transaction(amount=amount, type=type, category=category, description=description, date=tx_date, owner=user_data.get("sub")))
    db.commit(); return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

@router.post("/transaction/update/{tx_id}")
def update_transaction(request: Request, tx_id: int, amount: float = Form(...), type: str = Form(...), category: str = Form(...), description: str = Form(""), date: str = Form(None), db: Session = Depends(get_db)):
    user_data = get_current_user(request)
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if tx and (user_data.get("role") == "Admin" or tx.owner == user_data.get("sub")):
        tx.amount = amount; tx.type = type; tx.category = category; tx.description = description
        if date: tx.date = datetime.strptime(date, '%Y-%m-%d')
        db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

@router.post("/transaction/delete/{tx_id}")
def delete_transaction(request: Request, tx_id: int, db: Session = Depends(get_db)):
    user_data = get_current_user(request)
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if tx and (user_data.get("role") == "Admin" or tx.owner == user_data.get("sub")):
        db.delete(tx); db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

@router.post("/admin/purge_user")
def purge_user_data(request: Request, target_user: str = Form(...), db: Session = Depends(get_db)):
    user_data = get_current_user(request)
    if user_data and user_data.get("role") == "Admin":
        db.query(Transaction).filter(Transaction.owner == target_user).delete(); db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

@router.get("/export_csv")
def export_csv(request: Request, db: Session = Depends(get_db)):
    user_data = get_current_user(request)
    if not user_data or user_data.get("role") not in ["Admin", "Analyst"]: return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    transactions = db.query(Transaction).order_by(Transaction.date.desc()).all()
    output = io.StringIO(); writer = csv.writer(output)
    writer.writerow(["ID", "Owner", "Amount", "Type", "Category", "Date", "Description"])
    for t in transactions: writer.writerow([t.id, t.owner, t.amount, t.type, t.category, t.date.strftime("%Y-%m-%d %H:%M"), t.description])
    return Response(content=output.getvalue(), media_type="text/csv", headers={'Content-Disposition': 'attachment; filename="arthayan_transactions.csv"'})