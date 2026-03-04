"""
Flutterwave payment gateway implementation
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


class FlutterwaveGateway(PaymentGateway):
    """Flutterwave payment gateway implementation (Nigeria & Africa)"""
    
    BASE_URL = 'https://api.flutterwave.com/v3'
    
    def __init__(self, secret_key: str, public_key: str = None):
        """
        Initialize Flutterwave gateway
        
        Args:
            secret_key: Flutterwave secret key
            public_key: Flutterwave public key (optional, for frontend)
        """
        self.secret_key = secret_key
        self.public_key = public_key
        self.headers = {
            'Authorization': f'Bearer {secret_key}',
            'Content-Type': 'application/json',
        }
    
    def create_payment_session(self, order, amount: Decimal, currency: str = 'NGN') -> Dict[str, Any]:
        """
        Initialize a Flutterwave payment
        
        Args:
            order: Order instance
            amount: Payment amount
            currency: Currency code (default: NGN)
            
        Returns:
            Dict with payment_link, tx_ref
        """
        try:
            # Generate unique transaction reference
            tx_ref = f"FLW-{order.order_number}-{order.id}"
            
            # Prepare request data
            data = {
                'tx_ref': tx_ref,
                'amount': str(amount),
                'currency': currency,
                'redirect_url': settings.SITE_URL + reverse('gosh_main:payment_success') + f'?order={order.order_number}',
                'customer': {
                    'email': order.user.email if order.user else 'customer@goshen.com',
                    'name': order.recipient_name,
                    'phonenumber': order.phone,
                },
                'customizations': {
                    'title': 'Goshen Giant Food',
                    'description': f'Payment for order {order.order_number}',
                    'logo': settings.SITE_URL + '/static/gosh_main/images/logo.png',
                },
                'meta': {
                    'order_number': order.order_number,
                    'order_id': str(order.id),
                }
            }
            
            # Initialize payment
            logger.info(f"Sending Flutterwave API request: {data}")
            print(f"DEBUG FLW: Request data = {data}")  # Console debug
            
            response = requests.post(
                f'{self.BASE_URL}/payments',
                json=data,
                headers=self.headers,
                timeout=30
            )
            
            logger.info(f"Flutterwave API response status: {response.status_code}")
            print(f"DEBUG FLW: Response status = {response.status_code}")  # Console debug
            print(f"DEBUG FLW: Response body = {response.text}")  # Console debug
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Flutterwave API result: {result}")
            
            if result.get('status') == 'success':
                data = result['data']
                logger.info(f"Created Flutterwave payment {tx_ref} for order {order.order_number}")
                
                return {
                    'success': True,
                    'checkout_url': data['link'],
                    'tx_ref': tx_ref,
                }
            else:
                logger.error(f"Flutterwave initialization failed: {result.get('message')}")
                return {
                    'success': False,
                    'error': result.get('message', 'Payment initialization failed'),
                }
                
        except requests.RequestException as e:
            logger.error(f"Flutterwave API error: {str(e)}")
            print(f"DEBUG FLW: API Exception = {str(e)}")  # Console debug
            if hasattr(e, 'response') and e.response is not None:
                print(f"DEBUG FLW: Error response = {e.response.text}")  # Console debug
            return {
                'success': False,
                'error': f'API request failed: {str(e)}',
            }
        except Exception as e:
            logger.error(f"Error creating Flutterwave payment: {str(e)}")
            print(f"DEBUG FLW: General Exception = {str(e)}")  # Console debug
            return {
                'success': False,
                'error': str(e),
            }
    
    def verify_payment(self, reference: str) -> Dict[str, Any]:
        """
        Verify Flutterwave transaction
        
        Args:
            reference: Transaction ID
            
        Returns:
            Dict with payment status and details
        """
        try:
            # Verify transaction
            response = requests.get(
                f'{self.BASE_URL}/transactions/{reference}/verify',
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') == 'success':
                data = result['data']
                
                # Map Flutterwave status to our status
                flw_status = data.get('status', '').lower()
                if flw_status == 'successful':
                    status = 'paid'
                elif flw_status == 'failed':
                    status = 'failed'
                else:
                    status = 'pending'
                
                return {
                    'success': True,
                    'status': status,
                    'amount': Decimal(str(data.get('amount', 0))),
                    'currency': data.get('currency'),
                    'transaction_id': str(data.get('id')),
                    'tx_ref': data.get('tx_ref'),
                    'card_type': data.get('card', {}).get('type'),
                    'metadata': data.get('meta', {}),
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'Verification failed'),
                }
                
        except requests.RequestException as e:
            logger.error(f"Flutterwave verification error: {str(e)}")
            return {
                'success': False,
                'error': f'Verification request failed: {str(e)}',
            }
        except Exception as e:
            logger.error(f"Error verifying Flutterwave payment: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def process_webhook(self, payload: Dict[str, Any], signature: str = None) -> Dict[str, Any]:
        """
        Process Flutterwave webhook event
        
        Args:
            payload: Webhook payload
            signature: Flutterwave signature header (verif-hash)
            
        Returns:
            Dict with event details
        """
        try:
            # Verify webhook signature if provided
            if signature:
                # Flutterwave sends the secret hash in the header
                webhook_secret = getattr(settings, 'FLUTTERWAVE_WEBHOOK_SECRET', self.secret_key)
                if signature != webhook_secret:
                    logger.error("Flutterwave webhook signature verification failed")
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
            if event_type == 'charge.completed':
                status = data.get('status', '').lower()
                
                if status == 'successful':
                    return {
                        'success': True,
                        'event_type': 'payment_completed',
                        'tx_ref': data.get('tx_ref'),
                        'transaction_id': str(data.get('id')),
                        'amount': Decimal(str(data.get('amount', 0))),
                        'status': 'completed',
                        'metadata': data.get('meta', {}),
                    }
                else:
                    return {
                        'success': True,
                        'event_type': 'payment_failed',
                        'tx_ref': data.get('tx_ref'),
                        'transaction_id': str(data.get('id')),
                        'amount': Decimal(str(data.get('amount', 0))),
                        'status': 'failed',
                        'metadata': data.get('meta', {}),
                    }
            
            else:
                logger.info(f"Unhandled Flutterwave event type: {event_type}")
                return {
                    'success': True,
                    'event_type': event_type,
                    'status': 'ignored',
                }
                
        except Exception as e:
            logger.error(f"Error processing Flutterwave webhook: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
