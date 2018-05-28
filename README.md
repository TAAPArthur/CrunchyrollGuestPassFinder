# TAAPCrunchyBot
Automatically get Crunchyroll guest passes for free.

The script fishes for guest passes and activates a guest pass for a given user. Since a guest pass is only active for so long (~4 days) and since an account can only have ~20 guest pass activations a year, the script cycles through users accounts. (Remember one account per person)

After running edit: $HOME/.config/taapcrunchyroll-bot/taapcrunchyroll-bot.conf
Set these variables
  * numberOfGroups=    
  * getCredentialsScript=  
  * updateUserInfoScript=

numberOfGroups is the number of groups you want to have. A group should have at least 4 users. At any given time one of these accounts will be premium Crunchyroll access

getCredentialsScript -- should be a command that accept a group number as input and return the username and password (space seperated) for the account that should be 
activated next

updateUserInfoScript -- should be a command that will be run on success account activation. should accept account number and username and mark the next account to be used by getCredentialsScript
