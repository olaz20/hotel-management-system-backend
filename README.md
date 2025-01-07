

# Django Booking and Payment API

This project is a comprehensive Django-based API for managing user authentication, room bookings, payment processing, and related features. It incorporates authentication, nested routing, and integration with Stripe for payments.

## Features

### User Management
- **Signup**: Create a new user account.
- **Email Verification**: Verify user email with a code.
- **Login/Logout**: Manage user authentication sessions.
- **Password Reset**: Request and validate password reset operations.

### Booking Management
- **Room Categories**: Manage different categories of rooms.
- **Room Details**: Manage room data and reviews for specific rooms.
- **User Bookings**: Create, retrieve, and manage bookings for authenticated users.
- **Booking History**: View a history of user bookings.

### Payment Integration
- **Stripe Checkout**: Initiate and manage payments for bookings.
- **Payment Status**: Handle successful and canceled payment sessions.
- **Webhook Integration**: Receive Stripe webhooks for payment events.

## API Endpoints

### Authentication Endpoints
1. **Token Obtain Pair**
   - **URL**: `/api/token/`
   - **View**: `TokenObtainPairView`
   - **Description**: Obtain JWT access and refresh tokens.

2. **Token Refresh**
   - **URL**: `/api/token/refresh/`
   - **View**: `TokenRefreshView`
   - **Description**: Refresh the JWT access token.

3. **Signup**
   - **URL**: `/signup/`
   - **View**: `views.SignUpView`
   - **Description**: Create a new user account.

4. **Email Verification**
   - **URL**: `/email-verify/`
   - **View**: `views.EmailVerifyView`
   - **Description**: Verify a user's email.

5. **Password Reset Workflow**
   - **URL**: `/request-reset-email/`
   - **Description**: Request a password reset email.
   - **URL**: `/password-reset/<uidb64>/<token>/`
   - **Description**: Confirm password reset token.
   - **URL**: `/validate-reset-otp/`
   - **Description**: Validate OTP for password reset.
   - **URL**: `/password-reset-complete/`
   - **Description**: Complete password reset.

### Room and Booking Endpoints
1. **Room Categories**
   - **URL**: `/categories/`
   - **View**: `views.RoomTypeViewSet`
   - **Description**: Manage room categories.

2. **Rooms**
   - **URL**: `/rooms/`
   - **View**: `views.RoomViewSet`
   - **Description**: Manage rooms.

3. **Room Reviews**
   - **URL**: `/rooms/<room_pk>/reviews/`
   - **View**: `views.ReviewViewSet`
   - **Description**: Manage reviews for specific rooms.

4. **Bookings**
   - **URL**: `/bookings/`
   - **View**: `views.BookingViewSet`
   - **Description**: Create and manage bookings.

5. **Booking History**
   - **URL**: `/booking-history/`
   - **View**: `views.BookingHistoryView`
   - **Description**: View user's booking history.

### Payment Endpoints
1. **Stripe Checkout Session**
   - **URL**: `/create-checkout-session/<int:booking_id>/`
   - **View**: `views.create_checkout_session`
   - **Description**: Create a Stripe checkout session for a booking.

2. **Payment Success**
   - **URL**: `/payment/success/`
   - **View**: `views.payment_success`
   - **Description**: Handle successful payments.

3. **Payment Cancel**
   - **URL**: `/payment/cancel/`
   - **View**: `views.payment_cancel`
   - **Description**: Handle canceled payments.

4. **Stripe Webhook**
   - **URL**: `/stripe-webhook/`
   - **View**: `views.stripe_webhook`
   - **Description**: Handle Stripe webhook events.

## Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone <repository_url>
   cd <repository_name>
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Start the Development Server**:
   ```bash
   python manage.py runserver
   ```

5. **Access the API**:
   Navigate to `http://127.0.0.1:8000/` in your browser or use an API client like Postman.

## File Structure

- **`urls.py`**: Contains all routes and endpoint configurations.
- **`views.py`**: Implements the logic for handling API requests.
- **`models.py`**: Defines the database schema for users, rooms, bookings, etc.
- **`serializers.py`**: (if applicable) Serializes data for API communication.
- **`tests.py`**: (if applicable) Unit tests for the API.



-  detailed documentation for each endpoint using tools like Postman
  https://crimson-robot-501047.postman.co/workspace/New-Team-Workspace~b65e46e7-6d79-49c6-b3f2-d8eced2b90b8/collection/37670289-84146a43-6004-4aff-b902-3eef48dccba2?action=share&creator=37670289&active-environment=37670289-7d4bb8cc-8e47-4ab9-8dff-d1978b3617c5
- role-based access control for specific actions.
- pagination and filtering for room and booking listings.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

