
import aiohttp 
from config import TOPGG_TOKEN ,BOT_ID 



async def has_voted (user_id :int )->bool :
    """
    Check if the user with the given user_id has voted on top.gg.
    Returns True if the user has voted (voted==1), otherwise False.
    """
    url =f"https://top.gg/api/bots/{BOT_ID }/check?userId={user_id }"
    headers ={
    "Authorization":TOPGG_TOKEN 
    }
    async with aiohttp .ClientSession ()as session :
        async with session .get (url ,headers =headers )as response :
            if response .status ==200 :
                data =await response .json ()

                return data .get ("voted",0 )==1 
            else :
                return False 
