"""Generates realistic demo data so the platform can be walked through
end-to-end without any manual data entry.

Run with:  python -m app.seed.seed_data

Modeled on a chemicals / industrial lubricants / paints manufacturer -
raw materials are base oils, resins, pigments, solvents and additives
(received in drums, barrels, IBCs and bags), finished goods are packaged
lubricants, greases, paints and coatings (dispatched in cans, pails and
drums). Produces roughly: 10 suppliers, 15 customers, ~80 products
(raw material + finished good), 200 GRNs (= 200 traceable raw-material
batches + QR codes), ~500 issue movements, 100 production orders (with
raw-material consumption + finished-goods batches + QR codes), and 100
dispatches - spread realistically over the last ~120 days so the
dashboard trend charts have something meaningful to show.
"""

import random
from datetime import date, datetime, timedelta

from faker import Faker

from app.core.database import SessionLocal
from app.models.batch import Batch
from app.models.customer import Customer
from app.models.enums import (
    BatchStatus,
    BatchType,
    PackagingType,
    ProductType,
    ProductionOrderStatus,
)
from app.models.product import Product
from app.models.production_order import ProductionOrder
from app.models.supplier import Supplier
from app.services.audit_service import log_action
from app.services.dispatch_service import create_dispatch
from app.services.grn_service import create_grn
from app.services.id_generator import generate_production_order_no
from app.services.movement_service import issue_material
from app.services.production_service import consume_raw_batch, create_finished_goods
from app.models.enums import AuditAction

fake = Faker()
random.seed(42)
Faker.seed(42)

WAREHOUSES = [
    "RM-SOLVENT-01", "RM-PIGMENT-01", "RM-GENERAL-01", "RM-DRUM-YARD",
    "FG-PAINTS-01", "FG-LUBE-01",
]
DEPARTMENTS = [
    "Production", "Blending", "Filling & Packing", "Quality Control",
    "QA Lab", "Maintenance", "R&D", "Tinting",
]

SUPPLIER_SUFFIXES = [
    "Chemicals Pvt Ltd", "Petrochemicals Ltd", "Resins & Polymers",
    "Specialty Chemicals", "Industries Ltd",
]
CUSTOMER_SUFFIXES = [
    "Paints & Hardware", "Auto Spares", "Industrial Supplies",
    "Trading Co.", "Distributors",
]

# category -> (variants, list of realistic packaging/UoM options)
RAW_MATERIAL_SPECS: dict[str, tuple[list[str], list[str]]] = {
    "Base Oil": (["SN150", "SN500", "SN650", "Group II", "Group III"], ["LTR", "DRUM", "BARREL"]),
    "Alkyd Resin": (
        ["Long Oil 60%", "Medium Oil 55%", "Short Oil 50%", "70% Solids in Xylene"],
        ["LTR", "DRUM"],
    ),
    "Epoxy Resin": (["Liquid Grade", "Solid Grade", "Type 1", "Type 2"], ["KG", "DRUM"]),
    "Acrylic Emulsion": (["Interior Grade", "Exterior Grade", "High Build"], ["LTR", "DRUM"]),
    "Titanium Dioxide": (["Rutile Grade", "Anatase Grade", "R-902", "R-706"], ["KG"]),
    "Iron Oxide Pigment": (["Red", "Yellow", "Black", "Brown"], ["KG"]),
    "Phthalocyanine Blue": (["Alpha Form", "Beta Form"], ["KG"]),
    "Solvent - Xylene": (["Industrial Grade", "Technical Grade"], ["LTR", "DRUM", "BARREL"]),
    "Solvent - Toluene": (["Industrial Grade", "Technical Grade"], ["LTR", "DRUM", "BARREL"]),
    "White Spirit": (["Type I", "Type II", "Low Odour"], ["LTR", "DRUM", "BARREL"]),
    "Anti-Foaming Agent": (["Silicone Based", "Mineral Oil Based"], ["KG", "CAN"]),
    "Corrosion Inhibitor": (["Standard", "Heavy Duty"], ["KG", "CAN"]),
    "Viscosity Index Improver": (["Standard", "High Shear Stability"], ["KG", "DRUM"]),
    "Antioxidant Additive": (["Phenolic", "Aminic"], ["KG", "CAN"]),
    "Surfactant": (["Anionic", "Nonionic"], ["KG", "CAN"]),
    "Rheology Modifier": (["Cellulosic", "Associative"], ["KG", "CAN"]),
    "Calcium Carbonate Filler": (["Coated", "Uncoated", "Fine Grade"], ["KG"]),
    "Talc Filler": (["Micronized", "Coarse Grade"], ["KG"]),
    "Empty MS Drum 210L": (["Mild Steel", "Epoxy Lined"], ["EA"]),
    "Empty Tin Can": (["1L", "4L", "20L"], ["EA"]),
}

FINISHED_GOOD_SPECS: dict[str, tuple[list[str], list[str]]] = {
    "Engine Oil": (
        ["15W-40 API CI-4", "20W-50 API SL", "10W-30 API SN", "5W-30 Synthetic"],
        ["LTR", "CAN", "DRUM"],
    ),
    "Hydraulic Oil": (["ISO VG 32", "ISO VG 46", "ISO VG 68"], ["LTR", "CAN", "DRUM"]),
    "Gear Oil": (["SAE 90 GL-4", "SAE 140 GL-5", "80W-90"], ["LTR", "CAN", "DRUM"]),
    "Industrial Grease": (
        ["Lithium Complex NLGI 2", "Calcium Sulfonate NLGI 1"], ["KG", "CAN"],
    ),
    "Interior Emulsion Paint": (
        ["Premium Sheen", "Economy Matt", "Luxury Silk"], ["LTR", "PAIL"],
    ),
    "Exterior Emulsion Paint": (["Weatherproof", "Crack Shield"], ["LTR", "PAIL"]),
    "Enamel Paint": (["Synthetic Gloss", "Quick Dry"], ["LTR", "CAN"]),
    "Wood Varnish": (["Melamine Based", "Polyurethane"], ["LTR", "CAN"]),
    "Metal Primer": (["Red Oxide", "Zinc Chromate", "Epoxy"], ["LTR", "CAN"]),
    "Industrial Anti-Rust Coating": (["Single Pack", "Two Pack Epoxy"], ["LTR", "DRUM"]),
    "NC Thinner": (["Standard", "Fast Dry"], ["LTR", "CAN"]),
}


# Some products' uom is itself a container word (DRUM/BARREL/CAN/PAIL/BAG) -
# reuse that directly. Otherwise (LTR/KG/EA) pick a realistic container for
# a raw material vs. a finished good.
UOM_TO_PACKAGING = {
    "DRUM": PackagingType.DRUM,
    "BARREL": PackagingType.BARREL,
    "CAN": PackagingType.CAN,
    "PAIL": PackagingType.PAIL,
    "BAG": PackagingType.BAG,
}
RAW_MATERIAL_FALLBACK_PACKAGING = [PackagingType.DRUM, PackagingType.BARREL, PackagingType.BAG]
FINISHED_GOOD_FALLBACK_PACKAGING = [PackagingType.CAN, PackagingType.DRUM, PackagingType.PAIL]


def pick_packaging_type(uom: str, is_raw_material: bool) -> PackagingType:
    if uom in UOM_TO_PACKAGING:
        return UOM_TO_PACKAGING[uom]
    fallback = RAW_MATERIAL_FALLBACK_PACKAGING if is_raw_material else FINISHED_GOOD_FALLBACK_PACKAGING
    return random.choice(fallback)


def days_ago(n: int) -> datetime:
    return datetime.utcnow() - timedelta(days=n, hours=random.randint(0, 8), minutes=random.randint(0, 59))


def already_seeded(db) -> bool:
    return db.query(Supplier).count() > 0


def seed_suppliers(db) -> list[Supplier]:
    suppliers = []
    for i in range(1, 11):
        s = Supplier(
            code=f"SUP-{i:03d}",
            name=f"{fake.city()} {random.choice(SUPPLIER_SUFFIXES)}",
            contact_email=fake.company_email(),
            contact_phone=fake.phone_number(),
            address=fake.address().replace("\n", ", "),
        )
        db.add(s)
        suppliers.append(s)
    db.flush()
    return suppliers


def seed_customers(db) -> list[Customer]:
    customers = []
    for i in range(1, 16):
        c = Customer(
            code=f"CUS-{i:03d}",
            name=f"{fake.last_name()} {random.choice(CUSTOMER_SUFFIXES)}",
            contact_email=fake.company_email(),
            contact_phone=fake.phone_number(),
            address=fake.address().replace("\n", ", "),
        )
        db.add(c)
        customers.append(c)
    db.flush()
    return customers


def seed_products(db) -> tuple[list[Product], list[Product]]:
    raw_products, fg_products = [], []
    sku_counter = 1

    for category, (variants, uoms) in RAW_MATERIAL_SPECS.items():
        for variant in variants:
            p = Product(
                sku=f"RM-{sku_counter:04d}",
                name=f"{category} - {variant}",
                category=category,
                uom=random.choice(uoms),
                product_type=ProductType.RAW_MATERIAL,
                description=f"{category} ({variant}) - raw material for paint and lubricant manufacturing.",
            )
            db.add(p)
            raw_products.append(p)
            sku_counter += 1

    for category, (variants, uoms) in FINISHED_GOOD_SPECS.items():
        for variant in variants:
            p = Product(
                sku=f"FG-{sku_counter:04d}",
                name=f"{category} - {variant}",
                category=category,
                uom=random.choice(uoms),
                product_type=ProductType.FINISHED_GOOD,
                description=f"{category} ({variant}) - finished product ready for dispatch.",
            )
            db.add(p)
            fg_products.append(p)
            sku_counter += 1

    db.flush()
    return raw_products, fg_products


def seed_grns(db, suppliers: list[Supplier], raw_products: list[Product]) -> list[Batch]:
    batches = []
    for i in range(200):
        supplier = random.choice(suppliers)
        product = random.choice(raw_products)
        quantity = round(random.uniform(50, 1000), 2)
        received = days_ago(random.randint(1, 120))
        mfg_date = received.date() - timedelta(days=random.randint(0, 10))
        expiry_date = mfg_date + timedelta(days=random.randint(365, 730))

        grn = create_grn(
            db,
            supplier,
            product,
            quantity,
            batch_number=f"B{supplier.code[-3:]}{i:05d}",
            warehouse_location=random.choice(WAREHOUSES),
            uom=product.uom,
            lot_number=f"LOT{fake.random_number(digits=6, fix_len=True)}",
            manufacturing_date=mfg_date,
            expiry_date=expiry_date,
            packaging_type=pick_packaging_type(product.uom, is_raw_material=True),
            received_date=received,
        )
        batches.append(grn.batch)

        if (i + 1) % 40 == 0:
            db.flush()
    db.flush()
    return batches


def seed_issues(db, raw_batches: list[Batch]) -> None:
    eligible = [b for b in raw_batches if float(b.remaining_quantity) > 0]
    count = 0
    attempts = 0
    while count < 500 and attempts < 3000 and eligible:
        attempts += 1
        batch = random.choice(eligible)
        remaining = float(batch.remaining_quantity)
        if remaining <= 0:
            eligible.remove(batch)
            continue
        qty = round(min(remaining, remaining * random.uniform(0.05, 0.35)), 2)
        if qty <= 0:
            continue
        movement_date = days_ago(random.randint(0, 110))
        issue_material(
            db,
            batch,
            qty,
            department=random.choice(DEPARTMENTS),
            requested_by=fake.name(),
            movement_date=movement_date,
        )
        count += 1
        if count % 50 == 0:
            db.flush()
    db.flush()


def seed_production(db, fg_products: list[Product], raw_batches: list[Batch]) -> list[Batch]:
    fg_batches: list[Batch] = []
    consumable = [b for b in raw_batches if b.batch_type == BatchType.RAW_MATERIAL]

    for i in range(100):
        product = random.choice(fg_products)
        planned_qty = round(random.uniform(50, 500), 2)
        start = days_ago(random.randint(5, 100))

        po = ProductionOrder(
            production_order_no=generate_production_order_no(db),
            product_id=product.id,
            planned_quantity=planned_qty,
            produced_quantity=0,
            status=ProductionOrderStatus.PLANNED,
            start_date=start.date(),
            end_date=start.date() + timedelta(days=random.randint(1, 5)),
            created_at=start,
        )
        db.add(po)
        db.flush()
        log_action(
            db,
            AuditAction.PRODUCTION_ORDER_CREATED,
            "ProductionOrder",
            po.id,
            f"Production order {po.production_order_no} created for {planned_qty} {product.uom} of {product.name}",
        )

        usable = [b for b in consumable if float(b.remaining_quantity) > 1]
        for _ in range(random.randint(2, 5)):
            if not usable:
                break
            batch = random.choice(usable)
            remaining = float(batch.remaining_quantity)
            if remaining <= 1:
                usable.remove(batch)
                continue
            qty = round(min(remaining, remaining * random.uniform(0.1, 0.5)), 2)
            consume_raw_batch(
                db, po, batch, qty, consumed_by=fake.name(),
                event_time=start + timedelta(hours=random.randint(1, 48)),
            )

        produced_qty = round(planned_qty * random.uniform(0.85, 1.0), 2)
        production_date = (start + timedelta(days=random.randint(1, 5))).date()
        fg = create_finished_goods(
            db, po, produced_qty, production_date,
            warehouse_location=random.choice(WAREHOUSES),
            packaging_type=pick_packaging_type(product.uom, is_raw_material=False),
            event_time=datetime.combine(production_date, datetime.min.time()) + timedelta(hours=10),
        )
        fg_batches.append(fg.batch)

        if (i + 1) % 25 == 0:
            db.flush()
    db.flush()
    return fg_batches


def seed_dispatches(db, customers: list[Customer], fg_batches: list[Batch]) -> None:
    eligible = [b for b in fg_batches if float(b.remaining_quantity) > 0]
    count = 0
    attempts = 0
    while count < 100 and attempts < 1000 and eligible:
        attempts += 1
        batch = random.choice(eligible)
        remaining = float(batch.remaining_quantity)
        if remaining <= 0:
            eligible.remove(batch)
            continue
        qty = round(min(remaining, remaining * random.uniform(0.3, 1.0)), 2)
        if qty <= 0:
            continue
        base_date = batch.manufacturing_date or date.today()
        dispatch_date = base_date + timedelta(days=random.randint(1, 15))
        if dispatch_date > date.today():
            dispatch_date = date.today()
        create_dispatch(db, random.choice(customers), batch, qty, dispatch_date)
        count += 1
        if count % 25 == 0:
            db.flush()
    db.flush()


def run() -> None:
    # Schema is managed by Alembic - run `alembic upgrade head` first
    # (docker-compose's backend command does this automatically).
    db = SessionLocal()
    try:
        if already_seeded(db):
            print("Database already contains data - skipping seed. "
                  "Drop the DB volume first if you want to reseed.")
            return

        print("Seeding suppliers, customers, products...")
        suppliers = seed_suppliers(db)
        customers = seed_customers(db)
        raw_products, fg_products = seed_products(db)
        db.commit()

        print("Seeding 200 GRNs / raw-material batches + QR codes...")
        raw_batches = seed_grns(db, suppliers, raw_products)
        db.commit()

        print("Seeding ~500 issue movements...")
        seed_issues(db, raw_batches)
        db.commit()

        print("Seeding 100 production orders + consumption + finished goods + QR codes...")
        fg_batches = seed_production(db, fg_products, raw_batches)
        db.commit()

        print("Seeding 100 dispatches...")
        seed_dispatches(db, customers, fg_batches)
        db.commit()

        print("Seed complete.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
