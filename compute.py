import hmac
import hashlib

payload = '{\
    "event": "charge.success",\
    "data": {\
        "id": 4643239751,\
        "reference": "ce8b845d-e1f2-49d9-8bf5-7be43d9f46a6",\
        "status": "success",\
        "amount": 500000,\
        "metadata": {\
            "course_id": "2",\
            "payment_id": "9"\
        },\
        "customer": {\
            "email": "finegodyson2014@gmail.com"\
        }\
    }\
}'

secret_key = 'sk_test_fabc404e2e34238823556a8a0b15c9e1dfb8550a'  # Replace with your actual Paystack secret key
computed_signature = hmac.new(secret_key.encode(), payload.encode(), hashlib.sha512).hexdigest()
print(computed_signature)