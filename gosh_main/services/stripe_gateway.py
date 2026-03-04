"""
Stripe payment gateway implementation
"""
import stripe
from django.conf import settings
from django.urls import reverse
from decimal import Decimal
from typing import Dict, Any
import logging

from .payment_service import PaymentGateway

logger = logging.getLogger(__name__)


class StripeGateway(PaymentGateway):
    """Stripe payment gateway implementation"""
    
    def __init__(self, api_key: str, webhook_secret: str = None):
        """
        Initialize Stripe gateway
        
        Args:
            api_key: Stripe secret API key
            webhook_secret: Stripe webhook signing secret (optional)
        """
        self.api_key = api_key
        self.webhook_secret = webhook_secret
        stripe.api_key = api_key
    
    def create_payment_session(self, order, amount: Decimal, currency: str = 'NGN') -> Dict[str, Any]:
        """
        Create a Stripe Checkout Session
        
        Args:
            order: Order instance
            amount: Payment amount
            currency: Currency code (default: NGN)
            
        Returns:
            Dict with checkout_url, session_id
        """
        try:
            # Convert amount to cents/kobo (Stripe requires smallest currency unit)
            amount_cents = int(amount * 100)
            
            # Build line items from order
            line_items = []
            for item in order.items.all():
                line_items.append({
                    'price_data': {
                        'currency': currency.lower(),
                        'product_data': {
                            'name': item.product_name,
                        },
                        'unit_amount': int(item.product_price * 100),
                    },
                    'quantity': item.quantity,
                })
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=settings.SITE_URL + reverse('gosh_main:payment_success') + f'?session_id={{CHECKOUT_SESSION_ID}}&order={order.order_number}',
                cancel_url=settings.SITE_URL + reverse('gosh_main:payment_cancel') + f'?order={order.order_number}',
                client_reference_id=order.order_number,
                customer_email=order.user.email if order.user else None,
                metadata={
                    'order_number': order.order_number,
                    'order_id': str(order.id),
                }
            )
            
            logger.info(f"Created Stripe session {session.id} for order {order.order_number}")
            
            return {
                'success': True,
                'checkout_url': session.url,
                'session_id': session.id,
                'payment_intent_id': session.payment_intent,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating session: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def verify_payment(self, reference: str) -> Dict[str, Any]:
        """
        Verify Stripe payment session
        
        Args:
            reference: Stripe session ID or payment intent ID
            
        Returns:
            Dict with payment status and details
        """
        try:
            # Check if it's a session ID or payment intent ID
            if reference.startswith('cs_'):
                # It's a checkout session
                session = stripe.checkout.Session.retrieve(reference)
                
                return {
                    'success': True,
                    'status': session.payment_status,
                    'amount': Decimal(session.amount_total) / 100,
                    'currency': session.currency.upper(),
                    'transaction_id': session.payment_intent,
                    'metadata': session.metadata,
                }
            elif reference.startswith('pi_'):
                # It's a payment intent
                intent = stripe.PaymentIntent.retrieve(reference)
                
                return {
                    'success': True,
                    'status': intent.status,
                    'amount': Decimal(intent.amount) / 100,
                    'currency': intent.currency.upper(),
                    'transaction_id': intent.id,
                    'metadata': intent.metadata,
                }
            else:
                return {
                    'success': False,
                    'error': 'Invalid reference format',
                }
                
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error verifying payment: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def process_webhook(self, payload: Dict[str, Any], signature: str = None) -> Dict[str, Any]:
        """
        Process Stripe webhook event
        
        Args:
            payload: Raw webhook payload (bytes or dict)
            signature: Stripe signature header
            
        Returns:
            Dict with event details
        """
        try:
            if self.webhook_secret and signature:
                # Verify webhook signature
                event = stripe.Webhook.construct_event(
                    payload, signature, self.webhook_secret
                )
            else:
                # No signature verification (not recommended for production)
                event = payload if isinstance(payload, dict) else stripe.Event.construct_from(payload, stripe.api_key)
            
            event_type = event['type']
            
            # Handle different event types
            if event_type == 'checkout.session.completed':
                session = event['data']['object']
                return {
                    'success': True,
                    'event_type': 'payment_completed',
                    'order_number': session.get('client_reference_id') or session['metadata'].get('order_number'),
                    'transaction_id': session.get('payment_intent'),
                    'amount': Decimal(session['amount_total']) / 100,
                    'status': 'completed',
                }
            
            elif event_type == 'payment_intent.succeeded':
                intent = event['data']['object']
                return {
                    'success': True,
                    'event_type': 'payment_succeeded',
                    'transaction_id': intent['id'],
                    'amount': Decimal(intent['amount']) / 100,
                    'status': 'completed',
                    'metadata': intent.get('metadata', {}),
                }
            
            elif event_type == 'payment_intent.payment_failed':
                intent = event['data']['object']
                return {
                    'success': True,
                    'event_type': 'payment_failed',
                    'transaction_id': intent['id'],
                    'amount': Decimal(intent['amount']) / 100,
                    'status': 'failed',
                    'metadata': intent.get('metadata', {}),
                    'error': intent.get('last_payment_error', {}).get('message'),
                }
            
            else:
                logger.info(f"Unhandled Stripe event type: {event_type}")
                return {
                    'success': True,
                    'event_type': event_type,
                    'status': 'ignored',
                }
                
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Stripe webhook signature verification failed: {str(e)}")
            return {
                'success': False,
                'error': 'Invalid signature',
            }
        except Exception as e:
            logger.error(f"Error processing Stripe webhook: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
