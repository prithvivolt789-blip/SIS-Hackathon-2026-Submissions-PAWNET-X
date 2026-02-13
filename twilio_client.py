

import urequests
import ubinascii
import time


class TwilioClient:
    

    def __init__(self, account_sid, auth_token, from_number, api_url):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.api_url = api_url

        
        self.sms_api_url = f"https://studio.twilio.com/v2/Flows/FW35cf5ad3c9254a540a1023c364ec8f6c"

        
        self.auth_header = self._create_auth_header()
    
    def _create_auth_header(self):
        credentials = f"{self.account_sid}:{self.auth_token}"
        
        encoded = ubinascii.b2a_base64(credentials.encode()).decode().strip()
        return f"Basic {encoded}"
    
    def make_call(self, to_number, twiml_url, status_callback=None):
        
        
        payload = {
            "To": to_number,
            "From": self.from_number,
            "Url": twiml_url,
        }

        if status_callback:
            payload["StatusCallback"] = status_callback
            payload["StatusCallbackEvent"] = "initiated,ringing,answered,completed"

        headers = {
            "Authorization": self.auth_header,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        body_parts = []
        for k, v in payload.items():
            if k in ["Url", "StatusCallback"]:
            
                body_parts.append(f"{k}={v}")
            else:
            
                body_parts.append(f"{k}={self._url_encode(v)}")
        body = "&".join(body_parts)
        
        try:
            print(f" Initiating call to {to_number}...")
            
         
            response = urequests.post(
                self.api_url,
                data=body,
                headers=headers
            )
            
            if response.status_code == 201:
                
                result = response.json()
                call_sid = result.get("sid", "Unknown")
                status = result.get("status", "Unknown")
                print(f" Call initiated successfully!")
                print(f"   Call SID: {call_sid}")
                print(f"   Status: {status}")
                response.close()
                return result
            else:
                
                print(f" Call failed with status code: {response.status_code}")
                print(f"   Response: {response.text}")
                response.close()
                return None
                
        except Exception as e:
            print(f" Exception during call: {e}")
            return None
    
    def _url_encode(self, value):

        
        value = str(value)
        value = value.replace(" ", "%20")
        value = value.replace("+", "%2B")
        value = value.replace(":", "%3A")
        value = value.replace("/", "%2F")
        value = value.replace("?", "%3F")
        value = value.replace("=", "%3D")
        value = value.replace("&", "%26")
        value = value.replace("#", "%23")
        return value
    
    def test_connection(self):
       
        try:
            print(" Testing Twilio connection...")
           
            test_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}.json"
            headers = {"Authorization": self.auth_header}
            
            response = urequests.get(test_url, headers=headers)
            
            if response.status_code == 200:
                print(" Twilio connection successful!")
                response.close()
                return True
            else:
                print(f" Connection failed: {response.status_code}")
                response.close()
                return False
                
        except Exception as e:
            print(f" Connection test failed: {e}")
            return False

    def send_sms(self, to_number, message):
       
        print(f"\n Sending SMS to {to_number}...")

        # Prepare request payload
        payload = {
            "To": to_number,
            "From": self.from_number,
            "Body": message
        }

        
        body = "&".join([f"{k}={self._url_encode(v)}" for k, v in payload.items()])

        
        headers = {
            "Authorization": self.auth_header,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            
            response = urequests.post(
                self.sms_api_url,
                data=body,
                headers=headers
            )

            if response.status_code == 201:
              
                result = response.json()
                message_sid = result.get('sid', 'Unknown')
                print(f" SMS sent successfully!")
                print(f"   Message SID: {message_sid}")
                response.close()
                return result

            elif response.status_code == 401:
               
                print(" Authentication failed - check Account SID and Auth Token")
                response.close()
                return None

            elif response.status_code == 400:
                # Bad request
                error_data = response.json()
                error_msg = error_data.get('message', 'Unknown error')
                print(f" Bad request: {error_msg}")
                response.close()
                return None

            else:
                # Other error
                print(f" SMS failed with status code: {response.status_code}")
                print(f"   Response: {response.text}")
                response.close()
                return None

        except OSError as e:
            print(f" Network error sending SMS: {e}")
            return None

        except Exception as e:
            print(f" Error sending SMS: {e}")
            return None

