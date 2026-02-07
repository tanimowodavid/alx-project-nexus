import uuid
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import Category, Product, ProductVariant
from ai_assistant.utils import generate_product_embedding

class Command(BaseCommand):
    help = 'Seeds the database with Planet Inc products'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding data for Planet Inc...")

        # Create Categories
        cats_data = [
            {'name': 'Action Figures', 'desc': 'Premium articulated heroes and villains.'},
            {'name': 'Bicycles', 'desc': 'High-performance bikes for all ages.'},
            {'name': 'Toy Cars', 'desc': 'Die-cast and RC racing machines.'},
            {'name': 'Limited Edition', 'desc': 'Exclusive, rare galactic collectibles.'},
        ]
        
        categories = {}
        for item in cats_data:
            cat, _ = Category.objects.get_or_create(
                name=item['name'], 
                defaults={'description': item['desc']}
            )
            categories[item['name']] = cat

        # Product Data Helper
        products_to_create = [
            # --- BICYCLES ---
            {
                'name': 'Spider-Man Web-Slinger BMX',
                'desc': 'Limited Edition 20-inch bike. Features custom web-frame and LED rims. Perfect for young heroes.',
                'cats': ['Bicycles', 'Limited Edition'],
                'variants': [
                    {'name': 'Classic Red/Blue', 'price': 250.00, 'stock': 15, 'sku': 'BK-SPD-001'},
                    {'name': 'Stealth Black', 'price': 275.00, 'stock': 5, 'sku': 'BK-SPD-002'},
                ]
            },
            {
                'name': 'Titanium Trail Blazer',
                'desc': 'Professional mountain bike with 21-speed Shimano gears and hydraulic disc brakes.',
                'cats': ['Bicycles'],
                'variants': [
                    {'name': '26-inch Charcoal', 'price': 550.00, 'stock': 10, 'sku': 'BK-TTN-CHR'},
                    {'name': '29-inch Charcoal', 'price': 600.00, 'stock': 8, 'sku': 'BK-TTN-CHR-29'},
                ]
            },
            {
                'name': 'Little Rocket Balance Bike',
                'desc': 'No-pedal training bike for toddlers aged 2-4. Ultra-lightweight frame.',
                'cats': ['Bicycles'],
                'variants': [
                    {'name': 'Rocket Red', 'price': 85.00, 'stock': 40, 'sku': 'BK-LRT-RED'},
                    {'name': 'Cosmic Pink', 'price': 85.00, 'stock': 35, 'sku': 'BK-LRT-PNK'},
                ]
            },
            {
                'name': 'Lunar Foldable Commuter',
                'desc': 'Space-saving foldable bike for urban explorers. Fits in a car trunk or under a desk.',
                'cats': ['Bicycles'],
                'variants': [
                    {'name': 'Metallic Silver', 'price': 320.00, 'stock': 12, 'sku': 'BK-LUN-SLV'},
                ]
            },

            # --- ACTION FIGURES ---
            {
                'name': 'Galactic Knight Action Figure',
                'desc': '1/6 scale articulated figure with glowing plasma sword and removable armor.',
                'cats': ['Action Figures'],
                'variants': [
                    {'name': 'Standard Edition', 'price': 45.00, 'stock': 50, 'sku': 'AF-GK-001'},
                    {'name': 'Chrome Anniversary', 'price': 85.00, 'stock': 10, 'sku': 'AF-GK-002'},
                ]
            },
            {
                'name': 'Iron Valkyrie',
                'desc': 'Highly detailed female warrior figure with 32 points of articulation and spear accessory.',
                'cats': ['Action Figures'],
                'variants': [
                    {'name': 'Battle-Worn Gold', 'price': 55.00, 'stock': 25, 'sku': 'AF-IV-GLD'},
                ]
            },
            {
                'name': 'Cyberpunk Bounty Hunter',
                'desc': 'Futuristic mercenary with LED eyes and interchangeable cybernetic arms.',
                'cats': ['Action Figures', 'Limited Edition'],
                'variants': [
                    {'name': 'Neon Night', 'price': 110.00, 'stock': 12, 'sku': 'AF-CPH-NN'},
                ]
            },
            {
                'name': 'Deep Sea Explorer Mecha',
                'desc': 'Heavy-duty robotic suit designed for underwater missions. Includes working claw.',
                'cats': ['Action Figures'],
                'variants': [
                    {'name': 'Sub-Yellow', 'price': 65.00, 'stock': 20, 'sku': 'AF-DSM-YEL'},
                ]
            },
            {
                'name': 'Samurai X Ghost',
                'desc': 'Traditional samurai armor mixed with ghostly translucent plastic parts.',
                'cats': ['Action Figures'],
                'variants': [
                    {'name': 'Spectral White', 'price': 50.00, 'stock': 30, 'sku': 'AF-SXG-WHT'},
                ]
            },

            # --- TOY CARS ---
            {
                'name': 'Nebula Drift RC Racer',
                'desc': 'High-speed RC car with app control and neon underglow. 50mph top speed.',
                'cats': ['Toy Cars'],
                'variants': [
                    {'name': 'Electric Blue', 'price': 120.00, 'stock': 25, 'sku': 'RC-NB-BLU'},
                    {'name': 'Solar Orange', 'price': 120.00, 'stock': 20, 'sku': 'RC-NB-ORG'},
                ]
            },
            {
                'name': 'Vintage Stallion Die-cast',
                'desc': '1:24 scale replica of a 1960s muscle car. Opening doors and hood.',
                'cats': ['Toy Cars'],
                'variants': [
                    {'name': 'Cherry Red', 'price': 35.00, 'stock': 100, 'sku': 'DC-VST-RED'},
                    {'name': 'Midnight Black', 'price': 35.00, 'stock': 80, 'sku': 'DC-VST-BLK'},
                ]
            },
            {
                'name': 'Mars Rover Explorer',
                'desc': 'Educational toy car with working solar panels and 6-wheel independent suspension.',
                'cats': ['Toy Cars'],
                'variants': [
                    {'name': 'NASA White', 'price': 45.00, 'stock': 45, 'sku': 'TC-MRE-WHT'},
                ]
            },
            {
                'name': 'Hyper-Loop Concept Car',
                'desc': 'Futuristic aerodynamic design. Pull-back and release action.',
                'cats': ['Toy Cars'],
                'variants': [
                    {'name': 'Plasma Purple', 'price': 15.00, 'stock': 150, 'sku': 'TC-HLC-PUR'},
                    {'name': 'Laser Green', 'price': 15.00, 'stock': 150, 'sku': 'TC-HLC-GRN'},
                ]
            },

            # --- BULK EXTRAS ---
            {
                'name': 'Aero-Dynamic Road Bike',
                'desc': 'Carbon fiber frame for high-speed road racing. Weights only 8kg.',
                'cats': ['Bicycles'],
                'variants': [{'name': 'Swift Black', 'price': 1200.00, 'stock': 5, 'sku': 'BK-ADR-BLK'}]
            },
            {
                'name': 'Shadow Ninja Set',
                'desc': 'Pack of 3 stealth action figures with 15 accessories.',
                'cats': ['Action Figures'],
                'variants': [{'name': 'Triple Pack', 'price': 30.00, 'stock': 60, 'sku': 'AF-SNS-3PK'}]
            },
            {
                'name': 'Desert Storm RC Truck',
                'desc': 'All-terrain 4x4 monster truck with water-resistant electronics.',
                'cats': ['Toy Cars'],
                'variants': [{'name': 'Sand Camo', 'price': 145.00, 'stock': 18, 'sku': 'RC-DST-CAM'}]
            },
            {
                'name': 'Retro Comet Cruiser',
                'desc': 'Vintage style bicycle with modern lightweight alloy frame. A classic reimagined.',
                'cats': ['Bicycles'],
                'variants': [{'name': '24-inch Matte Green', 'price': 180.00, 'stock': 30, 'sku': 'BK-COM-GRN'}]
            },
            {
                'name': 'Dino-Bot Transformer',
                'desc': 'Mechanical T-Rex that converts into a warrior robot. Built-in sound effects.',
                'cats': ['Action Figures'],
                'variants': [{'name': 'Prehistoric Steel', 'price': 40.00, 'stock': 70, 'sku': 'AF-DBT-STL'}]
            },
            {
                'name': 'Golden Era F1 Replica',
                'desc': 'Limited edition 1:18 scale model of the 1988 championship car.',
                'cats': ['Toy Cars', 'Limited Edition'],
                'variants': [{'name': 'Championship Gold', 'price': 210.00, 'stock': 3, 'sku': 'DC-F1-GLD'}]
            },
            {
                'name': 'Urban Freestyle Scooter',
                'desc': 'Technically a ride-on, categorized under Bicycles for mobility. 360-degree spinning handlebars.',
                'cats': ['Bicycles'],
                'variants': [{'name': 'Acid Yellow', 'price': 95.00, 'stock': 40, 'sku': 'BK-UFS-YEL'}]
            }
        ]

        # Create Products and Variants
        for p_data in products_to_create:
            combined_text = f"{p_data['name']}: {p_data['desc']}"
            
            # Generate the vector coordinate
            self.stdout.write(f"Generating embedding for {p_data['name']}...")
            vector = generate_product_embedding(combined_text)

            product, created = Product.all_objects.get_or_create(
                name=p_data['name'],
                defaults={
                    'description': p_data['desc'],
                    'embedding': vector
                }
            )
            
            # Associate Categories
            for cat_name in p_data['cats']:
                product.category.add(categories[cat_name])

            # Create Variants
            for v_data in p_data['variants']:
                ProductVariant.all_objects.get_or_create(
                    sku=v_data['sku'],
                    defaults={
                        'product': product,
                        'variant_name': v_data['name'],
                        'price': v_data['price'],
                        'stock_quantity': v_data['stock']
                    }
                )

        self.stdout.write(self.style.SUCCESS('Successfully seeded Planet Inc. inventory!'))

