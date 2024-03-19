from celery import shared_task
from django.core.mail import send_mail
from datetime import timedelta
from django.utils import timezone
from .models import Product
from django.conf import settings
from django.utils.http import urlsafe_base64_encode 
from django.utils.encoding import force_bytes

@shared_task
def send_deactivation_email(product, user_email):
    # Generate activation token
    token = urlsafe_base64_encode(force_bytes(product.id))

    activation_link = f"http://127.0.0.1:8000/api/activate/{token}"
    subject = 'Product Deactivation Notification'
    message = f'Your product (Name: {product.name}) has been deactivated. Please click on the following link to activate your product:\n\n{activation_link}'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user_email]
    send_mail(subject, message, from_email, recipient_list)



@shared_task
def deactivate_expired_products():
    # Calculate the date 30 days ago
    thirty_days_ago = timezone.now() - timedelta(days=30)

    # Query for products that have been active for more than 30 days
    expired_products = Product.objects.filter(is_active=True, created_at__lte=thirty_days_ago)
    print(expired_products)

    # Deactivate each expired product and send deactivation email asynchronously
    for product in expired_products:
        product.is_active = False
        product.save()
        send_deactivation_email(product, product.creator_email)