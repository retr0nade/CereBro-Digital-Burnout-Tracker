import React, { useState } from 'react';

interface ExportOptions {
  table: string;
  limit: number;
}

const DataExport: React.FC = () => {
  const [exporting, setExporting] = useState(false);
  const [exportType, setExportType] = useState<'csv' | 'json' | null>(null);

  const tableOptions = [
    { value: 'all', label: 'All Tables' },
    { value: 'app_usage', label: 'App Usage' },
    { value: 'idle_periods', label: 'Idle Periods' },
    { value: 'input_activity', label: 'Input Activity' },
    { value: 'focus_sessions', label: 'Focus Sessions' },
    { value: 'breaks', label: 'Breaks' },
    { value: 'browser_activity', label: 'Browser Activity' },
    { value: 'system_metrics', label: 'System Metrics' }
  ];

  const limitOptions = [
    { value: 100, label: '100 records' },
    { value: 500, label: '500 records' },
    { value: 1000, label: '1,000 records' },
    { value: 5000, label: '5,000 records' },
    { value: 10000, label: '10,000 records' }
  ];

  const [options, setOptions] = useState<ExportOptions>({
    table: 'all',
    limit: 1000
  });

  const downloadExport = async (format: 'csv' | 'json') => {
    if (exporting) return;

    setExporting(true);
    setExportType(format);

    try {
      const params = new URLSearchParams({
        table: options.table,
        limit: options.limit.toString()
      });

      const response = await fetch(`http://localhost:5005/api/export/${format}?${params}`);
      
      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }

      // Get filename from response headers or generate one
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `cerebro_export_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.${format}`;
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (error) {
      console.error('Export failed:', error);
      alert(`Export failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setExporting(false);
      setExportType(null);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-6">
      <div className="bg-gray-800 rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-pink-400 mb-6">Data Export</h2>
        
        <div className="space-y-6">
          {/* Export Options */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Table Selection
              </label>
              <select
                value={options.table}
                onChange={(e) => setOptions(prev => ({ ...prev, table: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-pink-500"
              >
                {tableOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Record Limit
              </label>
              <select
                value={options.limit}
                onChange={(e) => setOptions(prev => ({ ...prev, limit: parseInt(e.target.value) }))}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-pink-500"
              >
                {limitOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Export Buttons */}
          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={() => downloadExport('csv')}
              disabled={exporting}
              className={`flex-1 px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
                exporting && exportType === 'csv'
                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  : 'bg-green-600 hover:bg-green-700 text-white hover:shadow-lg transform hover:scale-105'
              }`}
            >
              {exporting && exportType === 'csv' ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Exporting CSV...
                </span>
              ) : (
                <span className="flex items-center justify-center">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Download CSV
                </span>
              )}
            </button>

            <button
              onClick={() => downloadExport('json')}
              disabled={exporting}
              className={`flex-1 px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
                exporting && exportType === 'json'
                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white hover:shadow-lg transform hover:scale-105'
              }`}
            >
              {exporting && exportType === 'json' ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Exporting JSON...
                </span>
              ) : (
                <span className="flex items-center justify-center">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Download JSON
                </span>
              )}
            </button>
          </div>

          {/* Information */}
          <div className="bg-gray-700 rounded-lg p-4">
            <h3 className="text-lg font-medium text-pink-400 mb-2">Export Information</h3>
            <div className="text-sm text-gray-300 space-y-2">
              <p>
                <strong>CSV Format:</strong> Tabular data with headers, suitable for spreadsheet applications like Excel or Google Sheets.
              </p>
              <p>
                <strong>JSON Format:</strong> Structured data format, ideal for data analysis, programming, or API integration.
              </p>
              <p>
                <strong>Table Selection:</strong> Choose to export all tables or select specific data types.
              </p>
              <p>
                <strong>Record Limit:</strong> Control the number of records exported to manage file size and performance.
              </p>
            </div>
          </div>

          {/* Available Tables */}
          <div className="bg-gray-700 rounded-lg p-4">
            <h3 className="text-lg font-medium text-pink-400 mb-3">Available Data Tables</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <h4 className="font-medium text-white mb-2">Activity Tracking</h4>
                <ul className="space-y-1 text-gray-300">
                  <li>• <strong>App Usage:</strong> Application usage sessions and durations</li>
                  <li>• <strong>Input Activity:</strong> Keyboard and mouse activity logs</li>
                  <li>• <strong>Browser Activity:</strong> Web browsing sessions and URLs</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-white mb-2">Focus & Wellness</h4>
                <ul className="space-y-1 text-gray-300">
                  <li>• <strong>Focus Sessions:</strong> Dedicated focus time periods</li>
                  <li>• <strong>Breaks:</strong> Break periods and types</li>
                  <li>• <strong>Idle Periods:</strong> System idle time detection</li>
                  <li>• <strong>System Metrics:</strong> CPU and RAM usage monitoring</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataExport;
