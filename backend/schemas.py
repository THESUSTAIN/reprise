from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime


class UserCreateSchema(BaseModel):
    email: EmailStr
    password: str
    name: str
    ref: Optional[str] = None

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    credits: int
    bonus_credits: int = 0
    purchased_credits: int = 0
    plan: str
    openai_api_key: Optional[str] = Field(None, exclude=True)  # fix #32 — never expose in response
    created_at: datetime
    discount_type: Optional[str] = None
    discount_percent: int = 0
    discount_verified: bool = False
    partner_code: Optional[str] = None
    partner_url: Optional[str] = None
    memory: Optional[str] = None
    referral_code: Optional[str] = None
    settings: Optional[dict] = None
    cancel_at_period_end: bool = False
    thesustain_member: bool = False
    thesustain_type: Optional[str] = None
    two_factor_enabled: bool = False
    is_active: bool = True
    credits_last_reset: Optional[datetime] = None
    credits_per_month: int = 0
    onboarding_done: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class ChatRequest(BaseModel):
    message: str
    mode: str = "fast"
    conversation_id: Optional[str] = None
    openai_key: Optional[str] = None
    file_ids: Optional[List[str]] = None
    image_model: Optional[str] = None
    image_b64: Optional[str] = None
    image_mime: Optional[str] = None
    screenshot_b64: Optional[str] = None

class ConversationResponse(BaseModel):
    id: str
    title: str
    mode: str
    created_at: datetime
    updated_at: datetime

class ProjectCreateSchema(BaseModel):
    name: str
    hourly_rate: float = 0
    color: str = "#1E3A8A"

class ProjectResponse(BaseModel):
    id: str
    name: str
    hourly_rate: float
    color: str
    total_time_seconds: int
    total_cost: float
    is_running: bool
    timer_started_at: Optional[datetime]
    created_at: datetime

class WorkflowCreateSchema(BaseModel):
    name: str
    description: Optional[str] = ""
    steps: Optional[List[Dict[str, Any]]] = []
    schedule: Optional[Any] = None  # Can be string or object {frequency, time}
    status: Optional[str] = None

class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]
    schedule: Optional[Any] = None  # Can be string or object {frequency, time}
    status: str
    result: Optional[Any] = None
    last_run: Optional[datetime] = None
    created_at: datetime

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class AgentEstimateRequest(BaseModel):
    task: str
    task_type: Optional[str] = None

class AgentRunRequest(BaseModel):
    task: str
    task_type: Optional[str] = None
    conversation_id: Optional[str] = None

class OAuthLoginRequest(BaseModel):
    token: Optional[str] = None
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    provider: str = "google"
