from datetime import datetime


timestamp = datetime.now().strftime(
    "%Y%m%d%H%M%S"
)


RUNTIME_VALUES = {
    "runtime_first_name": "Demo",
    "runtime_last_name": "User1",
    "runtime_address": "100 Test Street",
    "runtime_city": "TestCity",
    "runtime_state": "TS",
    "runtime_zip": "00000",
    "runtime_phone": "9999999999",
    "runtime_ssn": "111111111",
    "runtime_username": f"demo_{timestamp}",
    "runtime_password": "DemoPass123!",
}