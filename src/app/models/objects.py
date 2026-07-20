# Standard Libaries
from typing import Dict, List, Tuple
# External Libraries
from pydantic import BaseModel
# Application Libaries
from app.models.base import Dimensions

class Object(BaseModel):
    key: str
    dimensions: Dimensions