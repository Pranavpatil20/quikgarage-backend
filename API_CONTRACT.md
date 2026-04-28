# QuikGarage API Contract (Starter)

## Auth

### POST `/api/auth/send-otp/`
Request:
```json
{ "phone_number": "9876543210" }
```
Response:
```json
{ "message": "OTP sent successfully.", "phone_number": "9876543210", "otp_dev_only": "123456" }
```

### POST `/api/auth/verify-otp/`
Request:
```json
{
  "phone_number": "9876543210",
  "otp_code": "123456",
  "role": "owner",
  "full_name": "Rahul Patil"
}
```

### POST `/api/auth/verify-firebase-otp/`
Request:
```json
{
  "firebase_id_token": "firebase_jwt_id_token",
  "role": "owner",
  "full_name": "Rahul Patil"
}
```
Response:
```json
{
  "user_id": 1,
  "full_name": "Rahul Patil",
  "phone_number": "+919876543210",
  "role": "owner",
  "refresh": "jwt_refresh",
  "access": "jwt_access"
}
```
Response:
```json
{
  "user_id": 1,
  "full_name": "Rahul Patil",
  "phone_number": "9876543210",
  "role": "owner",
  "refresh": "jwt_refresh",
  "access": "jwt_access"
}
```

## Customers (owner scope)
- `GET /api/customers/`
- `POST /api/customers/`
- `GET /api/customers/{id}/`
- `PATCH /api/customers/{id}/`

Create customer example:
```json
{
  "phone_number": "9999999999",
  "full_name": "Ravi",
  "vehicles": [
    { "vehicle_number": "MH12AB1234", "brand": "Honda", "model": "Activa" }
  ]
}
```

## Bookings
- `GET /api/bookings/?status=pending`
- `POST /api/bookings/`
- `POST /api/bookings/{id}/start_service/`
- `POST /api/bookings/{id}/complete/`
- `POST /api/bookings/{id}/cancel/`
- `GET /api/bookings/dashboard/`

Create booking example:
```json
{
  "customer": 1,
  "vehicle": 1,
  "service_type": "oil_change",
  "booking_date": "2026-04-27",
  "time_slot": "10:30:00",
  "notes": "Pickup requested"
}
```

## Invoices
- `GET /api/bookings/invoices/`
- `POST /api/bookings/invoices/`

Create invoice example:
```json
{
  "booking": 10,
  "service_cost": "1200.00",
  "parts_cost": "450.00",
  "is_paid": true
}
```
