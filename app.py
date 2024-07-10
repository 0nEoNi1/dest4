# Original URL with placeholders for missing characters
base_url = "https://drive.google.com/drive/folders/1D2M0ZB3S94C{}{}{}yMoN3DXVfnsJ4zE43c?usp=sharing"

# Possible characters in the missing positions (assuming alphanumeric)
possible_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

# Function to generate all possible URLs
def generate_urls():
    with open("possible_urls.txt", "w") as file:
        for char1 in possible_chars:
            for char2 in possible_chars:
                for char3 in possible_chars:
                    test_url = base_url.format(char1, char2, char3)
                    file.write(test_url + "\n")

# Generate and save URLs to a file
generate_urls()

print("All possible URLs have been saved to possible_urls.txt.")
