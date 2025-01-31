from faker import Faker
from django.contrib.auth.models import User

def create_fake_users():
    fake = Faker()
    password = "Riju@1234"
    users = []

    for _ in range(100):
        username = fake.unique.user_name()
        email = fake.unique.email()
        first_name = fake.first_name()
        last_name = fake.last_name()

        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)  # Set the password
        users.append(user)

    # Bulk create the users
    User.objects.bulk_create(users)

    print(f"100 users created successfully with the password '{password}'.")
