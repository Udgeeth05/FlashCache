from database import Base
from database import engine
from models import Product


def initialize_database():

    Base.metadata.create_all(
        bind=engine
    )

    from database import SessionLocal

    db = SessionLocal()

    try:

        existing_product = (
            db.query(Product)
            .filter(Product.id == 1)
            .first()
        )

        if existing_product is None:

            products = [
                Product(
                    id=1,
                    name="iPhone 17",
                    price=99999,
                    category="Mobile"
                ),
                Product(
                    id=2,
                    name="Galaxy S25",
                    price=89999,
                    category="Mobile"
                ),
                Product(
                    id=3,
                    name="MacBook Air",
                    price=119999,
                    category="Laptop"
                )
            ]

            db.add_all(
                products
            )

            db.commit()

    finally:

        db.close()