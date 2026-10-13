import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from items.models import Item
from accounts.models import UserProfile


class Command(BaseCommand):
    help = "Sets up demo accounts and sample reports for testing multiple concurrent users."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Setting up Multi-User Test Environment..."))

        password = "Password123!"

        # 1. Create / Update User 1: Alice (The Finder)
        alice, _ = User.objects.get_or_create(username="alice", defaults={
            "email": "alice@findback.org",
            "first_name": "Alice",
            "last_name": "Finder",
        })
        alice.set_password(password)
        alice.first_name = "Alice"
        alice.last_name = "Finder"
        alice.email = "alice@findback.org"
        alice.is_staff = False
        alice.is_active = True
        alice.save()

        # Ensure UserProfile exists
        UserProfile.objects.get_or_create(user=alice, defaults={
            "phone": "+1 (555) 111-2222",
            "location": "North Campus Hall",
            "bio": "Campus helper and student volunteer.",
        })

        # 2. Create / Update User 2: Bob (The Owner / Claimant)
        bob, _ = User.objects.get_or_create(username="bob", defaults={
            "email": "bob@findback.org",
            "first_name": "Bob",
            "last_name": "Owner",
        })
        bob.set_password(password)
        bob.first_name = "Bob"
        bob.last_name = "Owner"
        bob.email = "bob@findback.org"
        bob.is_staff = False
        bob.is_active = True
        bob.save()

        UserProfile.objects.get_or_create(user=bob, defaults={
            "phone": "+1 (555) 333-4444",
            "location": "Engineering Building",
            "bio": "CS Major. Always misplacing tech accessories.",
        })

        # 3. Create / Update Admin User
        admin_user, _ = User.objects.get_or_create(username="admin_demo", defaults={
            "email": "admin@findback.org",
            "first_name": "Admin",
            "last_name": "Officer",
        })
        admin_user.set_password(password)
        admin_user.first_name = "Admin"
        admin_user.last_name = "Officer"
        admin_user.email = "admin@findback.org"
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_active = True
        admin_user.save()

        UserProfile.objects.get_or_create(user=admin_user, defaults={
            "phone": "+1 (555) 999-0000",
            "location": "Campus Security Office",
            "bio": "Head of Platform Moderation and Lost & Found recovery.",
        })

        today = timezone.now().date()

        # 4. Seed Found Item for Alice
        found_item, _ = Item.objects.get_or_create(
            user=alice,
            title="Found Space Grey Apple AirPods Pro",
            defaults={
                "item_type": Item.ItemType.FOUND,
                "status": Item.ItemStatus.ACTIVE,
                "category": Item.ItemCategory.ELECTRONICS,
                "location": "University Library, 2nd Floor Study Desk",
                "date_occurred": today,
                "description": "Found a pair of AirPods Pro in a white charging case with a navy silicone protective sleeve.",
                "brand": "Apple",
                "color": "White / Navy",
                "identification_details": "Serial number ends in 492X. Left ear tip has small blue mark.",
                "moderation_status": Item.ModerationStatus.APPROVED,
            }
        )

        # 5. Seed Lost Item for Bob
        lost_item, _ = Item.objects.get_or_create(
            user=bob,
            title="Lost Blue Herschel Backpack",
            defaults={
                "item_type": Item.ItemType.LOST,
                "status": Item.ItemStatus.ACTIVE,
                "category": Item.ItemCategory.BAG,
                "location": "Student Union Cafeteria",
                "date_occurred": today - datetime.timedelta(days=1),
                "description": "Blue Herschel backpack with leather bottom strap containing notebooks and a calculator.",
                "brand": "Herschel Supply Co.",
                "color": "Navy Blue",
                "identification_details": "Keychain with a bronze brass compass attached to front zipper.",
                "moderation_status": Item.ModerationStatus.APPROVED,
            }
        )

        self.stdout.write(self.style.SUCCESS("Demo test users and items configured successfully!"))
        self.stdout.write("")
        self.stdout.write("=================================================================")
        self.stdout.write(self.style.WARNING("MULTI-USER CONCURRENT TEST ACCOUNTS:"))
        self.stdout.write("-----------------------------------------------------------------")
        self.stdout.write(f"1. User 1 (Finder):    Username: 'alice'       Password: '{password}'")
        self.stdout.write(f"2. User 2 (Claimant):  Username: 'bob'         Password: '{password}'")
        self.stdout.write(f"3. Staff Admin:        Username: 'admin_demo'  Password: '{password}'")
        self.stdout.write("=================================================================")
        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO("HOW TO TEST MULTIPLE USERS AT THE SAME TIME:"))
        self.stdout.write("1. Open Window A (Regular Chrome/Edge): Login as 'alice'")
        self.stdout.write("2. Open Window B (Incognito / Private Window): Login as 'bob'")
        self.stdout.write("3. As 'bob' in Window B, visit Browse Catalog, find Alice's item, and click 'Submit Claim'.")
        self.stdout.write("4. Watch Window A ('alice'): A real-time WebSocket notification alert appears instantly!")
        self.stdout.write("5. 'alice' reviews the claim, clicks 'Approve', and Bob's Window B receives live confirmation.")
        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO("TO ALLOW USERS ON OTHER DEVICES (PHONES/LAPTOPS ON WI-FI):"))
        self.stdout.write("Run:  python manage.py runserver 0.0.0.0:8000")
        self.stdout.write("Other devices can visit: http://<YOUR_IP_ADDRESS>:8000")
        self.stdout.write("=================================================================")
