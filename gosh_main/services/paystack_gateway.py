"""
Paystack payment gateway implementation
"""
import requests
import hashlib
import hmac
from django.conf import settings
from django.urls import reverse
from decimal import Decimal
from typing import Dict, Any
import logging

from .payment_service import PaymentGateway

logger = logging.getLogger(__name__)


class PaystackGateway(PaymentGateway):
    """Paystack payment gateway implementation (popular in Nigeria)"""
    
    BASE_URL = 'https://api.paystack.co'
    
    def __init__(self, secret_key: str, public_key: str = None):
        """
        Initialize Paystack gateway
        
        Args:
            secret_key: Paystack secret key
            public_key: Paystack public key (optional, for frontend)
        """
        self.secret_key = secret_key
        self.public_key = public_key
        self.headers = {
            'Authorization': f'Bearer {secret_key}',
            'Content-Type': 'application/json',
        }
    
    def create_payment_session(self, order, amount: Decimal, currency: str = 'NGN') -> Dict[str, Any]:
        """
        Initialize a Paystack transaction
        
        Args:
            order: Order instance
            amount: Payment amount
            currency: Currency code (default: NGN)
            
        Returns:
            Dict with authorization_url, access_code, reference
        """
        try:
            # Convert amount to kobo (smallest unit for NGN)
            amount_kobo = int(amount * 100)
            
            # Generate unique reference
            reference = f"{order.order_number}-{order.id}"
            
            # Prepare request data
            data = {
                'email': order.user.email if order.user else 'customer@goshen.com',
                'amount': amount_kobo,
                'currency': currency,
                'reference': reference,
                'callback_url': settings.SITE_URL + reverse('gosh_main:payment_success') + f'?order={order.order_number}',
                'metadata': {
                    'order_number': order.order_number,
                    'order_id': str(order.id),
                    'customer_name': order.recipient_name,
                    'custom_fields': [
                        {
                            'display_name': 'Order Number',
                            'variable_name': 'order_number',
                            'value': order.order_number,
                        }
                    ]
                }
            }
            
            # Initialize transaction
            response = requests.post(
                f'{self.BASE_URL}/transaction/initialize',
                json=data,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('status'):
                data = result['data']
                logger.info(f"Created Paystack transaction {reference} for order {order.order_number}")
                
                return {
                    'success': True,
                    'checkout_url': data['authorization_url'],
                    'access_code': data['access_code'],
                    'reference': data['reference'],
                }
            else:
                logger.error(f"Paystack initialization failed: {result.get('message')}")
                return {
                    'success': False,
                    'error': result.get('message', 'Transaction initialization failed'),
                }
                
        except requests.RequestException as e:
            logger.error(f"Paystack API error: {str(e)}")
            return {
                'success': False,
                'error': f'API request failed: {str(e)}',
            }
        except Exception as e:
            logger.error(f"Error creating Paystack transaction: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def verify_payment(self, reference: str) -> Dict[str, Any]:
        """
        Verify Paystack transaction
        
        Args:
            reference: Transaction reference
            
        Returns:
            Dict with payment status and details
        """
        try:
            # Verify transaction
            response = requests.get(
                f'{self.BASE_URL}/transaction/verify/{reference}',
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('status'):
                data = result['data']
                
                # Map Paystack status to our status
                paystack_status = data.get('status', '').lower()
                if paystack_status == 'success':
                    status = 'paid'
                elif paystack_status == 'failed':
                    status = 'failed'
                else:
                    status = 'pending'
                
                return {
                    'success': True,
                    'status': status,
                    'amount': Decimal(data['amount']) / 100,
                    'currency': data['currency'],
                    'transaction_id': str(data.get('id')),
                    'reference': data['reference'],
                    'gateway_response': data.get('gateway_response'),
                    'paid_at': data.get('paid_at'),
                    'metadata': data.get('metadata', {}),
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'Verification failed'),
                }
                
        except requests.RequestException as e:
            logger.error(f"Paystack verification error: {str(e)}")
            return {
                'success': False,
                'error': f'Verification request failed: {str(e)}',
            }
        except Exception as e:
            logger.error(f"Error verifying Paystack payment: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def process_webhook(self, payload: Dict[str, Any], signature: str = None) -> Dict[str, Any]:
        """
        Process Paystack webhook event
        
        Args:
            payload: Webhook payload
            signature: Paystack signature header (x-paystack-signature)
            
        Returns:
            Dict with event details
        """
        try:
            # Verify webhook signature if provided
            if signature and self.secret_key:
                # Compute hash
                if isinstance(payload, dict):
                    import json
                    payload_str = json.dumps(payload)
                else:
                    payload_str = payload
                
                computed_signature = hmac.new(
                    self.secret_key.encode('utf-8'),
                    payload_str.encode('utf-8'),
                    hashlib.sha512
                ).hexdigest()
                
                if computed_signature != signature:
                    logger.error("Paystack webhook signature verification failed")
                    return {
                        'success': False,
                        'error': 'Invalid signature',
                    }
            
            # Parse event
            if isinstance(payload, str):
                import json
                event = json.loads(payload)
            else:
                event = payload
            
            event_type = event.get('event')
            data = event.get('data', {})
            
            # Handle different event types
            if event_type == 'charge.success':
                return {
                    'success': True,
                    'event_type': 'payment_completed',
                    'reference': data.get('reference'),
                    'transaction_id': str(data.get('id')),
                    'amount': Decimal(data.get('amount', 0)) / 100,
                    'status': 'completed',
                    'metadata': data.get('metadata', {}),
                }
            
            elif event_type == 'charge.failed':
                return {
                    'success': True,
                    'event_type': 'payment_failed',
                    'reference': data.get('reference'),
                    'transaction_id': str(data.get('id')),
                    'amount': Decimal(data.get('amount', 0)) / 100,
                    'status': 'failed',
                    'metadata': data.get('metadata', {}),
                }
            
            else:
                logger.info(f"Unhandled Paystack event type: {event_type}")
                return {
                    'success': True,
                    'event_type': event_type,
                    'status': 'ignored',
                }
                
        except Exception as e:
            logger.error(f"Error processing Paystack webhook: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
