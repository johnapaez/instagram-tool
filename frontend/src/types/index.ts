export interface UserInfo {
  username: string;
  full_name?: string;
  profile_pic_url?: string;
  is_verified: boolean;
  follower_count: number;
  is_following_me: boolean;
  i_am_following: boolean;
}

export interface LoginResponse {
  success: boolean;
  session_id?: string;
  username?: string;
  error?: string;
}

export interface AnalysisResponse {
  total_followers: number;
  total_following: number;
  non_followers: UserInfo[];
  non_followers_count: number;
}

export interface UnfollowResponse {
  success: boolean;
  results: Array<{
    success: boolean;
    username: string;
    error?: string;
    timestamp: string;
  }>;
  errors: string[];
}

export interface ActionLog {
  id: number;
  action_type: string;
  username: string;
  status: string;
  created_at: string;
  details?: any;
}

export interface Stats {
  total_users: number;
  total_followers: number;
  total_following: number;
  non_followers: number;
  today_unfollows: number;
  remaining_today: number;
  daily_limit: number;
}

export interface WhitelistResponse {
  success: boolean;
  added: string[];
  already_whitelisted: string[];
  not_found: string[];
}
