using ClosedXML.Excel;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

public class FormulaAnalyzer
{
    public class FormulaInfo
    {
        public string Sheet { get; set; }
        public string CellReference { get; set; }
        public string Formula { get; set; }
        public string Pattern { get; set; }
        public string Classification { get; set; }
        public bool IsInPivotSheet { get; set; }
    }

    public class AnalysisResult
    {
        public List<FormulaInfo> SingleCellFormulas { get; set; } = new();
        public List<FormulaInfo> RowwiseDraggedFormulas { get; set; } = new();
        public List<FormulaInfo> ColumnwiseDraggedFormulas { get; set; } = new();
    }

    private const int BatchSize = 10000;

    public async Task<AnalysisResult> AnalyzeExcelFormulasAsync(string filePath)
    {
        var result = new AnalysisResult();
        var options = new LoadOptions { LoadDataOnly = true };

        using (var workbook = new XLWorkbook(filePath, options))
        {
            foreach (var worksheet in workbook.Worksheets)
            {
                var hasPivotTables = worksheet.PivotTables.Any();
                var usedRange = worksheet.RangeUsed();
                if (usedRange == null) continue;

                var firstRow = usedRange.FirstRow().RowNumber();
                var lastRow = usedRange.LastRow().RowNumber();
                var firstColumn = usedRange.FirstColumn().ColumnNumber();
                var lastColumn = usedRange.LastColumn().ColumnNumber();

                // Process in batches
                for (int startRow = firstRow; startRow <= lastRow; startRow += BatchSize)
                {
                    int endRow = Math.Min(startRow + BatchSize - 1, lastRow);
                    var batchRange = worksheet.Range(startRow, firstColumn, endRow, lastColumn);

                    var formulaCells = batchRange.Cells()
                        .Where(cell => cell.HasFormula)
                        .ToList();

                    var patterns = new Dictionary<(int Row, int Column), string>();
                    
                    // Process formulas in parallel
                    await Task.WhenAll(formulaCells.Select(async cell =>
                    {
                        var formula = cell.FormulaA1;
                        var pattern = ExtractFormulaPattern(formula);
                        patterns[(cell.Address.RowNumber, cell.Address.ColumnNumber)] = pattern;
                    }));

                    // Classify formulas in batch
                    foreach (var cell in formulaCells)
                    {
                        var pattern = patterns[(cell.Address.RowNumber, cell.Address.ColumnNumber)];
                        var classification = QuickClassifyFormula(worksheet, cell, pattern);

                        var formulaInfo = new FormulaInfo
                        {
                            Sheet = worksheet.Name,
                            CellReference = cell.Address.ToString(),
                            Formula = cell.FormulaA1,
                            Pattern = pattern,
                            Classification = classification,
                            IsInPivotSheet = hasPivotTables
                        };

                        lock (result)
                        {
                            switch (classification)
                            {
                                case "Single":
                                    result.SingleCellFormulas.Add(formulaInfo);
                                    break;
                                case "Rowwise":
                                    result.RowwiseDraggedFormulas.Add(formulaInfo);
                                    break;
                                case "Columnwise":
                                    result.ColumnwiseDraggedFormulas.Add(formulaInfo);
                                    break;
                            }
                        }
                    }

                    // Force garbage collection after each batch
                    GC.Collect();
                }
            }
        }

        return result;
    }

    private string ExtractFormulaPattern(string formula)
    {
        return System.Text.RegularExpressions.Regex.Replace(
            formula,
            @"\$?[A-Z]+\$?\d+",
            "[REF]",
            System.Text.RegularExpressions.RegexOptions.Compiled);
    }

    private string QuickClassifyFormula(IXLWorksheet worksheet, IXLCell cell, string pattern)
    {
        var row = cell.Address.RowNumber;
        var column = cell.Address.ColumnNumber;

        // Quick check adjacent cells only
        var rightCell = worksheet.Cell(row, column + 1);
        var bottomCell = worksheet.Cell(row + 1, column);

        bool hasRowPattern = rightCell.HasFormula && ExtractFormulaPattern(rightCell.FormulaA1) == pattern;
        bool hasColumnPattern = bottomCell.HasFormula && ExtractFormulaPattern(bottomCell.FormulaA1) == pattern;

        if (hasRowPattern && !hasColumnPattern) return "Rowwise";
        if (!hasRowPattern && hasColumnPattern) return "Columnwise";
        return "Single";
    }

    public async Task ExportResultsAsync(AnalysisResult results, string outputPath)
    {
        using (var workbook = new XLWorkbook())
        {
            // Create sheets with minimal formatting
            foreach (var category in new[] { "Single", "Rowwise", "Columnwise" })
            {
                var worksheet = workbook.Worksheets.Add(category);
                var formulas = category switch
                {
                    "Single" => results.SingleCellFormulas,
                    "Rowwise" => results.RowwiseDraggedFormulas,
                    "Columnwise" => results.ColumnwiseDraggedFormulas,
                    _ => new List<FormulaInfo>()
                };

                // Bulk insert data
                var data = formulas.Select(f => new[]
                {
                    f.Sheet,
                    f.CellReference,
                    f.Formula,
                    f.Pattern,
                    f.IsInPivotSheet.ToString()
                }).ToList();

                worksheet.Cell(1, 1).InsertData(data);
            }

            await Task.Run(() => workbook.SaveAs(outputPath));
        }
    }
}

// Usage
public class Program
{
    public static async Task Main()
    {
        var analyzer = new FormulaAnalyzer();
        try
        {
            var results = await analyzer.AnalyzeExcelFormulasAsync("input.xlsx");
            await analyzer.ExportResultsAsync(results, "formula_analysis.xlsx");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
        }
    }
}
