from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict
from .clock import today


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class ItemInput(Input):
    name: str = Field(min_length=1, max_length=250)
    brand: str = Field(default='', max_length=250)
    model: str = Field(default='', max_length=250)
    category: Literal['家电','数码','家居','耗材','其他'] = '其他'
    description: str = Field(default='', max_length=1000)
    purchaseDate: date
    purchasePrice: float = Field(default=0, ge=0, le=100_000_000, allow_inf_nan=False)
    purchaseChannel: str = Field(default='', max_length=250)
    serialNumber: str = Field(default='', max_length=250)
    warrantyMonths: int = Field(default=12, ge=0, le=120)
    returnWindowDays: int = Field(default=7, ge=0, le=365)
    location: str = Field(default='', max_length=250)
    status: Literal['正常使用','淘汰','转卖','回收'] = '正常使用'
    recognitionSessionId: str | None = None
    draftSessionId: str | None = None
    images: list[dict] = Field(default_factory=list, max_length=10)


    @field_validator('draftSessionId')
    @classmethod
    def draft_id(cls, value):
        if value is not None:
            import uuid
            try: uuid.UUID(value)
            except ValueError: raise ValueError('Draft ID 无效')
        return value

    @field_validator('purchaseDate')
    @classmethod
    def past_date(cls, value):
        if value > today():
            raise ValueError('购买日期不能晚于今天')
        return value


class MaintenanceInput(Input):
    type: str = Field(min_length=1, max_length=100)
    date: date
    intervalDays: int = Field(ge=1, le=3650)
    description: str = Field(default='', max_length=1000)
    cost: float = Field(default=0, ge=0, le=10_000_000, allow_inf_nan=False)


class RepairInput(Input):
    itemId: str
    issue: str = Field(min_length=1, max_length=250)
    reportDate: date
    status: Literal['待预约'] = '待预约'
    serviceType: Literal['官方售后','线下维修店','自行检查'] = '官方售后'
    cost: float = Field(default=0, ge=0, le=10_000_000, allow_inf_nan=False)
    description: str = Field(default='', max_length=1000)


class RepairUpdate(Input):
    status: Literal['待预约','诊断中','维修中','已完成']
    cost: float = Field(ge=0, le=10_000_000, allow_inf_nan=False)
    description: str = Field(default='', max_length=1000)


class ConsumableInput(Input):
    itemId: str
    name: str = Field(min_length=1, max_length=150)
    unit: str = Field(default='个', min_length=1, max_length=20)
    currentStock: float = Field(ge=0, le=1_000_000, allow_inf_nan=False)
    warningStock: float = Field(default=1, ge=0, le=1_000_000, allow_inf_nan=False)
    leadDays: int = Field(default=7, ge=0, le=365)


class StockInput(Input):
    date: date
    quantity: float = Field(gt=0, le=1_000_000, allow_inf_nan=False)
    cost: float = Field(default=0, ge=0, le=10_000_000, allow_inf_nan=False)


class ReminderAction(Input):
    action: Literal['complete','snooze']
    days: int = Field(default=7, ge=1, le=365)


class Question(Input):
    itemId: str
    question: str = Field(min_length=1, max_length=1000)
