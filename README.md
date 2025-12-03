# A Better Way to Implement Idempotent Payments

![idempotent-payments](https://montydimkpa-fyi-public.sfo3.cdn.digitaloceanspaces.com/media/payment-idempotency.png)

Idempotency in payments involves ensuring that a payment is only processed once, no matter how many times it is retried.

The goal is to prevent duplicate payment processing (double-debits, double-credits or wasted compute cycles repeating failed transactions).

## Building a payment identikit

The key to idempotency lies in correctly identifying a unique transaction; we must be able to determine that the same transaction is being repeated, even if the timestamp and other metadata are different.

We achieve this using a **payment identikit**; that is, a collection of discrete payment signatures that are unique to an individual payment transaction.

### Identikit components

![image1](https://montydimkpa-fyi-public.sfo3.cdn.digitaloceanspaces.com/media/articles/payment-idempotency/payment-image-1.png)

When it comes to idempotent payments, most Engineers know they need to have a unique identifier for each payment, but the way they go about generating the identifier or idempotency key (typically a random UUID) is **not ideal** because the identifier should be based on the payment metadata itself.

A payment transaction occurs between two parties; sender and receiver. The receiver is minimally identified by a Bank Code  and an Account Number. Account Name and other metadata may also be required by the payment processor, but for the purpose of our idempotency key generation, we will leave it at this:

- Receiver's Bank Code - **RBC**
- Receiver's Account Number - **RAN**

The majority of components for the idempotency key generation will come from the sender information, since they are initiating the transaction. We need to account for:

- Sender's Bank Code (to identify the originating institution) - **SBC**
- Sender's Account Number (to identify the sender) - **SAN**
- Transaction Timecode (to identify the time band in which the payment was sent, see the illustration below on time bands) - **TTC**
- Transaction Amount - **TAMT**
- Internal Transaction Narration (system-generated categoral label [enum] for the transaction, if available. This is NOT the internal system transaction id) - **ITN** (default: "")
- Client Type (the type of application [enum] used to send the payment; e.g. web app, mobile app, web api, etc.) - **CTYPE**
- Client ID (unique id of the client device, if available) - **CID** (default: "")
- Client Location (to help establish that the same user originated multiple payments) - **CLOC**


![image2](https://montydimkpa-fyi-public.sfo3.cdn.digitaloceanspaces.com/media/articles/payment-idempotency/payment-image-2.png)

Using a 15-minute timecode system as illustrated above means that we "lock" a unique transaction down for an interval of 15 minutes, disallowing the transaction from being repeated within that interval. Any suitable interval size (in minutes) can be used.

### Selected Hashing Scheme

![image3](https://montydimkpa-fyi-public.sfo3.cdn.digitaloceanspaces.com/media/articles/payment-idempotency/payment-image-3.png)


In our hashing scheme, we separately generate hashes for the sender and receiver sides based on their respective required components and join both hashes by a delimeter, which can simply be a period.

You can see code for generating this key on [Github](https://github.com/montyd1905/mds-blog-idempotent-payments/blob/main/idempotency_key.py).


## Advantages: Improved Security, Performance & Reliability

![image4](https://montydimkpa-fyi-public.sfo3.cdn.digitaloceanspaces.com/media/articles/payment-idempotency/payment-image-4.png)

- As you can see, our goal is to create an idempotency key (IK) that is based on the actual transaction, instead of just a unique random key that forces us to compare transaction details in some expensive downstream validation. This amounts to a more performant implementation.

- Secondly, we reduce security risks by generating the IK from the payload and internal business logic (which includes validations; so it is much harder to fake). Compare this with a simple random UUID which an attacker can simply fake and add to the header to con the system into processing a fake transaction.

- Finally, our "time lock" system removes the need for additional downstream TTL checks by effectively baking the TTL into the IK upstream at the request preprocessing stage (if a new transaction is detected as a duplicate within the given time interval, the resulting key is not unique and the transaction is simply ignored downstream). 
  - This improves reliability and performance.

## Examples

You can find examples on [Github](https://github.com/montyd1905/mds-blog-idempotent-payments/blob/main/example_usage.py).


