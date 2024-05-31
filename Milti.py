import multiprocessing
import openpyxl

def process_chunk(start_row, end_row, file_path, sheet_name):
    wb = openpyxl.load_workbook(file_path, data_only=False, read_only=True)
    ws = wb[sheet_name]
    formulas = []

    for row in ws.iter_rows(min_row=start_row, max_row=end_row, values_only=False):
        for cell in row:
            if cell.data_type == 'f':  # Check if the cell contains a formula
                formulas.append((cell.coordinate, cell.value))

    return formulas

def divide_chunks(total_rows, chunk_size):
    for i in range(1, total_rows + 1, chunk_size):
        yield i, min(i + chunk_size - 1, total_rows)

def process_large_excel(file_path, sheet_name='Sheet1', chunk_size=1000, num_workers=4):
    wb = openpyxl.load_workbook(file_path, read_only=True)
    ws = wb[sheet_name]
    total_rows = ws.max_row

    pool = multiprocessing.Pool(processes=num_workers)
    jobs = []

    for start_row, end_row in divide_chunks(total_rows, chunk_size):
        jobs.append(pool.apply_async(process_chunk, (start_row, end_row, file_path, sheet_name)))

    # Collect results
    results = [job.get() for job in jobs]

    # Combine results
    all_formulas = [formula for sublist in results for formula in sublist]
    return all_formulas

if __name__ == "__main__":
    file_path = 'largefile.xlsx'
    formulas = process_large_excel(file_path)
    print(f'Total formulas found: {len(formulas)}')
    for coord, formula in formulas:
        print(f"Cell {coord} has formula: {formula}")
