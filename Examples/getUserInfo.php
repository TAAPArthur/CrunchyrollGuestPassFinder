<?php
	$con = mysqli_connect("localhost","root",trim(file_get_contents("/var/www/password")),"CrunchyrollPremium");
	var_dump($argv);
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
	         ORDER BY (Users.GroupPosition-1+Size-ActivatedGroupMemberPosition)%Size;
		";
	$result=$con->query("$query");

    if(!isset($argv[2]) || ! is_numeric($argv[2]) )
        $argv[2]=0;
	if($result->num_rows){
	    
        for($i=0;$i<+$argv[2]+1;$i++)
    		$row = $result->fetch_array();
		echo $row[0]." ".$row[1]." ".$row[2];
	}
    else {
        $query="SELECT `CrunchyrollUsername` FROM Users INNER JOIN Groups ON GroupID = Groups.ID WHERE Groups.ID = $groupID AND ActivatedGroupMemberPosition=GroupPosition";
        $result=$con->query("$query");
        if($result->num_rows)
    		echo "Account is already premium. Current user is: ".$result->fetch_array()[0];
        exit(12);
    }
?>
