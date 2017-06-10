#!/bin/bash

pkgname='taapcrunchyroll-bot'

configDir="$HOME/.config/taapcrunchyroll-bot"
configFile="$configDir/taapcrunchyroll-bot.conf"
if [ ! $baseDir -e ]; then 
        mkdir -p $baseDir
fi 
if [ ! $configFile -e ]; then 
        touch $configFile     
fi 
exec >> "$configDir/bot.log"
exec 2>&1

numberOfGroups=1
getCredentialsScript=0
updateUserInfoScript=0

source $configFile

cd "/usr/lib/$pkgname/"

for i in `seq 1 $numberOfGroups`;
  do
       credentials=$getCredentialsScript $i
       uname= $(echo "$credentials" |cut -d " " -f1)
       if [ "$credentials" != "0" ]; then
			echo "Obtaining guest pass for $uname of Group $i";
			python3 activateCruncyrollGuestPass.py $credentials

			if [ "$?" == "0" ]; then
				echo "Guest pass obtained; Updating user info" 
				$updateUserInfoScript $i $uname
			else 
				echo "pyhton exited with error code $?"
			fi
	else

		echo "Account '$uname' is still activated"

       fi
  done
