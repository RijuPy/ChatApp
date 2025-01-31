from django.contrib.auth.models import User
from faker import Faker

def create_fake_users(count=10):
    faker = Faker()

    created_users = []
    for _ in range(count):
        username = faker.unique.user_name()
        email = faker.unique.email()
        first_name = faker.first_name()
        last_name = faker.last_name()

        # Create the user with a static password
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password="Riju@1234"  # Static password
        )
        created_users.append(user)

    return created_users
