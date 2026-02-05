import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle, XCircle, Clock } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './Card';
import { logsApi } from '../services/api';
import type { ActionLog } from '../types';
import { formatDate } from '../lib/utils';

const ActivityLog: React.FC = () => {
  const [logs, setLogs] = useState<ActionLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLogs();
    // Refresh logs every 30 seconds
    const interval = setInterval(loadLogs, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadLogs = async () => {
    try {
      const data = await logsApi.getLogs(50);
      setLogs(data);
    } catch (err) {
      console.error('Failed to load logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const getActionIcon = (actionType: string, status: string) => {
    if (status === 'success') {
      return <CheckCircle className="h-4 w-4 text-green-600" />;
    } else if (status === 'failed') {
      return <XCircle className="h-4 w-4 text-red-600" />;
    }
    return <Clock className="h-4 w-4 text-gray-400" />;
  };

  const getActionLabel = (actionType: string) => {
    const labels: Record<string, string> = {
      login: 'Login',
      fetch_followers: 'Fetch Followers',
      fetch_following: 'Fetch Following',
      unfollow: 'Unfollow',
    };
    return labels[actionType] || actionType;
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          <CardTitle>Activity Log</CardTitle>
        </div>
        <CardDescription>Recent actions and their status</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <p className="text-sm text-muted-foreground">Loading...</p>
        ) : logs.length === 0 ? (
          <p className="text-sm text-muted-foreground">No activity yet</p>
        ) : (
          <div className="space-y-2">
            {logs.map((log) => (
              <div
                key={log.id}
                className="flex items-center justify-between p-3 border rounded-md hover:bg-gray-50"
              >
                <div className="flex items-center gap-3">
                  {getActionIcon(log.action_type, log.status)}
                  <div>
                    <p className="text-sm font-medium">
                      {getActionLabel(log.action_type)}
                      {log.username && ` - @${log.username}`}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(log.created_at)}
                    </p>
                  </div>
                </div>
                <span
                  className={`text-xs px-2 py-1 rounded-full ${
                    log.status === 'success'
                      ? 'bg-green-100 text-green-700'
                      : log.status === 'failed'
                      ? 'bg-red-100 text-red-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {log.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ActivityLog;
