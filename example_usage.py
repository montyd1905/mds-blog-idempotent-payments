"""
Example usage of the idempotency key generator.

This demonstrates how to use the PaymentIdentikit class and the
convenience function to generate idempotency keys for payment transactions.
"""

from datetime import datetime
from idempotency_key import (
    PaymentIdentikit,
    ClientType,
    generate_payment_idempotency_key
)


def example_1_using_class():
    """Example using the PaymentIdentikit class."""
    print("Example 1: Using PaymentIdentikit class")
    print("-" * 50)
    
    # Create a payment identikit
    identikit = PaymentIdentikit(
        receiver_bank_code="BANK001",
        receiver_account_number="1234567890",
        sender_bank_code="BANK002",
        sender_account_number="9876543210",
        transaction_amount=1000.50,
        client_type=ClientType.WEB_APP,
        client_location="US-CA-SF",
        internal_transaction_narration="PAYMENT",
        client_id="client-device-12345"
    )
    
    # Generate idempotency key
    idempotency_key = identikit.generate_idempotency_key()
    print(f"Idempotency Key: {idempotency_key}")
    print()


def example_2_using_convenience_function():
    """Example using the convenience function."""
    print("Example 2: Using convenience function")
    print("-" * 50)
    
    idempotency_key = generate_payment_idempotency_key(
        receiver_bank_code="BANK001",
        receiver_account_number="1234567890",
        sender_bank_code="BANK002",
        sender_account_number="9876543210",
        transaction_amount=1000.50,
        client_type=ClientType.MOBILE_APP,
        client_location="US-NY-NYC"
    )
    
    print(f"Idempotency Key: {idempotency_key}")
    print()


def example_3_idempotency_verification():
    """Example demonstrating idempotency - same transaction produces same key."""
    print("Example 3: Idempotency verification")
    print("-" * 50)
    
    # Create a transaction at a specific time
    transaction_time = datetime(2024, 1, 15, 14, 30, 0)
    
    identikit = PaymentIdentikit(
        receiver_bank_code="BANK001",
        receiver_account_number="1234567890",
        sender_bank_code="BANK002",
        sender_account_number="9876543210",
        transaction_amount=500.00,
        client_type=ClientType.WEB_API,
        client_location="US-TX-AUS"
    )
    
    # Generate key multiple times with same time
    key1 = identikit.generate_idempotency_key(transaction_time=transaction_time)
    key2 = identikit.generate_idempotency_key(transaction_time=transaction_time)
    key3 = identikit.generate_idempotency_key(transaction_time=transaction_time)
    
    print(f"Key 1: {key1}")
    print(f"Key 2: {key2}")
    print(f"Key 3: {key3}")
    print(f"All keys match: {key1 == key2 == key3}")
    print()


def example_4_timecode_intervals():
    """Example demonstrating how timecode intervals work."""
    print("Example 4: Timecode intervals (15-minute windows)")
    print("-" * 50)
    
    identikit = PaymentIdentikit(
        receiver_bank_code="BANK001",
        receiver_account_number="1234567890",
        sender_bank_code="BANK002",
        sender_account_number="9876543210",
        transaction_amount=100.00,
        client_type=ClientType.WEB_APP,
        client_location="US-CA-LA"
    )
    
    # Transactions at 14:00, 14:05, 14:10, 14:14 (all in same 15-min window)
    times = [
        datetime(2024, 1, 15, 14, 0, 0),
        datetime(2024, 1, 15, 14, 5, 0),
        datetime(2024, 1, 15, 14, 10, 0),
        datetime(2024, 1, 15, 14, 14, 0),
    ]
    
    print("Transactions within the same 15-minute interval:")
    for t in times:
        timecode = identikit.generate_timecode(transaction_time=t)
        key = identikit.generate_idempotency_key(transaction_time=t)
        print(f"  Time: {t.strftime('%Y-%m-%d %H:%M')} -> Timecode: {timecode} -> Key: {key[:16]}...")
    
    # Transaction at 14:15 (different 15-min window)
    t2 = datetime(2024, 1, 15, 14, 15, 0)
    timecode2 = identikit.generate_timecode(transaction_time=t2)
    key2 = identikit.generate_idempotency_key(transaction_time=t2)
    print(f"\nTransaction in different interval:")
    print(f"  Time: {t2.strftime('%Y-%m-%d %H:%M')} -> Timecode: {timecode2} -> Key: {key2[:16]}...")
    print()


def example_5_different_transactions():
    """Example showing different transactions produce different keys."""
    print("Example 5: Different transactions produce different keys")
    print("-" * 50)
    
    base_time = datetime(2024, 1, 15, 14, 30, 0)
    
    # Transaction 1: Different amount
    identikit1 = PaymentIdentikit(
        receiver_bank_code="BANK001",
        receiver_account_number="1234567890",
        sender_bank_code="BANK002",
        sender_account_number="9876543210",
        transaction_amount=100.00,
        client_type=ClientType.WEB_APP,
        client_location="US-CA-SF"
    )
    key1 = identikit1.generate_idempotency_key(transaction_time=base_time)
    
    # Transaction 2: Same as 1 but different amount
    identikit2 = PaymentIdentikit(
        receiver_bank_code="BANK001",
        receiver_account_number="1234567890",
        sender_bank_code="BANK002",
        sender_account_number="9876543210",
        transaction_amount=200.00,  # Different amount
        client_type=ClientType.WEB_APP,
        client_location="US-CA-SF"
    )
    key2 = identikit2.generate_idempotency_key(transaction_time=base_time)
    
    # Transaction 3: Same as 1 but different receiver
    identikit3 = PaymentIdentikit(
        receiver_bank_code="BANK003",  # Different receiver
        receiver_account_number="1234567890",
        sender_bank_code="BANK002",
        sender_account_number="9876543210",
        transaction_amount=100.00,
        client_type=ClientType.WEB_APP,
        client_location="US-CA-SF"
    )
    key3 = identikit3.generate_idempotency_key(transaction_time=base_time)
    
    print(f"Transaction 1 (amount: 100.00): {key1[:32]}...")
    print(f"Transaction 2 (amount: 200.00): {key2[:32]}...")
    print(f"Transaction 3 (different receiver): {key3[:32]}...")
    print(f"\nAll keys are unique: {len({key1, key2, key3}) == 3}")
    print()


if __name__ == "__main__":
    example_1_using_class()
    example_2_using_convenience_function()
    example_3_idempotency_verification()
    example_4_timecode_intervals()
    example_5_different_transactions()
    
    print("=" * 50)
    print("All examples completed!")

