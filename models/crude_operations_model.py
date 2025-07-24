from typing import Generic, TypeVar, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

class CrudeOperationsModel(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: type[ModelType]):
        self.model = model

    def create(self, db: Session, obj_in: Dict[str, Any]) -> ModelType:
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def read(self, db: Session, filters: Dict[str, Any]) -> Optional[ModelType]:
        conditions = []
        for key, value in filters.items():
            if hasattr(self.model, key):
                conditions.append(getattr(self.model, key) == value)
        
        if conditions:
            return db.query(self.model).filter(and_(*conditions)).first()
        return None

    def update(self, db: Session, filters: Dict[str, Any], update_data: Dict[str, Any]) -> Optional[ModelType]:
        conditions = []
        for key, value in filters.items():
            if hasattr(self.model, key):
                conditions.append(getattr(self.model, key) == value)
        
        if conditions:
            db_obj = db.query(self.model).filter(and_(*conditions)).first()
            if db_obj:
                for key, value in update_data.items():
                    if hasattr(db_obj, key):
                        setattr(db_obj, key, value)
                db.commit()
                db.refresh(db_obj)
                return db_obj
        return None

    def delete(self, db: Session, filters: Dict[str, Any]) -> bool:
        conditions = []
        for key, value in filters.items():
            if hasattr(self.model, key):
                conditions.append(getattr(self.model, key) == value)
        
        if conditions:
            db_obj = db.query(self.model).filter(and_(*conditions)).first()
            if db_obj:
                db.delete(db_obj)
                db.commit()
                return True
        return False

    def list(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all() 