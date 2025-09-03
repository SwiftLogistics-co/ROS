from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from app.schemas.schemas import Address, AddressCreate, AddressUpdate, ResponseMessage

router = APIRouter()


@router.post("/", response_model=Address)
def create_address(
    address: AddressCreate,
    db: Session = Depends(get_db)
):
    """Create a new delivery address"""
    db_address = models.Address(**address.dict())
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    return db_address


@router.get("/", response_model=List[Address])
def list_addresses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    city: Optional[str] = None,
    state: Optional[str] = None,
    priority: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List all delivery addresses with optional filtering"""
    query = db.query(models.Address)
    
    if city:
        query = query.filter(models.Address.city.ilike(f"%{city}%"))
    if state:
        query = query.filter(models.Address.state.ilike(f"%{state}%"))
    if priority:
        query = query.filter(models.Address.priority == priority)
    
    addresses = query.offset(skip).limit(limit).all()
    return addresses


@router.get("/{address_id}", response_model=Address)
def get_address(address_id: int, db: Session = Depends(get_db)):
    """Get address by ID"""
    address = db.query(models.Address).filter(models.Address.id == address_id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    return address


@router.put("/{address_id}", response_model=Address)
def update_address(
    address_id: int,
    address_update: AddressUpdate,
    db: Session = Depends(get_db)
):
    """Update address information"""
    address = db.query(models.Address).filter(models.Address.id == address_id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    
    update_data = address_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(address, field, value)
    
    db.commit()
    db.refresh(address)
    return address


@router.delete("/{address_id}", response_model=ResponseMessage)
def delete_address(address_id: int, db: Session = Depends(get_db)):
    """Delete address"""
    address = db.query(models.Address).filter(models.Address.id == address_id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    
    db.delete(address)
    db.commit()
    return ResponseMessage(message=f"Address {address_id} deleted successfully")
