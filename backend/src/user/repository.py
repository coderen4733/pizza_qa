from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.user.enums import UserRole
from src.user.models import User

#  * 정렬 기준 이름 -> 실제 DB 컬럼 연결표
#  - 요청으로 받은 정렬 기준(문자열)을 실제 컬럼으로 바꿀 때 사용
#    => 이 표에 없는 컬럼으로는 정렬할 수 없음 (schemas.py의 Literal과 이중으로 막음)
SORTABLE_COLUMNS = {
    "created_at": User.created_at,
    "updated_at": User.updated_at,
    "email": User.email,
    "id": User.id,
}


# 사용자(User) 생성(C) API
async def create_user(
    session: AsyncSession,
    user: User,
) -> User:
    # 1. Repository -> DB
    # 1-1. add
    session.add(user)
    # 1-2. flush
    await session.flush()
    # 2. user 객체 갱신
    await session.refresh(user)
    # 3. Repository -> Service
    return user


# 사용자(User) 조회(R-D) API (by email)
async def get_user_by_email(
    session: AsyncSession,
    email: str,
) -> User | None:
    # 1. Repository <- DB
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    # 2. Repository -> Service
    data = result.scalar_one_or_none()  # 하나만 가져오되 없으면 None 반환
    return data


# 사용자(User) 조회(R-D) API (by id) - 토큰재발급용
async def get_user_by_id(
    session: AsyncSession,
    user_id: int,
) -> User | None:
    # 1. Repository <- DB
    data = await session.get(User, user_id)  # PK값은 session.get()으로 조회 가능
    # 2. Repository -> Service
    return data


# 사용자(User) 수정(U) API
async def update_user(
    session: AsyncSession,
    user: User,
) -> User:
    # 1. Repository -> DB
    await session.flush()
    # 2. user 객체 갱신
    await session.refresh(user)
    # 3. Repository -> Service
    return user


# 사용자(User) 목록 조회(R-L) API
async def get_users_list(
    session: AsyncSession,
    *,
    is_active: bool | None,
    role: UserRole | None,
    email: str | None,
    sort_by: str,
    order: str,
    offset: int,
    limit: int,
) -> tuple[list[User], int]:
    # 1. Filter Conditions
    conditions = []
    if is_active is not None:
        # is_active는 False도 "값이 있는 것"이므로 "is not None"으로 검사해야 함
        # (if is_active: 로 쓰면 False일 때 조건이 빠지는 버그가 생김)
        conditions.append(User.is_active == is_active)
    if role is not None:
        conditions.append(User.role == role)
    if email:
        # icontains: 대소문자 구분 없이 "포함" 검색 (SQL: email ILIKE '%kim%')
        # autoescape=True: 검색어의 %, _ 를 "특수 기호"가 아니라 "그냥 글자"로 취급
        #  => 검색어로 "%"를 보내서 모든 email이 검색되는 문제를 막음
        conditions.append(User.email.icontains(email, autoescape=True))

    # 2. Repository <- DB : 전체 개수 조회 (페이지와 상관없이 조건에 맞는 사용자 수)
    #  - where(*conditions): 리스트 안의 조건들을 모두 AND로 연결 (조건이 없으면 WHERE 없음)
    count_query = select(func.count()).select_from(User).where(*conditions)
    total = await session.scalar(count_query) or 0

    # 3. Sort & Order By
    sort_column = SORTABLE_COLUMNS[sort_by]
    if order == "desc":
        order_by = [sort_column.desc(), User.id.desc()]
    else:
        order_by = [sort_column.asc(), User.id.asc()]

    # 4. Repository <- DB : 현재 페이지의 사용자 목록 조회
    #  - offset: 앞에서부터 건너뛸 개수 / limit: 가져올 최대 개수
    #    예) 20명씩 3페이지 => offset=40, limit=20 => 41번째~60번째 사용자
    query = select(User).where(*conditions).order_by(*order_by).offset(offset).limit(limit)
    result = await session.execute(query)
    users = list(result.scalars().all())

    # 5. Repository -> Service
    return users, total
