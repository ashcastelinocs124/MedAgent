"""Data models for user profiles, conditions, and medications.

Pure dataclasses with no external dependencies.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class Sex(Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class HealthLiteracy(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Condition:
    """A user's medical condition mapped to a brain subcategory."""

    name: str
    category_id: str  # e.g. "hormones_metabolism_nutrition"
    subcategory_id: str  # e.g. "diabetes_type_1_type_2_gestational"
    icd10_code: Optional[str] = None
    diagnosed_date: Optional[date] = None
    active: bool = True


@dataclass
class Medication:
    """A medication the user is currently taking."""

    name: str
    category_id: str  # primary category this medication relates to
    related_condition: Optional[str] = None  # condition name this treats
    rxnorm_code: Optional[str] = None


@dataclass
class UserProfile:
    """Complete user profile for personalization."""

    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    age: Optional[int] = None
    sex: Sex = Sex.PREFER_NOT_TO_SAY
    conditions: list[Condition] = field(default_factory=list)
    medications: list[Medication] = field(default_factory=list)
    health_literacy: HealthLiteracy = HealthLiteracy.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
