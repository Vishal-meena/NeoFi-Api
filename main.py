from fastapi import FastAPI, Depends, HTTPException, status, Query, Path
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

import models
import schemas
import auth
from database import engine, get_db

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="NeoFi Event Management API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth endpoints
@app.post("/api/auth/register", response_model=schemas.User)
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/auth/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/refresh", response_model=schemas.Token)
async def refresh_token(
    current_user: models.User = Depends(auth.get_current_user)
):
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/logout")
async def logout():

    return {"message": "Successfully logged out"}

# Event Management endpoints
@app.post("/api/events", response_model=schemas.Event)
async def create_event(
    event: schemas.EventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_event = models.Event(
        **event.dict(),
        owner_id=current_user.id
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    # Create initial version
    event_version = models.EventVersion(
        **event.dict(),
        event_id=db_event.id,
        modified_by_id=current_user.id,
        version_number=1
    )
    db.add(event_version)
    db.commit()
    
    return db_event

@app.get("/api/events", response_model=List[schemas.Event])
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    
    query = db.query(models.Event).filter(models.Event.owner_id == current_user.id)
    
   
    if start_date:
        query = query.filter(models.Event.start_time >= start_date)
    if end_date:
        query = query.filter(models.Event.end_time <= end_date)
    
    
    events = query.offset(skip).limit(limit).all()
    
    
    
    return events

@app.get("/api/events/{event_id}", response_model=schemas.EventWithPermissions)
async def get_event(
    event_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    
    if event.owner_id != current_user.id:
    
        raise HTTPException(status_code=403, detail="Not authorized to access this event")
    
    
    permissions = db.query(models.event_permissions).filter(
        models.event_permissions.c.event_id == event_id
    ).all()
    
    
    event_dict = {
        **event.__dict__,
        "permissions": [
            {"user_id": p.user_id, "role": p.role, "created_at": p.created_at}
            for p in permissions
        ]
    }
    
    return event_dict

@app.put("/api/events/{event_id}", response_model=schemas.Event)
async def update_event(
    event_id: int,
    event_update: schemas.EventUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    
    if db_event.owner_id != current_user.id:
        
        raise HTTPException(status_code=403, detail="Not authorized to update this event")
    
    
    update_data = event_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_event, key, value)
    
    
    current_version = db.query(models.EventVersion).filter(
        models.EventVersion.event_id == event_id
    ).order_by(models.EventVersion.version_number.desc()).first()
    
    new_version = models.EventVersion(
        event_id=db_event.id,
        title=db_event.title,
        description=db_event.description,
        start_time=db_event.start_time,
        end_time=db_event.end_time,
        location=db_event.location,
        is_recurring=db_event.is_recurring,
        recurrence_pattern=db_event.recurrence_pattern,
        recurrence_end_date=db_event.recurrence_end_date,
        modified_by_id=current_user.id,
        version_number=current_version.version_number + 1 if current_version else 1
    )
    
    db.add(new_version)
    db.commit()
    db.refresh(db_event)
    
    return db_event

@app.delete("/api/events/{event_id}")
async def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    
    if db_event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this event")
    
    db.delete(db_event)
    db.commit()
    
    return {"message": "Event deleted successfully"}

@app.post("/api/events/batch", response_model=List[schemas.Event])
async def create_batch_events(
    batch: schemas.BatchEventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    created_events = []
    
    for event_data in batch.events:
        db_event = models.Event(
            **event_data.dict(),
            owner_id=current_user.id
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        
        
        event_version = models.EventVersion(
            **event_data.dict(),
            event_id=db_event.id,
            modified_by_id=current_user.id,
            version_number=1
        )
        db.add(event_version)
        db.commit()
        
        created_events.append(db_event)
    
    return created_events

# Collaboration endpoints
@app.post("/api/events/{event_id}/share")
async def share_event(
    event_id: int,
    permissions: List[schemas.PermissionCreate],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    
    if db_event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can share this event")
    
    
    for perm in permissions:
        
        user = db.query(models.User).filter(models.User.id == perm.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User with id {perm.user_id} not found")
        
        
        existing_perm = db.query(models.event_permissions).filter(
            models.event_permissions.c.event_id == event_id,
            models.event_permissions.c.user_id == perm.user_id
        ).first()
        
        if existing_perm:
            
            db.execute(
                models.event_permissions.update().where(
                    models.event_permissions.c.event_id == event_id,
                    models.event_permissions.c.user_id == perm.user_id
                ).values(role=perm.role)
            )
        else:
           
            db.execute(
                models.event_permissions.insert().values(
                    event_id=event_id,
                    user_id=perm.user_id,
                    role=perm.role
                )
            )
    
    db.commit()
    
    
    permissions = db.query(models.event_permissions).filter(
        models.event_permissions.c.event_id == event_id
    ).all()
    
    return {
        "message": "Event shared successfully",
        "permissions": [
            {"user_id": p.user_id, "role": p.role, "created_at": p.created_at}
            for p in permissions
        ]
    }

# Version History endpoints
@app.get("/api/events/{event_id}/history/{version_id}", response_model=schemas.EventVersion)
async def get_event_version(
    event_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    
    if event.owner_id != current_user.id:
        
        raise HTTPException(status_code=403, detail="Not authorized to access this event")
    
    
    version = db.query(models.EventVersion).filter(
        models.EventVersion.event_id == event_id,
        models.EventVersion.version_number == version_id
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return version

@app.post("/api/events/{event_id}/rollback/{version_id}", response_model=schemas.Event)
async def rollback_event(
    event_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    
    if event.owner_id != current_user.id:
        
        raise HTTPException(status_code=403, detail="Not authorized to update this event")
    
    
    version = db.query(models.EventVersion).filter(
        models.EventVersion.event_id == event_id,
        models.EventVersion.version_number == version_id
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    
    event.title = version.title
    event.description = version.description
    event.start_time = version.start_time
    event.end_time = version.end_time
    event.location = version.location
    event.is_recurring = version.is_recurring
    event.recurrence_pattern = version.recurrence_pattern
    event.recurrence_end_date = version.recurrence_end_date
    
    
    current_version = db.query(models.EventVersion).filter(
        models.EventVersion.event_id == event_id
    ).order_by(models.EventVersion.version_number.desc()).first()
    
    new_version = models.EventVersion(
        event_id=event.id,
        title=event.title,
        description=event.description,
        start_time=event.start_time,
        end_time=event.end_time,
        location=event.location,
        is_recurring=event.is_recurring,
        recurrence_pattern=event.recurrence_pattern,
        recurrence_end_date=event.recurrence_end_date,
        modified_by_id=current_user.id,
        version_number=current_version.version_number + 1
    )
    
    db.add(new_version)
    db.commit()
    db.refresh(event)
    
    return event

# Changelog & Diff endpoints
@app.get("/api/events/{event_id}/changelog")
async def get_event_changelog(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    
    if event.owner_id != current_user.id:
        
        raise HTTPException(status_code=403, detail="Not authorized to access this event")
    
    
    versions = db.query(models.EventVersion).filter(
        models.EventVersion.event_id == event_id
    ).order_by(models.EventVersion.version_number).all()
    
    
    changelog = []
    for version in versions:
        modifier = db.query(models.User).filter(models.User.id == version.modified_by_id).first()
        changelog.append({
            "version": version.version_number,
            "modified_by": modifier.username if modifier else "Unknown",
            "modified_at": version.created_at,
            "changes": {
                "title": version.title,
                "description": version.description,
                "start_time": version.start_time,
                "end_time": version.end_time,
                "location": version.location,
                "is_recurring": version.is_recurring,
                "recurrence_pattern": version.recurrence_pattern,
                "recurrence_end_date": version.recurrence_end_date
            }
        })
    
    return {"changelog": changelog}

@app.get("/api/events/{event_id}/diff/{version_id1}/{version_id2}")
async def get_event_diff(
    event_id: int,
    version_id1: int,
    version_id2: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    
    if event.owner_id != current_user.id:
        
        raise HTTPException(status_code=403, detail="Not authorized to access this event")
    
    
    version1 = db.query(models.EventVersion).filter(
        models.EventVersion.event_id == event_id,
        models.EventVersion.version_number == version_id1
    ).first()
    
    version2 = db.query(models.EventVersion).filter(
        models.EventVersion.event_id == event_id,
        models.EventVersion.version_number == version_id2
    ).first()
    
    if not version1 or not version2:
        raise HTTPException(status_code=404, detail="One or both versions not found")
    
    
    differences = []
    for field in ["title", "description", "start_time", "end_time", "location", 
                  "is_recurring", "recurrence_pattern", "recurrence_end_date"]:
        val1 = getattr(version1, field)
        val2 = getattr(version2, field)
        if val1 != val2:
            differences.append({
                "field": field,
                "old_value": val1,
                "new_value": val2
            })
    
    return {
        "version1": version_id1,
        "version2": version_id2,
        "differences": differences
    }

@app.get('/')
async def root():
    return {"message": "Neofi Event management API"}
