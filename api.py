from fastapi import APIRouter, Depends, HTTPException, HTTP_401_UNAUTHORIZED
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Contact, User
from pydantic import BaseModel
from datetime import date, timedelta
from auth import create_access_token, verify_token, CredentialsException
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    birthday: date
    extra_info: str = None
    
class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

@router.post("/users/register")
def register_user(user: UserCreate, db: Session = Depends(SessionLocal)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(email=user.email)
    new_user.set_password(user.password)
    db.add(new_user)
    db.commit()
    return {"email": new_user.email, "id": new_user.id}

@router.post("/users/login")
def login(user: UserLogin, db: Session = Depends(SessionLocal)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not db_user.check_password(user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception)


@router.get("/contacts/")
def get_contacts(db: Session = Depends(SessionLocal), current_user: User = Depends(get_current_user)):
    return db.query(Contact).filter(Contact.user_id == current_user.id).all()



@router.post("/contacts/")
def create_contact(contact: ContactCreate, db: Session = Depends(SessionLocal)):
    db_contact = Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@router.get("/contacts/")
def get_contacts(name: str = None, surname: str = None, email: str = None, db: Session = Depends(SessionLocal)):
    query = db.query(Contact)
    if name:
        query = query.filter(Contact.first_name == name)
    if surname:
        query = query.filter(Contact.last_name == surname)
    if email:
        query = query.filter(Contact.email == email)
    return query.all()

@router.get("/contacts/{contact_id}")
def get_contact(contact_id: int, db: Session = Depends(SessionLocal)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.put("/contacts/{contact_id}")
def update_contact(contact_id: int, contact: ContactCreate, db: Session = Depends(SessionLocal)):
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    for key, value in contact.dict().items():
        setattr(db_contact, key, value)
    db.commit()
    return db_contact

@router.delete("/contacts/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(SessionLocal)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(contact)
    db.commit()
    return {"message": "Contact deleted successfully"}

@router.get("/contacts/birthdays/")
def get_upcoming_birthdays(db: Session = Depends(SessionLocal())):
    today = date.today()
    start_date = today - timedelta(days=today.weekday())
    end_date = start_date + timedelta(days=7)
    upcoming_birthdays = db.query(Contact).filter(Contact.birthday >= start_date, Contact.birthday <= end_date).all()
    return upcoming_birthdays