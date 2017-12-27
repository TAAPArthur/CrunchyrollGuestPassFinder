<?php
	$con = mysqli_connect("localhost","root",trim(file_get_contents("/var/www/password")),"CrunchyrollPremium");
	$groupID=+$argv[1];
	$query="SELECT `CrunchyrollUsername`,`CrunchyrollPassword`,Position
		FROM (
			SELECT MAX(`ActivatedGroupMemberPosition`)%COUNT(*)+1 AS Position 
			FROM `Users` INNER JOIN Groups ON Groups.ID=GroupID 
			WHERE `GroupID`=$groupID AND (Groups.PremiumStartDate IS NULL OR PremiumStartDate < NOW() - INTERVAL 3 DAY) GROUP BY GroupID)
			AS Temp INNER JOIN Users WHERE Position=`GroupPosition`
		";
	$result=$con->query("$query");
	
	if($result->num_rows){
		$row = $result->fetch_array();
		echo $row[0]." ".$row[1]." ".$row[2];
    }
    else echo 0;
	
	
?>
