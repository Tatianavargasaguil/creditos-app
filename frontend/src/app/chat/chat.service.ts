import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';

export interface Message {
  id: number;
  sender_id: number;
  recipient_id: number;
  sender_name?: string;
  content: string;
  read: boolean;
  created_at: string;
}

export interface ChatUser {
  id: number;
  name: string;
  email: string;
  role: string;
  unread_count?: number;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private apiUrl = 'http://localhost:8010/api/chat';
  
  messages = signal<Message[]>([]);
  conversations = signal<ChatUser[]>([]);
  unreadCount = computed(() => 
    this.messages().filter(m => !m.read).length
  );

  constructor(private http: HttpClient) {
    this.loadConversations();
  }

  loadConversations(): void {
    this.http.get<ChatUser[]>(`${this.apiUrl}/conversations`)
      .subscribe({
        next: (data) => this.conversations.set(data),
        error: (err) => console.error('Error loading conversations:', err)
      });
  }

  getConversations(): Observable<ChatUser[]> {
    return this.http.get<ChatUser[]>(`${this.apiUrl}/conversations`);
  }

  getMessages(userId: number): Observable<Message[]> {
    return this.http.get<Message[]>(`${this.apiUrl}/messages?user_id=${userId}`);
  }

  sendMessage(recipientId: number, content: string): Observable<Message> {
    return this.http.post<Message>(`${this.apiUrl}/messages`, {
      recipient_id: recipientId,
      content: content
    });
  }

  deleteMessage(messageId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/messages/${messageId}`);
  }

  getAvailableUsers(): Observable<ChatUser[]> {
    return this.http.get<ChatUser[]>(`${this.apiUrl}/users`);
  }

  markAsRead(userId: number): void {
    this.http.put(`${this.apiUrl}/messages/${userId}/read`, {})
      .subscribe();
  }
}
