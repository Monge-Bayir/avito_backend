from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    user_id = Column(String, primary_key=True)
    username = Column(String)
    is_active = Column(Boolean, default=True)
    team_name = Column(String, ForeignKey('teams.team_name'))  # Связь с командой


class Team(Base):
    __tablename__ = 'teams'
    team_name = Column(String, primary_key=True)
    members = relationship('User', backref='team')  # Связь с пользователями


class PullRequest(Base):
    __tablename__ = 'pull_requests'
    pull_request_id = Column(String, primary_key=True)
    pull_request_name = Column(String)
    author_id = Column(String)
    status = Column(String, default="OPEN")
    assigned_reviewers = Column(String)