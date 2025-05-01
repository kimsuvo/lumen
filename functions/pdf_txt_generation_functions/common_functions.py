

import pytz 
from datetime import datetime 
from .constants import TIMEZONE 

def convert_to_timezone (timestamp :str )->str :
    """
    Convert a UTC timestamp string (YYYY-mm-dd HH:MM:SS) 
    to the configured local time based on TIMEZONE.
    """
    tz =pytz .timezone (TIMEZONE )
    try :
        utc_time =datetime .strptime (timestamp ,'%Y-%m-%d %H:%M:%S')
        local_time =utc_time .astimezone (tz )
        return local_time .strftime ('%Y-%m-%d %I:%M %p')
    except ValueError :
        return "Invalid Timestamp"
