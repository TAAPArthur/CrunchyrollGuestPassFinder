# Crunchyroll Guest Pass finder
Automatically get Crunchyroll guest passes for free.

The script fishes for guest passes and activates a guest pass for a given user. Since a guest pass is only active for so long (~4 days) and since an account can only have ~20 guest pass activations a year, the script cycles through users accounts. (Remember one account per person)

After running edit: $HOME/.config/crunchyroll-guest-pass-finder/accounts.json
The JSON file is an array of dictionaries containing the following fields
Fields are: 
Username - username of the account
Password - password of the account
Active (optional) - if set and false, then the account is ignored
Duration (optional)- how to wait after the account is activated until the next account should be activated. Default is 4
