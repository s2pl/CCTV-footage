# User Management System

A comprehensive user management system with JWT authentication and role-based access control.

## Features

- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: Four user roles (Super Admin, Admin, Developer, Visitor)
- **User Management**: Create, update, delete, and manage users
- **Session Management**: Track and manage user sessions
- **Activity Logging**: Comprehensive audit trail of user actions
- **Password Management**: Secure password handling with validation

## User Roles

### 1. Super Admin
- Full system access
- Can create, modify, and delete any user
- Can change user roles
- Access to all system features

### 2. Admin
- Can manage users (except superadmins)
- Access to admin panel
- Can view user activities and sessions

### 3. Developer
- Access to development features
- Limited user management capabilities
- Can view system logs

### 4. Visitor
- Basic system access
- Read-only access to public features
- Cannot modify system settings

## API Endpoints

### Authentication
- `POST /api/users/auth/login/` - User login
- `POST /api/users/auth/logout/` - User logout
- `POST /api/users/auth/change_password/` - Change password
- `POST /api/users/auth/reset_password/` - Request password reset
- `POST /api/users/auth/reset_password_confirm/` - Confirm password reset

### User Management
- `GET /api/users/users/` - List all users
- `POST /api/users/users/` - Create new user
- `GET /api/users/users/{id}/` - Get user details
- `PUT /api/users/users/{id}/` - Update user
- `DELETE /api/users/users/{id}/` - Delete user
- `GET /api/users/users/profile/` - Get current user profile
- `PUT /api/users/users/update_profile/` - Update current user profile
- `POST /api/users/users/{id}/activate/` - Activate/deactivate user
- `POST /api/users/users/{id}/change_role/` - Change user role

### Sessions & Activities
- `GET /api/users/sessions/` - List user sessions
- `POST /api/users/sessions/revoke_all/` - Revoke all sessions for a user
- `GET /api/users/activities/` - List user activities

### User Creation
- `POST /api/users/create-user/` - Create new user (superadmin only)

## Setup Instructions

### 1. Install Dependencies
```bash
pip install PyJWT
```

### 2. Update Django Settings
Add to your `settings.py`:
```python
AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.users.auth.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}
```

### 3. Run Migrations
```bash
python manage.py makemigrations users
python manage.py migrate
```

### 4. Create Super Admin
```bash
python manage.py createsuperadmin --email admin@example.com --password securepassword
```

## Usage Examples

### Creating a Super Admin
```bash
python manage.py createsuperadmin \
    --email admin@example.com \
    --password SecurePass123 \
    --first-name "Admin" \
    --last-name "User"
```

### Login via API
```bash
curl -X POST http://localhost:8000/api/users/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"email": "admin@example.com", "password": "SecurePass123"}'
```

### Using JWT Token
```bash
curl -X GET http://localhost:8000/api/users/users/profile/ \
    -H "Authorization: Bearer <your_jwt_token>"
```

## Security Features

- **JWT Tokens**: Secure, time-limited authentication tokens
- **Password Validation**: Django's built-in password strength validation
- **Session Tracking**: Monitor and control user sessions
- **Activity Logging**: Complete audit trail of user actions
- **Role-Based Permissions**: Granular access control
- **IP Tracking**: Log user IP addresses for security

## Customization

### Adding New Roles
1. Update `ROLE_CHOICES` in `models.py`
2. Add corresponding permission methods
3. Update permission classes as needed

### Custom Permissions
Create new permission classes in `permissions.py`:
```python
class CustomPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # Your custom logic here
        return True
```

### Activity Types
Add new activity types in `models.py`:
```python
ACTIVITY_TYPES = [
    # ... existing types ...
    ('custom_action', 'Custom Action'),
]
```

## Testing

Run the test suite:
```bash
python manage.py test apps.users
```

## Troubleshooting

### Common Issues

1. **JWT Token Expired**: Tokens expire after 24 hours by default
2. **Permission Denied**: Check user role and permissions
3. **Migration Errors**: Ensure all dependencies are installed

### Debug Mode
Enable debug logging in Django settings for detailed error information.

## Contributing

1. Follow Django coding standards
2. Add tests for new features
3. Update documentation
4. Ensure all tests pass

## License

This project is part of the Shree Swami Smartha system.
