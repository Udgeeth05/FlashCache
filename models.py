from sqlalchemy import Column, Integer, String

from database import Base


class Product(Base):

    __tablename__ = "products"

    id = Column(
        Integer,
        primary_key=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    price = Column(
        Integer,
        nullable=False
    )

    category = Column(
        String(50),
        nullable=False
    )