from decimal import Decimal
from django.core.management.base import BaseCommand
from stores.models import Store
from products.models import Product, Category

class Command(BaseCommand):
    help = "Seeds realistic demo supermarket data (stores, categories, products) for hackathon demonstrations."

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo store and product data...")

        # 1. Stores
        stores_data = [
            {
                "name": "Dmart",
                "address": "Linking Road, Bandra West, Mumbai",
                "opening_hours": "8:00 AM - 10:30 PM",
                "distance_km": Decimal("1.2"),
            },
            {
                "name": "Reliance Smart",
                "address": "SV Road, Andheri West, Mumbai",
                "opening_hours": "8:00 AM - 10:00 PM",
                "distance_km": Decimal("2.4"),
            },
            {
                "name": "General Store",
                "address": "Station Road, Vile Parle, Mumbai",
                "opening_hours": "7:30 AM - 11:00 PM",
                "distance_km": Decimal("0.8"),
            },
            {
                "name": "Sona Super Shop",
                "address": "Market Lane, Santacruz, Mumbai",
                "opening_hours": "9:00 AM - 9:30 PM",
                "distance_km": Decimal("1.8"),
            },
        ]

        store_objects = {}
        for s_data in stores_data:
            store, created = Store.objects.get_or_create(
                name=s_data["name"],
                defaults={
                    "address": s_data["address"],
                    "opening_hours": s_data["opening_hours"],
                    "distance_km": s_data["distance_km"],
                }
            )
            if not created:
                store.address = s_data["address"]
                store.opening_hours = s_data["opening_hours"]
                store.distance_km = s_data["distance_km"]
                store.save()
            store_objects[store.name] = store

        # 2. Categories
        category_names = [
            "Groceries & Staples",
            "Dairy & Bakery",
            "Fresh Vegetables & Produce",
            "Snacks & Beverages",
            "Spices & Seasonings",
        ]

        cat_objects = {}
        for c_name in category_names:
            cat, _ = Category.objects.get_or_create(name=c_name)
            cat_objects[c_name] = cat

        # 3. Products
        # Each item has realistic prices, quantities, and units across stores
        demo_catalog = [
            # Staples & Grains
            {
                "name": "Basmati Rice 1kg",
                "category": "Groceries & Staples",
                "unit": "1kg",
                "prices": {"Dmart": 95.0, "Reliance Smart": 92.0, "General Store": 100.0, "Sona Super Shop": 98.0},
                "stock": 45,
            },
            {
                "name": "Economy Sona Masoori Rice 1kg",
                "category": "Groceries & Staples",
                "unit": "1kg",
                "prices": {"Dmart": 58.0, "Reliance Smart": 55.0, "General Store": 62.0, "Sona Super Shop": 60.0},
                "stock": 60,
            },
            {
                "name": "Sharbati Whole Wheat Atta 1kg",
                "category": "Groceries & Staples",
                "unit": "1kg",
                "prices": {"Dmart": 48.0, "Reliance Smart": 50.0, "General Store": 52.0, "Sona Super Shop": 50.0},
                "stock": 50,
            },
            {
                "name": "Toor Dal 500g",
                "category": "Groceries & Staples",
                "unit": "500g",
                "prices": {"Dmart": 75.0, "Reliance Smart": 72.0, "General Store": 80.0, "Sona Super Shop": 78.0},
                "stock": 40,
            },
            {
                "name": "Moong Dal 500g",
                "category": "Groceries & Staples",
                "unit": "500g",
                "prices": {"Dmart": 65.0, "Reliance Smart": 62.0, "General Store": 70.0, "Sona Super Shop": 68.0},
                "stock": 35,
            },
            {
                "name": "Tata Salt 1kg",
                "category": "Groceries & Staples",
                "unit": "1kg",
                "prices": {"Dmart": 25.0, "Reliance Smart": 26.0, "General Store": 28.0, "Sona Super Shop": 27.0},
                "stock": 100,
            },

            # Dairy
            {
                "name": "Fresh Paneer 200g",
                "category": "Dairy & Bakery",
                "unit": "200g",
                "prices": {"Dmart": 85.0, "Reliance Smart": 90.0, "General Store": 95.0, "Sona Super Shop": 92.0},
                "stock": 30,
            },
            {
                "name": "Premium Malai Paneer 250g",
                "category": "Dairy & Bakery",
                "unit": "250g",
                "prices": {"Dmart": 115.0, "Reliance Smart": 120.0, "General Store": 125.0, "Sona Super Shop": 122.0},
                "stock": 25,
            },
            {
                "name": "Amul Masti Dahi 400g",
                "category": "Dairy & Bakery",
                "unit": "400g",
                "prices": {"Dmart": 35.0, "Reliance Smart": 35.0, "General Store": 38.0, "Sona Super Shop": 36.0},
                "stock": 40,
            },
            {
                "name": "Amul Butter 100g",
                "category": "Dairy & Bakery",
                "unit": "100g",
                "prices": {"Dmart": 55.0, "Reliance Smart": 56.0, "General Store": 58.0, "Sona Super Shop": 56.0},
                "stock": 35,
            },

            # Fresh Produce
            {
                "name": "Fresh Tomatoes 1kg",
                "category": "Fresh Vegetables & Produce",
                "unit": "1kg",
                "prices": {"Dmart": 30.0, "Reliance Smart": 28.0, "General Store": 35.0, "Sona Super Shop": 32.0},
                "stock": 50,
            },
            {
                "name": "Red Onions 1kg",
                "category": "Fresh Vegetables & Produce",
                "unit": "1kg",
                "prices": {"Dmart": 35.0, "Reliance Smart": 38.0, "General Store": 40.0, "Sona Super Shop": 38.0},
                "stock": 55,
            },
            {
                "name": "Fresh Potatoes 1kg",
                "category": "Fresh Vegetables & Produce",
                "unit": "1kg",
                "prices": {"Dmart": 25.0, "Reliance Smart": 24.0, "General Store": 28.0, "Sona Super Shop": 26.0},
                "stock": 65,
            },
            {
                "name": "Fresh Green Peas 250g",
                "category": "Fresh Vegetables & Produce",
                "unit": "250g",
                "prices": {"Dmart": 40.0, "Reliance Smart": 38.0, "General Store": 45.0, "Sona Super Shop": 42.0},
                "stock": 30,
            },
            {
                "name": "Fresh Coriander & Green Chilies",
                "category": "Fresh Vegetables & Produce",
                "unit": "bunch",
                "prices": {"Dmart": 15.0, "Reliance Smart": 14.0, "General Store": 18.0, "Sona Super Shop": 16.0},
                "stock": 40,
            },

            # Oils & Spices
            {
                "name": "Fortune Sunlite Sunflower Oil 500ml",
                "category": "Groceries & Staples",
                "unit": "500ml",
                "prices": {"Dmart": 75.0, "Reliance Smart": 78.0, "General Store": 82.0, "Sona Super Shop": 80.0},
                "stock": 40,
            },
            {
                "name": "Everest Garam Masala 100g",
                "category": "Spices & Seasonings",
                "unit": "100g",
                "prices": {"Dmart": 35.0, "Reliance Smart": 34.0, "General Store": 36.0, "Sona Super Shop": 36.0},
                "stock": 50,
            },
            {
                "name": "Jeera Cumin Seeds 100g",
                "category": "Spices & Seasonings",
                "unit": "100g",
                "prices": {"Dmart": 42.0, "Reliance Smart": 40.0, "General Store": 45.0, "Sona Super Shop": 44.0},
                "stock": 45,
            },
            {
                "name": "Turmeric Haldi Powder 100g",
                "category": "Spices & Seasonings",
                "unit": "100g",
                "prices": {"Dmart": 28.0, "Reliance Smart": 27.0, "General Store": 30.0, "Sona Super Shop": 29.0},
                "stock": 50,
            },
        ]

        created_count = 0
        updated_count = 0

        for item in demo_catalog:
            cat = cat_objects[item["category"]]
            for store_name, price in item["prices"].items():
                store = store_objects.get(store_name)
                if not store:
                    continue

                product, created = Product.objects.get_or_create(
                    name=item["name"],
                    store=store,
                    defaults={
                        "category": cat,
                        "price": Decimal(str(price)),
                        "unit": item["unit"],
                        "stock_quantity": item["stock"],
                        "offer_type": "NONE",
                    }
                )
                if created:
                    created_count += 1
                else:
                    product.category = cat
                    product.unit = item["unit"]
                    product.price = Decimal(str(price))
                    product.stock_quantity = max(product.stock_quantity, item["stock"])
                    product.save()
                    updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded demo data: {created_count} products created, {updated_count} updated across {len(store_objects)} stores."
        ))
