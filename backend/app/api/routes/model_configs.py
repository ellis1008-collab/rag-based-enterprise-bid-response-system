from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.security import get_api_key_cipher, mask_api_key
from app.db.session import get_db
from app.llm.service import LLMService
from app.models import ModelConfig
from app.schemas import (
    DeleteResponse,
    ModelConfigCreate,
    ModelConfigRead,
    ModelConfigTestResponse,
    ModelConfigUpdate,
)

router = APIRouter(prefix="/models/configs", tags=["model-configs"])


def get_model_config_or_404(db: Session, config_id: int) -> ModelConfig:
    config = db.get(ModelConfig, config_id)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model config not found.",
        )
    return config


def to_model_config_read(config: ModelConfig) -> ModelConfigRead:
    api_key = get_api_key_cipher().decrypt(config.api_key_encrypted)
    return ModelConfigRead(
        id=config.id,
        name=config.name,
        provider=config.provider,
        base_url=config.base_url,
        masked_api_key=mask_api_key(api_key),
        model_name=config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        is_default=config.is_default,
        enabled=config.enabled,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


def unset_default_configs(db: Session) -> None:
    db.execute(update(ModelConfig).values(is_default=False))


@router.get("", response_model=list[ModelConfigRead])
def list_model_configs(db: Session = Depends(get_db)) -> list[ModelConfigRead]:
    configs = db.scalars(select(ModelConfig).order_by(ModelConfig.created_at.desc()))
    return [to_model_config_read(config) for config in configs]


@router.post("", response_model=ModelConfigRead, status_code=status.HTTP_201_CREATED)
def create_model_config(payload: ModelConfigCreate, db: Session = Depends(get_db)) -> ModelConfigRead:
    has_existing_config = db.scalar(select(ModelConfig.id).limit(1)) is not None
    should_be_default = payload.is_default or not has_existing_config

    if should_be_default:
        unset_default_configs(db)

    config = ModelConfig(
        name=payload.name,
        provider=payload.provider,
        base_url=payload.base_url,
        api_key_encrypted=get_api_key_cipher().encrypt(payload.api_key),
        model_name=payload.model_name,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        is_default=should_be_default,
        enabled=payload.enabled,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return to_model_config_read(config)


@router.patch("/{config_id}", response_model=ModelConfigRead)
def update_model_config(
    config_id: int,
    payload: ModelConfigUpdate,
    db: Session = Depends(get_db),
) -> ModelConfigRead:
    config = get_model_config_or_404(db, config_id)
    update_data = payload.model_dump(exclude_unset=True)

    if update_data.get("is_default") is True:
        unset_default_configs(db)

    api_key = update_data.pop("api_key", None)
    if api_key is not None:
        config.api_key_encrypted = get_api_key_cipher().encrypt(api_key)

    for field_name, value in update_data.items():
        setattr(config, field_name, value)

    db.add(config)
    db.commit()
    db.refresh(config)
    return to_model_config_read(config)


@router.delete("/{config_id}", response_model=DeleteResponse)
def delete_model_config(config_id: int, db: Session = Depends(get_db)) -> DeleteResponse:
    config = get_model_config_or_404(db, config_id)
    db.delete(config)
    db.commit()
    return DeleteResponse(status="deleted")


@router.post("/{config_id}/test", response_model=ModelConfigTestResponse)
async def test_model_config(config_id: int, db: Session = Depends(get_db)) -> ModelConfigTestResponse:
    config = get_model_config_or_404(db, config_id)
    service = LLMService(db=db, model_config=config, allow_fallback=False)
    try:
        result = await service.invoke_text("请只回复 OK", prompt_type="model_config_test")
    except Exception as exc:
        return ModelConfigTestResponse(success=False, message=str(exc), latency_ms=0)

    return ModelConfigTestResponse(
        success=result.content.strip().upper() == "OK",
        message=result.content,
        latency_ms=result.latency_ms,
    )


@router.post("/{config_id}/set-default", response_model=ModelConfigRead)
def set_default_model_config(config_id: int, db: Session = Depends(get_db)) -> ModelConfigRead:
    config = get_model_config_or_404(db, config_id)
    unset_default_configs(db)
    config.is_default = True
    config.enabled = True
    db.add(config)
    db.commit()
    db.refresh(config)
    return to_model_config_read(config)
