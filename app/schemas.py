from pydantic import BaseModel, field_validator
from typing import List

class UserBase(BaseModel):
    user_id: str
    username: str
    team_name: str
    is_active: bool

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    is_active: bool

class TeamMember(BaseModel):
    user_id: str
    username: str
    is_active: bool

class TeamSchema(BaseModel):
    team_name: str
    members: List[TeamMember] = []

    class Config:
        orm_mode = True

class PullRequestBase(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: str  # OPEN | MERGED
    assigned_reviewers: List[str]  # Список user_id назначенных ревьюверов

    class Config:
        orm_mode = True

class PullRequestCreate(PullRequestBase):
    pass

class PullRequestResponse(PullRequestBase):
    class Config:
        orm_mode = True

class PullRequestShort(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: str

    class Config:
        orm_mode = True

class ErrorResponse(BaseModel):
    error: dict

    class Config:
        orm_mode = True

class UserActivateRequest(BaseModel):
    user_id: str
    is_active: bool


class PullRequestResponse(PullRequestBase):
    @field_validator("assigned_reviewers", mode="before")
    @classmethod
    def parse_assigned_reviewers(cls, v):
        if isinstance(v, list):
            return [str(x) for x in v]

        if isinstance(v, str):
            v = v.strip('{}').strip()
            if not v:
                return []
            return [item.strip() for item in v.split(',')]

        return v

    class Config:
        orm_mode = True