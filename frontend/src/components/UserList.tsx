import React, { useState } from 'react';
import { Check, UserMinus, AlertCircle, Shield, BadgeCheck, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, ShieldCheck, ExternalLink } from 'lucide-react';
import Button from './Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './Card';
import { actionApi, statsApi, whitelistApi } from '../services/api';
import type { UserInfo } from '../types';

interface UserListProps {
  users: UserInfo[];
  sessionId: string;
  onUnfollowComplete: () => void;
}

const UserList: React.FC<UserListProps> = ({ users, sessionId, onUnfollowComplete }) => {
  const [selectedUsers, setSelectedUsers] = useState<Set<string>>(new Set());
  const [unfollowing, setUnfollowing] = useState(false);
  const [whitelisting, setWhitelisting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [dailyLimit, setDailyLimit] = useState<number | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(20);

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
    const newSelected = new Set(selectedUsers);
    currentUsers.forEach(user => newSelected.add(user.username));
    setSelectedUsers(newSelected);
  };

  const deselectAll = () => {
    setSelectedUsers(new Set());
  };

  // Pagination calculations
  const totalPages = Math.ceil(users.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentUsers = users.slice(startIndex, endIndex);

  const handlePageSizeChange = (newSize: number) => {
    setItemsPerPage(newSize);
    setCurrentPage(1);
  };

  const goToPage = (page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
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

  const handleWhitelist = async () => {
    if (selectedUsers.size === 0) {
      setError('Please select at least one user');
      return;
    }

    setWhitelisting(true);
    setError('');
    setSuccess('');

    try {
      const usernames = Array.from(selectedUsers);
      const response = await whitelistApi.addToWhitelist(
        usernames,
        'Batch whitelisted from UI'
      );

      if (response.success) {
        const totalAdded = response.added.length;
        const alreadyWhitelisted = response.already_whitelisted.length;
        let message = `Successfully whitelisted ${totalAdded} user${totalAdded !== 1 ? 's' : ''}`;
        if (alreadyWhitelisted > 0) {
          message += ` (${alreadyWhitelisted} already whitelisted)`;
        }
        setSuccess(message);
        setSelectedUsers(new Set());
        setTimeout(() => {
          onUnfollowComplete(); // Refresh the list
        }, 2000);
      } else {
        setError('Failed to whitelist users');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to whitelist users');
    } finally {
      setWhitelisting(false);
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

        {/* Pagination Controls */}
        <div className="flex items-center justify-between border-t pt-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Show:</span>
            {[10, 20, 50, 100].map((size) => (
              <button
                key={size}
                onClick={() => handlePageSizeChange(size)}
                className={`px-3 py-1 text-sm rounded ${
                  itemsPerPage === size
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                {size}
              </button>
            ))}
            <span className="text-sm text-gray-600 ml-2">
              Showing {startIndex + 1}-{Math.min(endIndex, users.length)} of {users.length}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => goToPage(1)}
              disabled={currentPage === 1}
              className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              title="First page"
            >
              <ChevronsLeft className="h-5 w-5" />
            </button>
            <button
              onClick={() => goToPage(currentPage - 1)}
              disabled={currentPage === 1}
              className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Previous page"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <span className="text-sm text-gray-600 px-2">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => goToPage(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Next page"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
            <button
              onClick={() => goToPage(totalPages)}
              disabled={currentPage === totalPages}
              className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Last page"
            >
              <ChevronsRight className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* User Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 max-h-[600px] overflow-y-auto p-1">
          {currentUsers.map((user) => (
            <div
              key={user.username}
              className={`relative border rounded-lg p-3 hover:shadow-md transition-shadow cursor-pointer ${
                selectedUsers.has(user.username) ? 'ring-2 ring-blue-500 bg-blue-50' : 'bg-white'
              }`}
              onClick={() => toggleUser(user.username)}
            >
              <input
                type="checkbox"
                checked={selectedUsers.has(user.username)}
                onChange={() => toggleUser(user.username)}
                className="absolute top-2 left-2 h-4 w-4 rounded border-gray-300 z-10"
                onClick={(e) => e.stopPropagation()}
              />
              <a
                href={`https://www.instagram.com/${user.username}`}
                target="_blank"
                rel="noopener noreferrer"
                className="absolute top-2 right-2 p-1 bg-white rounded-full hover:bg-gray-100 z-10"
                onClick={(e) => e.stopPropagation()}
                title="View on Instagram"
              >
                <ExternalLink className="h-3 w-3 text-gray-600" />
              </a>
              <div className="flex flex-col items-center text-center mt-4">
                {user.profile_pic_url ? (
                  <img
                    src={`http://localhost:8000/api/proxy/image?url=${encodeURIComponent(user.profile_pic_url)}`}
                    alt={user.username}
                    className="h-16 w-16 rounded-full object-cover mb-2"
                  />
                ) : (
                  <div className="h-16 w-16 rounded-full bg-gray-200 flex items-center justify-center mb-2">
                    <span className="text-gray-500 text-xl font-medium">
                      {user.username.charAt(0).toUpperCase()}
                    </span>
                  </div>
                )}
                <div className="w-full">
                  <div className="flex items-center justify-center gap-1 mb-1">
                    <p className="font-medium text-sm truncate">@{user.username}</p>
                    {user.is_verified && (
                      <BadgeCheck className="h-3 w-3 text-blue-500 flex-shrink-0" />
                    )}
                  </div>
                  {user.full_name && (
                    <p className="text-xs text-gray-600 truncate" title={user.full_name}>
                      {user.full_name}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-2">
          <Button
            variant="outline"
            onClick={handleWhitelist}
            disabled={whitelisting || unfollowing || selectedUsers.size === 0}
          >
            {whitelisting ? (
              <>Whitelisting ({selectedUsers.size})...</>
            ) : (
              <>
                <ShieldCheck className="mr-2 h-4 w-4" />
                Whitelist Selected ({selectedUsers.size})
              </>
            )}
          </Button>
          <Button
            variant="destructive"
            onClick={handleUnfollow}
            disabled={unfollowing || whitelisting || selectedUsers.size === 0}
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
