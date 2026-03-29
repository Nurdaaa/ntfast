from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.core.database import Base


class Subject(Base):
    """
    Subject model for monitored individuals/entities

    Идентификация субъектов БЕЗ ИИН/БИН:
    - unique_identifier: главный ключ идентификации
      - Для владельца счета: IBAN (например "KZ00722C000000000000")
      - Для получателей: normalized_name + type (например "erzhan_o_individual")
    - iin_bin: опциональный (может быть NULL)
    """

    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)

    # Уникальный идентификатор субъекта (главный ключ идентификации)
    unique_identifier = Column(String(200), unique=True, index=True, nullable=False)

    name = Column(String(200), nullable=False, index=True)

    # ИИН/БИН теперь опциональный (может не быть в данных)
    iin_bin = Column(String(12), index=True, nullable=True)

    type = Column(String(20), nullable=False)  # individual, legal_entity, account_owner
    risk_level = Column(Integer, default=0)  # 0-10 risk score
    status = Column(String(20), default="active")  # active, suspended, blocked
    phone_number = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Subject(id={self.id}, name='{self.name}', unique_identifier='{self.unique_identifier}', type='{self.type}')>"
