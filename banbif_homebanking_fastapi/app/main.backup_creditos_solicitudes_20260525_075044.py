from datetime import datetime

import hashlib

import os



from fastapi import FastAPI, Request, Form

from fastapi.responses import RedirectResponse

from fastapi.staticfiles import StaticFiles

from fastapi.templating import Jinja2Templates

from itsdangerous import TimestampSigner, BadSignature, SignatureExpired

from sqlmodel import Session, select



from app.config import settings

from app.db import engine, create_db_and_tables

from app.models import User, Account, Movement, CreditApplication



app = FastAPI(title=settings.app_name, debug=True)



app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

signer = TimestampSigner(settings.secret_key)





def hash_password(password: str) -> str:

    salt = os.urandom(16)

    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)

    return salt.hex() + ":" + key.hex()





def verify_password(password: str, stored: str) -> bool:

    try:

        salt_hex, key_hex = stored.split(":")

        salt = bytes.fromhex(salt_hex)

        new_key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)

        return new_key.hex() == key_hex

    except Exception:

        return False





def make_cookie(user_id: int) -> str:

    return signer.sign(str(user_id)).decode()





def get_user_from_cookie(request: Request, session: Session):

    token = request.cookies.get("banbif_session")

    if not token:

        return None

    try:

        user_id = int(signer.unsign(token, max_age=60 * 60 * 8).decode())

        return session.get(User, user_id)

    except (BadSignature, SignatureExpired, ValueError):

        return None





def new_account_number(document: str) -> str:

    return "BBF-" + document[-4:] + "-" + str(int(datetime.utcnow().timestamp()))[-6:]





def seed_data():

    with Session(engine) as session:

        user = session.exec(select(User).where(User.document == "60829685")).first()

        if user:

            return



        user = User(

            document="60829685",

            full_name="JUAN DIEGO RAMIREZ QUILLATUPA",

            email="juandiego@banbifdemo.pe",

            password_hash=hash_password("123456"),

            phone="999888777",

            address="Huancayo, Peru"

        )

        session.add(user)

        session.commit()

        session.refresh(user)



        account = Account(

            user_id=user.id,

            account_number="BBF-9685-001",

            account_type="Cuenta Ahorro Digital BanBif",

            currency="PEN",

            balance=3500.00,

            status="activa"

        )

        session.add(account)

        session.commit()

        session.refresh(account)



        session.add(Movement(

            account_id=account.id,

            description="Apertura de cuenta BanBif",

            operation_type="deposito",

            amount=3500.00

        ))



        session.add(CreditApplication(

            user_id=user.id,

            product="Prestamo Personal BanBif",

            amount=8000.00,

            months=12,

            monthly_income=2500.00,

            purpose="Estudios y gastos personales",

            status="en evaluacion",

            analyst_comment="Solicitud en revision por el area de creditos."

        ))



        session.commit()





@app.on_event("startup")

def on_startup():

    create_db_and_tables()

    seed_data()





@app.get("/")

def home():

    return RedirectResponse("/login", status_code=303)





@app.get("/login")

def login_page(request: Request):

    return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "error": None})





@app.post("/login")

def login(request: Request, document: str = Form(...), password: str = Form(...)):

    with Session(engine) as session:

        user = session.exec(select(User).where(User.document == document)).first()



        if not user or not verify_password(password, user.password_hash):

            return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "error": "Documento o contraseña incorrectos."}

            )



        response = RedirectResponse("/dashboard", status_code=303)

        response.set_cookie("banbif_session", make_cookie(user.id), httponly=True, samesite="lax")

        return response





@app.get("/registro")

def register_page(request: Request):

    return templates.TemplateResponse(request=request, name="registro.html", context={"request": request, "error": None})





@app.post("/registro")

def register(

    request: Request,

    document: str = Form(...),

    full_name: str = Form(...),

    email: str = Form(...),

    password: str = Form(...)

):

    with Session(engine) as session:

        exists = session.exec(select(User).where((User.document == document) | (User.email == email))).first()

        if exists:

            return templates.TemplateResponse(request=request, name="registro.html", context={"request": request, "error": "Ya existe un usuario con ese documento o correo."}

            )



        user = User(

            document=document,

            full_name=full_name.upper(),

            email=email,

            password_hash=hash_password(password)

        )

        session.add(user)

        session.commit()

        session.refresh(user)



        account = Account(

            user_id=user.id,

            account_number=new_account_number(document),

            account_type="Cuenta Ahorro Digital BanBif",

            currency="PEN",

            balance=0.00,

            status="activa"

        )

        session.add(account)

        session.commit()



        response = RedirectResponse("/dashboard", status_code=303)

        response.set_cookie("banbif_session", make_cookie(user.id), httponly=True, samesite="lax")

        return response





@app.get("/logout")

def logout():

    response = RedirectResponse("/login", status_code=303)

    response.delete_cookie("banbif_session")

    return response





@app.get("/dashboard")

def dashboard(request: Request):

    with Session(engine) as session:

        user = get_user_from_cookie(request, session)

        if not user:

            return RedirectResponse("/login", status_code=303)



        accounts = session.exec(select(Account).where(Account.user_id == user.id)).all()

        credits = session.exec(select(CreditApplication).where(CreditApplication.user_id == user.id)).all()



        movements = []

        for account in accounts:

            account_movements = session.exec(

                select(Movement).where(Movement.account_id == account.id)

            ).all()

            movements.extend(account_movements)



        movements = sorted(movements, key=lambda x: x.created_at, reverse=True)[:5]

        total_balance = sum(account.balance for account in accounts)



        return templates.TemplateResponse(request=request, name="dashboard.html", context={

                "request": request,

                "user": user,

                "accounts": accounts,

                "credits": credits,

                "movements": movements,

                "total_balance": total_balance

            }

        )





@app.get("/ahorros")

def savings(request: Request):

    with Session(engine) as session:

        user = get_user_from_cookie(request, session)

        if not user:

            return RedirectResponse("/login", status_code=303)



        accounts = session.exec(select(Account).where(Account.user_id == user.id)).all()

        movements = []



        for account in accounts:

            movements.extend(session.exec(select(Movement).where(Movement.account_id == account.id)).all())



        movements = sorted(movements, key=lambda x: x.created_at, reverse=True)



        return templates.TemplateResponse(request=request, name="ahorros.html", context={"request": request, "user": user, "accounts": accounts, "movements": movements, "msg": None}

        )





@app.post("/ahorros/deposito")

def deposit(request: Request, account_id: int = Form(...), amount: float = Form(...)):

    with Session(engine) as session:

        user = get_user_from_cookie(request, session)

        if not user:

            return RedirectResponse("/login", status_code=303)



        account = session.get(Account, account_id)

        if not account or account.user_id != user.id or amount <= 0:

            return RedirectResponse("/ahorros", status_code=303)



        account.balance += amount

        session.add(account)

        session.add(Movement(

            account_id=account.id,

            description="Deposito realizado desde Home Banking",

            operation_type="deposito",

            amount=amount

        ))

        session.commit()



        return RedirectResponse("/ahorros", status_code=303)





@app.get("/transferencias")

def transfers_page(request: Request):

    with Session(engine) as session:

        user = get_user_from_cookie(request, session)

        if not user:

            return RedirectResponse("/login", status_code=303)



        accounts = session.exec(select(Account).where(Account.user_id == user.id)).all()

        return templates.TemplateResponse(request=request, name="transferencias.html", context={"request": request, "user": user, "accounts": accounts, "error": None, "success": None}

        )





@app.post("/transferencias")

def make_transfer(

    request: Request,

    origin_account_id: int = Form(...),

    destination_account_number: str = Form(...),

    amount: float = Form(...),

    description: str = Form(...)

):

    with Session(engine) as session:

        user = get_user_from_cookie(request, session)

        if not user:

            return RedirectResponse("/login", status_code=303)



        accounts = session.exec(select(Account).where(Account.user_id == user.id)).all()

        origin = session.get(Account, origin_account_id)

        destination = session.exec(

            select(Account).where(Account.account_number == destination_account_number)

        ).first()



        if not origin or origin.user_id != user.id:

            return templates.TemplateResponse(request=request, name="transferencias.html", context={"request": request, "user": user, "accounts": accounts, "error": "Cuenta origen invalida.", "success": None}

            )



        if not destination:

            return templates.TemplateResponse(request=request, name="transferencias.html", context={"request": request, "user": user, "accounts": accounts, "error": "La cuenta destino no existe.", "success": None}

            )



        if amount <= 0 or origin.balance < amount:

            return templates.TemplateResponse(request=request, name="transferencias.html", context={"request": request, "user": user, "accounts": accounts, "error": "Monto invalido o saldo insuficiente.", "success": None}

            )



        origin.balance -= amount

        destination.balance += amount



        session.add(origin)

        session.add(destination)

        session.add(Movement(

            account_id=origin.id,

            description="Transferencia enviada: " + description,

            operation_type="transferencia_salida",

            amount=-amount

        ))

        session.add(Movement(

            account_id=destination.id,

            description="Transferencia recibida: " + description,

            operation_type="transferencia_entrada",

            amount=amount

        ))

        session.commit()



        return templates.TemplateResponse(request=request, name="transferencias.html", context={"request": request, "user": user, "accounts": accounts, "error": None, "success": "Transferencia realizada correctamente."}

        )





@app.get("/creditos")

def credits_page(request: Request, amount: float = 5000, months: int = 12, rate: float = 18):

    with Session(engine) as session:

        user = get_user_from_cookie(request, session)

        if not user:

            return RedirectResponse("/login", status_code=303)



        credits = session.exec(select(CreditApplication).where(CreditApplication.user_id == user.id)).all()



        monthly_rate = rate / 100 / 12

        if monthly_rate > 0:

            payment = amount * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)

        else:

            payment = amount / months



        return templates.TemplateResponse(request=request, name="creditos.html", context={

                "request": request,

                "user": user,

                "credits": credits,

                "amount": amount,

                "months": months,

                "rate": rate,

                "payment": round(payment, 2),

                "msg": None

            }

        )





@app.post("/creditos/solicitar")

def request_credit(

    request: Request,

    product: str = Form(...),

    amount: float = Form(...),

    months: int = Form(...),

    monthly_income: float = Form(...),

    purpose: str = Form(...)

):

    with Session(engine) as session:

        user = get_user_from_cookie(request, session)

        if not user:

            return RedirectResponse("/login", status_code=303)



        credit = CreditApplication(

            user_id=user.id,

            product=product,

            amount=amount,

            months=months,

            monthly_income=monthly_income,

            purpose=purpose,

            status="enviado",

            analyst_comment="Solicitud enviada al core bancario para evaluacion."

        )

        session.add(credit)

        session.commit()



        return RedirectResponse("/creditos", status_code=303)





@app.get("/perfil")

def profile(request: Request):

    with Session(engine) as session:

        user = get_user_from_cookie(request, session)

        if not user:

            return RedirectResponse("/login", status_code=303)



        return templates.TemplateResponse(request=request, name="perfil.html", context={"request": request, "user": user})





@app.get("/core")

def core_bank(request: Request):

    with Session(engine) as session:

        user = get_user_from_cookie(request, session)

        if not user:

            return RedirectResponse("/login", status_code=303)



        credits = session.exec(select(CreditApplication)).all()

        accounts = session.exec(select(Account)).all()



        total_approved = sum(c.amount for c in credits if c.status in ["aprobado", "desembolsado"])

        active_portfolio = sum(a.balance for a in accounts)



        return templates.TemplateResponse(request=request, name="core.html", context={

                "request": request,

                "user": user,

                "credits": credits,

                "accounts": accounts,

                "total_approved": total_approved,

                "active_portfolio": active_portfolio

            }

        )





@app.post("/core/creditos/estado")

def update_credit_status(

    request: Request,

    credit_id: int = Form(...),

    status: str = Form(...),

    comment: str = Form(...)

):

    with Session(engine) as session:

        user = get_user_from_cookie(request, session)

        if not user:

            return RedirectResponse("/login", status_code=303)



        credit = session.get(CreditApplication, credit_id)

        if credit:

            credit.status = status

            credit.analyst_comment = comment

            session.add(credit)



            if status == "desembolsado":

                account = session.exec(select(Account).where(Account.user_id == credit.user_id)).first()

                if account:

                    account.balance += credit.amount

                    session.add(account)

                    session.add(Movement(

                        account_id=account.id,

                        description="Desembolso de credito BanBif",

                        operation_type="desembolso_credito",

                        amount=credit.amount

                    ))



            session.commit()



        return RedirectResponse("/core", status_code=303)






# ===== REACT API START =====
from fastapi import Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def user_to_dict(user):
    return {
        "id": user.id,
        "document": user.document,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
                "address": user.address,
        "address": user.address,
    }

def account_to_dict(account):
    return {
        "id": account.id,
        "user_id": account.user_id,
        "account_number": account.account_number,
        "account_type": account.account_type,
        "currency": account.currency,
        "balance": account.balance,
        "status": account.status,
    }

def movement_to_dict(m):
    return {
        "id": m.id,
        "account_id": m.account_id,
        "description": m.description,
        "operation_type": m.operation_type,
        "amount": m.amount,
        "created_at": m.created_at.strftime("%d/%m/%Y %H:%M"),
    }

def credit_to_dict(c):
    return {
        "id": c.id,
        "user_id": c.user_id,
        "product": c.product,
        "amount": c.amount,
        "months": c.months,
        "monthly_income": c.monthly_income,
        "purpose": c.purpose,
        "status": c.status,
        "analyst_comment": c.analyst_comment,
        "created_at": c.created_at.strftime("%d/%m/%Y"),
    }

@app.post("/api/login")
def api_login(request: Request, data: dict = Body(...)):
    document = data.get("document")
    password = data.get("password")

    with Session(engine) as session:
        user = session.exec(select(User).where(User.document == document)).first()

        if not user or not verify_password(password, user.password_hash):
            return JSONResponse({"ok": False, "message": "Documento o contrasena incorrectos"}, status_code=401)

        response = JSONResponse({"ok": True, "user": user_to_dict(user)})
        response.set_cookie("banbif_session", make_cookie(user.id), httponly=True, samesite="lax")
        return response

@app.post("/api/register")
def api_register(data: dict = Body(...)):
    document = data.get("document")
    full_name = data.get("full_name")
    email = data.get("email")
    password = data.get("password")

    with Session(engine) as session:
        exists = session.exec(select(User).where((User.document == document) | (User.email == email))).first()

        if exists:
            return JSONResponse({"ok": False, "message": "Ya existe un usuario con ese documento o correo."}, status_code=400)

        user = User(
            document=document,
            full_name=full_name.upper(),
            email=email,
            password_hash=hash_password(password)
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        account = Account(
            user_id=user.id,
            account_number=new_account_number(document),
            account_type="Cuenta Ahorro Digital BanBif",
            currency="PEN",
            balance=0,
            status="activa"
        )
        session.add(account)
        session.commit()

        response = JSONResponse({"ok": True, "user": user_to_dict(user)})
        response.set_cookie("banbif_session", make_cookie(user.id), httponly=True, samesite="lax")
        return response

@app.get("/api/me")
def api_me(request: Request):
    with Session(engine) as session:
        user = get_user_from_cookie(request, session)
        if not user:
            return JSONResponse({"ok": False}, status_code=401)
        return {"ok": True, "user": user_to_dict(user)}

@app.post("/api/logout")
def api_logout():
    response = JSONResponse({"ok": True})
    response.delete_cookie("banbif_session")
    return response

@app.get("/api/dashboard")
def api_dashboard(request: Request):
    with Session(engine) as session:
        user = get_user_from_cookie(request, session)
        if not user:
            return JSONResponse({"ok": False}, status_code=401)

        accounts = session.exec(select(Account).where(Account.user_id == user.id)).all()
        credits = session.exec(select(CreditApplication).where(CreditApplication.user_id == user.id)).all()

        movements = []
        for account in accounts:
            movements.extend(session.exec(select(Movement).where(Movement.account_id == account.id)).all())

        movements = sorted(movements, key=lambda x: x.created_at, reverse=True)
        total_balance = sum(account.balance for account in accounts)

        return {
            "ok": True,
            "user": user_to_dict(user),
            "accounts": [account_to_dict(a) for a in accounts],
            "credits": [credit_to_dict(c) for c in credits],
            "movements": [movement_to_dict(m) for m in movements],
            "total_balance": total_balance,
        }

@app.post("/api/ahorros/deposito")
def api_deposit(request: Request, data: dict = Body(...)):
    with Session(engine) as session:
        user = get_user_from_cookie(request, session)
        if not user:
            return JSONResponse({"ok": False}, status_code=401)

        account_id = int(data.get("account_id"))
        amount = float(data.get("amount"))

        account = session.get(Account, account_id)

        if not account or account.user_id != user.id or amount <= 0:
            return JSONResponse({"ok": False, "message": "Operacion invalida"}, status_code=400)

        description = str(data.get("description") or "Deposito realizado desde banca digital").strip()

        account.balance += amount
        session.add(account)
        session.add(Movement(
            account_id=account.id,
            description=description,
            operation_type="deposito",
            amount=amount
        ))
        session.commit()

        return {"ok": True, "message": "Deposito registrado correctamente"}

@app.post("/api/transferencias")
def api_transfer(request: Request, data: dict = Body(...)):
    with Session(engine) as session:
        user = get_user_from_cookie(request, session)
        if not user:
            return JSONResponse({"ok": False, "message": "Sesion no valida"}, status_code=401)

        try:
            origin_account_id = int(data.get("origin_account_id"))
            destination_account_number = str(data.get("destination_account_number") or "").strip().upper()
            amount = round(float(str(data.get("amount") or "0").replace(",", ".")), 2)
            description = str(data.get("description") or "Transferencia desde banca digital").strip()
        except (TypeError, ValueError):
            return JSONResponse({"ok": False, "message": "Datos de transferencia invalidos"}, status_code=400)

        if not destination_account_number:
            return JSONResponse({"ok": False, "message": "Ingresa la cuenta destino"}, status_code=400)

        if amount <= 0:
            return JSONResponse({"ok": False, "message": "El monto debe ser mayor a cero"}, status_code=400)

        origin = session.get(Account, origin_account_id)
        destination = session.exec(
            select(Account).where(Account.account_number == destination_account_number)
        ).first()

        if not origin or origin.user_id != user.id:
            return JSONResponse({"ok": False, "message": "Cuenta origen invalida"}, status_code=400)

        if origin.status != "activa":
            return JSONResponse({"ok": False, "message": "La cuenta origen no esta activa"}, status_code=400)

        if not destination:
            return JSONResponse({"ok": False, "message": "La cuenta destino no existe en el core bancario"}, status_code=400)

        if destination.status != "activa":
            return JSONResponse({"ok": False, "message": "La cuenta destino no esta activa"}, status_code=400)

        if origin.id == destination.id:
            return JSONResponse({"ok": False, "message": "No puedes transferir a la misma cuenta"}, status_code=400)

        if round(float(origin.balance or 0), 2) < amount:
            return JSONResponse({"ok": False, "message": "Saldo insuficiente para completar la transferencia"}, status_code=400)

        description = description[:80]
        origin.balance = round(float(origin.balance or 0) - amount, 2)
        destination.balance = round(float(destination.balance or 0) + amount, 2)

        session.add(origin)
        session.add(destination)
        session.add(Movement(
            account_id=origin.id,
            description=f"Transferencia enviada a {destination.account_number}: {description}",
            operation_type="transferencia_salida",
            amount=-amount
        ))
        session.add(Movement(
            account_id=destination.id,
            description=f"Transferencia recibida de {origin.account_number}: {description}",
            operation_type="transferencia_entrada",
            amount=amount
        ))
        session.commit()

        return {
            "ok": True,
            "message": "Transferencia realizada correctamente",
            "origin_balance": origin.balance,
        }


@app.post("/api/creditos/solicitar")
def api_credit_request(request: Request, data: dict = Body(...)):
    with Session(engine) as session:
        user = get_user_from_cookie(request, session)
        if not user:
            return JSONResponse({"ok": False}, status_code=401)

        credit = CreditApplication(
            user_id=user.id,
            product=data.get("product"),
            amount=float(data.get("amount")),
            months=int(data.get("months")),
            monthly_income=float(data.get("monthly_income")),
            purpose=data.get("purpose"),
            status="enviado",
            analyst_comment="Solicitud enviada desde React al core bancario."
        )
        session.add(credit)
        session.commit()

        return {"ok": True, "message": "Solicitud enviada correctamente"}

@app.get("/api/core")
def api_core(request: Request):
    with Session(engine) as session:
        user = get_user_from_cookie(request, session)
        if not user:
            return JSONResponse({"ok": False}, status_code=401)

        credits = session.exec(select(CreditApplication)).all()
        accounts = session.exec(select(Account)).all()

        total_approved = sum(c.amount for c in credits if c.status in ["aprobado", "desembolsado"])
        active_portfolio = sum(a.balance for a in accounts)

        return {
            "ok": True,
            "credits": [credit_to_dict(c) for c in credits],
            "accounts": [account_to_dict(a) for a in accounts],
            "total_approved": total_approved,
            "active_portfolio": active_portfolio,
        }

@app.post("/api/core/creditos/estado")
def api_update_credit_status(request: Request, data: dict = Body(...)):
    with Session(engine) as session:
        user = get_user_from_cookie(request, session)
        if not user:
            return JSONResponse({"ok": False}, status_code=401)

        credit = session.get(CreditApplication, int(data.get("credit_id")))

        if not credit:
            return JSONResponse({"ok": False, "message": "Credito no encontrado"}, status_code=404)

        credit.status = data.get("status")
        credit.analyst_comment = data.get("comment")
        session.add(credit)

        if credit.status == "desembolsado":
            account = session.exec(select(Account).where(Account.user_id == credit.user_id)).first()
            if account:
                account.balance += credit.amount
                session.add(account)
                session.add(Movement(
                    account_id=account.id,
                    description="Desembolso de credito BanBif",
                    operation_type="desembolso_credito",
                    amount=credit.amount
                ))

        session.commit()
        return {"ok": True, "message": "Estado actualizado correctamente"}

# ===== REACT API END =====


# ===== REGISTER FIX START =====
from fastapi import Body
from fastapi.responses import JSONResponse

@app.post("/api/register2")
def api_register2(data: dict = Body(...)):
    document = str(data.get("document", "")).strip()
    full_name = str(data.get("full_name", "")).strip()
    email = str(data.get("email", "")).strip()
    password = str(data.get("password", "")).strip()

    if not document or not full_name or not email or not password:
        return JSONResponse(
            {"ok": False, "message": "Completa todos los campos para registrarte."},
            status_code=400
        )

    with Session(engine) as session:
        user = session.exec(select(User).where(User.document == document)).first()
        email_owner = session.exec(select(User).where(User.email == email)).first()

        if email_owner and (not user or email_owner.id != user.id):
            return JSONResponse(
                {"ok": False, "message": "Ese correo ya esta registrado con otro usuario."},
                status_code=400
            )

        if user:
            user.full_name = full_name.upper()
            user.email = email
            user.password_hash = hash_password(password)
            session.add(user)
            session.commit()
            session.refresh(user)
        else:
            user = User(
                document=document,
                full_name=full_name.upper(),
                email=email,
                password_hash=hash_password(password)
            )
            session.add(user)
            session.commit()
            session.refresh(user)

        account = session.exec(select(Account).where(Account.user_id == user.id)).first()

        if not account:
            account = Account(
                user_id=user.id,
                account_number=new_account_number(document),
                account_type="Cuenta Ahorro Digital BanBif",
                currency="PEN",
                balance=0,
                status="activa"
            )
            session.add(account)
            session.commit()

        response = JSONResponse({"ok": True, "user": user_to_dict(user)})
        response.set_cookie("banbif_session", make_cookie(user.id), httponly=True, samesite="lax")
        return response
# ===== REGISTER FIX END =====


# ===== REGISTER SUPER FIX START =====
from fastapi import Body
from fastapi.responses import JSONResponse

@app.post("/api/register-fixed")
def api_register_fixed(data: dict = Body(...)):
    document = str(data.get("document", "")).strip()
    full_name = str(data.get("full_name", "")).strip()
    email = str(data.get("email", "")).strip()
    password = str(data.get("password", "")).strip()

    if not document or not full_name or not email or not password:
        return JSONResponse(
            {"ok": False, "message": "Completa todos los campos."},
            status_code=400
        )

    with Session(engine) as session:
        user = session.exec(select(User).where(User.document == document)).first()
        email_owner = session.exec(select(User).where(User.email == email)).first()

        if email_owner and (not user or email_owner.id != user.id):
            return JSONResponse(
                {"ok": False, "message": "Ese correo ya esta registrado con otro usuario."},
                status_code=400
            )

        if user:
            user.full_name = full_name.upper()
            user.email = email
            user.password_hash = hash_password(password)
            session.add(user)
            session.commit()
            session.refresh(user)
        else:
            user = User(
                document=document,
                full_name=full_name.upper(),
                email=email,
                password_hash=hash_password(password)
            )
            session.add(user)
            session.commit()
            session.refresh(user)

        account = session.exec(select(Account).where(Account.user_id == user.id)).first()

        if not account:
            account = Account(
                user_id=user.id,
                account_number=new_account_number(document),
                account_type="Cuenta Ahorro Digital BanBif",
                currency="PEN",
                balance=0,
                status="activa"
            )
            session.add(account)
            session.commit()

        response = JSONResponse({
            "ok": True,
            "user": {
                "id": user.id,
                "document": user.document,
                "full_name": user.full_name,
                "email": user.email,
                "phone": user.phone,
                "address": user.address,
                "address": user.address
            }
        })
        response.set_cookie("banbif_session", make_cookie(user.id), httponly=True, samesite="lax")
        return response
# ===== REGISTER SUPER FIX END =====


# ===== REGISTER FINAL FIX START =====
from fastapi import Body
from fastapi.responses import JSONResponse

@app.post("/api/register-final")
def api_register_final(data: dict = Body(...)):
    try:
        document = str(data.get("document", "")).strip()
        full_name = str(data.get("full_name", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", "")).strip()

        if not document or not full_name or not email or not password:
            return JSONResponse(
                {"ok": False, "message": "Completa todos los campos."},
                status_code=400
            )

        if len(document) < 8:
            return JSONResponse(
                {"ok": False, "message": "El DNI debe tener al menos 8 digitos."},
                status_code=400
            )

        with Session(engine) as session:
            user_by_document = session.exec(
                select(User).where(User.document == document)
            ).first()

            user_by_email = session.exec(
                select(User).where(User.email == email)
            ).first()

            if user_by_email and user_by_document and user_by_email.id != user_by_document.id:
                return JSONResponse(
                    {"ok": False, "message": "Ese correo ya pertenece a otro usuario."},
                    status_code=400
                )

            if user_by_email and not user_by_document:
                return JSONResponse(
                    {"ok": False, "message": "Ese correo ya esta registrado. Usa otro correo."},
                    status_code=400
                )

            if user_by_document:
                user = user_by_document
                user.full_name = full_name.upper()
                user.email = email
                user.password_hash = hash_password(password)
                session.add(user)
                session.commit()
                session.refresh(user)
            else:
                user = User(
                    document=document,
                    full_name=full_name.upper(),
                    email=email,
                    password_hash=hash_password(password),
                    phone="999999999",
                    address="Huancayo, Peru"
                )
                session.add(user)
                session.commit()
                session.refresh(user)

            account = session.exec(
                select(Account).where(Account.user_id == user.id)
            ).first()

            if not account:
                account = Account(
                    user_id=user.id,
                    account_number=new_account_number(document),
                    account_type="Cuenta Ahorro Digital BanBif",
                    currency="PEN",
                    balance=0.0,
                    status="activa"
                )
                session.add(account)
                session.commit()

            response = JSONResponse({
                "ok": True,
                "message": "Cuenta creada correctamente.",
                "user": {
                    "id": user.id,
                    "document": user.document,
                    "full_name": user.full_name,
                    "email": user.email,
                    "phone": user.phone,
                "address": user.address,
                    "address": user.address
                }
            })

            response.set_cookie(
                "banbif_session",
                make_cookie(user.id),
                httponly=True,
                samesite="lax"
            )

            return response

    except Exception as e:
        return JSONResponse(
            {"ok": False, "message": "Error interno en registro: " + str(e)},
            status_code=500
        )
# ===== REGISTER FINAL FIX END =====


# ===== REGISTER SAFE REAL START =====
from fastapi import Body
from fastapi.responses import JSONResponse

@app.post("/api/register-safe")
def api_register_safe_real(data: dict = Body(...)):
    try:
        document = str(data.get("document", "")).strip()
        full_name = str(data.get("full_name", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", "")).strip()

        if not document or not full_name or not email or not password:
            return JSONResponse(
                {"ok": False, "message": "Completa todos los campos."},
                status_code=400
            )

        with Session(engine) as session:
            existing_document = session.exec(
                select(User).where(User.document == document)
            ).first()

            existing_email = session.exec(
                select(User).where(User.email == email)
            ).first()

            if existing_email and not existing_document:
                return JSONResponse(
                    {"ok": False, "message": "Ese correo ya existe. Usa otro correo."},
                    status_code=400
                )

            if existing_document:
                user = existing_document
                user.full_name = full_name.upper()
                user.email = email
                user.password_hash = hash_password(password)
                user.phone = user.phone or "999999999"
                user.address = user.address or "Huancayo, Peru"
                session.add(user)
                session.commit()
                session.refresh(user)
            else:
                user = User(
                    document=document,
                    full_name=full_name.upper(),
                    email=email,
                    password_hash=hash_password(password),
                    phone="999999999",
                    address="Huancayo, Peru"
                )
                session.add(user)
                session.commit()
                session.refresh(user)

            account = session.exec(
                select(Account).where(Account.user_id == user.id)
            ).first()

            if not account:
                account = Account(
                    user_id=user.id,
                    account_number=new_account_number(document),
                    account_type="Cuenta Ahorro Digital BanBif",
                    currency="PEN",
                    balance=0.0,
                    status="activa"
                )
                session.add(account)
                session.commit()

            response = JSONResponse({
                "ok": True,
                "message": "Cuenta creada correctamente.",
                "user": {
                    "id": user.id,
                    "document": user.document,
                    "full_name": user.full_name,
                    "email": user.email,
                    "phone": user.phone,
                "address": user.address,
                    "address": user.address
                }
            })

            response.set_cookie(
                "banbif_session",
                make_cookie(user.id),
                httponly=True,
                samesite="lax"
            )

            return response

    except Exception as e:
        return JSONResponse(
            {"ok": False, "message": "Error real: " + str(e)},
            status_code=500
        )
# ===== REGISTER SAFE REAL END =====


# ===== CORS LOCALHOST FIX =====
try:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
except Exception:
    pass
# ===== CORS LOCALHOST FIX END =====


# ===== PING FIX START =====
@app.get("/api/ping")
def api_ping():
    return {"ok": True, "message": "FastAPI conectado correctamente"}
# ===== PING FIX END =====


# ===== PING CHECK FINAL =====
@app.get("/api/ping")
def api_ping():
    return {"ok": True, "message": "FastAPI funcionando"}
# ===== PING CHECK FINAL END =====


# ===== PING FINAL DEFINITIVO =====
@app.get("/api/ping-final")
def api_ping_final():
    return {"ok": True, "message": "FastAPI conectado"}
# ===== PING FINAL DEFINITIVO END =====


# ===== REGISTER DB FINAL START =====
from fastapi import Body as _Body, Response as _Response, HTTPException as _HTTPException
from sqlmodel import Session as _Session, select as _select
from app.db import engine as _engine, create_db_and_tables as _create_db_and_tables
from app.models import User as _User, Account as _Account
import hashlib as _hashlib

@app.post("/api/register-db")
def api_register_db_final(response: _Response, data: dict = _Body(...)):
    _create_db_and_tables()

    document = str(data.get("document", "")).strip()
    full_name = str(data.get("full_name", "")).strip().upper()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", "")).strip()

    if not document or not full_name or not email or not password:
        raise _HTTPException(status_code=400, detail="Completa todos los campos")

    if len(document) < 8:
        raise _HTTPException(status_code=400, detail="El DNI debe tener minimo 8 digitos")

    if len(password) < 6:
        raise _HTTPException(status_code=400, detail="La contrasena debe tener minimo 6 caracteres")

    try:
        password_hash = hash_password(password)
    except Exception:
        password_hash = _hashlib.sha256(password.encode("utf-8")).hexdigest()

    with _Session(_engine) as session:
        user = session.exec(_select(_User).where(_User.document == document)).first()

        if user:
            user.full_name = full_name
            user.email = email
            user.password_hash = password_hash
            if not user.phone:
                user.phone = "999999999"
            if not user.address:
                user.address = "Peru"
            session.add(user)
            session.commit()
            session.refresh(user)
            message = "Cuenta actualizada con exito"
        else:
            user = _User(
                document=document,
                full_name=full_name,
                email=email,
                password_hash=password_hash,
                phone="999999999",
                address="Peru"
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            message = "Cuenta registrada con exito"

        account = session.exec(_select(_Account).where(_Account.user_id == user.id)).first()

        if not account:
            try:
                account_number = new_account_number(document)
            except Exception:
                account_number = f"BBF-{document[-4:]}-001"

            account = _Account(
                user_id=user.id,
                account_number=account_number,
                account_type="Cuenta Ahorro Digital BanBif",
                currency="PEN",
                balance=0.00,
                status="activa"
            )
            session.add(account)
            session.commit()

        response.set_cookie(
            key="user_id",
            value=str(user.id),
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 6
        )

        return {
            "ok": True,
            "message": message,
            "user": {
                "id": user.id,
                "document": user.document,
                "full_name": user.full_name,
                "email": user.email
            }
        }
# ===== REGISTER DB FINAL END =====


# ===== REGISTER SUPABASE REAL FINAL START =====
from fastapi import Body as _Body, Response as _Response, HTTPException as _HTTPException
from sqlmodel import Session as _Session, select as _select
from app.db import engine as _engine, create_db_and_tables as _create_db_and_tables
from app.models import User as _User, Account as _Account
import hashlib as _hashlib

@app.post("/api/register-db")
def api_register_db_real(response: _Response, data: dict = _Body(...)):
    _create_db_and_tables()

    document = str(data.get("document", "")).strip()
    full_name = str(data.get("full_name", "")).strip().upper()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", "")).strip()

    if not document or not full_name or not email or not password:
        raise _HTTPException(status_code=400, detail="Completa todos los campos")

    if len(document) < 8:
        raise _HTTPException(status_code=400, detail="El DNI debe tener minimo 8 digitos")

    if len(password) < 6:
        raise _HTTPException(status_code=400, detail="La contrasena debe tener minimo 6 caracteres")

    try:
        password_hash = hash_password(password)
    except Exception:
        password_hash = _hashlib.sha256(password.encode("utf-8")).hexdigest()

    with _Session(_engine) as session:
        user = session.exec(_select(_User).where(_User.document == document)).first()

        if user:
            raise _HTTPException(status_code=400, detail="Este DNI ya esta registrado")

        user = _User(
            document=document,
            full_name=full_name,
            email=email,
            password_hash=password_hash,
            phone="999999999",
            address="Peru"
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        try:
            account_number = new_account_number(document)
        except Exception:
            account_number = f"BBF-{document[-4:]}-001"

        account = _Account(
            user_id=user.id,
            account_number=account_number,
            account_type="Cuenta Ahorro Digital BanBif",
            currency="PEN",
            balance=0.00,
            status="activa"
        )

        session.add(account)
        session.commit()

        response.set_cookie(
            key="user_id",
            value=str(user.id),
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 6
        )

        return {
            "ok": True,
            "message": "Cuenta creada y guardada con exito",
            "user": {
                "id": user.id,
                "document": user.document,
                "full_name": user.full_name,
                "email": user.email
            }
        }
# ===== REGISTER SUPABASE REAL FINAL END =====


# ===== REGISTER COMPLETE PHONE START =====
from fastapi import Body as _BodyC, HTTPException as _HTTPExceptionC
from sqlmodel import Session as _SessionC, select as _selectC
from app.db import engine as _engineC, create_db_and_tables as _create_db_and_tablesC
from app.models import User as _UserC, Account as _AccountC
import hashlib as _hashlibC

@app.post("/api/register-complete")
def api_register_complete(data: dict = _BodyC(...)):
    _create_db_and_tablesC()

    document = str(data.get("document", "")).strip()
    full_name = str(data.get("full_name", "")).strip().upper()
    email = str(data.get("email", "")).strip().lower()
    phone = str(data.get("phone", "")).strip()
    address = str(data.get("address", "")).strip()
    password = str(data.get("password", "")).strip()

    if not document or not full_name or not email or not phone or not address or not password:
        raise _HTTPExceptionC(status_code=400, detail="Completa todos los campos")

    if len(document) != 8 or not document.isdigit():
        raise _HTTPExceptionC(status_code=400, detail="El DNI debe tener 8 digitos")

    if len(phone) != 9 or not phone.isdigit():
        raise _HTTPExceptionC(status_code=400, detail="El telefono debe tener 9 digitos")

    if len(password) < 6:
        raise _HTTPExceptionC(status_code=400, detail="La contrasena debe tener minimo 6 caracteres")

    try:
        password_hash = hash_password(password)
    except Exception:
        password_hash = _hashlibC.sha256(password.encode("utf-8")).hexdigest()

    with _SessionC(_engineC) as session:
        existing = session.exec(_selectC(_UserC).where(_UserC.document == document)).first()
        if existing:
            raise _HTTPExceptionC(status_code=400, detail="Este DNI ya esta registrado")

        user = _UserC(
            document=document,
            full_name=full_name,
            email=email,
            phone=phone,
            address=address,
            password_hash=password_hash
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        try:
            account_number = new_account_number(document)
        except Exception:
            account_number = f"BBF-{document[-4:]}-001"

        account = _AccountC(
            user_id=user.id,
            account_number=account_number,
            account_type="Cuenta Ahorro Digital BanBif",
            currency="PEN",
            balance=0.00,
            status="activa"
        )

        session.add(account)
        session.commit()

        return {
            "ok": True,
            "message": "Cuenta creada y guardada con exito",
            "user": {
                "id": user.id,
                "document": user.document,
                "full_name": user.full_name,
                "email": user.email,
                "phone": user.phone,
                "address": user.address
            }
        }
# ===== REGISTER COMPLETE PHONE END =====
