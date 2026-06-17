export interface AuthUser {
  id: number;
  username: string;
  full_name: string;
  role: 'admin' | 'user' | 'advisor';
  active: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}
