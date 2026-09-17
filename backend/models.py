import uuid
from datetime import datetime, timezone
from sqlalchemy import Index, String, Integer, Float, Boolean, Text, DateTime, JSON, ForeignKey, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


def utcnow():
    return datetime.now(timezone.utc)


def new_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default="user")  # user, admin, super_admin, partenaire, presta-partenaire, etudiant
    credits: Mapped[int] = mapped_column(Integer, default=180)
    bonus_credits: Mapped[int] = mapped_column(Integer, default=0)
    purchased_credits: Mapped[int] = mapped_column(Integer, default=0)
    plan: Mapped[str] = mapped_column(String(20), default="free")
    openai_key: Mapped[str] = mapped_column(String(255), nullable=True)
    oauth_provider: Mapped[str] = mapped_column(String(20), nullable=True)
    oauth_id: Mapped[str] = mapped_column(String(255), nullable=True)
    settings: Mapped[dict] = mapped_column(JSON, default=lambda: {
        "default_mode": "fast",
        "language": "fr",
        "theme": "light",
        "notifications": True,
        "timer_alert_hours": 0
    })
    referral_code: Mapped[str] = mapped_column(String(50), nullable=True, unique=True)
    referred_by: Mapped[str] = mapped_column(String(36), nullable=True)
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    discount_type: Mapped[str] = mapped_column(String(30), nullable=True)
    discount_percent: Mapped[int] = mapped_column(Integer, default=0)
    # Annulation abonnement
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    cancellation_reason: Mapped[str] = mapped_column(String(500), nullable=True)
    discount_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    discount_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    discount_doc_url: Mapped[str] = mapped_column(String(500), nullable=True)
    partner_code: Mapped[str] = mapped_column(String(50), nullable=True)
    partner_url: Mapped[str] = mapped_column(String(500), nullable=True)
    thesustain_member: Mapped[bool] = mapped_column(Boolean, default=False)
    thesustain_type: Mapped[str] = mapped_column(String(30), nullable=True)
    # #57 — Default to '{}' string but handle NULL safely in code
    memory: Mapped[str] = mapped_column(Text, nullable=True, default="{}")
    credits_last_reset: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    workflows = relationship("Workflow", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    folders = relationship("Folder", back_populates="user", cascade="all, delete-orphan")
    owned_teams = relationship("Team", back_populates="owner", cascade="all, delete-orphan", foreign_keys="[Team.owner_id]")


class UploadedFile(Base):
    """Référence vers un fichier uploadé, stocké dans le stockage objet Emergent
    (et non sur le disque du pod). La DB est la source de vérité."""
    __tablename__ = "uploaded_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    original_name: Mapped[str] = mapped_column(String(500), nullable=True)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=True)
    size: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)



class Folder(Base):
    __tablename__ = "folders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    color: Mapped[str] = mapped_column(String(7), default="#1E3A8A")
    emoji: Mapped[str] = mapped_column(String(10), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    knowledge_notes: Mapped[str] = mapped_column(Text, nullable=True)
    ai_intro: Mapped[str] = mapped_column(Text, nullable=True)
    team_id: Mapped[str] = mapped_column(String(36), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="folders")
    conversations = relationship("Conversation", back_populates="folder")


class Conversation(Base):
    __tablename__ = "conversations"
    # FIX PERFORMANCE: Index composite (user_id, updated_at) pour accélérer
    # la requête get_conversations triée par date (ORDER BY updated_at DESC)
    __table_args__ = (
        Index("ix_conv_user_updated", "user_id", "updated_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="Nouvelle conversation")
    mode: Mapped[str] = mapped_column(String(20), default="fast")
    # #58 — Use a lambda for default to avoid SQLAlchemy mutable default bug
    messages: Mapped[list] = mapped_column(JSON, default=lambda: [])
    folder_id: Mapped[str] = mapped_column(String(36), ForeignKey("folders.id", ondelete="SET NULL"), nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    shared: Mapped[bool] = mapped_column(Boolean, default=False)
    share_id: Mapped[str] = mapped_column(String(36), nullable=True)
    manus_task_id: Mapped[str] = mapped_column(String(255), nullable=True)
    total_credits_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="conversations")
    folder = relationship("Folder", back_populates="conversations")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hourly_rate: Mapped[float] = mapped_column(Float, default=0)
    color: Mapped[str] = mapped_column(String(7), default="#1E3A8A")
    total_time_seconds: Mapped[int] = mapped_column(Integer, default=0)
    is_running: Mapped[bool] = mapped_column(Boolean, default=False)
    timer_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="projects")


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    steps: Mapped[list] = mapped_column(JSON, default=list)
    schedule: Mapped[dict] = mapped_column(JSON, nullable=True)  # {frequency, time} or string for legacy
    status: Mapped[str] = mapped_column(String(20), default="idle")
    last_run: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    result: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="workflows")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    package_id: Mapped[str] = mapped_column(String(50), nullable=True)
    amount: Mapped[float] = mapped_column(Float, default=0)
    credits: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="completed")
    mollie_payment_id: Mapped[str] = mapped_column(String(50), nullable=True)
    checkout_url: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="transactions")


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'credits' or 'discount'
    value: Mapped[int] = mapped_column(Integer, default=0)  # credits amount or discount %
    max_uses: Mapped[int] = mapped_column(Integer, default=100)
    current_uses: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PromoUsage(Base):
    __tablename__ = "promo_usages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    promo_code_id: Mapped[str] = mapped_column(String(36), ForeignKey("promo_codes.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    message_index: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback: Mapped[str] = mapped_column(String(10), nullable=False)  # 'up' or 'down'
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)



class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="general")  # general, billing, technical, feature_request
    status: Mapped[str] = mapped_column(String(20), default="open")  # open, in_progress, resolved, closed
    priority: Mapped[str] = mapped_column(String(20), default="normal")  # low, normal, high, urgent
    admin_notes: Mapped[str] = mapped_column(Text, nullable=True)
    admin_response: Mapped[str] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[str] = mapped_column(String(36), nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User")



# ==================== ÉQUIPE / TEAM ====================

class Team(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    shared_credits: Mapped[int] = mapped_column(Integer, default=0)
    plan: Mapped[str] = mapped_column(String(20), default="team")
    max_seats: Mapped[int] = mapped_column(Integer, default=10)
    chatbot_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    team_code: Mapped[str] = mapped_column(String(32), nullable=True, unique=True, index=True)
    bot_name: Mapped[str] = mapped_column(String(100), nullable=True, default="Assistant")
    bot_tone: Mapped[str] = mapped_column(String(30), nullable=True, default="professional")
    bot_context: Mapped[str] = mapped_column(Text, nullable=True, default="")
    credit_limit_per_member: Mapped[int] = mapped_column(Integer, default=50)
    auto_recharge: Mapped[bool] = mapped_column(Boolean, default=False)
    chrome_link: Mapped[bool] = mapped_column(Boolean, default=False)
    settings: Mapped[dict] = mapped_column(JSON, default=lambda: {})
    primary_color: Mapped[str] = mapped_column(String(20), nullable=True, default="#1D4E8A")
    accent_color: Mapped[str] = mapped_column(String(20), nullable=True, default="#C9A84C")
    welcome_message: Mapped[str] = mapped_column(Text, nullable=True, default="")
    footer_text: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    logo_url: Mapped[str] = mapped_column(String(500), nullable=True, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    owner = relationship("User", back_populates="owned_teams", foreign_keys=[owner_id])


class TeamMember(Base):
    __tablename__ = "team_members"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    team_id: Mapped[str] = mapped_column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="member")  # owner, admin, member
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, active, removed
    invite_token: Mapped[str] = mapped_column(String(64), nullable=True, unique=True)
    credits_allocated: Mapped[int] = mapped_column(Integer, default=0)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    team = relationship("Team", back_populates="members")



class CustomPrompt(Base):
    __tablename__ = "custom_prompts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="general")
    icon: Mapped[str] = mapped_column(String(50), default="sparkles")
    color: Mapped[str] = mapped_column(String(50), default="bg-blue-50 text-blue-600")
    action: Mapped[str] = mapped_column(String(20), default="insert")  # insert or auto_send
    plan_required: Mapped[str] = mapped_column(String(20), default="free")  # free, pro, business
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # admin-created system prompts
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)  # null for system
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)



class KnowledgeFile(Base):
    __tablename__ = "knowledge_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    team_id: Mapped[str] = mapped_column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=True)
    size: Mapped[int] = mapped_column(Integer, default=0)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="processing")  # processing, active, error
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)



class CreditLog(Base):
    __tablename__ = "credit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    team_id: Mapped[str] = mapped_column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    conversation_id: Mapped[str] = mapped_column(String(36), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[str] = mapped_column(String(30), nullable=True)  # fast, pro, agent, gemini, grok, perplexity, image
    log_type: Mapped[str] = mapped_column(String(30), nullable=False)  # chat_deduction, gift, purchase, bonus, refund, add_to_pool, owner_deduction
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ApiCost(Base):
    __tablename__ = "api_costs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    conversation_id: Mapped[str] = mapped_column(String(36), nullable=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # claude, openai, gemini, grok, perplexity, mammouth
    model: Mapped[str] = mapped_column(String(100), nullable=True)
    mode: Mapped[str] = mapped_column(String(30), nullable=True)  # fast, pro, agent, etc.
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_eur: Mapped[float] = mapped_column(Float, default=0.0)  # estimated cost in EUR
    credits_charged: Mapped[int] = mapped_column(Integer, default=0)  # credits charged to user
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    referrer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    referred_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    referred_email: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending, completed, expired
    bonus_credits: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(30), default="info")  # info, warning, success, promo
    is_global: Mapped[bool] = mapped_column(Boolean, default=False)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AiFeedback(Base):
    __tablename__ = "ai_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    conversation_id: Mapped[str] = mapped_column(String(36), nullable=True)
    message_index: Mapped[int] = mapped_column(Integer, nullable=True)
    rating: Mapped[str] = mapped_column(String(10), nullable=False)  # up, down
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    mode: Mapped[str] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EmailLog(Base):
    __tablename__ = "email_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=True)
    template: Mapped[str] = mapped_column(String(100), nullable=True)  # welcome, invite, reset, etc.
    status: Mapped[str] = mapped_column(String(30), default="sent")  # sent, failed, bounced
    error: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AdminLog(Base):
    __tablename__ = "admin_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    admin_email: Mapped[str] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=True)  # user, promo, setting
    target_id: Mapped[str] = mapped_column(String(36), nullable=True)
    details: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)



class PlatformSetting(Base):
    __tablename__ = "platform_settings"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="{}")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ShopWaitlist(Base):
    __tablename__ = "shop_waitlist"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    discount_optin: Mapped[bool] = mapped_column(Boolean, default=True)
    locale: Mapped[str] = mapped_column(String(10), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(60), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AdminReminder(Base):
    """Relance admin (manuelle ou planifiée) à envoyer à un user ou cohorte."""
    __tablename__ = "admin_reminders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    type: Mapped[str] = mapped_column(String(50), default="email")      # email | sms | whatsapp
    target_email: Mapped[str] = mapped_column(String(255), nullable=True)
    target_user_id: Mapped[str] = mapped_column(String(36), nullable=True)
    target_cohort: Mapped[str] = mapped_column(String(50), nullable=True)  # ex: "free_users_30d"
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=False)
    brand: Mapped[str] = mapped_column(String(20), default="myextension")
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | sent | failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EmailCampaign(Base):
    """Welcome Blast & autres campagnes mass-mail."""
    __tablename__ = "email_campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(50), default="welcome_blast")
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=False)
    brand: Mapped[str] = mapped_column(String(20), default="zayado")
    filter_json: Mapped[str] = mapped_column(Text, nullable=True)  # JSON: cohort filter
    total_targets: Mapped[int] = mapped_column(Integer, default=0)
    total_sent: Mapped[int] = mapped_column(Integer, default=0)
    total_failed: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft | running | done | failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class BroadcastNotification(Base):
    """Notifications broadcast affichées en modal (app) ou bandeau (boutique).
    L'admin crée + active, l'utilisateur la voit au prochain chargement (1x via localStorage).
    Distinct du modèle Notification (notifications per-user pour le centre de notif).
    """
    __tablename__ = "broadcast_notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=True)
    embed_url: Mapped[str] = mapped_column(Text, nullable=True)        # iframe URL (Canva, etc.)
    cta_label: Mapped[str] = mapped_column(String(80), nullable=True)
    cta_url: Mapped[str] = mapped_column(String(500), nullable=True)
    surface: Mapped[str] = mapped_column(String(20), default="app_modal")  # app_modal | shop_banner | shop_modal
    audience: Mapped[str] = mapped_column(String(30), default="all")       # all | logged | guests | shop_visitors
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)



# ── Features: Captures, Priority, Energy, Focus, Structuration ──

class Capture(Base):
    __tablename__ = "captures"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(30), default="idee")
    source: Mapped[str] = mapped_column(String(30), default="text")
    status: Mapped[str] = mapped_column(String(30), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UserPriority(Base):
    __tablename__ = "user_priorities"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    why: Mapped[str] = mapped_column(Text, nullable=True)
    estimated_time: Mapped[str] = mapped_column(String(50), default="2h")
    date: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UserEnergy(Base):
    __tablename__ = "user_energy"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=True)
    date: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UserFocusSession(Base):
    __tablename__ = "user_focus_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task: Mapped[str] = mapped_column(String(500), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UserStructuration(Base):
    __tablename__ = "user_structuration"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    pillar: Mapped[str] = mapped_column(String(50), nullable=False)
    action_index: Mapped[int] = mapped_column(Integer, nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DiagnosticResult(Base):
    __tablename__ = "diagnostic_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    answers: Mapped[str] = mapped_column(Text, nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    clarity: Mapped[int] = mapped_column(Integer, default=0)
    energy: Mapped[int] = mapped_column(Integer, default=0)
    alignment: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UserOnboarding(Base):
    __tablename__ = "user_onboarding"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=True)
    sector: Mapped[str] = mapped_column(String(100), nullable=True)
    objective: Mapped[str] = mapped_column(String(255), nullable=True)
    challenge: Mapped[str] = mapped_column(String(255), nullable=True)
    budget: Mapped[str] = mapped_column(String(50), nullable=True)
    experience: Mapped[str] = mapped_column(String(50), nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UserData(Base):
    """Generic key-value store per user for activity data."""
    __tablename__ = "user_data"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, default="{}")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)



class VectorMemory(Base):
    """Vector memory for AI Agent — stores embeddings for semantic search."""
    __tablename__ = "vector_memories"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array of floats
    source: Mapped[str] = mapped_column(String(50), default="manual")  # manual, conversation, document, agent
    source_id: Mapped[str] = mapped_column(String(36), nullable=True)  # conversation_id or document reference
    category: Mapped[str] = mapped_column(String(50), default="general")  # general, preference, fact, instruction, context
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")  # extra metadata as JSON
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)



class License(Base):
    __tablename__ = "licenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    plan_type: Mapped[str] = mapped_column(String(50), nullable=False)  # chatbot_starter, chatbot_pro, chatbot_lifetime, pilote_chatbot_lifetime
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, used, revoked, expired
    activated_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    activated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    team_id: Mapped[str] = mapped_column(String(36), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    max_chatbots: Mapped[int] = mapped_column(Integer, default=1)
    monthly_credits: Mapped[int] = mapped_column(Integer, default=1000)
    is_lifetime: Mapped[bool] = mapped_column(Boolean, default=False)
    is_downloadable: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)



# ── Affiliate / Reseller System (Dokan-style) ──

class AffiliateCommission(Base):
    __tablename__ = "affiliate_commissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    affiliate_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    transaction_id: Mapped[str] = mapped_column(String(36), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)
    sale_amount: Mapped[float] = mapped_column(Float, default=0.0)
    commission_rate: Mapped[float] = mapped_column(Float, default=0.0)  # 0.10 = 10%
    commission_amount: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending, approved, paid, rejected
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AffiliatePayout(Base):
    __tablename__ = "affiliate_payouts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    affiliate_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    method: Mapped[str] = mapped_column(String(50), default="bank_transfer")  # bank_transfer, paypal, credits
    reference: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending, processing, completed, failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)



class CustomAgent(Base):
    __tablename__ = "custom_agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    avatar: Mapped[str] = mapped_column(String(10), nullable=True, default="bot")
    color: Mapped[str] = mapped_column(String(7), default="#1D4E8A")
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="Tu es un assistant IA utile.")
    tools: Mapped[list] = mapped_column(JSON, default=list)
    model_preference: Mapped[str] = mapped_column(String(50), default="auto")
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    deployed_channels: Mapped[list] = mapped_column(JSON, default=list)  # ["web", "telegram", "whatsapp", "discord"]
    webhook_token: Mapped[str] = mapped_column(String(64), nullable=True)  # Unique token for external channel webhooks
    use_user_memory: Mapped[bool] = mapped_column(Boolean, default=True)  # toggle mémoire longue durée
    team_id: Mapped[str] = mapped_column(String(36), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("custom_agents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Identifiant du client externe (numéro WhatsApp, chat_id Telegram, session_id widget web).
    # NULL = conversation de test du propriétaire dans l'app (comportement historique).
    contact: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    # Canal d'origine du message : "whatsapp" | "whatsapp_web" | "telegram" | "web" | "test"
    channel: Mapped[str] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class FinanceEntryDB(Base):
    __tablename__ = "finance_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # "revenu" | "depense"
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="autre")
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)   # ex: "hash:abc123" pour déduplication CSV
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class BudgetGoalDB(Base):
    __tablename__ = "budget_goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    period: Mapped[str] = mapped_column(String(20), default="mois")


class WellnessCheckin(Base):
    __tablename__ = "wellness_checkins"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    energy: Mapped[int] = mapped_column(Integer, nullable=False)       # 1-5
    mood: Mapped[int] = mapped_column(Integer, nullable=False)         # 1-5
    stress: Mapped[int] = mapped_column(Integer, nullable=False)       # 1-5
    sleep: Mapped[int] = mapped_column(Integer, nullable=False)        # 1-5
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    score: Mapped[int] = mapped_column(Integer, nullable=True)         # 0-100 computed
    ai_insight: Mapped[str] = mapped_column(Text, nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)



# ── Application Logs (monitoring par fonctionnalité) ──────────────

class AppLog(Base):
    """Logs applicatifs détaillés par fonctionnalité — pour le monitoring admin."""
    __tablename__ = "app_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    level: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # INFO, WARNING, ERROR, CRITICAL
    feature: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # chat, auth, payment, extension, affiliate, admin, agent, oauth
    action: Mapped[str] = mapped_column(String(100), nullable=True)  # ex: "chat_request", "login_failed", "payment_webhook"
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_email: Mapped[str] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=True)  # JSON avec contexte complet
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=True)  # durée de l'opération en ms
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class UserConnection(Base):
    """Secure service connections for agents & workflows (Brevo, Gmail, SMTP, etc.)."""
    __tablename__ = "user_connections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # brevo, gmail, smtp, whatsapp, telegram, ovh
    label: Mapped[str] = mapped_column(String(255), nullable=True)  # user-defined label
    credentials: Mapped[str] = mapped_column(Text, nullable=False, default="{}")  # JSON encrypted credentials
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_token: Mapped[str] = mapped_column(String(100), nullable=True)
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class RailwayProject(Base):
    """Suivi des projets Railway créés pour chaque client."""
    __tablename__ = "railway_projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    railway_project_id: Mapped[str] = mapped_column(String(100), nullable=True)
    railway_url: Mapped[str] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending | deploying | active | error
    plan: Mapped[str] = mapped_column(String(30), nullable=True)        # pro | business
    agent_name: Mapped[str] = mapped_column(String(100), nullable=True)
    monthly_cost: Mapped[float] = mapped_column(Float, default=5.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class IncomingNewsletter(Base):
    """Newsletter externe reçue via Brevo Inbound Parse (email vers newsletter@inbox.zayado.net)."""
    __tablename__ = "incoming_newsletters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    sender_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sender_name: Mapped[str] = mapped_column(String(255), nullable=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=True)
    received_to: Mapped[str] = mapped_column(String(255), nullable=True)   # inbox alias
    html_body: Mapped[str] = mapped_column(Text, nullable=True)
    text_body: Mapped[str] = mapped_column(Text, nullable=True)
    raw_headers: Mapped[str] = mapped_column(Text, nullable=True)          # JSON
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    # Processing
    status: Mapped[str] = mapped_column(String(30), default="received")   # received | processing | prepared | failed | archived
    error: Mapped[str] = mapped_column(Text, nullable=True)


class PreparedNewsletter(Base):
    """Version reformulée (ton Zayado + niche TPE/indépendants) d'une newsletter entrante."""
    __tablename__ = "prepared_newsletters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    incoming_id: Mapped[str] = mapped_column(String(36), ForeignKey("incoming_newsletters.id", ondelete="CASCADE"), nullable=False, index=True)
    # Source (dénormalisée pour affichage rapide sans jointure)
    source_subject: Mapped[str] = mapped_column(String(500), nullable=True)
    source_sender: Mapped[str] = mapped_column(String(255), nullable=True)
    # Version reformulée
    rewritten_subject: Mapped[str] = mapped_column(String(500), nullable=True)
    rewritten_html: Mapped[str] = mapped_column(Text, nullable=True)
    rewritten_text: Mapped[str] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)              # 2-3 lignes pour la vue liste
    # Workflow
    status: Mapped[str] = mapped_column(String(30), default="draft")       # draft | validated | pushed_to_brevo | sent | rejected
    brevo_draft_id: Mapped[str] = mapped_column(String(100), nullable=True)
    reviewed_by: Mapped[str] = mapped_column(String(36), nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ── Ajouté automatiquement : modèles module Simulation (ticket Simulation Client) ──
# ══════════════════════════════════════════════════════════════════
# À COPIER-COLLER À LA FIN DE backend/models.py (ne PAS remplacer le
# fichier existant — ceci est un ajout, pas un fichier autonome).
# Aucune migration Alembic nécessaire : les tables sont créées
# automatiquement au démarrage via Base.metadata.create_all
# (même mécanisme que toutes les autres tables du fichier).
# ══════════════════════════════════════════════════════════════════


class SimuProfile(Base):
    """Profil pédagogique de l'utilisateur pour le module Simulation.

    Volontairement séparé de `users` (pas de nouvelle colonne sur User) :
    un user peut ne jamais toucher au module, ou changer de programme
    en cours de route sans qu'on touche au schéma central.
    """
    __tablename__ = "simu_profile"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    programme_label: Mapped[str] = mapped_column(String(255), nullable=False)   # texte libre : "Master 2 Marketing Digital", "Licence Pro RH"…
    diploma_level: Mapped[str] = mapped_column(String(30), default="master")     # licence | licence_pro | bachelor | master | mba
    domain: Mapped[str] = mapped_column(String(100), nullable=True)              # déduit par l'IA au 1er lancement : "finance", "marketing"…
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    average_score: Mapped[float] = mapped_column(Float, default=0.0)
    current_day: Mapped[int] = mapped_column(Integer, default=1)                 # sert à calculer l'escalade de difficulté
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SimuClient(Base):
    """Client virtuel généré par l'IA pour un utilisateur."""
    __tablename__ = "simu_client"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    company_size: Mapped[str] = mapped_column(String(20), default="small")       # small | mid | large
    personality: Mapped[str] = mapped_column(String(30), default="collaborative")  # demanding | collaborative | difficult | urgent
    budget: Mapped[int] = mapped_column(Integer, default=10000)
    initial_problem: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SimuTask(Base):
    """Tâche/demande envoyée par un client virtuel."""
    __tablename__ = "simu_task"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("simu_client.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)                  # 1 à 5, escalade avec current_day
    key_points: Mapped[dict] = mapped_column(JSON, default=list)                 # points attendus, utilisés pour l'évaluation
    rubric: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="pending")           # pending | submitted | reviewed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SimuResponse(Base):
    """Réponse de l'utilisateur à une tâche + feedback IA."""
    __tablename__ = "simu_response"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("simu_task.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=True)                   # 0-10
    ai_feedback: Mapped[dict] = mapped_column(JSON, default=dict)                # {comments, what_went_well, improvements_needed, learning_point, client_reaction}
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class VisionCard(Base):
    """Carte unifiée du Vision Board (backlog #1). Une ligne = une carte posée sur le
    canvas. Si entity_type/entity_id sont renseignés, la carte est "intelligente" :
    sa valeur est résolue en direct depuis la table source (routes/vision_cards.py::
    resolve_card) à chaque lecture — cache_* n'est qu'un fallback si l'entité a été
    supprimée, jamais la source de vérité."""
    __tablename__ = "vision_cards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    board_id: Mapped[str] = mapped_column(String(50), default="main", index=True)
    card_type: Mapped[str] = mapped_column(String(30), default="postit")         # postit, ca, impact, client, image, shape...
    entity_type: Mapped[str] = mapped_column(String(30), nullable=True)          # aggregate, finance_entry, budget_goal, lead, project, ou None (carte libre)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=True)
    manual_content: Mapped[str] = mapped_column(Text, nullable=True)
    x: Mapped[float] = mapped_column(Float, default=40)
    y: Mapped[float] = mapped_column(Float, default=40)
    width: Mapped[float] = mapped_column(Float, default=220)
    height: Mapped[float] = mapped_column(Float, default=140)
    rotation: Mapped[float] = mapped_column(Float, default=0)
    z: Mapped[int] = mapped_column(Integer, default=0)
    style: Mapped[dict] = mapped_column(JSON, default=dict)
    connections: Mapped[list] = mapped_column(JSON, default=list)
    # Cache de fallback (best-effort), utilisé uniquement si l'entité source est introuvable
    cache_label: Mapped[str] = mapped_column(String(300), nullable=True)
    cache_value: Mapped[str] = mapped_column(String(300), nullable=True)
    cache_progress: Mapped[float] = mapped_column(Float, nullable=True)
    cache_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class VisionBoardSnapshot(Base):
    """Version sauvegardée du board (backlog #22 — historique/versioning).
    Un snapshot = une copie figée de toutes les VisionCard d'un board à un
    instant T (JSON), restaurable. Volontairement manuel (bouton "Sauvegarder
    une version"), pas d'auto-snapshot périodique pour ce premier jet — évite
    d'accumuler des versions sans valeur entre deux sauvegardes explicites."""
    __tablename__ = "vision_board_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    board_id: Mapped[str] = mapped_column(String(50), default="main", index=True)
    label: Mapped[str] = mapped_column(String(200), nullable=True)
    cards_json: Mapped[list] = mapped_column(JSON, default=list)  # copie des champs persistables de chaque VisionCard
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class VisionScoreSnapshot(Base):
    """Point d'historique du Score Business (backlog #21 — KPI Vision :
    graphes + prévisions). Alimenté par routes/vision_brain.py::get_panel,
    au maximum 1 point par jour et par utilisateur — remplace le simple
    "score précédent" (vision_brain_score_prev, un seul point) par une
    vraie série temporelle exploitable pour un graphe."""
    __tablename__ = "vision_score_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    pillars: Mapped[dict] = mapped_column(JSON, default=dict)  # {vision, execution, finance, impact, energie, croissance}
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AnalyticsEvent(Base):
    """Événement produit (backlog #16 — métriques activation & rétention).
    Choix technique : table interne plutôt qu'un outil tiers (Mixpanel/
    PostHog) — aucun compte/clé externe à obtenir pour commencer à avoir
    de vrais chiffres, migrable plus tard si un outil dédié est voulu.
    `event_name` est un petit vocabulaire fixe (voir routes/analytics.py::
    EVENT_NAMES) pour que les agrégations restent fiables — pas de texte
    libre qui fragmenterait les stats en variantes orthographiques."""
    __tablename__ = "analytics_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_name: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    properties: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
