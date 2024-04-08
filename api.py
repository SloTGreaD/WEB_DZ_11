from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Contact
from pydantic import BaseModel
from datetime import date, timedelta

router = APIRouter()

class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    birthday: date
    extra_info: str = None

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