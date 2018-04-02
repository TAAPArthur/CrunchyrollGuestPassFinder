<?php
	$con = mysqli_connect("localhost","root",trim(file_get_contents("/var/www/password")),"CrunchyrollPremium");
	$groupID=+$argv[1];
	$query="SELECT `CrunchyrollUsername`,`CrunchyrollPassword`,GroupPosition
		From Users
		INNER JOIN (
	    		SELECT GroupID,MAX(GroupPosition)+1 AS Size,ActivatedGroupMemberPosition
	        	FROM Users INNER JOIN Groups ON Groups.ID=GroupID 
	            	WHERE (Groups.PremiumStartDate IS NULL OR PremiumStartDate < NOW() - INTERVAL 4 DAY)  GROUP BY GroupID
	         )
	         As Temp ON Temp.GroupID=Users.GroupID
	         WHERE Active=1 and Users.`GroupID`=$groupID
	         ORDER BY (Users.GroupPosition-1+Size-ActivatedGroupMemberPosition)%Size LIMIT 1
		";
	$result=$con->query("$query");

	if($result->num_rows){
		$row = $result->fetch_array();
		echo $row[0]." ".$row[1]." ".$row[2];
	}
    else echo 0;


?>
