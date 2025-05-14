<?php
require 'good_code.php';
require 'bad_code.php';

echo "Good Code Output:\n";
$good = new GoodCode();
$good->run();

echo "\n\nBad Code Output:\n";
$bad = new BadCode();
$bad->run();
?>
