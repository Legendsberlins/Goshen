"""
Payment service infrastructure for handling multiple payment gateways
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class PaymentGateway(ABC):
    """Abstract base class for payment gateways"""
    
    @abstractmethod
    def create_payment_session(self, order, amount: Decimal, currency: str = 'NGN') -> Dict[str, Any]:
        """
        Create a payment session/checkout
        
        Returns:
            Dict containing payment_url, session_id, and any other relevant data
        """
        pass
    
    @abstractmethod
    def verify_payment(self, reference: str) -> Dict[str, Any]:
        """
        Verify payment status
        
        Returns:
            Dict containing status, amount, and transaction details
        """
        pass
    
    @abstractmethod
    def process_webhook(self, payload: Dict[str, Any], signature: str = None) -> Dict[str, Any]:
        """
        Process webhook notification from payment gateway
        
        Returns:
            Dict containing status and transaction details
        """
        pass


class PaymentService:
    """
    Main payment service that routes requests to appropriate gateway
    """
    
    def __init__(self):
        self.gateways = {}
    
    def register_gateway(self, name: str, gateway: PaymentGateway):
        """Register a payment gateway"""
        self.gateways[name] = gateway
        logger.info(f"Registered payment gateway: {name}")
    
    def get_gateway(self, name: str) -> Optional[PaymentGateway]:
        """Get a registered gateway by name"""
        return self.gateways.get(name)
    
    def create_payment(self, gateway_name: str, order, amount: Decimal, currency: str = 'NGN') -> Dict[str, Any]:
        """
        Create a payment session using the specified gateway
        
        Args:
            gateway_name: Name of the payment gateway to use
            order: Order instance
            amount: Payment amount
            currency: Currency code (default: NGN)
            
        Returns:
            Dict with payment details
        """
        logger.info(f"Looking for gateway: {gateway_name}, available: {list(self.gateways.keys())}")
        print(f"DEBUG PS: Requested gateway = {gateway_name}, registered = {list(self.gateways.keys())}")
        
        gateway = self.get_gateway(gateway_name)
        if not gateway:
            error_msg = f"Payment gateway '{gateway_name}' not found"
            logger.error(error_msg)
            print(f"DEBUG PS: {error_msg}")
            raise ValueError(error_msg)
        
        try:
            logger.info(f"Calling create_payment_session on {gateway_name} gateway")
            result = gateway.create_payment_session(order, amount, currency)
            logger.info(f"Created payment session for order {order.order_number} via {gateway_name}")
            return result
        except Exception as e:
            logger.error(f"Error creating payment via {gateway_name}: {str(e)}", exc_info=True)
            print(f"DEBUG PS: Exception in create_payment - {str(e)}")
            raise
    
    def verify_payment(self, gateway_name: str, reference: str) -> Dict[str, Any]:
        """Verify payment status"""
        gateway = self.get_gateway(gateway_name)
        if not gateway:
            raise ValueError(f"Payment gateway '{gateway_name}' not found")
        
        try:
            result = gateway.verify_payment(reference)
            logger.info(f"Verified payment {reference} via {gateway_name}: {result.get('status')}")
            return result
        except Exception as e:
            logger.error(f"Error verifying payment via {gateway_name}: {str(e)}")
            raise
    
    def process_webhook(self, gateway_name: str, payload: Dict[str, Any], signature: str = None) -> Dict[str, Any]:
        """Process webhook from payment gateway"""
        gateway = self.get_gateway(gateway_name)
        if not gateway:
            raise ValueError(f"Payment gateway '{gateway_name}' not found")
        
        try:
            result = gateway.process_webhook(payload, signature)
            logger.info(f"Processed webhook from {gateway_name}")
            return result
        except Exception as e:
            logger.error(f"Error processing webhook from {gateway_name}: {str(e)}")
            raise


# Global payment service instance
payment_service = PaymentService()
