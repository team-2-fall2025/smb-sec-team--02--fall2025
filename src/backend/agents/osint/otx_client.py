import os
from OTXv2 import OTXv2, IndicatorTypes
from dotenv import load_dotenv
from db.mongo import db
load_dotenv()

IPv4New = IndicatorTypes.IndicatorTypes(
    name="IPv4",
    description="An IPv4 address indicating the online location of a server or other computer.",
    api_support=True,
    sections=["general"],
    slug="IPv4"
)

OTX_API_KEY = os.getenv("OSINT_OTX_API_KEY")
RATE_LIMIT = 10
otx = OTXv2(OTX_API_KEY)
# Get everything OTX knows about google.com
def otx_intel_events(ip):
    try:
        result = otx.get_indicator_details_full(IPv4New, ip)
        pulses = result["general"]["pulse_info"]["pulses"]
        # print(ip, len(pulses))
        return pulses

    except Exception: 
        return []
