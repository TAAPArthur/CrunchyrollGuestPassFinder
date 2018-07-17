<?php

	$con = mysqli_connect("localhost","root",trim(file_get_contents("/var/www/password")),"CrunchyrollPremium");
	$success=+$argv[1];
	$groupID=+$argv[2];
    
	if($success==0){
        $activatedGroupMember=+$argv[3];
		$con->query("UPDATE Groups SET PremiumStartDate=NOW(), ActivatedGroupMemberPosition=$activatedGroupMember 
		WHERE ID=$groupID");
		shell_exec("taapmessage \"$argv[2] is now active\"");
	}
	else{
	    if($success>0)
	        if(is_numeric($argv[3])&&+$argv[3]>=0){
    	        $activatedGroupMember=+$argv[3];
        		$con->query("UPDATE Groups SET ActivatedGroupMemberPosition=$activatedGroupMember WHERE ID=$groupID");
    		}
		shell_exec("taapmessage \"Group $argv[2] failed to be activated. error code:$success $argv[4] \"");
	}

	$con->close();

?>
