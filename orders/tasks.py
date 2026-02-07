from celery import shared_task
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from .models import Order
from products.models import ProductVariant
from carts.models import Cart
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_order_payment(order_id):
    try:
        with transaction.atomic():
            # Lock the Order row to prevent any other process from touching it
            order = Order.objects.select_for_update().get(id=order_id)

            # Idempotency Check: In case the user refreshes the callback page
            if order.status == 'confirmed':
                return f"Order {order_id} already confirmed."

            # Get and sort Variant IDs to prevent Deadlocks
            variant_ids = sorted([item.variant_snapshot.get('id') for item in order.items.all()])
            
            # Lock the ProductVariant rows
            variants = ProductVariant.objects.select_for_update().filter(id__in=variant_ids)

            # Stock Check
            for item in order.items.all():
                v_id = item.variant_snapshot.get('id')
                variant = variants.get(id=v_id)
                if variant.stock_quantity < item.quantity:
                    order.status = 'cancelled'
                    order.save()

                    # Send Email to user
                    send_mail(
                        subject=f"Order Cancelled: #{order.id}",
                        message="You tried to make an order but oops! didn't work🙂",
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[order.user.email],
                        fail_silently=True,
                    )
                    logger.warning(f'Order {order_id} cancelled as a result of low stock')
                    return f"Stock low for {variant.variant_name}. Order #{order_id} cancelled."

            # Deduct Stock & Update Order
            for item in order.items.all():
                v_id = item.variant_snapshot.get('id')
                variant = variants.get(id=v_id)
                variant.stock_quantity -= item.quantity
                variant.save()

            order.status = 'confirmed'
            order.save()

            # Clear the User's Cart
            user_cart = Cart.objects.get(user=order.user)
            user_cart.items.all().delete()
            user_cart.save()

            # Send Email to user
            send_mail(
                subject=f"Order Confirmed: #{order.id}",
                message="Thank you for your purchase! Your order is being processed ASAP.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[order.user.email],
                fail_silently=False,
            )
            logger.info(f'Order {order_id} made succesfully by {order.user.email}')
            return f"Order {order_id} successful: Stock updated and cart cleared."

    except Order.DoesNotExist:
        return f"Error: Order {order_id} not found."
    except Exception as e:
        order.status = 'cancelled'
        order.save()

        # Send Email to user
        send_mail(
            subject=f"Order Cancelled: #{order.id}",
            message="You tried to make an order but oops! didn't work🙂",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[order.user.email],
            fail_silently=True,
        )
        logger.error(f'Unexpected Error: {str(e)} while processing order {order_id}')
        return f"Unexpected Error: {str(e)}"