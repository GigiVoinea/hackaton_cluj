import React from 'react';
import { useState } from 'react';

function App() {
  // Mock data for demonstration
  const transactions = [
    { id: 1, category: 'Groceries', amount: 54.23, date: '2024-05-20' },
    { id: 2, category: 'Transport', amount: 15.00, date: '2024-05-19' },
    { id: 3, category: 'Dining', amount: 32.50, date: '2024-05-18' },
    { id: 4, category: 'Utilities', amount: 120.00, date: '2024-05-17' },
  ];

  // Alerts mock data
  const [alerts, setAlerts] = useState([
    { id: 1, type: 'warning', message: "You're close to your monthly budget!", time: '2m ago' },
    { id: 2, type: 'info', message: 'Unusual transaction detected.', time: '1h ago' },
    { id: 3, type: 'success', message: 'You saved $50 this week! 🎉', time: '3h ago' },
  ]);

  const alertStyles = {
    warning: 'bg-warning/20 border-warning text-warning',
    info: 'bg-info/20 border-info text-info',
    success: 'bg-success/20 border-success text-success',
    error: 'bg-error/20 border-error text-error',
  };

  const alertIcons = {
    warning: '⚠️',
    info: 'ℹ️',
    success: '✅',
    error: '❌',
  };

  const dismissAlert = (id) => setAlerts(alerts.filter(a => a.id !== id));

  return (
    <div className="min-h-screen flex flex-col items-center p-4 font-sans bg-gradient-to-br from-blue-50 to-green-100">
      {/* Header */}
      <header className="w-full max-w-2xl flex justify-between items-center py-4 mb-4">
        <h1 className="text-2xl md:text-3xl font-bold text-primary flex items-center gap-2">
          Finn <span className="text-accent">•</span> <span className="hidden sm:inline">Your Financial Buddy</span>
        </h1>
        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold shadow-soft">U</div>
      </header>

      {/* Alerts Area */}
      {alerts.length > 0 && (
        <section className="w-full max-w-2xl flex flex-col gap-3 mb-6">
          {alerts.map(alert => (
            <div
              key={alert.id}
              className={`relative flex items-center border-l-4 p-4 rounded-lg shadow-soft animate-fade-in transition-all duration-300 ${alertStyles[alert.type]}`}
              tabIndex={0}
              aria-live="polite"
            >
              <span className="mr-3 text-2xl" aria-hidden>{alertIcons[alert.type]}</span>
              <div className="flex-1">
                <span className="block font-medium">{alert.message}</span>
                <span className="block text-xs text-gray-400">{alert.time}</span>
              </div>
              <button
                onClick={() => dismissAlert(alert.id)}
                className="ml-4 text-gray-400 hover:text-gray-700 text-lg font-bold px-2 focus:outline-none focus:ring-2 focus:ring-primary rounded"
                aria-label="Dismiss alert"
              >
                ×
              </button>
            </div>
          ))}
        </section>
      )}

      {/* Spending Summary */}
      <section className="w-full max-w-2xl bg-white rounded-2xl shadow-soft p-6 mb-6 flex flex-col md:flex-row justify-between items-center transition-all duration-300">
        <div>
          <h2 className="text-lg font-semibold text-gray-700">Total Spent This Month</h2>
          <p className="text-3xl font-bold text-accent">$221.73</p>
        </div>
        <div className="mt-4 md:mt-0">
          <span className="inline-block bg-accent/20 text-accent px-3 py-1 rounded-full text-sm font-semibold">+5% from last month</span>
        </div>
      </section>

      {/* Chart Placeholder */}
      <section className="w-full max-w-2xl bg-white rounded-2xl shadow-soft p-6 mb-6 flex flex-col items-center transition-all duration-300">
        <h3 className="text-md font-semibold text-gray-700 mb-2">Spending by Category</h3>
        <div className="w-full h-40 flex items-center justify-center bg-gradient-to-r from-primary/10 to-accent/10 rounded-lg">
          {/* Chart.js or Recharts can be integrated here */}
          <span className="text-gray-400">[Chart Placeholder]</span>
        </div>
      </section>

      {/* Recent Transactions */}
      <section className="w-full max-w-2xl bg-white rounded-2xl shadow-soft p-6 mb-20 transition-all duration-300">
        <h3 className="text-md font-semibold text-gray-700 mb-4">Recent Transactions</h3>
        <ul>
          {transactions.map(tx => (
            <li key={tx.id} className="flex justify-between items-center py-2 border-b last:border-b-0 group">
              <span className="font-medium text-gray-600 group-hover:text-primary transition-colors duration-200">{tx.category}</span>
              <span className="text-gray-400 text-sm">{tx.date}</span>
              <span className="font-bold text-primary">${tx.amount.toFixed(2)}</span>
            </li>
          ))}
        </ul>
      </section>

      {/* Floating Action Button */}
      <button
        className="fixed bottom-8 right-8 bg-primary hover:bg-primary-dark text-white rounded-full w-16 h-16 flex items-center justify-center shadow-lg text-3xl transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-accent"
        aria-label="Add transaction"
      >
        +
      </button>
    </div>
  );
}

export default App; 