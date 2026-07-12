import React, { useState, useEffect } from 'react';
import { Login } from './components/Login';
import { TaskList } from './components/TaskList';
import { TaskUpload } from './components/TaskUpload';
import { CreateTask } from './components/CreateTask';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [showUpload, setShowUpload] = useState(false);

  useEffect(() => {
    const handleStorage = (e: StorageEvent) => {
      if (e.key === 'token') setToken(e.newValue);
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
  };

  if (!token) {
    return <Login setToken={setToken} />;
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <nav className="bg-purple-800 p-4 flex justify-between items-center">
        <h1 className="text-white text-2xl font-bold">📋 AI Tasks</h1>
        <div className="flex gap-3">
          <button
            onClick={() => setShowUpload(!showUpload)}
            className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded transition-colors"
            aria-label={showUpload ? 'Close upload' : 'Upload photo'}
          >
            {showUpload ? '✖ Close' : '📷 Upload Photo'}
          </button>
          <button
            onClick={handleLogout}
            className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded transition-colors"
          >
            Logout
          </button>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto p-4 space-y-4">
        {showUpload && <TaskUpload token={token} onClose={() => setShowUpload(false)} />}
        <CreateTask token={token} />
        <TaskList token={token} />
      </div>
    </div>
  );
}

export default App;
