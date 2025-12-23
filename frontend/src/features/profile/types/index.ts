/**
 * Profile Types
 */

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  role: string;
  avatar?: string;
  phone?: string;
  department?: string;
  created_at: string;
  last_login?: string;
}

export interface ProfileUpdateData {
  name?: string;
  phone?: string;
  avatar?: string;
}

export interface ActivityLog {
  id: number;
  action: string;
  resource: string;
  created_at: string;
  ip_address: string;
}
