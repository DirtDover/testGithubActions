<?php
class BadCode {
    public $data;

    public function __construct() {
        $this->data = "Uninitialized Data";
    }

    public function run() {
        echo $this->data . "\n";
    }

    // Example of bad practice: SQL Injection vulnerability
    public function unsafeQuery($userInput) {
        $conn = new mysqli("localhost", "user", "password", "database");
        $result = $conn->query("SELECT * FROM users WHERE username = '$userInput'");
        while ($row = $result->fetch_assoc()) {
            echo "User: " . $row["username"] . "\n";
        }
        $conn->close();
    }

    // Example of bad practice: Hardcoded credentials
    public function hardcodedCredentials() {
        $conn = new mysqli("localhost", "root", "rootpassword", "sensitive_database");
        if ($conn->connect_error) {
            die("Connection failed: " . $conn->connect_error);
        }
        echo "Connected successfully\n";
        $conn->close();
    }

    // Example of bad practice: Lack of error handling
    public function divide($a, $b) {
        return $a / $b;
    }

    // Example of bad practice: No input validation
    public function processUserInput($input) {
        echo "Processing input: " . $input . "\n";
    }

    // Example of bad practice: Global variable usage
    public function useGlobalVariable() {
        global $globalVar;
        echo "Global variable: " . $globalVar . "\n";
    }

    // Example of bad practice: Function with too many responsibilities
    public function complexFunction() {
        $data = $this->fetchData();
        $processedData = $this->processData($data);
        $this->saveData($processedData);
        $this->sendNotification();
    }

    private function fetchData() {
        return "Data";
    }

    private function processData($data) {
        return strtoupper($data);
    }

    private function saveData($data) {
        file_put_contents("data.txt", $data);
    }

    private function sendNotification() {
        echo "Notification sent.\n";
    }

    // Example of bad practice: Deeply nested code
    public function nestedCode() {
        for ($i = 0; $i < 10; $i++) {
            if ($i % 2 == 0) {
                for ($j = 0; $j < 5; $j++) {
                    if ($j % 2 == 0) {
                        echo "i: $i, j: $j\n";
                    }
                }
            }
        }
    }

    // Example of bad practice: Using a weak hashing algorithm
    public function weakHashing($data) {
        return md5($data); // Noncompliant: MD5 is considered a weak hashing algorithm
    }

    // Example of bad practice: Inconsistent naming conventions
    public function doSomething() {
        $SomeValue = "Value";
        echo $SomeValue;
    }
}
?>
