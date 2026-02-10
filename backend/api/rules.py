from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models.post_rule import PostRule, RuleField
from schemas.post_rule import PostRuleCreate, PostRuleUpdate, PostRuleResponse

router = APIRouter(prefix="/api/rules", tags=["rules"])


@router.get("/{site_id}", response_model=list[PostRuleResponse])
async def list_rules(site_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PostRule)
        .where(PostRule.site_id == site_id)
        .options(selectinload(PostRule.fields))
        .order_by(PostRule.created_at.desc())
    )
    return result.scalars().all()


@router.get("/detail/{rule_id}", response_model=PostRuleResponse)
async def get_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PostRule)
        .where(PostRule.id == rule_id)
        .options(selectinload(PostRule.fields))
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("/", response_model=PostRuleResponse, status_code=201)
async def create_rule(data: PostRuleCreate, db: AsyncSession = Depends(get_db)):
    rule = PostRule(
        site_id=data.site_id,
        name=data.name,
        url_pattern=data.url_pattern,
        forward_to=data.forward_to,
        is_active=data.is_active,
        success_redirect=data.success_redirect,
        success_message=data.success_message,
        rate_limit_requests=data.rate_limit_requests,
        rate_limit_window=data.rate_limit_window,
        honeypot_field=data.honeypot_field,
        enable_csrf=data.enable_csrf,
    )
    db.add(rule)
    await db.flush()

    for field_data in data.fields:
        field = RuleField(
            rule_id=rule.id,
            field_name=field_data.field_name,
            field_type=field_data.field_type,
            required=field_data.required,
            max_length=field_data.max_length,
            validation_regex=field_data.validation_regex,
        )
        db.add(field)

    await db.commit()

    result = await db.execute(
        select(PostRule)
        .where(PostRule.id == rule.id)
        .options(selectinload(PostRule.fields))
    )
    return result.scalar_one()


@router.put("/{rule_id}", response_model=PostRuleResponse)
async def update_rule(rule_id: str, data: PostRuleUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PostRule)
        .where(PostRule.id == rule_id)
        .options(selectinload(PostRule.fields))
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    for key, value in data.model_dump(exclude_unset=True, exclude={"fields"}).items():
        setattr(rule, key, value)

    if data.fields is not None:
        for field in rule.fields:
            await db.delete(field)
        await db.flush()

        for field_data in data.fields:
            field = RuleField(
                rule_id=rule.id,
                field_name=field_data.field_name,
                field_type=field_data.field_type,
                required=field_data.required,
                max_length=field_data.max_length,
                validation_regex=field_data.validation_regex,
            )
            db.add(field)

    await db.commit()

    result = await db.execute(
        select(PostRule)
        .where(PostRule.id == rule.id)
        .options(selectinload(PostRule.fields))
    )
    return result.scalar_one()


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    rule = await db.get(PostRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)
    await db.commit()
