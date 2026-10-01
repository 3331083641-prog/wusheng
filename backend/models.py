"""Independently designed lifecycle schema; money stored as integer cents."""
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, ForeignKey, JSON, UniqueConstraint
from .database import Base, uid, timestamp


class Item(Base):
    __tablename__ = 'items'
    id = Column(String, primary_key=True, default=uid)
    name = Column(String(250), nullable=False)
    brand = Column(String(250), default='')
    model = Column(String(250), default='')
    category = Column(String, default='其他', index=True)
    description = Column(Text, default='')
    purchaseDate = Column(String, nullable=False)
    purchasePrice = Column(Integer, default=0)
    purchaseChannel = Column(String(250), default='')
    serialNumber = Column(String(250), default='', index=True)
    warrantyMonths = Column(Integer, default=12)
    warrantyEndDate = Column(String, nullable=True)
    returnWindowDays = Column(Integer, default=7)
    returnDeadline = Column(String, nullable=True)
    status = Column(String, default='正常使用')
    coverImage = Column(String, default='')
    location = Column(String(250), default='')
    createdAt = Column(String, default=timestamp)
    updatedAt = Column(String, default=timestamp)
    isDemo = Column(Boolean, default=False)


class ItemImage(Base):
    __tablename__ = 'item_images'
    id = Column(String, primary_key=True, default=uid)
    itemId = Column(String, ForeignKey('items.id', ondelete='CASCADE'), nullable=False, index=True)
    filePath = Column(String, nullable=False)
    type = Column(String, default='product')
    source = Column(String, default='upload')


class Document(Base):
    __tablename__ = 'documents'
    id = Column(String, primary_key=True, default=uid)
    itemId = Column(String, ForeignKey('items.id', ondelete='CASCADE'), nullable=False, index=True)
    type = Column(String, default='manual')
    filename = Column(String, nullable=False)
    filePath = Column(String, nullable=False)
    extractedText = Column(Text, default='')
    uploadedAt = Column(String, default=timestamp)


class LifecycleEvent(Base):
    __tablename__ = 'lifecycle_events'
    id = Column(String, primary_key=True, default=uid)
    itemId = Column(String, ForeignKey('items.id', ondelete='CASCADE'), nullable=False, index=True)
    type = Column(String, nullable=False)
    date = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, default='')
    source = Column(String, default='engine')
    relatedId = Column(String, nullable=False)
    __table_args__ = (UniqueConstraint('itemId', 'type', 'relatedId'),)


class MaintenanceRecord(Base):
    __tablename__ = 'maintenance_records'
    id = Column(String, primary_key=True, default=uid)
    itemId = Column(String, ForeignKey('items.id', ondelete='CASCADE'), nullable=False, index=True)
    type = Column(String, nullable=False)
    date = Column(String, nullable=False)
    intervalDays = Column(Integer, default=90)
    nextDueDate = Column(String, nullable=False)
    description = Column(Text, default='')
    cost = Column(Integer, default=0)


class RepairRecord(Base):
    __tablename__ = 'repair_records'
    id = Column(String, primary_key=True, default=uid)
    itemId = Column(String, ForeignKey('items.id', ondelete='CASCADE'), nullable=False, index=True)
    issue = Column(String(250), nullable=False)
    reportDate = Column(String, nullable=False)
    status = Column(String, default='待预约')
    serviceType = Column(String, default='官方售后')
    cost = Column(Integer, default=0)
    description = Column(Text, default='')
    completionDate = Column(String, nullable=True)
    progress = Column(JSON, default=list)


class Consumable(Base):
    __tablename__ = 'consumables'
    id = Column(String, primary_key=True, default=uid)
    itemId = Column(String, ForeignKey('items.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    unit = Column(String(20), default='个')
    currentStock = Column(Float, default=0)
    warningStock = Column(Float, default=1)
    leadDays = Column(Integer, default=7)
    coverImage = Column(String, default='/assets/filter.jpg')


class ConsumptionRecord(Base):
    __tablename__ = 'consumption_records'
    id = Column(String, primary_key=True, default=uid)
    consumableId = Column(String, ForeignKey('consumables.id', ondelete='CASCADE'), nullable=False, index=True)
    date = Column(String, nullable=False)
    quantityUsed = Column(Float, nullable=False)


class RestockRecord(Base):
    __tablename__ = 'restock_records'
    id = Column(String, primary_key=True, default=uid)
    consumableId = Column(String, ForeignKey('consumables.id', ondelete='CASCADE'), nullable=False, index=True)
    date = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    cost = Column(Integer, default=0)


class Reminder(Base):
    __tablename__ = 'reminders'
    id = Column(String, primary_key=True, default=uid)
    itemId = Column(String, ForeignKey('items.id', ondelete='CASCADE'), nullable=False, index=True)
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    dueDate = Column(String, nullable=False, index=True)
    originalDueDate = Column(String, nullable=False)
    status = Column(String, default='pending')
    priority = Column(String, default='普通')
    relatedId = Column(String, nullable=False)
    __table_args__ = (UniqueConstraint('itemId', 'type', 'relatedId'),)


class RecognitionResult(Base):
    __tablename__ = 'recognition_results'
    id = Column(String, primary_key=True, default=uid)
    sessionId = Column(String, nullable=False, index=True)
    field = Column(String, nullable=False)
    value = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    sourceImage = Column(String, nullable=False)
    rawText = Column(Text, default='')


class RecognitionSession(Base):
    __tablename__ = 'recognition_sessions'
    id = Column(String, primary_key=True, default=uid)
    images = Column(JSON, default=list)
    createdAt = Column(String, default=timestamp)
    itemId = Column(String, ForeignKey('items.id', ondelete='SET NULL'), nullable=True)
