from openpyxl import load_workbook

def find_mini_table_ranges(file_path):
    wb = load_workbook(file_path, read_only=True)
    mini_table_ranges = []

    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        max_row = sheet.max_row
        max_col = sheet.max_column

        in_mini_table = False
        mini_table_start = None

        for row in range(1, max_row + 1):
            for col in range(1, max_col + 1):
                cell_value = sheet.cell(row=row, column=col).value
                if cell_value is not None:
                    # If cell is not empty
                    if not in_mini_table:
                        # If not already in a mini table, mark the start of a new mini table
                        in_mini_table = True
                        mini_table_start = (row, col)
                elif in_mini_table:
                    # If cell is empty and was previously in a mini table
                    in_mini_table = False
                    mini_table_end = (row - 1, col - 1)
                    mini_table_ranges.append((sheet_name, mini_table_start, mini_table_end))

        # Check if the last cell contains data, indicating the end of a mini table
        if in_mini_table:
            mini_table_end = (max_row, max_col)
            mini_table_ranges.append((sheet_name, mini_table_start, mini_table_end))

    return mini_table_ranges

# Example usage
file_path = "example.xlsx"  # Change this to your Excel file path
ranges = find_mini_table_ranges(file_path)
for sheet_name, mini_table_start, mini_table_end in ranges:
    print(f"Mini table range in '{sheet_name}': From {mini_table_start} to {mini_table_end}")
