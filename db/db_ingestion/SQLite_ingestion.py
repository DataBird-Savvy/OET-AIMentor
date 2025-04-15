import json

# Define the path to your JSON file
json_file_path = '/content/data_listening_onedata.json'

# Read and load the JSON file
with open(json_file_path, 'r') as file:
    data = json.load(file)


input_list=[]
# Recursive function to search for 'input' in the JSON structure
def extract_input(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'input':  # If 'input' is found, add it to the list
                input_list.append(value)
            else:
                extract_input(value)  # Recursively search in nested structures
    elif isinstance(data, list):
        for item in data:
            extract_input(item)  # Recursively search in list items

# Call the function to extract all 'input' values
extract_input(data)

# Print the list of 'input' values
print(len(input_list))


input_list=[]
# Recursive function to search for 'input' in the JSON structure
def extract_input(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'input':  # If 'input' is found, add it to the list
                input_list.append(value)
            else:
                extract_input(value)  # Recursively search in nested structures
    elif isinstance(data, list):
        for item in data:
            extract_input(item)  # Recursively search in list items

# Call the function to extract all 'input' values
extract_input(data)

# Print the list of 'input' values
print(len(input_list))