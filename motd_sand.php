<?php
// Local file path where MOTD.txt will be saved
$local_file = '/home/MOTD.txt';

// MySQL database configuration for Sandstorm stats
$servername_sandstorm = "";
$username_sandstorm = "";
$password_sandstorm = "";
$dbname_sandstorm = "";

// MySQL database configuration for Banlist
$servername_banlist = "";
$username_banlist = "";
$password_banlist = "";
$dbname_banlist = "";

try {
    // Create a new PDO instance for Sandstorm stats
    $pdo_sandstorm = new PDO("mysql:host=$servername_sandstorm;dbname=$dbname_sandstorm", $username_sandstorm, $password_sandstorm);
    $pdo_sandstorm->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // Create a new PDO instance for Banlist
    $pdo_banlist = new PDO("mysql:host=$servername_banlist;dbname=$dbname_banlist", $username_banlist, $password_banlist);
    $pdo_banlist->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // Get the list of banned steam IDs
    $banlist_query = "SELECT steamid FROM banlist";
    $stmt_banlist = $pdo_banlist->prepare($banlist_query);
    $stmt_banlist->execute();
    $banned_steamids = $stmt_banlist->fetchAll(PDO::FETCH_COLUMN);

    // Handle the case where there are banned players
    $ban_condition = '';
    if (!empty($banned_steamids)) {
        $banned_steamids_str = "'" . implode("','", $banned_steamids) . "'";
        $ban_condition = "WHERE p.steam_id NOT IN ($banned_steamids_str)";
    }

    // SQL query to select the top 10 players by ELO, excluding banned players
    $query = "
        SELECT 
            p.player_name, 
            p.elo2 
        FROM players p
        $ban_condition
        ORDER BY p.elo2 DESC 
        LIMIT 10";

    $stmt_sandstorm = $pdo_sandstorm->prepare($query);
    $stmt_sandstorm->execute();

    // Fetch all results
    $players = $stmt_sandstorm->fetchAll(PDO::FETCH_ASSOC);

    // Initialize the MOTD content with the static text
    $motd = <<<EOD
Welcome to ↳ЯR↰ Gaming!\n
\n
Join our Discord Channel: rrgaming \n
Visit the website: https://rrgaming.net. \n
Top 10 ↳ЯR↰ rrgaming.net Leaderboard:\n\n
\n
EOD;

    // Add the leaderboard data to the MOTD (only ELO and player name)
    if (count($players) > 0) {
        foreach ($players as $player) {
            $player_name = $player['player_name'];
            $elo = number_format($player['elo2'], 2);
            $motd .= "| $elo | $player_name |\n";  // Format: | ELO | Playername |
        }
    } else {
        $motd .= "\nNo data available.\n";
    }

    // Convert the content to UTF-8 explicitly
    $motd_utf8 = mb_convert_encoding($motd, 'UTF-8', 'auto');

    // Write the MOTD content to a local file with UTF-8 encoding
    file_put_contents($local_file, $motd_utf8);

    echo "MOTD file successfully written to $local_file\n";

} catch (PDOException $e) {
    echo "Error: " . $e->getMessage();
}
?>

