import json
import uuid
from enum import Enum, IntEnum
from typing import Optional
from app.api import RoomWaitResponse

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import NoResultFound

from .db import engine


class InvalidToken(Exception):
    """指定されたtokenが不正だったときに投げる"""


class SafeUser(BaseModel):
    """token を含まないUser"""

    id: int
    name: str
    leader_card_id: int

    class Config:
        orm_mode = True


def create_user(name: str, leader_card_id: int) -> str:
    """Create new user and returns their token"""
    token = str(uuid.uuid4())
    # NOTE: tokenが衝突したらリトライする必要がある.
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "INSERT INTO `user` (name, token, leader_card_id) VALUES (:name, :token, :leader_card_id)"
            ),
            {"name": name, "token": token, "leader_card_id": leader_card_id},
        )
        # print(result)
    return token


def _get_user_by_token(conn, token: str) -> Optional[SafeUser]:
    # TODO: 実装
    result = conn.execute(
        text("SELECT `id`, `name`, `leader_card_id` FROM `user` WHERE `token`=:token"),
        dict(token=token),
    )
    try:
        row = result.one()
    except NoResultFound:
        return None
    return SafeUser.from_orm(row)


def get_user_by_token(token: str) -> Optional[SafeUser]:
    with engine.begin() as conn:
        return _get_user_by_token(conn, token)


def update_user(token: str, name: str, leader_card_id: int) -> None:
    # このコードを実装してもらう
    with engine.begin() as conn:
        # TODO: 実装
        result = conn.execute(
            text(
                "UPDATE `user` SET `name`=:name, `leader_card_id`=:leader_card_id WHERE `token`=:token"
            ),
            dict(token=token, name=name, leader_card_id=leader_card_id),
        )


# room
class LiveDifficulty(Enum):
    normal = 1
    hard = 2


def create_room(live_id: int, select_difficulty: LiveDifficulty, user: SafeUser) -> int:
    with engine.begin() as conn:
        result = conn.execute(
            text("INSERT INTO `room` (live_id) VALUES(:live_id)"),
            dict(live_id=live_id, select_difficulty=select_difficulty),
        )
        room_id = result.lastrowid
        room_user_result = conn.execute(
            text(
                "INSERT INTO `room_user` (`room_id`,`user_id`,`score`) VALUES(:room_id,:user_id,:score)"
            ),
            dict(room_id=room_id, user_id=user.id, score=None),
        )
    return room_id


class RoomInfo(BaseModel):
    room_id: int
    live_id: int
    joined_user_count: int
    max_user_count: int

    class Config:
        orm_mode = True


def list_room(live_id: int) -> list[RoomInfo]:
    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT * FROM `room` WHERE live_id=:live_id"), dict(live_id=live_id)
        )
        try:
            rows = result.all()
        except NoResultFound:
            return None
        room_list = []
        for i in range(len(rows)):
            room_list.append(RoomInfo.from_orm(rows[i]))
        return room_list


class JoinRoomResult(Enum):
    Ok = 1  # 入場Ok
    RoomFull = 2  # 満員
    Disbanded = 3  # 解散済み
    OtherError = 4  # その他エラー


def join_room(
    room_id: int, select_difficulty: LiveDifficulty, user: SafeUser
) -> JoinRoomResult:
    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT * FROM `room` WHERE room_id=:room_id"), dict(room_id=room_id)
        )
        try:
            row = result.one()
        except NoResultFound:
            return 3
        row = RoomInfo.from_orm(row)
        if row.max_user_count - row.joined_user_count >= 1:
            update_result = conn.execute(
                text(
                    "UPDATE `room` SET  `joined_user_count`=`joined_user_count`+1 WHERE `room_id`=:room_id"
                ),
                dict(room_id=room_id),
            )
            join_result = conn.execute(
                text(
                    "INSERT INTO `room_user` (`room_id`,`user_id`,`score`) VALUES(:room_id,:user_id,:score)"
                ),
                dict(room_id=room_id, user_id=user.id, score=None),
            )
            return 1
        elif row.max_user_count == row.joined_user_count:
            return 2
        else:
            return 4


class RoomUser(BaseModel):
    user_id: int
    name: str
    leader_card_id: int
    select_difficulty: LiveDifficulty
    is_me: bool
    is_host: bool

    class Config:
        orm_mode = True


class WaitRoomStatus(Enum):
    Waiting = 1
    LiveStart = 2
    Dissolution = 3


 def room_wait(room_id: int)->RoomWaitResponse:
     room_wait_result: RoomWaitResponse
     room_wait_result.response=1
     with engine.begin() as conn:
        result = conn.execute(
            text("SELECT * FROM `room` WHERE room_id=:room"), dict(room_id=room_id)
        )
        try:
            row = result.one()
        except NoResultFound:
            room_wait_result.status=3
            return room_wait_result
        row.
   return 
