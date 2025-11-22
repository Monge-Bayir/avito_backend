from random import choice
from typing import List

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db, init_db
from app.models import User, Team as TeamModel, PullRequest
from app.schemas import UserCreate, UserResponse, TeamSchema, PullRequestCreate, PullRequestResponse, PullRequestShort

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    init_db()


@app.post("/users/", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.user_id == user.user_id).first()
    if db_user:
        raise HTTPException(status_code=400, detail="User already exists")
    new_user = User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/team/add", response_model=TeamSchema)
def create_team(team: TeamSchema, db: Session = Depends(get_db)):
    db_team = db.query(TeamModel).filter(TeamModel.team_name == team.team_name).first()
    if db_team:
        raise HTTPException(status_code=400, detail="Team already exists")

    db_team = TeamModel(team_name=team.team_name)
    db.add(db_team)
    db.commit()
    db.refresh(db_team)

    if not team.members:
        team.members = []

    for member in team.members:
        db_user = db.query(User).filter(User.user_id == member.user_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail=f"User {member.user_id} not found")

        db_user.team_name = team.team_name
        db.add(db_user)
    db.commit()

    return db_team


@app.post("/pullRequest/create", response_model=PullRequestResponse)
def create_pull_request(pr: PullRequestCreate, db: Session = Depends(get_db)):
    author = db.query(User).filter(User.user_id == pr.author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    team = db.query(User).filter(User.team_name == author.team_name).all()

    active_reviewers = [user for user in team if user.is_active and user.user_id != pr.author_id]

    if len(active_reviewers) < 2:
        raise HTTPException(status_code=400, detail="Not enough active reviewers for the PR.")

    assigned_reviewers = list(set([reviewer.user_id for reviewer in active_reviewers[:2]]))  # Преобразуем в список

    new_pr = PullRequest(
        pull_request_id=pr.pull_request_id,
        pull_request_name=pr.pull_request_name,
        author_id=pr.author_id,
        assigned_reviewers=assigned_reviewers,
    )

    db.add(new_pr)
    db.commit()
    db.refresh(new_pr)

    return new_pr



@app.post("/pullRequest/reassign", response_model=PullRequestResponse)
def reassign_reviewer(
    pr_id: str,
    old_reviewer_id: str,
    db: Session = Depends(get_db),
):
    pr = db.query(PullRequest).filter(PullRequest.pull_request_id == pr_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Pull Request not found.")

    if pr.status == "MERGED":
        raise HTTPException(status_code=400, detail="Cannot reassign reviewers for a merged PR.")

    assigned = pr.assigned_reviewers
    if isinstance(assigned, str):
        raw = assigned.strip("{}").strip()
        assigned = [] if not raw else [s.strip() for s in raw.split(",")]

    if old_reviewer_id not in assigned:
        raise HTTPException(status_code=404, detail="Old reviewer not found in PR.")

    old_reviewer = db.query(User).filter(User.user_id == old_reviewer_id).first()
    if not old_reviewer:
        raise HTTPException(status_code=404, detail="Reviewer user not found.")

    if not old_reviewer.team_name:
        raise HTTPException(status_code=400, detail="Reviewer has no team.")

    candidates = (
        db.query(User)
        .filter(
            User.team_name == old_reviewer.team_name,
            User.is_active.is_(True),
            User.user_id != old_reviewer_id,
        )
        .all()
    )

    if not candidates:
        raise HTTPException(status_code=400, detail="No available candidates to reassign.")

    new_reviewer = choice(candidates).user_id

    new_assigned = [
        new_reviewer if uid == old_reviewer_id else uid
        for uid in assigned
    ]

    pr.assigned_reviewers = "{" + ",".join(new_assigned) + "}"

    db.commit()

    pr.assigned_reviewers = new_assigned

    return pr


@app.post("/pullRequest/merge", response_model=PullRequestResponse)
def merge_pull_request(pr_id: str, db: Session = Depends(get_db)):
    pr = db.query(PullRequest).filter(PullRequest.pull_request_id == pr_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Pull Request not found.")

    if pr.status == "MERGED":
        return pr

    pr.status = "MERGED"
    db.commit()
    db.refresh(pr)
    return pr


@app.get("/users/{user_id}/pr", response_model=List[PullRequestShort])
def get_user_pr(user_id: str, db: Session = Depends(get_db)):
    prs = db.query(PullRequest).all()
    result = []

    for pr in prs:
        assigned = pr.assigned_reviewers

        if isinstance(assigned, str):
            raw = assigned.strip("{}").strip()
            reviewer_ids = [] if not raw else [s.strip() for s in raw.split(",")]
        else:
            reviewer_ids = assigned or []

        if user_id in reviewer_ids:
            result.append(pr)

    return result

if __name__ == '__main__':
    uvicorn.run('app.main:app', host='127.0.0.1', port=8000, reload=True)