import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Search, Download, Copy, Trash2, Save, Filter, X, Check, Edit, CheckSquare, Square } from 'lucide-react';
import type { AccessRecord } from '@/contexts/DataContext';

interface ExcelLikeTableProps {
  records: AccessRecord[];
  columns: string[];
  onUpdateRecord: (id: string, updates: Partial<AccessRecord>) => void;
  onUpdateMultiple: (updates: { id: string; updates: Partial<AccessRecord> }[]) => void;
  onExport: (format: 'csv' | 'excel') => void;
  canEdit: boolean;
}

interface CellPosition {
  row: number;
  col: number;
}

interface SelectedRange {
  start: CellPosition;
  end: CellPosition;
}

interface ColumnFilter {
  column: string;
  value: string;
  type: 'text' | 'select' | 'date';
}

type BatchOperationType = 'status' | 'comments' | 'certifier';

export default function ExcelLikeTable({
                                         records,
                                         columns,
                                         onUpdateRecord,
                                         onUpdateMultiple,
                                         onExport,
                                         canEdit
                                       }: ExcelLikeTableProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [columnFilters, setColumnFilters] = useState<ColumnFilter[]>([]);
  const [selectedCells, setSelectedCells] = useState<Set<string>>(new Set());
  const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set());
  const [selectAll, setSelectAll] = useState(false);
  const [selectedRange, setSelectedRange] = useState<SelectedRange | null>(null);
  const [isSelecting, setIsSelecting] = useState(false);
  const [editingCell, setEditingCell] = useState<CellPosition | null>(null);
  const [editValue, setEditValue] = useState('');
  const [copiedData, setCopiedData] = useState<string[][] | null>(null);
  const [showBatchDialog, setShowBatchDialog] = useState(false);
  const [batchOperation, setBatchOperation] = useState<BatchOperationType>('status');
  const [batchValue, setBatchValue] = useState('');
  const tableRef = useRef<HTMLTableElement>(null);

  // System columns that should always be shown
  const systemColumns = ['id','status', 'comments', 'createdAt', 'updatedAt'];

  const LeftSystemColumns = ['ProcessOwnerStatus','ProcessOwnerComment','AreaOwnerStatus','AreaOwnerComment','CertifierStatus','CertifierComment'];

  // Define dropdown options for specific status columns
  const getStatusOptions = (column: string): string[] => {
    switch (column) {
      case 'ProcessOwnerStatus':
        return ['Open for Review', 'Review Completed', 'Certified'];
      case 'AreaOwnerStatus':
        return ['Access Required', 'Access Retained', 'Access Removed', 'Open for Review'];
      case 'CertifierStatus':
        return ['Open for Review', 'Certified', 'Rejected'];
      default:
        return ['Pending', 'In Review', 'Certified', 'Rejected', 'Open for Review', 'Access Required'];
    }
  };

  // Check if a column is a status column with predefined options
  const isStatusColumn = (column: string): boolean => {
    return ['ProcessOwnerStatus', 'AreaOwnerStatus', 'CertifierStatus', 'status'].includes(column);
  };

  // Combine data columns with system columns (checkbox column will be added in render)
  const allColumns = [...LeftSystemColumns.filter(col => !columns.includes(col)),...columns, ...systemColumns.filter(col => !columns.includes(col))];

  // Get unique values for each column for filter dropdowns
  const getUniqueColumnValues = (column: string): string[] => {
    const values = new Set<string>();
    records.forEach(record => {
      const value = getCellValue(record, column);
      if (value && value.trim()) {
        values.add(value);
      }
    });
    return Array.from(values).sort();
  };

  // Apply all filters to records
  const filteredRecords = records.filter(record => {
    // Global search filter
    const matchesSearch = searchTerm === '' || Object.values(record.data).some(value =>
            String(value).toLowerCase().includes(searchTerm.toLowerCase())
        ) || record.status.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (record.comments && record.comments.toLowerCase().includes(searchTerm.toLowerCase()));

    // Status filter
    const matchesStatus = statusFilter === 'all' || record.status === statusFilter;

    // Column-specific filters
    const matchesColumnFilters = columnFilters.every(filter => {
      const cellValue = getCellValue(record, filter.column).toLowerCase();
      const filterValue = filter.value.toLowerCase();

      if (filter.type === 'select') {
        return filterValue === 'all' || cellValue === filterValue;
      } else {
        return cellValue.includes(filterValue);
      }
    });

    return matchesSearch && matchesStatus && matchesColumnFilters;
  });

  // Update selectAll state when selectedRows or filteredRecords change
  useEffect(() => {
    if (filteredRecords.length === 0) {
      setSelectAll(false);
    } else {
      const allFilteredIds = filteredRecords.map(record => record.id);
      const allSelected = allFilteredIds.every(id => selectedRows.has(id));
      setSelectAll(allSelected);
    }
  }, [selectedRows, filteredRecords]);

  const getCellValue = (record: AccessRecord, column: string): string => {
    switch (column) {
      case 'id':
        return record.id;
      case 'status':
        return record.status;
      case 'comments':
        return record.comments || '';
      case 'createdAt':
        return new Date(record.createdAt).toLocaleDateString();
      case 'updatedAt':
        return new Date(record.updatedAt).toLocaleDateString();
      default:
        return String(record.data[column] || '');
    }
  };

  const setCellValue = (record: AccessRecord, column: string, value: string): Partial<AccessRecord> => {
    switch (column) {
      case 'status':
        return { status: value as AccessRecord['status'] };
      case 'comments':
        return { comments: value };
      default:
        return { data: { ...record.data, [column]: value } };
    }
  };

  const getCellId = (row: number, col: number): string => {
    return `${row}-${col}`;
  };

  // Handle row selection
  const handleRowSelect = (recordId: string, checked: boolean) => {
    const newSelectedRows = new Set(selectedRows);
    if (checked) {
      newSelectedRows.add(recordId);
    } else {
      newSelectedRows.delete(recordId);
    }
    setSelectedRows(newSelectedRows);
  };

  // Handle select all
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      const allFilteredIds = filteredRecords.map(record => record.id);
      setSelectedRows(new Set(allFilteredIds));
    } else {
      setSelectedRows(new Set());
    }
    setSelectAll(checked);
  };

  const handleMouseDown = (row: number, col: number, event: React.MouseEvent) => {
    if (!canEdit) return;

    event.preventDefault();

    if (event.ctrlKey || event.metaKey) {
      // Ctrl+click for multi-selection
      const cellId = getCellId(row, col);
      const newSelected = new Set(selectedCells);
      if (newSelected.has(cellId)) {
        newSelected.delete(cellId);
      } else {
        newSelected.add(cellId);
      }
      setSelectedCells(newSelected);
    } else {
      // Start new selection
      setSelectedRange({ start: { row, col }, end: { row, col } });
      setSelectedCells(new Set([getCellId(row, col)]));
      setIsSelecting(true);
    }
  };

  const handleMouseEnter = (row: number, col: number) => {
    if (!isSelecting || !selectedRange) return;

    const newRange = { ...selectedRange, end: { row, col } };
    setSelectedRange(newRange);

    // Update selected cells for range
    const newSelected = new Set<string>();
    const minRow = Math.min(newRange.start.row, newRange.end.row);
    const maxRow = Math.max(newRange.start.row, newRange.end.row);
    const minCol = Math.min(newRange.start.col, newRange.end.col);
    const maxCol = Math.max(newRange.start.col, newRange.end.col);

    for (let r = minRow; r <= maxRow; r++) {
      for (let c = minCol; c <= maxCol; c++) {
        newSelected.add(getCellId(r, c));
      }
    }
    setSelectedCells(newSelected);
  };

  const handleMouseUp = () => {
    setIsSelecting(false);
  };

  const handleDoubleClick = (row: number, col: number) => {
    if (!canEdit) return;

    const record = filteredRecords[row];
    const column = allColumns[col];
    const value = getCellValue(record, column);

    setEditingCell({ row, col });
    setEditValue(value);
  };

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (selectedCells.size === 0) return;

    switch (e.key) {
      case 'c':
      case 'C':
        if (e.ctrlKey || e.metaKey) {
          e.preventDefault();
          handleCopy();
        }
        break;
      case 'v':
      case 'V':
        if (e.ctrlKey || e.metaKey) {
          e.preventDefault();
          handlePaste();
        }
        break;
      case 'Delete':
        e.preventDefault();
        handleDelete();
        break;
      case 'Enter':
        if (editingCell) {
          handleSaveEdit();
        }
        break;
      case 'Escape':
        setEditingCell(null);
        setEditValue('');
        setSelectedCells(new Set());
        break;
    }
  }, [selectedCells, editingCell, editValue]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [handleKeyDown]);

  const handleCopy = () => {
    if (selectedCells.size === 0) return;

    const cellPositions = Array.from(selectedCells).map(cellId => {
      const [row, col] = cellId.split('-').map(Number);
      return { row, col };
    });

    // Sort by row, then by column
    cellPositions.sort((a, b) => a.row - b.row || a.col - b.col);

    const data: string[][] = [];
    const rowGroups = new Map<number, { row: number; col: number }[]>();

    cellPositions.forEach(pos => {
      if (!rowGroups.has(pos.row)) {
        rowGroups.set(pos.row, []);
      }
      rowGroups.get(pos.row)!.push(pos);
    });

    Array.from(rowGroups.keys()).sort().forEach(rowNum => {
      const rowCells = rowGroups.get(rowNum)!.sort((a, b) => a.col - b.col);
      const rowData = rowCells.map(pos => {
        const record = filteredRecords[pos.row];
        const column = allColumns[pos.col];
        return getCellValue(record, column);
      });
      data.push(rowData);
    });

    setCopiedData(data);

    // Copy to clipboard
    const textData = data.map(row => row.join('\t')).join('\n');
    navigator.clipboard.writeText(textData);
  };

  const handlePaste = () => {
    if (selectedCells.size === 0 || !copiedData) return;

    const updates: { id: string; updates: Partial<AccessRecord> }[] = [];
    const firstCellId = Array.from(selectedCells)[0];
    const [startRow, startCol] = firstCellId.split('-').map(Number);

    copiedData.forEach((rowData, rowOffset) => {
      const targetRow = startRow + rowOffset;
      if (targetRow >= filteredRecords.length) return;

      const record = filteredRecords[targetRow];
      let recordUpdates: Partial<AccessRecord> = {};

      rowData.forEach((cellValue, colOffset) => {
        const targetCol = startCol + colOffset;
        if (targetCol >= allColumns.length) return;

        const column = allColumns[targetCol];
        const cellUpdate = setCellValue(record, column, cellValue);
        recordUpdates = { ...recordUpdates, ...cellUpdate };
      });

      if (Object.keys(recordUpdates).length > 0) {
        updates.push({ id: record.id, updates: recordUpdates });
      }
    });

    if (updates.length > 0) {
      onUpdateMultiple(updates);
    }
  };

  const handleDelete = () => {
    if (selectedCells.size === 0) return;

    const updates: { id: string; updates: Partial<AccessRecord> }[] = [];
    const processedRecords = new Set<string>();

    selectedCells.forEach(cellId => {
      const [row, col] = cellId.split('-').map(Number);
      const record = filteredRecords[row];

      if (processedRecords.has(record.id)) return;

      const column = allColumns[col];
      if (column !== 'id' && column !== 'createdAt') {
        const cellUpdate = setCellValue(record, column, '');
        updates.push({ id: record.id, updates: cellUpdate });
        processedRecords.add(record.id);
      }
    });

    if (updates.length > 0) {
      onUpdateMultiple(updates);
    }
  };

  const handleSaveEdit = () => {
    if (!editingCell) return;

    const record = filteredRecords[editingCell.row];
    const column = allColumns[editingCell.col];
    const updates = setCellValue(record, column, editValue);

    onUpdateRecord(record.id, updates);
    setEditingCell(null);
    setEditValue('');
  };

  const handleBatchUpdate = () => {
    if (selectedRows.size === 0) return;
    setShowBatchDialog(true);
  };

  const executeBatchUpdate = () => {
    if (selectedRows.size === 0 || !batchValue) return;

    const updates: { id: string; updates: Partial<AccessRecord> }[] = [];

    selectedRows.forEach(recordId => {
      let recordUpdate: Partial<AccessRecord> = {};

      switch (batchOperation) {
        case 'status':
          recordUpdate = { status: batchValue as AccessRecord['status'] };
          break;
        case 'comments':
          recordUpdate = { comments: batchValue };
          break;
        case 'certifier':
          recordUpdate = { certifierId: batchValue };
          break;
      }

      updates.push({ id: recordId, updates: recordUpdate });
    });

    if (updates.length > 0) {
      onUpdateMultiple(updates);
    }

    setShowBatchDialog(false);
    setBatchValue('');
    setSelectedRows(new Set());
  };

  const handleExportSelected = (format: 'csv' | 'excel') => {
    if (selectedRows.size === 0) {
      onExport(format);
      return;
    }

    // Create export data for selected rows only
    const selectedRecords = filteredRecords.filter(record => selectedRows.has(record.id));
    
    const allExportColumns = [...allColumns, 'id', 'status', 'comments', 'createdAt', 'updatedAt'];
    const headers = allExportColumns;
    const csvContent = [
      headers.join(','),
      ...selectedRecords.map(record => 
        allExportColumns.map(col => {
          let value = '';
          switch (col) {
            case 'id':
              value = record.id;
              break;
            case 'status':
              value = record.status;
              break;
            case 'comments':
              value = record.comments || '';
              break;
            case 'createdAt':
              value = record.createdAt;
              break;
            case 'updatedAt':
              value = record.updatedAt;
              break;
            default:
              value = String(record.data[col] || '');
          }
          return `"${value.replace(/"/g, '""')}"`;
        }).join(',')
      )
    ].join('\n');

    // Create and download file
    const blob = new Blob([csvContent], { type: format === 'csv' ? 'text/csv' : 'application/vnd.ms-excel' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `selected_records_${new Date().toISOString().split('T')[0]}.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const isCellSelected = (row: number, col: number): boolean => {
    return selectedCells.has(getCellId(row, col));
  };

  const addColumnFilter = (column: string, value: string, type: 'text' | 'select' | 'date' = 'text') => {
    setColumnFilters(prev => {
      const existing = prev.findIndex(f => f.column === column);
      if (existing >= 0) {
        const updated = [...prev];
        updated[existing] = { column, value, type };
        return updated;
      } else {
        return [...prev, { column, value, type }];
      }
    });
  };

  const removeColumnFilter = (column: string) => {
    setColumnFilters(prev => prev.filter(f => f.column !== column));
  };

  const clearAllFilters = () => {
    setColumnFilters([]);
    setSearchTerm('');
    setStatusFilter('all');
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'Certified':
        return 'default';
      case 'Rejected':
        return 'destructive';
      case 'In Review':
        return 'secondary';
      case 'Open for Review':
        return 'outline';
      case 'Access Required':
        return 'outline';
      case 'Review Completed':
        return 'default';
      case 'Access Retained':
        return 'default';
      case 'Access Removed':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Access Records ({filteredRecords.length})</CardTitle>
            <div className="flex items-center space-x-2">
              {selectedRows.size > 0 && (
                  <div className="flex items-center space-x-1">
                    <Badge variant="secondary">{selectedRows.size} rows selected</Badge>
                    <Button size="sm" variant="outline" onClick={handleBatchUpdate}>
                      <Edit className="w-4 h-4 mr-1" />
                      Batch Update
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => handleExportSelected('csv')}>
                      <Download className="w-4 h-4 mr-1" />
                      Export Selected
                    </Button>
                  </div>
              )}
              {selectedCells.size > 0 && (
                  <div className="flex items-center space-x-1">
                    <Badge variant="outline">{selectedCells.size} cells selected</Badge>
                    <Button size="sm" variant="outline" onClick={handleCopy}>
                      <Copy className="w-4 h-4 mr-1" />
                      Copy
                    </Button>
                    <Button size="sm" variant="outline" onClick={handleDelete}>
                      <Trash2 className="w-4 h-4 mr-1" />
                      Clear
                    </Button>
                  </div>
              )}
              <Button variant="outline" size="sm" onClick={() => onExport('csv')}>
                <Download className="w-4 h-4 mr-2" />
                CSV
              </Button>
              <Button variant="outline" size="sm" onClick={() => onExport('excel')}>
                <Download className="w-4 h-4 mr-2" />
                Excel
              </Button>
            </div>
          </div>

          {/* Global Search and Status Filter */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 flex-1">
              <Search className="w-4 h-4 text-gray-400" />
              <Input
                  placeholder="Search all columns..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="max-w-sm"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="Pending">Pending</SelectItem>
                <SelectItem value="In Review">In Review</SelectItem>
                <SelectItem value="Certified">Certified</SelectItem>
                <SelectItem value="Rejected">Rejected</SelectItem>
                <SelectItem value="Open for Review">Open for Review</SelectItem>
                <SelectItem value="Access Required">Access Required</SelectItem>
                <SelectItem value="Review Completed">Review Completed</SelectItem>
                <SelectItem value="Access Retained">Access Retained</SelectItem>
                <SelectItem value="Access Removed">Access Removed</SelectItem>
              </SelectContent>
            </Select>
            {(columnFilters.length > 0 || searchTerm || statusFilter !== 'all') && (
                <Button variant="outline" size="sm" onClick={clearAllFilters}>
                  <X className="w-4 h-4 mr-1" />
                  Clear Filters
                </Button>
            )}
          </div>

          {/* Active Column Filters Display */}
          {columnFilters.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {columnFilters.map(filter => (
                    <Badge key={filter.column} variant="secondary" className="flex items-center gap-1">
                      {filter.column}: {filter.value}
                      <X
                          className="w-3 h-3 cursor-pointer"
                          onClick={() => removeColumnFilter(filter.column)}
                      />
                    </Badge>
                ))}
              </div>
          )}

          {copiedData && (
              <div className="text-sm text-blue-600 bg-blue-50 p-2 rounded">
                Copied {copiedData.length} row(s) × {copiedData[0]?.length || 0} column(s). Press Ctrl+V to paste.
              </div>
          )}
        </CardHeader>

        <CardContent>
          {filteredRecords.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No records found. {records.length === 0 ? 'Upload data to get started.' : 'Try adjusting your search or filters.'}
              </div>
          ) : (
              <div className="overflow-auto max-h-[600px] border rounded">
                <table ref={tableRef} className="w-full text-sm">
                  <thead className="sticky top-0 bg-gray-50 border-b">
                  <tr>
                    {/* Checkbox column header */}
                    <th className="text-left py-2 px-3 font-medium text-gray-700 border-r w-12">
                      <Checkbox
                        checked={selectAll}
                        onCheckedChange={handleSelectAll}
                        aria-label="Select all rows"
                      />
                    </th>
                    {allColumns.map((column, colIndex) => (
                        <th key={column} className="text-left py-2 px-3 font-medium text-gray-700 border-r min-w-[120px]">
                          <div className="flex items-center justify-between">
                            <span>{column.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').trim()}</span>
                            <Popover>
                              <PopoverTrigger asChild>
                                <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                                  <Filter className="w-3 h-3" />
                                </Button>
                              </PopoverTrigger>
                              <PopoverContent className="w-56">
                                <div className="space-y-2">
                                  <div className="font-medium text-sm">Filter {column}</div>
                                  {isStatusColumn(column) ? (
                                      <Select
                                          value={columnFilters.find(f => f.column === column)?.value || 'all'}
                                          onValueChange={(value) => value === 'all' ? removeColumnFilter(column) : addColumnFilter(column, value, 'select')}
                                      >
                                        <SelectTrigger>
                                          <SelectValue placeholder="Select status" />
                                        </SelectTrigger>
                                        <SelectContent>
                                          <SelectItem value="all">All</SelectItem>
                                          {getStatusOptions(column).map(value => (
                                              <SelectItem key={value} value={value}>{value}</SelectItem>
                                          ))}
                                        </SelectContent>
                                      </Select>
                                  ) : getUniqueColumnValues(column).length <= 20 ? (
                                      <Select
                                          value={columnFilters.find(f => f.column === column)?.value || 'all'}
                                          onValueChange={(value) => value === 'all' ? removeColumnFilter(column) : addColumnFilter(column, value, 'select')}
                                      >
                                        <SelectTrigger>
                                          <SelectValue placeholder="Select value" />
                                        </SelectTrigger>
                                        <SelectContent>
                                          <SelectItem value="all">All</SelectItem>
                                          {getUniqueColumnValues(column).map(value => (
                                              <SelectItem key={value} value={value}>{value}</SelectItem>
                                          ))}
                                        </SelectContent>
                                      </Select>
                                  ) : (
                                      <Input
                                          placeholder="Filter text..."
                                          value={columnFilters.find(f => f.column === column)?.value || ''}
                                          onChange={(e) => {
                                            if (e.target.value) {
                                              addColumnFilter(column, e.target.value, 'text');
                                            } else {
                                              removeColumnFilter(column);
                                            }
                                          }}
                                      />
                                  )}
                                </div>
                              </PopoverContent>
                            </Popover>
                          </div>
                        </th>
                    ))}
                  </tr>
                  </thead>
                  <tbody>
                  {filteredRecords.map((record, rowIndex) => (
                      <tr key={record.id} className={`border-b hover:bg-gray-50 ${selectedRows.has(record.id) ? 'bg-blue-50' : ''}`}>
                        {/* Checkbox column */}
                        <td className="py-2 px-3 border-r">
                          <Checkbox
                            checked={selectedRows.has(record.id)}
                            onCheckedChange={(checked) => handleRowSelect(record.id, !!checked)}
                            aria-label={`Select row ${rowIndex + 1}`}
                          />
                        </td>
                        {allColumns.map((column, colIndex) => {
                          const isSelected = isCellSelected(rowIndex, colIndex);
                          const isEditing = editingCell?.row === rowIndex && editingCell?.col === colIndex;
                          const cellValue = getCellValue(record, column);

                          return (
                              <td
                                  key={`${record.id}-${column}`}
                                  className={`py-2 px-3 border-r cursor-pointer ${
                                      isSelected ? 'bg-blue-200 border-blue-400' : ''
                                  } ${canEdit ? 'hover:bg-gray-100' : ''}`}
                                  onMouseDown={(e) => handleMouseDown(rowIndex, colIndex, e)}
                                  onMouseEnter={() => handleMouseEnter(rowIndex, colIndex)}
                                  onDoubleClick={() => handleDoubleClick(rowIndex, colIndex)}
                              >
                                {isEditing ? (
                                    isStatusColumn(column) ? (
                                        <Select value={editValue} onValueChange={setEditValue}>
                                          <SelectTrigger className="w-full h-8">
                                            <SelectValue />
                                          </SelectTrigger>
                                          <SelectContent>
                                            {getStatusOptions(column).map(option => (
                                                <SelectItem key={option} value={option}>{option}</SelectItem>
                                            ))}
                                          </SelectContent>
                                        </Select>
                                    ) : (
                                        <Input
                                            value={editValue}
                                            onChange={(e) => setEditValue(e.target.value)}
                                            onBlur={handleSaveEdit}
                                            onKeyDown={(e) => {
                                              if (e.key === 'Enter') handleSaveEdit();
                                              if (e.key === 'Escape') {
                                                setEditingCell(null);
                                                setEditValue('');
                                              }
                                            }}
                                            className="w-full h-8"
                                            autoFocus
                                        />
                                    )
                                ) : isStatusColumn(column) ? (
                                    <Badge variant={getStatusBadgeVariant(cellValue)}>
                                      {cellValue}
                                    </Badge>
                                ) : (
                                    <span className="block truncate" title={cellValue}>
                              {cellValue}
                            </span>
                                )}
                              </td>
                          );
                        })}
                      </tr>
                  ))}
                  </tbody>
                </table>
              </div>
          )}

          {canEdit && (
              <div className="mt-4 text-sm text-gray-600">
                <p><strong>Excel-like Controls:</strong></p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Use checkboxes to select individual rows or select all with the header checkbox</li>
                  <li>Click and drag to select multiple cells, Ctrl+Click for individual selection</li>
                  <li>Double-click to edit a cell</li>
                  <li>Ctrl+C to copy, Ctrl+V to paste, Delete to clear</li>
                  <li>Use column filter buttons to filter individual columns</li>
                  <li>Select rows and use "Batch Update" for bulk operations</li>
                </ul>
              </div>
          )}
        </CardContent>

        {/* Batch Update Dialog */}
        <Dialog open={showBatchDialog} onOpenChange={setShowBatchDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Batch Update</DialogTitle>
              <DialogDescription>
                Update {selectedRows.size} selected rows with the same value.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Operation</label>
                <Select value={batchOperation} onValueChange={(value: BatchOperationType) => setBatchOperation(value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="status">Update Status</SelectItem>
                    <SelectItem value="comments">Update Comments</SelectItem>
                    <SelectItem value="certifier">Update Certifier</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Value</label>
                {batchOperation === 'status' ? (
                    <Select value={batchValue} onValueChange={setBatchValue}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Pending">Pending</SelectItem>
                        <SelectItem value="In Review">In Review</SelectItem>
                        <SelectItem value="Certified">Certified</SelectItem>
                        <SelectItem value="Rejected">Rejected</SelectItem>
                        <SelectItem value="Open for Review">Open for Review</SelectItem>
                        <SelectItem value="Access Required">Access Required</SelectItem>
                        <SelectItem value="Review Completed">Review Completed</SelectItem>
                        <SelectItem value="Access Retained">Access Retained</SelectItem>
                        <SelectItem value="Access Removed">Access Removed</SelectItem>
                      </SelectContent>
                    </Select>
                ) : (
                    <Input
                        value={batchValue}
                        onChange={(e) => setBatchValue(e.target.value)}
                        placeholder={`Enter ${batchOperation}...`}
                    />
                )}
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowBatchDialog(false)}>
                Cancel
              </Button>
              <Button onClick={executeBatchUpdate} disabled={!batchValue}>
                <Check className="w-4 h-4 mr-1" />
                Update {selectedRows.size} Records
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </Card>
  );
}
