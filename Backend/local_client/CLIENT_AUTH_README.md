# Client Authentication - CLIENT_TOKEN and CLIENT_ID

## Overview

The CCTV Local Recording Client uses authentication tokens to securely communicate with the Django backend API.

## CLIENT_TOKEN (Required)

### What is CLIENT_TOKEN?

`CLIENT_TOKEN` is a secure authentication token that identifies and authenticates your local recording client with the backend API. It's a randomly generated URL-safe token (32 bytes) that acts as a Bearer token in API requests.

### How is it generated?

When you create a new `LocalRecordingClient` record in Django Admin, the system automatically generates a unique `CLIENT_TOKEN` using Python's `secrets.token_urlsafe(32)` function. This ensures each client has a unique, secure token.

### Where to get CLIENT_TOKEN?

1. **Log in to Django Admin Panel**
   - Navigate to `http://your-backend-url/admin/`

2. **Go to Local Recording Clients**
   - Navigate to: **CCTV → Local Recording Clients**

3. **Create or View a Client**
   - Click "Add Local Recording Client" to create a new client
   - OR click on an existing client to view its details

4. **Copy the Token**
   - In the client details page, find the `client_token` field
   - Copy the entire token value
   - Paste it into your `.env` file as `CLIENT_TOKEN=your_token_here`

### Example

```
CLIENT_TOKEN=abc123XYZ456def789GHI012jkl345MNO678pqr901STU234vwx567
```

### How is it used?

The client uses this token in the `Authorization` header for all API requests:

```python
headers = {
    'Authorization': f'Bearer {CLIENT_TOKEN}',
    'Content-Type': 'application/json'
}
```

The backend validates this token against the `LocalRecordingClient` records in the database and ensures the client has permission to access the API.

---

## CLIENT_ID (Optional)

### What is CLIENT_ID?

`CLIENT_ID` is the UUID (Universally Unique Identifier) of the `LocalRecordingClient` record in the database. It's the primary key (`id` field) of the client record.

### Where to get CLIENT_ID?

1. **In Django Admin** (same location as CLIENT_TOKEN)
   - Navigate to: **CCTV → Local Recording Clients**
   - Open the client record
   - Copy the `id` field (UUID format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

2. **Example UUID format:**
   ```
   CLIENT_ID=550e8400-e29b-41d4-a716-446655440000
   ```

### Is CLIENT_ID required?

**No, CLIENT_ID is optional.** The client can typically identify itself using just the CLIENT_TOKEN. However, setting CLIENT_ID can provide:
- Faster client lookups
- Better logging and debugging
- Explicit client identification

### How is it used?

If provided, the client can use this ID for:
- Client identification in logs
- Caching client information
- Debugging and troubleshooting

---

## Security Best Practices

1. **Keep CLIENT_TOKEN Secret**
   - Never commit `.env` files to version control
   - Don't share tokens publicly
   - Treat tokens like passwords

2. **Rotate Tokens**
   - If a token is compromised, delete the old client record and create a new one
   - Update the token in your local client's `.env` file

3. **Limit Token Access**
   - Each client should have its own unique token
   - Don't reuse tokens across multiple installations

4. **Monitor Client Status**
   - Check "Last Heartbeat" in Django Admin to ensure clients are active
   - Offline clients may indicate connection or token issues

---

## Troubleshooting

### "Invalid client token" Error

- Verify the CLIENT_TOKEN is correct in your `.env` file
- Check for extra spaces or newlines in the token
- Ensure the client record exists in Django Admin
- Verify the token hasn't been changed in Django Admin

### "Missing or invalid authorization token" Error

- Ensure CLIENT_TOKEN is set in your `.env` file
- Check that the `.env` file is in the correct location
- Verify the file is being loaded by the application

### Client Status Shows "Offline"

- Check that the CLIENT_TOKEN is correct
- Verify the BACKEND_API_URL is accessible
- Check network connectivity
- Review application logs for errors

---

## Quick Reference

| Setting | Required | Example | Location |
|---------|----------|---------|----------|
| `CLIENT_TOKEN` | **Yes** | `abc123XYZ...` | Django Admin → CCTV → Local Recording Clients → client_token field |
| `CLIENT_ID` | No | `550e8400-...` | Django Admin → CCTV → Local Recording Clients → id field |

---

## Related Files

- `config.py` - Configuration management
- `api_client.py` - API client implementation
- `.env.example` - Example configuration file
- `install.sh` / `install.bat` - Installation scripts

