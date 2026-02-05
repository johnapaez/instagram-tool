import axios from 'axios';
import type {
  LoginResponse,
  AnalysisResponse,
  UnfollowResponse,
  ActionLog,
  Stats,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const authApi = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const response = await api.post('/auth/login', { username, password });
    return response.data;
  },

  logout: async (sessionId: string): Promise<void> => {
    await api.post('/auth/logout', null, { params: { session_id: sessionId } });
  },
};

export const analysisApi = {
  getFollowers: async (username: string, sessionId: string, limit = 500) => {
    const response = await api.get(`/analysis/followers/${username}`, {
      params: { session_id: sessionId, limit },
    });
    return response.data;
  },

  getFollowing: async (username: string, sessionId: string, limit = 500) => {
    const response = await api.get(`/analysis/following/${username}`, {
      params: { session_id: sessionId, limit },
    });
    return response.data;
  },

  getNonFollowers: async (
    sessionId: string,
    minFollowers = 10000,
    excludeVerified = true
  ): Promise<AnalysisResponse> => {
    const response = await api.get('/analysis/non-followers', {
      params: {
        session_id: sessionId,
        min_followers: minFollowers,
        exclude_verified: excludeVerified,
      },
    });
    return response.data;
  },
};

export const actionApi = {
  unfollowUsers: async (
    usernames: string[],
    sessionId: string
  ): Promise<UnfollowResponse> => {
    const response = await api.post('/actions/unfollow', {
      usernames,
      session_id: sessionId,
    });
    return response.data;
  },
};

export const logsApi = {
  getLogs: async (limit = 100, actionType?: string): Promise<ActionLog[]> => {
    const response = await api.get('/logs', {
      params: { limit, action_type: actionType },
    });
    return response.data;
  },
};

export const statsApi = {
  getStats: async (): Promise<Stats> => {
    const response = await api.get('/stats');
    return response.data;
  },
};

export default api;
