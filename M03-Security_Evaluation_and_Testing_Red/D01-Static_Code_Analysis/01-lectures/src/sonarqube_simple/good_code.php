<?php
class DivisionByZeroException extends InvalidArgumentException {}

class GoodCode {
    private $message;

    public function __construct() {
        $this->message = "Hello, SonarQube!";
    }

    public function run() {
        echo $this->message . "\n";
    }

    // Example of good practice: Proper error handling with dedicated exception
    public function divide($a, $b) {
        try {
            if ($b == 0) {
                throw new DivisionByZeroException("Division by zero.");
            }
            return $a / $b;
        } catch (DivisionByZeroException $e) {
            echo 'Caught exception: ',  $e->getMessage(), "\n";
            return null;
        }
    }

    // Example of good practice: Proper encapsulation
    public function setMessage($message) {
        if (is_string($message)) {
            $this->message = $message;
        }
    }

    public function getMessage() {
        return $this->message;
    }

    // Example of good practice: Using prepared statements to prevent SQL injection
    public function safeQuery($userInput) {
        $conn = new mysqli("localhost", getenv('DB_USER'), getenv('DB_PASSWORD'), "database");

        if ($conn->connect_error) {
            die("Connection failed: " . $conn->connect_error);
        }

        $stmt = $conn->prepare("SELECT * FROM users WHERE username = ?");
        $stmt->bind_param("s", $userInput);
        $stmt->execute();
        $result = $stmt->get_result();

        while ($row = $result->fetch_assoc()) {
            echo "User: " . $row["username"] . "\n";
        }

        $stmt->close();
        $conn->close();
    }

    // Example of good practice: Using dependency injection
    private $logger;

    public function setLogger($logger) {
        $this->logger = $logger;
    }

    public function logMessage($message) {
        if ($this->logger) {
            $this->logger->log($message);
        } else {
            echo "Logger not set.\n";
        }
    }

    // Example of good practice: Adhering to Single Responsibility Principle (SRP)
    public function formatMessage($message) {
        return strtoupper($message);
    }

    // Example of good practice: Writing clean, readable code
    public function calculateSum($numbers) {
        if (!is_array($numbers)) {
            throw new InvalidArgumentException("Input should be an array.");
        }

        $sum = 0;
        foreach ($numbers as $number) {
            if (!is_numeric($number)) {
                throw new InvalidArgumentException("All elements in the array should be numbers.");
            }
            $sum += $number;
        }
        return $sum;
    }

    // Example of good practice: Properly closing resources
    public function safeFileRead($filename) {
        if (!file_exists($filename)) {
            throw new InvalidArgumentException("File does not exist.");
        }

        $file = fopen($filename, "r");
        if ($file) {
            while (($line = fgets($file)) !== false) {
                echo $line;
            }
            fclose($file);
        } else {
            throw new InvalidArgumentException("Failed to open file.");
        }
    }
}
