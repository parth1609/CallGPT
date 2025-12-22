import os
from vapi import Vapi, CreateByoPhoneNumberDto
from vapi.core.api_error import ApiError

VAPI_API_TOKEN = "02ed50e1-8433-4ac9-ae19-c488fc839899"

# Instantiate the Vapi client with your API token
# For security, load your token from an environment variable
try:
    client = Vapi(token=VAPI_API_TOKEN)
except Exception as e:
    print(f"Failed to initialize Vapi client: {e}")
    print("Please ensure your VAPI_API_TOKEN environment variable is set.")
    exit()


def make_vapi_call(assistant_id: str, phone_number_id: str, customer_number: str):
    """
    Initiates an outbound call using the Vapi API.
    """
    try:
        # Debug context to help diagnose issues like international calling restrictions
        print(
            f"Creating call with assistant_id={assistant_id}, phone_number_id={phone_number_id}, customer={customer_number}"
        )
        response = client.calls.create(
            assistant_id=assistant_id,
            phone_number_id=phone_number_id,
            customer={"number": customer_number},
        )
        print("Call initiated successfully.")
        print(f"Call ID: {response.id}")
        print(f"Call Status: {response.status}")
        return response
    except ApiError as e:
        # Print full API error to understand 4xx/5xx issues (e.g., international calling not enabled)
        print(f"Vapi API error during call create: {e.status_code} - {e.body}")
        return None
    except Exception as e:
        print(f"Failed to create call: {e}")
        return None


def create_byo_phone_number(
    credential_id: str,
    name: str | None = None,
    assistant_id: str | None = None,
    number: str | None = None,
):
    """
    Create a BYO (bring-your-own) phone number in Vapi.


    """
    try:
        resp = client.phone_numbers.create(
            request=CreateByoPhoneNumberDto(
                credential_id=credential_id,
                name=name,
                assistant_id=assistant_id,
                number=number,
            )
        )
        print("PhoneNumber created successfully.")
        print(f"PhoneNumber ID: {resp.id}")
        print(f"Status: {resp.status}")
        print(f"Number: {getattr(resp, 'number', None)}")
        return resp
    except ApiError as e:
        print(f"Vapi API error: {e.status_code} - {e.body}")
    except Exception as e:
        print(f"Failed to create BYO phone number: {e}")
    return None


if __name__ == "__main__":
    # Replace these placeholders with your actual IDs and number
    YOUR_ASSISTANT_ID = "c4c26995-887d-486f-99ff-3dc53a73aad"
    YOUR_PHONE_NUMBER_ID = "5739c5fc-d3f8-408e-b022-893f6632980"
    CUSTOMER_PHONE_NUMBER = "+1"  # Use E.164 format

    # Check that the environment variable for the token is set
    if not VAPI_API_TOKEN:
        print("VAPI_API_TOKEN environment variable is not set. Exiting.")
    else:
        make_vapi_call(YOUR_ASSISTANT_ID, YOUR_PHONE_NUMBER_ID, CUSTOMER_PHONE_NUMBER)

        # Optionally create a BYO phone number when env vars are set to avoid accidental API calls.
        # Set RUN_CREATE_BYO=1 and VAPI_CREDENTIAL_ID=<your_credential_id> to enable.
        run_create_byo = os.getenv("RUN_CREATE_BYO") == "1"
        byo_credential_id = os.getenv("VAPI_CREDENTIAL_ID")
        if run_create_byo and byo_credential_id:
            create_byo_phone_number(
                credential_id=byo_credential_id,
                name=os.getenv("VAPI_PHONE_NAME"),
                assistant_id=os.getenv("VAPI_DEFAULT_ASSISTANT_ID"),
                number=os.getenv("VAPI_DID"),
            )
