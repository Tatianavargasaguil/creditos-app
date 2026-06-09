import { HttpClient } from '@angular/common/http';
import { Injectable, signal } from '@angular/core';
import { tap } from 'rxjs';
import { AuthUser, LoginResponse } from './auth.models';
import { NotificationItem } from './notification.models';

const API_URL = 'http://localhost:8010/api';
const TOKEN_KEY = 'creditos_token';
const USER_KEY = 'creditos_user';

@Injectable({ providedIn: 'root' })
export class AuthService {
  user = signal<AuthUser | null>(this.readUser());

  constructor(private readonly http: HttpClient) {}

  get token(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  login(username: string, password: string) {
    return this.http.post<LoginResponse>(`${API_URL}/auth/login`, { username, password }).pipe(
      tap((response) => {
        localStorage.setItem(TOKEN_KEY, response.access_token);
        localStorage.setItem(USER_KEY, JSON.stringify(response.user));
        this.user.set(response.user);
      })
    );
  }

  users() {
    return this.http.get<AuthUser[]>(`${API_URL}/users`);
  }

  createUser(payload: { username: string; full_name: string; password: string; role: 'admin' | 'user' }) {
    return this.http.post<AuthUser>(`${API_URL}/users`, payload);
  }

  deleteUser(userId: number) {
    return this.http.delete<void>(`${API_URL}/users/${userId}`);
  }

  notificationRecipients() {
    return this.http.get<AuthUser[]>(`${API_URL}/notifications/recipients`);
  }

  notifications(box: 'inbox' | 'sent' | 'all' = 'inbox') {
    return this.http.get<NotificationItem[]>(`${API_URL}/notifications`, { params: { box } });
  }

  createNotification(payload: { recipient_id: number; subject: string; message: string; credit_id?: number | null }) {
    return this.http.post<NotificationItem>(`${API_URL}/notifications`, payload);
  }

  markNotificationRead(notificationId: number) {
    return this.http.post<NotificationItem>(`${API_URL}/notifications/${notificationId}/read`, {});
  }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    this.user.set(null);
  }

  private readUser(): AuthUser | null {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) {
      return null;
    }
    try {
      return JSON.parse(raw) as AuthUser;
    } catch {
      return null;
    }
  }
}
