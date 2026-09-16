from datetime import timedelta, datetime

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from starlette import status

from app.config.settings import settings
from app.database.mysql import get_db
from app.models.user import User
from app.schemas.user import TokenData, UserResponse, UserCreate, Token

# 创建路由实例
router = APIRouter()

# 令牌获取方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    truncated_password = plain_password[:72]

    return bcrypt.checkpw(truncated_password.encode('utf-8'),hashed_password.encode('utf-8') )

def get_password_hash(password: str) -> str:
    """获取密码哈希值"""
    truncated_password = password[:72]

    salt = bcrypt.gensalt()

    hashed = bcrypt.hashpw(truncated_password.encode('utf-8'), salt)

    return hashed.decode('utf-8')

def authenticate_user(db:Session,username:str,password:str):
    """认证用户"""
    #从数据库查询
    user = db.query(User).filter(User.username == username).first()

    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

def create_access_token(data:dict,expires_delta:timedelta | None = None):
    """创建访问令牌"""
    to_encode = data.copy()
    # 如果设置了过期时间差
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # 将过期时间添加到要编写的数据中
    to_encode.update({"exp":expire})
    encode_jwt = jwt.encode(to_encode,settings.SECRET_KEY,algorithm=settings.ALGORITHM)
    return encode_jwt


async def get_current_user(token:str = Depends(oauth2_scheme),db:Session = Depends(get_db)):
    """获取当前用户：从 token 中解析用户信息并返回用户对象"""
    # 定义认证异常
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 解码 JWT token，验证签名和过期时间
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub: str = payload.get("sub")
        if sub is None:
            raise credentials_exception
        # 将sub字符串转为数字user_id
        user_id = int(sub)
    # 同时捕获JWT解析异常 + 字符串转int失败异常
    except (JWTError, ValueError):
        raise credentials_exception
    # 根据id查询用户
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


@router.post("/register", response_model=UserResponse)
def register(user:UserCreate,db:Session = Depends(get_db)):
    """用户注册:创建新用户账号"""
    # 检查用户名和邮箱名是否已经存在
    existing_user = db.query(User).filter((User.username == user.username) | (User.email == user.email)).first()

    #如果用户已经存在
    if existing_user:
        if existing_user.username == user.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )

    # 对用户密码进行哈希加密
    hashed_password = get_password_hash(user.password)

    # 创建用户ORM对象
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
    )

    # 将用户对象添加到数据库会话
    db.add(db_user)
    # 提交事务，保存到数据库
    db.commit()
    # 刷新用户对象，获取数据库生成的字段（如 id、created_at）
    db.refresh(db_user)
    # 返回创建成功的用户对象
    return db_user

@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(),db:Session = Depends(get_db)):
    """用户登录：访问获取令牌"""
    user = authenticate_user(db,form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # ==========修改这里，sub存user.id，转字符串==========
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}
