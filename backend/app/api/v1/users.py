from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_users():
    return {"users": []}


@router.post("/")
async def create_user():
    return {"message": "User created"}
