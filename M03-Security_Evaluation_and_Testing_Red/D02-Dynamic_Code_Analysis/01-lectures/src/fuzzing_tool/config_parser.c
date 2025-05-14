// config_parser.c (with intentional vulnerabilities)
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_LINE_LENGTH 100
#define MAX_KEY_LENGTH 20
#define MAX_VALUE_LENGTH 80

typedef struct {
    char key[MAX_KEY_LENGTH];
    char value[MAX_VALUE_LENGTH];
} ConfigItem;

ConfigItem config[10];
int config_count = 0;

void parse_config(const char* input) {
    char line[MAX_LINE_LENGTH];
    char *token;
    int line_num = 0;

    while (sscanf(input + line_num * MAX_LINE_LENGTH, "%99[^\n]", line) == 1) {
        token = strtok(line, "=");
        if (token != NULL && config_count < 10) {
            // Vulnerability 1: Buffer overflow in key
            strcpy(config[config_count].key, token);

            token = strtok(NULL, "=");
            if (token != NULL) {
                // Vulnerability 2: Buffer overflow in value
                strcpy(config[config_count].value, token);
                
                // Vulnerability 3: Format string vulnerability
                printf(config[config_count].value);
                
                config_count++;
            }
        }
        line_num++;
    }

    // Vulnerability 4: Integer overflow
    if (config_count > 0) {
        int total_length = 0;
        for (int i = 0; i < config_count; i++) {
            total_length += strlen(config[i].value);
        }
        printf("Total length of values: %d\n", total_length);
    }
}

void print_config() {
    for (int i = 0; i < config_count; i++) {
        printf("%s = %s\n", config[i].key, config[i].value);
    }
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <config_string>\n", argv[0]);
        return 1;
    }

    // Vulnerability 5: Command injection
    char command[256];
    snprintf(command, sizeof(command), "echo %s", argv[1]);
    system(command);

    parse_config(argv[1]);
    print_config();

    return 0;
}
