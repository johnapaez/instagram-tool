import React, { useState, useEffect } from 'react';
import {
  Users,
  UserMinus,
  AlertTriangle,
  RefreshCw,
  LogOut,
  Shield,
  TrendingUp,
  Clock,
} from 'lucide-react';
import Button from './Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './Card';
import UserList from './UserList';
import ActivityLog from './ActivityLog';
import { analysisApi, authApi, statsApi } from '../services/api';
import type { UserInfo, Stats } from '../types';
import { formatNumber } from '../lib/utils';

interface DashboardProps {
  sessionId: string;
  username: string;
  onLogout: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ sessionId, username, onLogout }) => {
  const [loading, setLoading] = useState(false);
  const [syncingFollowers, setSyncingFollowers] = useState(false);
  const [syncingFollowing, setSyncingFollowing] = useState(false);
  const [nonFollowers, setNonFollowers] = useState<UserInfo[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await statsApi.getStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const handleSyncFollowers = async () => {
    setSyncingFollowers(true);
    setError('');

    try {
      await analysisApi.getFollowers(username, sessionId, 999999);
      await loadStats();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to sync followers');
    } finally {
      setSyncingFollowers(false);
    }
  };

  const handleSyncFollowing = async () => {
    setSyncingFollowing(true);
    setError('');

    try {
      await analysisApi.getFollowing(username, sessionId, 999999);
      await loadStats();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to sync following');
    } finally {
      setSyncingFollowing(false);
    }
  };

  const handleAnalyze = async () => {
    setError('');

    try {
      // Get non-followers based on current database state
      const analysis = await analysisApi.getNonFollowers(sessionId);

      setNonFollowers(analysis.non_followers);
      await loadStats();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze followers');
    }
  };

  const handleLogout = async () => {
    try {
      await authApi.logout(sessionId);
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      onLogout();
    }
  };

  const handleUnfollowComplete = () => {
    loadStats();
    handleAnalyze();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Instagram Follower Manager
              </h1>
              <p className="text-sm text-gray-600">@{username}</p>
            </div>
            <Button variant="outline" onClick={handleLogout}>
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <Card>
              <CardHeader className="pb-3">
                <CardDescription>Total Followers</CardDescription>
                <CardTitle className="text-3xl">
                  {formatNumber(stats.total_followers)}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardDescription>Following</CardDescription>
                <CardTitle className="text-3xl">
                  {formatNumber(stats.total_following)}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardDescription>Non-Followers</CardDescription>
                <CardTitle className="text-3xl text-orange-600">
                  {formatNumber(stats.non_followers)}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <UserMinus className="h-4 w-4 text-orange-600" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardDescription>Today's Unfollows</CardDescription>
                <CardTitle className="text-3xl">
                  {stats.today_unfollows}/{stats.daily_limit}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardContent>
            </Card>
          </div>
        )}

        {/* Analysis Section */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Analyze Followers</CardTitle>
            <CardDescription>
              Fetch your followers and following lists to identify non-followers
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <div className="bg-destructive/15 text-destructive px-4 py-3 rounded-md flex items-start gap-2">
                <AlertTriangle className="h-5 w-5 mt-0.5 flex-shrink-0" />
                <p className="text-sm">{error}</p>
              </div>
            )}

            <div className="bg-amber-50 border border-amber-200 text-amber-800 px-4 py-3 rounded-md flex items-start gap-2">
              <Shield className="h-5 w-5 mt-0.5 flex-shrink-0" />
              <div className="text-sm">
                <p className="font-medium mb-1">Sync Instructions</p>
                <p>
                  First sync your followers and following lists separately (may take a few minutes each).
                  Then analyze to identify non-followers. Each sync is independent and safe to interrupt.
                </p>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <Button
                onClick={handleSyncFollowers}
                disabled={syncingFollowers}
                className="flex-1"
                variant="outline"
              >
                {syncingFollowers ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Syncing Followers...
                  </>
                ) : (
                  <>
                    <Users className="mr-2 h-4 w-4" />
                    Sync Followers
                  </>
                )}
              </Button>

              <Button
                onClick={handleSyncFollowing}
                disabled={syncingFollowing}
                className="flex-1"
                variant="outline"
              >
                {syncingFollowing ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Syncing Following...
                  </>
                ) : (
                  <>
                    <TrendingUp className="mr-2 h-4 w-4" />
                    Sync Following
                  </>
                )}
              </Button>

              <Button
                onClick={handleAnalyze}
                disabled={syncingFollowers || syncingFollowing}
                className="flex-1"
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Analyze Non-Followers
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* User List */}
        {nonFollowers.length > 0 && (
          <div className="mb-8">
            <UserList
              users={nonFollowers}
              sessionId={sessionId}
              onUnfollowComplete={handleUnfollowComplete}
            />
          </div>
        )}

        {/* Activity Log */}
        <ActivityLog />
      </main>
    </div>
  );
};

export default Dashboard;
