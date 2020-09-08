# Crunchyroll Guest Pass finder
Automatically get Crunchyroll guest passes for free.

The script fishes for guest passes and activates a guest pass for a given user. A guest pass seems to be active for about 4 days.

# Usage
```
crunchyroll-guest-pass-finder -u $USER --save            # Save username and password (provided via stdin) unencrypted to disk
crunchyroll-guest-pass-finder -u $USER                   # Fish for guest passes for $USER
crunchyroll-guest-pass-finder -a                         # Fish for guest passes for all known users
```
