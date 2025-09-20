from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from decimal import Decimal


# Enums for type safety
class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    NARRATOR = "narrator"


class PromptTriggerType(str, Enum):
    TIME_INTERVAL = "time_interval"
    MESSAGE_COUNT = "message_count"
    CONTEXT_CHANGE = "context_change"
    MANUAL = "manual"


class ImageGenerationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    CUSTOM = "custom"


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


# Core Character Management
class Character(SQLModel, table=True):
    __tablename__ = "characters"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200)
    description: str = Field(default="", max_length=2000)
    personality_traits: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    background: str = Field(default="", max_length=5000)
    behavioral_parameters: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    example_dialogues: List[str] = Field(default=[], sa_column=Column(JSON))
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    is_template: bool = Field(default=False)
    template_category: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    conversations: List["Conversation"] = Relationship(back_populates="character")
    character_states: List["CharacterState"] = Relationship(back_populates="character")


class Scenario(SQLModel, table=True):
    __tablename__ = "scenarios"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200)
    description: str = Field(default="", max_length=2000)
    environment_description: str = Field(default="", max_length=5000)
    context_rules: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    interaction_constraints: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    initial_state: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    is_template: bool = Field(default=False)
    template_category: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    conversations: List["Conversation"] = Relationship(back_populates="scenario")


# Conversation Management
class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=300)
    character_id: int = Field(foreign_key="characters.id")
    scenario_id: Optional[int] = Field(default=None, foreign_key="scenarios.id")
    status: ConversationStatus = Field(default=ConversationStatus.ACTIVE)
    system_prompt_config: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    custom_settings: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    character: Character = Relationship(back_populates="conversations")
    scenario: Optional[Scenario] = Relationship(back_populates="conversations")
    messages: List["Message"] = Relationship(back_populates="conversation")
    character_states: List["CharacterState"] = Relationship(back_populates="conversation")
    image_generations: List["ImageGeneration"] = Relationship(back_populates="conversation")


class Message(SQLModel, table=True):
    __tablename__ = "messages"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversations.id")
    role: MessageRole
    content: str = Field(max_length=10000)
    message_metadata: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    is_edited: bool = Field(default=False)
    original_content: Optional[str] = Field(default=None, max_length=10000)
    is_temporary: bool = Field(default=False)  # For prompt injections
    order_index: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    conversation: Conversation = Relationship(back_populates="messages")


# Prompt Engineering System
class PromptTemplate(SQLModel, table=True):
    __tablename__ = "prompt_templates"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200)
    description: str = Field(default="", max_length=1000)
    template_content: str = Field(max_length=5000)
    variables: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    conditions: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    category: str = Field(default="general", max_length=100)
    is_system: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    prompt_injections: List["PromptInjection"] = Relationship(back_populates="prompt_template")


class PromptInjection(SQLModel, table=True):
    __tablename__ = "prompt_injections"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200)
    prompt_template_id: int = Field(foreign_key="prompt_templates.id")
    trigger_type: PromptTriggerType
    trigger_config: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    frequency: int = Field(default=1)  # How often to trigger
    is_active: bool = Field(default=True)
    priority: int = Field(default=0)  # Higher numbers = higher priority
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    prompt_template: PromptTemplate = Relationship(back_populates="prompt_injections")
    injection_executions: List["PromptInjectionExecution"] = Relationship(back_populates="prompt_injection")


class PromptInjectionExecution(SQLModel, table=True):
    __tablename__ = "prompt_injection_executions"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    prompt_injection_id: int = Field(foreign_key="prompt_injections.id")
    conversation_id: int = Field(foreign_key="conversations.id")
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    result_content: str = Field(max_length=10000)
    variables_used: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    success: bool = Field(default=True)
    error_message: Optional[str] = Field(default=None, max_length=1000)

    # Relationships
    prompt_injection: PromptInjection = Relationship(back_populates="injection_executions")


# State Management
class CharacterState(SQLModel, table=True):
    __tablename__ = "character_states"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key="characters.id")
    conversation_id: int = Field(foreign_key="conversations.id")
    mood: str = Field(default="neutral", max_length=100)
    relationship_status: str = Field(default="neutral", max_length=100)
    feelings: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    custom_attributes: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    energy_level: Decimal = Field(default=Decimal("5.0"), max_digits=3, decimal_places=1)
    stress_level: Decimal = Field(default=Decimal("0.0"), max_digits=3, decimal_places=1)
    is_current: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    character: Character = Relationship(back_populates="character_states")
    conversation: Conversation = Relationship(back_populates="character_states")


class StateField(SQLModel, table=True):
    __tablename__ = "state_fields"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    field_type: str = Field(max_length=50)  # text, number, boolean, json, etc.
    description: str = Field(default="", max_length=500)
    default_value: str = Field(default="", max_length=1000)
    validation_rules: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    is_system: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Image Generation Integration
class ComfyUIWorkflow(SQLModel, table=True):
    __tablename__ = "comfyui_workflows"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200)
    description: str = Field(default="", max_length=1000)
    workflow_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    template_type: str = Field(default="general", max_length=100)
    artistic_style: str = Field(default="realistic", max_length=100)
    prompt_injection_points: List[str] = Field(default=[], sa_column=Column(JSON))
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    image_generations: List["ImageGeneration"] = Relationship(back_populates="workflow")


class ImageGeneration(SQLModel, table=True):
    __tablename__ = "image_generations"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversations.id")
    workflow_id: int = Field(foreign_key="comfyui_workflows.id")
    scene_description: str = Field(max_length=2000)
    generated_prompt: str = Field(max_length=5000)
    status: ImageGenerationStatus = Field(default=ImageGenerationStatus.PENDING)
    image_url: Optional[str] = Field(default=None, max_length=500)
    comfyui_job_id: Optional[str] = Field(default=None, max_length=200)
    generation_params: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    error_message: Optional[str] = Field(default=None, max_length=1000)
    processing_time_seconds: Optional[Decimal] = Field(default=None, max_digits=8, decimal_places=2)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    # Relationships
    conversation: Conversation = Relationship(back_populates="image_generations")
    workflow: ComfyUIWorkflow = Relationship(back_populates="image_generations")


# Model Management
class AIModel(SQLModel, table=True):
    __tablename__ = "ai_models"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200)
    provider: ModelProvider
    model_id: str = Field(max_length=200)  # e.g., "gpt-4", "claude-3-opus"
    api_endpoint: Optional[str] = Field(default=None, max_length=500)
    api_key_name: Optional[str] = Field(default=None, max_length=100)  # Environment variable name
    configuration: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    capabilities: List[str] = Field(default=[], sa_column=Column(JSON))
    max_tokens: Optional[int] = Field(default=None)
    cost_per_token_input: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=8)
    cost_per_token_output: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=8)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    model_presets: List["ModelPreset"] = Relationship(back_populates="ai_model")
    conversation_sessions: List["ConversationSession"] = Relationship(back_populates="ai_model")


class ModelPreset(SQLModel, table=True):
    __tablename__ = "model_presets"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200)
    ai_model_id: int = Field(foreign_key="ai_models.id")
    temperature: Decimal = Field(default=Decimal("0.7"), max_digits=3, decimal_places=2)
    top_p: Decimal = Field(default=Decimal("1.0"), max_digits=3, decimal_places=2)
    frequency_penalty: Decimal = Field(default=Decimal("0.0"), max_digits=3, decimal_places=2)
    presence_penalty: Decimal = Field(default=Decimal("0.0"), max_digits=3, decimal_places=2)
    max_tokens: Optional[int] = Field(default=None)
    custom_parameters: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    is_default: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    ai_model: AIModel = Relationship(back_populates="model_presets")


class ConversationSession(SQLModel, table=True):
    __tablename__ = "conversation_sessions"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversations.id")
    ai_model_id: int = Field(foreign_key="ai_models.id")
    session_start: datetime = Field(default_factory=datetime.utcnow)
    session_end: Optional[datetime] = Field(default=None)
    total_tokens_used: int = Field(default=0)
    total_cost: Decimal = Field(default=Decimal("0.00"), max_digits=10, decimal_places=4)
    message_count: int = Field(default=0)
    performance_metrics: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Relationships
    ai_model: AIModel = Relationship(back_populates="conversation_sessions")


# Non-persistent schemas for validation and API
class CharacterCreate(SQLModel, table=False):
    name: str = Field(max_length=200)
    description: str = Field(default="", max_length=2000)
    personality_traits: Dict[str, Any] = Field(default={})
    background: str = Field(default="", max_length=5000)
    behavioral_parameters: Dict[str, Any] = Field(default={})
    example_dialogues: List[str] = Field(default=[])
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    is_template: bool = Field(default=False)
    template_category: Optional[str] = Field(default=None, max_length=100)


class CharacterUpdate(SQLModel, table=False):
    name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    personality_traits: Optional[Dict[str, Any]] = Field(default=None)
    background: Optional[str] = Field(default=None, max_length=5000)
    behavioral_parameters: Optional[Dict[str, Any]] = Field(default=None)
    example_dialogues: Optional[List[str]] = Field(default=None)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    is_template: Optional[bool] = Field(default=None)
    template_category: Optional[str] = Field(default=None, max_length=100)


class ScenarioCreate(SQLModel, table=False):
    name: str = Field(max_length=200)
    description: str = Field(default="", max_length=2000)
    environment_description: str = Field(default="", max_length=5000)
    context_rules: Dict[str, Any] = Field(default={})
    interaction_constraints: Dict[str, Any] = Field(default={})
    initial_state: Dict[str, Any] = Field(default={})
    is_template: bool = Field(default=False)
    template_category: Optional[str] = Field(default=None, max_length=100)


class ConversationCreate(SQLModel, table=False):
    title: str = Field(max_length=300)
    character_id: int
    scenario_id: Optional[int] = Field(default=None)
    system_prompt_config: Dict[str, Any] = Field(default={})
    custom_settings: Dict[str, Any] = Field(default={})


class MessageCreate(SQLModel, table=False):
    conversation_id: int
    role: MessageRole
    content: str = Field(max_length=10000)
    message_metadata: Dict[str, Any] = Field(default={})
    is_temporary: bool = Field(default=False)


class MessageUpdate(SQLModel, table=False):
    content: Optional[str] = Field(default=None, max_length=10000)
    message_metadata: Optional[Dict[str, Any]] = Field(default=None)


class CharacterStateUpdate(SQLModel, table=False):
    mood: Optional[str] = Field(default=None, max_length=100)
    relationship_status: Optional[str] = Field(default=None, max_length=100)
    feelings: Optional[Dict[str, Any]] = Field(default=None)
    custom_attributes: Optional[Dict[str, Any]] = Field(default=None)
    energy_level: Optional[Decimal] = Field(default=None, max_digits=3, decimal_places=1)
    stress_level: Optional[Decimal] = Field(default=None, max_digits=3, decimal_places=1)


class ImageGenerationRequest(SQLModel, table=False):
    conversation_id: int
    workflow_id: int
    scene_description: str = Field(max_length=2000)
    generation_params: Dict[str, Any] = Field(default={})


class ModelPresetCreate(SQLModel, table=False):
    name: str = Field(max_length=200)
    ai_model_id: int
    temperature: Decimal = Field(default=Decimal("0.7"), max_digits=3, decimal_places=2)
    top_p: Decimal = Field(default=Decimal("1.0"), max_digits=3, decimal_places=2)
    frequency_penalty: Decimal = Field(default=Decimal("0.0"), max_digits=3, decimal_places=2)
    presence_penalty: Decimal = Field(default=Decimal("0.0"), max_digits=3, decimal_places=2)
    max_tokens: Optional[int] = Field(default=None)
    custom_parameters: Dict[str, Any] = Field(default={})
    is_default: bool = Field(default=False)
