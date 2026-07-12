import React, { useState, useEffect, useCallback, useRef } from 'react';

interface Task {
  id: string;
  text: string;
  priority: 'urgent' | 'normal' | 'low' | string;
  deadline: string | null;
  photo_url: string | null;
}

interface TaskListProps {
  token: string;
}

export function TaskList({ token }: TaskListProps) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [priorityFilter, setPriorityFilter] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const abortControllerRef = useRef<AbortController | null>(null);

  const loadTasks = useCallback(async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    setIsLoading(true);
    setError('');

    try {
      const response = await fetch(
        `/api/tasks?priority=${encodeURIComponent(priorityFilter)}`,
        {
          headers: { 'Authorization': `Bearer ${token}` },
          signal: abortController.signal,
        }
      );

      if (response.status === 401) {
        throw new Error('Session expired. Please log in again.');
      }
      if (!response.ok) {
        throw new Error(`Failed to load tasks: ${response.statusText}`);
      }

      const data = await response.json();
      setTasks(data.tasks || []);
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        return;
      }
      setError(err instanceof Error ? err.message : 'Failed to load tasks');
    } finally {
      setIsLoading(false);
    }
  }, [priorityFilter, token]);

  useEffect(() => {
    loadTasks();
    return () => {
      abortControllerRef.current?.abort();
    };
  }, [loadTasks]);

  const deleteTask = async (taskId: string) => {
    if (!window.confirm('Are you sure you want to delete this task?')) {
      return;
    }

    try {
      const response = await fetch(`/api/tasks/${taskId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) {
        throw new Error('Failed to delete task');
      }

      setTasks((prev) => prev.filter((t) => t.id !== taskId));
      loadTasks();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete task');
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-500 text-white';
      case 'normal': return 'bg-yellow-500 text-gray-900';
      case 'low': return 'bg-green-500 text-white';
      default: return 'bg-gray-500 text-white';
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  const isOverdue = (deadline: string | null) => {
    if (!deadline) return false;
    return new Date(deadline) < new Date();
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="bg-gray-700 text-white p-2 rounded focus:outline-none focus:ring-2 focus:ring-purple-400"
          disabled={isLoading}
          aria-label="Filter by priority"
        >
          <option value="">All Priorities</option>
          <option value="urgent">Urgent</option>
          <option value="normal">Normal</option>
          <option value="low">Low</option>
        </select>

        {isLoading && (
          <span className="text-purple-300 text-sm animate-pulse">
            Loading...
          </span>
        )}
      </div>

      {error && (
        <div
          className="bg-red-500/20 border border-red-500 text-red-200 p-3 rounded"
          role="alert"
          aria-live="polite"
        >
          {error}
          <button
            onClick={loadTasks}
            className="ml-2 underline hover:text-white"
          >
            Retry
          </button>
        </div>
      )}

      <div className="space-y-4">
        {tasks.length === 0 && !isLoading && !error && (
          <div className="text-center text-gray-400 py-12">
            <p className="text-lg mb-2">No tasks found</p>
            <p className="text-sm">
              {priorityFilter
                ? 'Try changing the priority filter'
                : 'Create your first task to get started'}
            </p>
          </div>
        )}

        {tasks.map((task) => (
          <div
            key={task.id}
            className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition-colors"
          >
            {task.photo_url && (
              <div className="mb-3">
                <img
                  src={task.photo_url}
                  alt={`Photo for task: ${task.text}`}
                  className="w-full h-40 object-cover rounded"
                  loading="lazy"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
              </div>
            )}

            <p className="text-white text-lg font-medium">{task.text}</p>

            <div className="flex items-center mt-3 flex-wrap gap-2">
              <span
                className={`${getPriorityColor(task.priority)} px-2 py-1 rounded text-sm font-medium capitalize`}
              >
                {task.priority}
              </span>

              {task.deadline && (
                <span
                  className={`text-sm flex items-center gap-1 ${
                    isOverdue(task.deadline)
                      ? 'text-red-400 font-medium'
                      : 'text-gray-400'
                  }`}
                >
                  📅 {formatDate(task.deadline)}
                  {isOverdue(task.deadline) && ' (Overdue)'}
                </span>
              )}

              <button
                onClick={() => deleteTask(task.id)}
                className="ml-auto text-red-400 hover:text-red-300 p-1 rounded hover:bg-red-400/10 transition-colors"
                aria-label={`Delete task: ${task.text}`}
              >
                🗑️ Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
