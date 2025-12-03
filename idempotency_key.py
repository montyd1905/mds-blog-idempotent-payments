"""
Idempotency Key Generator for Payment Transactions

This module implements the idempotency key scheme described in the article
"A Better Way to Implement Idempotent Payments". The key is generated from
payment metadata components to ensure that duplicate transactions within
a time interval are correctly identified.
"""

import hashlib
from datetime import datetime
from typing import Optional
from enum import Enum


class ClientType(Enum):
    """Enumeration of client types that can initiate payments."""
    WEB_APP = "web_app"
    MOBILE_APP = "mobile_app"
    WEB_API = "web_api"
    DESKTOP_APP = "desktop_app"
    OTHER = "other"


class PaymentIdentikit:
    """
    Payment Identikit - A collection of discrete payment signatures
    that uniquely identify a payment transaction.
    
    Components:
    - RBC: Receiver's Bank Code
    - RAN: Receiver's Account Number
    - SBC: Sender's Bank Code
    - SAN: Sender's Account Number
    - TTC: Transaction Timecode (15-minute interval)
    - TAMT: Transaction Amount
    - ITN: Internal Transaction Narration (optional)
    - CTYPE: Client Type
    - CID: Client ID (optional)
    - CLOC: Client Location
    """
    
    def __init__(
        self,
        receiver_bank_code: str,
        receiver_account_number: str,
        sender_bank_code: str,
        sender_account_number: str,
        transaction_amount: float,
        client_type: ClientType,
        client_location: str,
        internal_transaction_narration: Optional[str] = None,
        client_id: Optional[str] = None,
        timecode_interval_minutes: int = 15
    ):
        """
        Initialize a Payment Identikit.
        
        Args:
            receiver_bank_code: Receiver's Bank Code (RBC)
            receiver_account_number: Receiver's Account Number (RAN)
            sender_bank_code: Sender's Bank Code (SBC)
            sender_account_number: Sender's Account Number (SAN)
            transaction_amount: Transaction Amount (TAMT)
            client_type: Client Type (CTYPE) - enum value
            client_location: Client Location (CLOC)
            internal_transaction_narration: Internal Transaction Narration (ITN), defaults to ""
            client_id: Client ID (CID), defaults to ""
            timecode_interval_minutes: Time interval in minutes for timecode generation, defaults to 15
        """
        self.receiver_bank_code = receiver_bank_code.upper().strip()
        self.receiver_account_number = receiver_account_number.strip()
        self.sender_bank_code = sender_bank_code.upper().strip()
        self.sender_account_number = sender_account_number.strip()
        self.transaction_amount = transaction_amount
        self.client_type = client_type
        self.client_location = client_location.strip()
        self.internal_transaction_narration = internal_transaction_narration or ""
        self.client_id = client_id or ""
        self.timecode_interval_minutes = timecode_interval_minutes
        
        # Validate required fields
        self._validate()
    
    def _validate(self):
        """Validate that all required fields are present."""
        required_fields = [
            ("receiver_bank_code", self.receiver_bank_code),
            ("receiver_account_number", self.receiver_account_number),
            ("sender_bank_code", self.sender_bank_code),
            ("sender_account_number", self.sender_account_number),
            ("client_location", self.client_location),
        ]
        
        for field_name, field_value in required_fields:
            if not field_value:
                raise ValueError(f"{field_name} cannot be empty")
        
        if self.transaction_amount <= 0:
            raise ValueError("transaction_amount must be greater than 0")
    
    def generate_timecode(self, transaction_time: Optional[datetime] = None) -> str:
        """
        Generate a transaction timecode (TTC) based on a time interval.
        
        The timecode represents a time band that "locks" a unique transaction
        for a specific interval (default 15 minutes). This prevents duplicate
        transactions within the same time interval.
        
        Args:
            transaction_time: The transaction timestamp. If None, uses current time.
            
        Returns:
            A string representing the timecode in format: YYYYMMDDHHMM
        """
        if transaction_time is None:
            transaction_time = datetime.utcnow()
        
        # Calculate the timecode interval
        # Round down to the nearest interval
        minutes = transaction_time.minute
        interval_minutes = self.timecode_interval_minutes
        rounded_minutes = (minutes // interval_minutes) * interval_minutes
        
        # Create timecode: YYYYMMDDHHMM (where MM is the rounded minute)
        timecode = transaction_time.strftime(f"%Y%m%d%H{rounded_minutes:02d}")
        
        return timecode
    
    def generate_idempotency_key(
        self,
        transaction_time: Optional[datetime] = None,
        hash_algorithm: str = "sha256"
    ) -> str:
        """
        Generate an idempotency key from the payment identikit components.
        
        The key is generated by separately hashing the receiver and sender
        components, then joining both hashes with a period delimiter.
        This ensures that:
        1. The same transaction (same metadata) produces the same key
        2. Different transactions produce different keys
        3. Duplicate transactions within the same time interval are detected
        
        Args:
            transaction_time: The transaction timestamp. If None, uses current time.
            hash_algorithm: The hashing algorithm to use (default: sha256)
            
        Returns:
            A string representing the idempotency key in format: receiver_hash.sender_hash
        """
        timecode = self.generate_timecode(transaction_time)
        
        # Build receiver-side components: RBC|RAN
        receiver_string = "|".join([
            self.receiver_bank_code,
            self.receiver_account_number
        ])
        
        # Build sender-side components: SBC|SAN|TTC|TAMT|ITN|CTYPE|CID|CLOC
        sender_string = "|".join([
            self.sender_bank_code,
            self.sender_account_number,
            timecode,
            f"{self.transaction_amount:.2f}",  # Format amount to 2 decimal places
            self.internal_transaction_narration,
            self.client_type.value,
            self.client_id,
            self.client_location
        ])
        
        # Generate separate hashes for receiver and sender
        receiver_hash_obj = hashlib.new(hash_algorithm)
        receiver_hash_obj.update(receiver_string.encode('utf-8'))
        receiver_hash = receiver_hash_obj.hexdigest()
        
        sender_hash_obj = hashlib.new(hash_algorithm)
        sender_hash_obj.update(sender_string.encode('utf-8'))
        sender_hash = sender_hash_obj.hexdigest()
        
        # Join both hashes with a period delimiter
        idempotency_key = f"{receiver_hash}.{sender_hash}"
        
        return idempotency_key


def generate_payment_idempotency_key(
    receiver_bank_code: str,
    receiver_account_number: str,
    sender_bank_code: str,
    sender_account_number: str,
    transaction_amount: float,
    client_type: ClientType,
    client_location: str,
    internal_transaction_narration: Optional[str] = None,
    client_id: Optional[str] = None,
    transaction_time: Optional[datetime] = None,
    timecode_interval_minutes: int = 15,
    hash_algorithm: str = "sha256"
) -> str:
    """
    Convenience function to generate an idempotency key directly.
    
    Args:
        receiver_bank_code: Receiver's Bank Code (RBC)
        receiver_account_number: Receiver's Account Number (RAN)
        sender_bank_code: Sender's Bank Code (SBC)
        sender_account_number: Sender's Account Number (SAN)
        transaction_amount: Transaction Amount (TAMT)
        client_type: Client Type (CTYPE)
        client_location: Client Location (CLOC)
        internal_transaction_narration: Internal Transaction Narration (ITN), optional
        client_id: Client ID (CID), optional
        transaction_time: Transaction timestamp, optional (defaults to now)
        timecode_interval_minutes: Time interval for timecode, defaults to 15
        hash_algorithm: Hashing algorithm, defaults to sha256
        
    Returns:
        A string representing the idempotency key in format: receiver_hash.sender_hash
    """
    identikit = PaymentIdentikit(
        receiver_bank_code=receiver_bank_code,
        receiver_account_number=receiver_account_number,
        sender_bank_code=sender_bank_code,
        sender_account_number=sender_account_number,
        transaction_amount=transaction_amount,
        client_type=client_type,
        client_location=client_location,
        internal_transaction_narration=internal_transaction_narration,
        client_id=client_id,
        timecode_interval_minutes=timecode_interval_minutes
    )
    
    return identikit.generate_idempotency_key(
        transaction_time=transaction_time,
        hash_algorithm=hash_algorithm
    )

