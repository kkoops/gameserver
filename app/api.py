from enum import Enum

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from . import model
from .model import (
    LiveDifficulty,
    ResultUser,
    RoomUser,
    SafeUser,
    WaitRoomStatus,
    get_user_by_token,
    room_wait_user,
)

app = FastAPI()

# Sample APIs


@app.get("/")
async def root():
    return {"message": "Hello World"}


# User APIs


class UserCreateRequest(BaseModel):
    user_name: str
    leader_card_id: int


class UserCreateResponse(BaseModel):
    user_token: str


@app.post("/user/create", response_model=UserCreateResponse)
def user_create(req: UserCreateRequest):
    """新規ユーザー作成"""
    token = model.create_user(req.user_name, req.leader_card_id)
    return UserCreateResponse(user_token=token)


bearer = HTTPBearer()


def get_auth_token(cred: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    assert cred is not None
    if not cred.credentials:
        raise HTTPException(status_code=401, detail="invalid credential")
    return cred.credentials


@app.get("/user/me", response_model=SafeUser)
def user_me(token: str = Depends(get_auth_token)):
    user = model.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=404)
    # print(f"user_me({token=}, {user=})")
    return user


class Empty(BaseModel):
    pass


@app.post("/user/update", response_model=Empty)
def update(req: UserCreateRequest, token: str = Depends(get_auth_token)):
    """Update user attributes"""
    # print(req)
    model.update_user(token, req.user_name, req.leader_card_id)
    return {}


# room APIs
class RoomCreateResponse(BaseModel):
    room_id: int


class RoomCreateRequest(BaseModel):
    live_id: int
    select_difficulty: model.LiveDifficulty


@app.post("/room/create", response_model=RoomCreateResponse)
def room_create(req: RoomCreateRequest, token: str = Depends(get_auth_token)):
    """新規ルーム作成"""
    user = get_user_by_token(token)
    room_id = model.create_room(req.live_id, req.select_difficulty, user)
    return RoomCreateResponse(room_id=room_id)


class RoomListResponse(BaseModel):
    room_info_list: list[model.RoomInfo]


class RoomListRequest(BaseModel):
    live_id: int


@app.post("/room/list", response_model=RoomListResponse)
def room_list(req: RoomListRequest):
    """ルームリスト表示"""
    room_list_info = model.list_room(req.live_id)
    return RoomListResponse(room_info_list=room_list_info)


class RoomJoinRequest(BaseModel):
    room_id: int
    select_difficulty: LiveDifficulty


class RoomJoinResponse(BaseModel):
    join_room_result: model.JoinRoomResult


@app.post("/room/join", response_model=RoomJoinResponse)
def room_join(req: RoomJoinRequest, token: str = Depends(get_auth_token)):
    """ルーム参加"""
    user = get_user_by_token(token)
    join_room_result = model.join_room(req.room_id, req.select_difficulty, user)
    return RoomJoinResponse(join_room_result=join_room_result)


class RoomWaitRequest(BaseModel):
    room_id: int


class RoomWaitResponse(BaseModel):
    status: model.WaitRoomStatus
    room_user_list: list[RoomUser]


@app.post("/room/wait", response_model=RoomWaitResponse)
def room_wait(req: RoomWaitRequest):
    # room_wait_result: RoomWaitResponse
    status: int = model.room_wait_status(req.room_id)
    room_user_list: list[RoomUser] = model.room_wait_user(req.room_id)
    return RoomWaitResponse(status=status, room_user_list=room_user_list)


class RoomStartRequest(BaseModel):
    room_id: int


class RoomStartResponse(BaseModel):
    pass


@app.post("/room/start", response_model=RoomStartResponse)
def room_start(req: RoomStartRequest):
    model.start_room(req.room_id)
    return RoomStartResponse


class RoomEndRequest(BaseModel):
    room_id: int
    judge_count_list: list[int]
    score: int


class RoomEndResponse(BaseModel):
    pass


@app.post("/room/end", response_model=RoomEndResponse)
def room_end(req: RoomEndRequest, token=Depends(get_auth_token)):
    user = get_user_by_token(token)
    model.end_room(req.room_id, req.judge_count_list, req.score, user)
    return RoomEndResponse


class RoomResultRequest(BaseModel):
    room_id: int


class RoomReultResponse(BaseModel):
    result_user_list: list[model.ResultUser]


@app.post("/room/result", response_model=RoomReultResponse)
def room_result(req: RoomResultRequest):
    result_user_list: list[ResultUser] = model.result_room(req.room_id)
    return RoomReultResponse(result_user_list=result_user_list)


class RoomLeaveRequest(BaseModel):
    room_id: int


class RoomLeaveResponse(BaseModel):
    pass


@app.post("/room/leave", respose_model=RoomLeaveResponse)
def room_leave(req: RoomLeaveRequest, token=Depends(get_auth_token)):
    user = get_user_by_token(token)
    model.leave_room(req.room_id, user)
    return RoomLeaveResponse
