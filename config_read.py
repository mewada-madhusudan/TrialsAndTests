import json
import openpyxl


def read_config_file(config_file_path):
    with open(config_file_path, 'r') as config_file:
        formulas = json.load(config_file)
    return formulas

# Example usage
config_file_path = 'config.json'
file_path = 'blank_temp.xlsx'
formulas = read_config_file(config_file_path)
wb = openpyxl.load_workbook(file_path)

for sheet_name in formulas:
    print(sheet_name)
    sheet = wb[sheet_name]
    for key, value in formulas[sheet_name].items():
        print(f"Key: {key} & Formula: {value}")
        sheet[key].value = value


# Save the workbook
wb.save(file_path)


# print(formulas)
# def update_formula(file_path, sheet_name, cell_coordinate, new_formula):
#     # Load the workbook
#
#     # Select the worksheet
#     sheet = wb[sheet_name]
#     # Update the formula of the specified cell
#     sheet[cell_coordinate].value = new_formula
# # Example usage
#
# sheet_name = 'Sheet1'
# cell_coordinate = 'A1'
# new_formula = '=SUM(B1:B10)'  # New formula to be set
#
# update_formula(file_path, sheet_name, cell_coordinate, new_formula)
