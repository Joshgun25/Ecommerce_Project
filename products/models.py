from django.db import models
from authentication.models import CustomUser
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    creator_email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, default=None)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='products/product_images/', default='default_image.jpg')

    def __str__(self):
        return self.name
    
    def deactivate(self):
        self.is_active = False
        self.save()

    def activate(self):
        self.is_active = True
        self.save()

    def is_deactivated(self):
        return not self.is_active
    

class Comment(models.Model):
    product = models.ForeignKey(Product, related_name='comments', on_delete=models.CASCADE)
    user_email = models.EmailField()
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user_email} on {self.product.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.send_notification()

    def send_notification(self):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"product_{self.product.id}",
            {
                "type": "comment_notification",
                "comment": {
                    "user_email": self.user_email,
                    "text": self.text,
                    "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        )