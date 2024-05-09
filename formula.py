# import xlwings as xw
#
# # Open the Excel workbook
# wb = xw.Book("example.xlsx")
#
# # Specify the range where you want to autofill the function
# sheet = wb.sheets['Sheet1']
# range_to_fill = sheet.range('A1:A10')
#
# # Enter the function in the first cell
# range_to_fill[0].formula = '=SUM(B1:C1)'
#
# # Autofill the function in the selected range
# range_to_fill.autofill('down')
import xlwings as xw

# Connect to the Excel application
wb = xw.Book('example.xlsx')

# Specify the range you want to autofill
range_to_fill = wb.sheets['Sheet1'].range('A1:A10')

# Specify the values or formulas you want to autofill
values_or_formulas = '=B1*2'  # or any other values or formulas

# Use autofill to fill the range
range_to_fill.api.autofill(range_to_fill )