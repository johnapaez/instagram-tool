import React, { useState } from 'react';
import { Check, UserMinus, AlertCircle, Shield, BadgeCheck } from 'lucide-react';
import Button from './Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './Card';
import { actionApi, statsApi } from '../services/api';
import type { UserInfo } from '../types';
import { formatNumber } from '../lib/utils';

interface UserListProps {
  users: UserInfo[];
  sessionId: string;
  onUnfollowComplete: () => void;
}

const UserList: React.FC<UserListProps> = ({ users, sessionId, onUnfollowComplete }) => {
  const [selectedUsers, setSelectedUsers] = useState<Set<string>>(new Set());
  const [unfollowing, setUnfollowing] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [dailyLimit, setDailyLimit] = useState<number | null>(null);

  React.useEffect(() => {
    loadDailyLimit();
  }, []);

  const loadDailyLimit = async () => {
    try {
      const stats = await statsApi.getStats();
      setDailyLimit(stats.remaining_today);
    } catch (err) {
      console.error('Failed to load daily limit:', err);
    }
  };

  const toggleUser = (username: string) => {
    const newSelected = new Set(selectedUsers);
    if (newSelected.has(username)) {
      newSelected.delete(username);
    } else {
      newSelected.add(username);
    }
    setSelectedUsers(newSelected);
  };

  const selectAll = () => {
    if (dailyLimit !== null && users.length > dailyLimit) {
      setSelectedUsers(new Set(users.slice(0, dailyLimit).map((u) => u.username)));
    } else {
      setSelectedUsers(new Set(users.map((u) => u.username)));
    }
  };

  const deselectAll = () => {
    setSelectedUsers(new Set());
  };

  const handleUnfollow = async () => {
    if (selectedUsers.size === 0) {
      setError('Please select at least one user');
      return;
    }

    if (dailyLimit !== null && selectedUsers.size > dailyLimit) {
      setError(
        `You can only unfollow ${dailyLimit} more users today. Please reduce your selection.`
      );
      return;
    }

    setUnfollowing(true);
    setError('');
    setSuccess('');

    try {
      const usernames = Array.from(selectedUsers);
      const response = await actionApi.unfollowUsers(usernames, sessionId);

      if (response.success) {
        setSuccess(`Successfully unfollowed ${usernames.length} users`);
        setSelectedUsers(new Set());
        setTimeout(() => {
          onUnfollowComplete();
        }, 2000);
      } else {
        setError(
          `Unfollowed with some errors: ${response.errors.join(', ')}`
        );
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to unfollow users');
    } finally {
      setUnfollowing(false);
      await loadDailyLimit();
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle>Non-Followers ({users.length})</CardTitle>
            <CardDescription>
              Select users to unfollow. {selectedUsers.size} selected
              {dailyLimit !== null && ` • ${dailyLimit} remaining today`}
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={selectAll}>
              Select All
            </Button>
            <Button variant="outline" size="sm" onClick={deselectAll}>
              Deselect All
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <div className="bg-destructive/15 text-destructive px-4 py-3 rounded-md flex items-start gap-2">
            <AlertCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
            <p className="text-sm">{error}</p>
          </div>
        )}

        {success && (
          <div className="bg-green-50 text-green-800 px-4 py-3 rounded-md flex items-start gap-2">
            <Check className="h-5 w-5 mt-0.5 flex-shrink-0" />
            <p className="text-sm">{success}</p>
          </div>
        )}

        <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-md flex items-start gap-2">
          <Shield className="h-5 w-5 mt-0.5 flex-shrink-0" />
          <div className="text-sm">
            <p className="font-medium mb-1">Safety Settings Active</p>
            <p>
              Unfollowing will happen with 30-60 second delays between each user to
              avoid detection. This is not instantaneous.
            </p>
          </div>
        </div>

        {/* User List */}
        <div className="border rounded-md divide-y max-h-[500px] overflow-y-auto">
          {users.map((user) => (
            <div
              key={user.username}
              className={`p-4 flex items-center justify-between hover:bg-gray-50 cursor-pointer ${
                selectedUsers.has(user.username) ? 'bg-blue-50' : ''
              }`}
              onClick={() => toggleUser(user.username)}
            >
              <div className="flex items-center gap-3 flex-1">
                <input
                  type="checkbox"
                  checked={selectedUsers.has(user.username)}
                  onChange={() => toggleUser(user.username)}
                  className="h-4 w-4 rounded border-gray-300"
                  onClick={(e) => e.stopPropagation()}
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-medium">@{user.username}</p>
                    {user.is_verified && (
                      <BadgeCheck className="h-4 w-4 text-blue-500" />
                    )}
                  </div>
                  {user.full_name && (
                    <p className="text-sm text-gray-600">{user.full_name}</p>
                  )}
                  <p className="text-xs text-gray-500">
                    {formatNumber(user.follower_count)} followers
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Unfollow Button */}
        <div className="flex justify-end">
          <Button
            variant="destructive"
            onClick={handleUnfollow}
            disabled={unfollowing || selectedUsers.size === 0}
          >
            {unfollowing ? (
              <>Processing ({selectedUsers.size} users)...</>
            ) : (
              <>
                <UserMinus className="mr-2 h-4 w-4" />
                Unfollow Selected ({selectedUsers.size})
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default UserList;
