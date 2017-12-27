<?php
	$con = mysqli_connect("localhost","root",trim(file_get_contents("/var/www/password")),"CrunchyrollPremium");
	$groupID=+$argv[1];
	$premiumAccountToUseNext=+$argv[4];
	echo "premiumAccountToUseNext $premiumAccountToUseNext";
	$con->query("UPDATE Groups SET PremiumStartDate=NOW() WHERE ID=$groupID");
	$con->query("UPDATE Users SET ActivatedGroupMemberPosition=$premiumAccountToUseNext WHERE GroupID=$groupID");
	$con->close();
?>
