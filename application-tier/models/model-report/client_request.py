import requests
import json

# Define the FastAPI endpoint URL
# If running locally, replace with your local address (e.g., "http://127.0.0.1:8001/generate-customs-declaration")
# api_url = "http://127.0.0.1:8000/generate-customs-declaration/import"
api_url = "http://127.0.0.1:8000/generate-customs-declaration/export" 

# Sample input data (using the dummy data from cell sbU3n-2y_uWp)
ocr_data_input = {
  "invoice_number": "01739-0006-6206",
  "country_export": "Korea",
  "country_import": "Australia",
  "shipper": {
    "company_name": "Seoul Instruments Co., Ltd.",
    "address": "22, Eonju-ro 114-gil, Gangnam-gu, Seoul, Korea",
    "phone": "+82-2-1234-5678",
    "email": "export@seoulinst.com"
  },
  "importer": {
    "company_name": "Qorfolk Southern",
    "address": "44 Maitland Rd, 2304, Mayfield, WA 2458",
    "phone": "+71-5320-5711",
    "fax": "+28-5127-4492",
    "postal_code": "2458",
    "email": "import@qorfolksouthern.au"
  },
  "buyer": {
    "company_name": "Southern BioTech Pty Ltd.",
    "address": "12 Tech Park Avenue, Brisbane QLD 4000, Australia",
    "postal_code": "4000",
    "phone": "+61-7-4001-2233",
    "email": "purchasing@southernbiotech.au"
  },
  "total_amount": "$5,657.87",
  "gross_weight": "33 KG",
  "net_weight": "30 KG",
  "total_packages": "60",
  "bill_number": "HG173752",
  "port_departure": "KIMASI, GREECE",
  "port_destination": "YONEGURA, JAPAN",
  "vessel_name": "TANTO TENANG",
  "vessel_nationality": "INDIA",
  "items": [
    {
      "item_name": "Thermometer",
      "quantity": "96",
      "unit": "ea",
      "unit_price": "$47.44",
      "amount": "$9,064.67",
      "hs_code": "9025.19",
      "gross_weight": "33 KG",
      "net_weight": "30 KG",
      "total_package": "60"
    }
  ]
}

hsk_data_input = {
  "hsk_code": "8528.30-0000"
}

# Prepare the request payload according to the Pydantic models
payload = {
    "ocr_data": ocr_data_input,
    "hsk_data": hsk_data_input
}


try:
    # Add a small delay to give the server time to start
    print("Attempting to send request...")

    # Send the POST request
    response = requests.post(api_url, json=payload)
    print("POST " + api_url)
    response.raise_for_status()

    # Print the JSON response
    print("API Response:")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))

except requests.exceptions.RequestException as e:
    print(f"Error sending request: {e}")
    print("Please ensure the FastAPI application is running and the API URL is correct.")