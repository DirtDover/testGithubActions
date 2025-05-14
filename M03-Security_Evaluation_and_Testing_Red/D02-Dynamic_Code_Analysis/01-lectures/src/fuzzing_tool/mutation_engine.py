import random
import subprocess

MAX_KEY_LENGTH = 20
MAX_VALUE_LENGTH = 80


class MutationEngine:
    def __init__(self, seed_inputs):
        self.seed_inputs = seed_inputs

    def mutate(self, input_data):
        if not input_data:
            return random.randbytes(
                random.randint(1, 10)
            )  # Generate some random data if input is empty
        mutation_technique = random.choice(
            [
                self.bit_flip,
                self.byte_swap,
                self.insert_random_bytes,
                self.delete_random_bytes,
            ]
        )
        return mutation_technique(input_data)

    def bit_flip(self, data):
        mutated = bytearray(data)
        bit_to_flip = random.randint(0, len(mutated) * 8 - 1)
        byte_index = bit_to_flip // 8
        bit_index = bit_to_flip % 8
        mutated[byte_index] ^= 1 << bit_index
        return bytes(mutated)

    def byte_swap(self, data):
        if len(data) < 2:
            return self.insert_random_bytes(
                data
            )  # If not enough data to swap, insert instead
        mutated = bytearray(data)
        i, j = random.sample(range(len(mutated)), 2)
        mutated[i], mutated[j] = mutated[j], mutated[i]
        return bytes(mutated)

    def insert_random_bytes(self, data):
        mutated = bytearray(data)
        num_bytes = random.randint(1, 3)
        position = random.randint(0, len(mutated))
        for _ in range(num_bytes):
            mutated.insert(position, random.randint(0, 255))
        return bytes(mutated)

    def delete_random_bytes(self, data):
        if len(data) < 2:
            return self.insert_random_bytes(
                data
            )  # If not enough data to delete, insert instead
        mutated = bytearray(data)
        num_bytes = min(random.randint(1, 3), len(mutated) - 1)
        position = random.randint(0, len(mutated) - num_bytes)
        del mutated[position : position + num_bytes]
        return bytes(mutated)

    def generate_mutated_input(self):
        seed = random.choice(self.seed_inputs)
        num_lines = random.randint(1, 5)
        mutated = bytearray()
        for _ in range(num_lines):
            key_length = random.randint(1, min(MAX_KEY_LENGTH, len(seed)))
            value_length = random.randint(1, min(MAX_VALUE_LENGTH, len(seed)))
            key = self.mutate(seed[:key_length])
            value = self.mutate(seed[key_length : key_length + value_length])
            line = key + b"=" + value + b"\n"
            mutated.extend(line)
        return bytes(mutated)


def fuzz(engine, num_iterations):
    for i in range(num_iterations):
        mutated_input = engine.generate_mutated_input()
        print(f"Iteration {i}: {mutated_input}")
        try:
            result = subprocess.run(
                ["./config_parser", mutated_input.decode("utf-8", errors="ignore")],
                capture_output=True,
                text=True,
                timeout=1,
            )
            if result.returncode != 0:
                print(f"Iteration {i}: Crash detected!")
                print(f"Input: {mutated_input}")
                print(f"Error output: {result.stderr}")
                # You might want to save this input to a file for further analysis
                with open(f"crash_input_{i}.txt", "wb") as f:
                    f.write(mutated_input)

        except subprocess.TimeoutExpired:
            print(f"Iteration {i}: Timeout occurred")
            print(f"Input: {mutated_input}")
        except Exception as e:
            print(f"Iteration {i}: An unexpected error occurred: {str(e)}")
            print(f"Input: {mutated_input}")


# Example usage
seed_inputs = [
    b"key1=value1\n",
    b"long_key=long_value_string\n",
    b"empty=\n",
    b"multiple=lines\nwith=values\n",
]

engine = MutationEngine(seed_inputs)

# Run the fuzzer for 100 iterations
fuzz(engine, 100)
