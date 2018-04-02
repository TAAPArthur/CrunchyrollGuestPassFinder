<?php

	sleep(60);
	$con = mysqli_connect("localhost","root",trim(file_get_contents("/var/www/password")),"CrunchyrollPremium");
	$success=+$argv[1]
	$groupID=+$argv[2];
	$premiumAccountToUseNext=+$argv[5];
	if($success==0){
		echo "premiumAccountToUseNext $premiumAccountToUseNext";
		$con->query("UPDATE Groups SET PremiumStartDate=NOW(), ActivatedGroupMemberPosition=$premiumAccountToUseNext 
		WHERE ID=$groupID");
		shell_exec("taapbot \"$argv[2] is now active\"");
	}
	else{
		$con->query("UPDATE Groups SET ActivatedGroupMemberPosition=$premiumAccountToUseNext WHERE ID=$groupID");
		shell_exec("taapbot \"$argv[2] failed to be activated\"");

	}

	$con->close();

?>
