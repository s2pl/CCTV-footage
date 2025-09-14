from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superadmin user'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True, help='Email address for the superadmin')
        parser.add_argument('--password', type=str, required=True, help='Password for the superadmin')
        parser.add_argument('--first-name', type=str, default='', help='First name (optional)')
        parser.add_argument('--last-name', type=str, default='', help='Last name (optional)')
        parser.add_argument('--username', type=str, default='', help='Username (optional)')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        username = options['username']

        # Validate email
        try:
            validate_email(email)
        except ValidationError:
            self.stdout.write(
                self.style.ERROR(f'Invalid email address: {email}')
            )
            return

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'User with email {email} already exists')
            )
            return

        # Create superadmin user
        try:
            user = User.objects.create_user(
                email=email,
                username=username or email.split('@')[0],
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='superadmin',
                is_active=True,
                is_verified=True,
                is_staff=True,
                is_superuser=True
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created superadmin user: {email}'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superadmin user: {str(e)}')
            )
