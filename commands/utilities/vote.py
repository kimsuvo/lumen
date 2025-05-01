import discord 
from discord .ext import commands 
from functions .topgg .vote import has_voted 

class VoteLumen (commands .Cog ):
    def __init__ (self ,bot :commands .Bot ):
        self .bot =bot 

    @commands .command (name ="vote")
    async def vote (self ,ctx :commands .Context ):
        """Checks if the user has voted and sends the appropriate embed."""
        voted =await has_voted (ctx .author .id )

        if voted :

            embed =discord .Embed (
            title ="Already Voted",
            description ="It looks like you've already voted for Lumen! Thank you for your continued support.",
            color =0x000001 
            )
            await ctx .send (embed =embed )
        else :

            embed =discord .Embed (
            title ="Vote for Lumen",
            description =(
            "Support Lumen by voting on Top.gg!\n\n"
            "Every vote helps us grow and continue providing you with a great experience."
            ),
            color =0x000001 
            )

            view =discord .ui .View ()
            vote_button =discord .ui .Button (
            label ="Vote Lumen",
            url ="https://top.gg/bot/1324057734009720915/vote",
            style =discord .ButtonStyle .link 
            )
            view .add_item (vote_button )

            await ctx .send (embed =embed ,view =view )


async def setup (bot :commands .Bot ):
    await bot .add_cog (VoteLumen (bot ))
