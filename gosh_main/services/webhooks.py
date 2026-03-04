"""
Webhook handlers for payment gateways
"""
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from decimal import Decimal
import json
import logging

from ..models import Order, Payment
from .payment_service import payment_service

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Handle Stripe webhook events
    """
    try:
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        # Process webhook
        result = payment_service.process_webhook('stripe', payload, sig_header)
        
        if not result.get('success'):
            logger.error(f"Stripe webhook processing failed: {result.get('error')}")
            return JsonResponse({'error': result.get('error')}, status=400)
        
        # Handle the event
        event_type = result.get('event_type')
        
        if event_type in ['payment_completed', 'payment_succeeded']:
            # Update order and payment status
            order_number = result.get('order_number')
            if order_number:
                try:
                    order = Order.objects.get(order_number=order_number)
                    
                    # Create or update payment record
                    payment, created = Payment.objects.get_or_create(
                        order=order,
                        gateway_transaction_id=result.get('transaction_id'),
                        defaults={
                            'payment_method': 'stripe',
                            'amount': result.get('amount', order.total),
                            'status': 'completed',
                            'gateway_reference': result.get('transaction_id'),
                        }
                    )
                    
                    if not created:
                        payment.status = 'completed'
                        payment.completed_at = timezone.now()
                        payment.save()
                    else:
                        payment.completed_at = timezone.now()
                        payment.save()
                    
                    # Update order payment status
                    order.payment_status = 'paid'
                    order.status = 'processing'
                    order.save()
                    
                    logger.info(f"Order {order_number} marked as paid via Stripe")
                    
                    # Send confirmation email
                    from .email_service import send_order_confirmation_email
                    send_order_confirmation_email(order)
                    
                except Order.DoesNotExist:
                    logger.error(f"Order {order_number} not found for Stripe webhook")
        
        elif event_type == 'payment_failed':
            # Mark payment as failed
            transaction_id = result.get('transaction_id')
            if transaction_id:
                try:
                    payment = Payment.objects.get(gateway_transaction_id=transaction_id)
                    payment.status = 'failed'
                    payment.save()
                    
                    payment.order.payment_status = 'failed'
                    payment.order.save()
                    
                    logger.info(f"Payment {transaction_id} marked as failed")
                except Payment.DoesNotExist:
                    logger.error(f"Payment {transaction_id} not found for failure update")
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Error in Stripe webhook handler: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def paystack_webhook(request):
    """
    Handle Paystack webhook events
    """
    try:
        payload = request.body.decode('utf-8')
        sig_header = request.META.get('HTTP_X_PAYSTACK_SIGNATURE')
        
        # Process webhook
        result = payment_service.process_webhook('paystack', payload, sig_header)
        
        if not result.get('success'):
            logger.error(f"Paystack webhook processing failed: {result.get('error')}")
            return HttpResponse(status=400)
        
        # Handle the event
        event_type = result.get('event_type')
        
        if event_type == 'payment_completed':
            # Extract order number from reference
            reference = result.get('reference', '')
            metadata = result.get('metadata', {})
            
            order_number = metadata.get('order_number')
            if not order_number and '-' in reference:
                # Try to extract from reference format: ORDER-XXX-YYY-id
                parts = reference.rsplit('-', 1)
                if parts:
                    order_number = parts[0]
            
            if order_number:
                try:
                    order = Order.objects.get(order_number=order_number)
                    
                    # Create or update payment record
                    payment, created = Payment.objects.get_or_create(
                        order=order,
                        gateway_reference=reference,
                        defaults={
                            'payment_method': 'paystack',
                            'amount': result.get('amount', order.total),
                            'status': 'completed',
                            'gateway_transaction_id': result.get('transaction_id'),
                        }
                    )
                    
                    if not created:
                        payment.status = 'completed'
                        payment.gateway_transaction_id = result.get('transaction_id')
                        payment.completed_at = timezone.now()
                        payment.save()
                    else:
                        payment.completed_at = timezone.now()
                        payment.save()
                    
                    # Update order payment status
                    order.payment_status = 'paid'
                    order.status = 'processing'
                    order.save()
                    
                    logger.info(f"Order {order_number} marked as paid via Paystack")
                    
                    # Send confirmation email
                    from .email_service import send_order_confirmation_email
                    send_order_confirmation_email(order)
                    
                except Order.DoesNotExist:
                    logger.error(f"Order {order_number} not found for Paystack webhook")
        
        elif event_type == 'payment_failed':
            reference = result.get('reference', '')
            try:
                payment = Payment.objects.get(gateway_reference=reference)
                payment.status = 'failed'
                payment.save()
                
                payment.order.payment_status = 'failed'
                payment.order.save()
                
                logger.info(f"Payment {reference} marked as failed")
            except Payment.DoesNotExist:
                logger.error(f"Payment {reference} not found for failure update")
        
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.error(f"Error in Paystack webhook handler: {str(e)}")
        return HttpResponse(status=500)

@csrf_exempt
@require_http_methods(["POST"])
def flutterwave_webhook(request):
    """
    Handle Flutterwave webhook events
    """
    try:
        payload = request.body.decode('utf-8')
        sig_header = request.META.get('HTTP_VERIF_HASH')
        
        # Process webhook
        result = payment_service.process_webhook('flutterwave', payload, sig_header)
        
        if not result.get('success'):
            logger.error(f"Flutterwave webhook processing failed: {result.get('error')}")
            return HttpResponse(status=400)
        
        # Handle the event
        event_type = result.get('event_type')
        
        if event_type == 'payment_completed':
            # Extract order number from tx_ref
            tx_ref = result.get('tx_ref', '')
            metadata = result.get('metadata', {})
            
            order_number = metadata.get('order_number')
            if not order_number and '-' in tx_ref:
                # Try to extract from tx_ref format: FLW-ORDER-XXX-YYY-id
                parts = tx_ref.split('-', 1)
                if len(parts) > 1:
                    order_part = parts[1].rsplit('-', 1)[0]
                    order_number = order_part
            
            if order_number:
                try:
                    order = Order.objects.get(order_number=order_number)
                    
                    # Create or update payment record
                    payment, created = Payment.objects.get_or_create(
                        order=order,
                        gateway_reference=tx_ref,
                        defaults={
                            'payment_method': 'flutterwave',
                            'amount': result.get('amount', order.total),
                            'status': 'completed',
                            'gateway_transaction_id': result.get('transaction_id'),
                        }
                    )
                    
                    if not created:
                        payment.status = 'completed'
                        payment.gateway_transaction_id = result.get('transaction_id')
                        payment.completed_at = timezone.now()
                        payment.save()
                    else:
                        payment.completed_at = timezone.now()
                        payment.save()
                    
                    # Update order payment status
                    order.payment_status = 'paid'
                    order.status = 'processing'
                    order.save()
                    
                    logger.info(f"Order {order_number} marked as paid via Flutterwave")
                    
                    # Send confirmation email
                    from .email_service import send_order_confirmation_email
                    send_order_confirmation_email(order)
                    
                except Order.DoesNotExist:
                    logger.error(f"Order {order_number} not found for Flutterwave webhook")
        
        elif event_type == 'payment_failed':
            tx_ref = result.get('tx_ref', '')
            try:
                payment = Payment.objects.get(gateway_reference=tx_ref)
                payment.status = 'failed'
                payment.save()
                
                payment.order.payment_status = 'failed'
                payment.order.save()
                
                logger.info(f"Payment {tx_ref} marked as failed")
            except Payment.DoesNotExist:
                logger.error(f"Payment {tx_ref} not found for failure update")
        
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.error(f"Error in Flutterwave webhook handler: {str(e)}")
        return HttpResponse(status=500)