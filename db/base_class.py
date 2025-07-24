import re
from typing import Any
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import as_declarative, declared_attr

@as_declarative()
class Base:
    id:Any
    metadata: MetaData
    __name__: str
    
    @declared_attr
    def __tablename__(self) -> str:
        """CamelCase __name__ to snake_case __tablename__"""
        return "_".join(x.lower() for x in re.findall(r"[A-Z][a-z]*", self.__name__))