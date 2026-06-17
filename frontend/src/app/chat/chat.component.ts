import { Component, signal, computed, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { ChatService, Message, ChatUser } from './chat.service';
import { AuthService } from '../core/auth.service';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent implements OnInit {
  chatService = inject(ChatService);
  authService = inject(AuthService);

  isOpen = signal(false);
  activeUser = signal<ChatUser | null>(null);
  currentMessages = signal<Message[]>([]);
  newMessage = signal('');
  availableUsers = signal<ChatUser[]>([]);
  isLoading = signal(false);
  unreadByUser = signal<Map<number, number>>(new Map());

  ngOnInit(): void {
    this.loadAvailableUsers();
    this.loadUnreadCounts();
    // Recargar usuarios cada 5 segundos
    setInterval(() => this.loadAvailableUsers(), 5000);
    // Recargar unread counts cada 3 segundos
    setInterval(() => this.loadUnreadCounts(), 3000);
  }

  loadUnreadCounts(): void {
    this.chatService.getConversations().subscribe({
      next: (conversations: ChatUser[]) => {
        const unreadMap = new Map<number, number>();
        conversations.forEach((user: ChatUser) => {
          unreadMap.set(user.id, user.unread_count || 0);
        });
        this.unreadByUser.set(unreadMap);
      },
      error: (err: unknown) => console.error('Error loading unread counts:', err)
    });
  }

  getUnreadCount(userId: number): number {
    return this.unreadByUser().get(userId) || 0;
  }

  loadAvailableUsers(): void {
    this.isLoading.set(true);
    this.chatService.getAvailableUsers().subscribe({
      next: (users: ChatUser[]) => {
        this.availableUsers.set(users);
        this.isLoading.set(false);
      },
      error: (err: unknown) => {
        console.error('Error loading users:', err);
        this.isLoading.set(false);
      }
    });
  }

  selectUser(user: ChatUser): void {
    this.activeUser.set(user);
    this.isLoading.set(true);
    
    this.chatService.getMessages(user.id).subscribe({
      next: (messages: Message[]) => {
        this.currentMessages.set(messages);
        this.isLoading.set(false);
        // Limpiar unread count para este usuario después de cargar
        const unreadMap = new Map(this.unreadByUser());
        unreadMap.set(user.id, 0);
        this.unreadByUser.set(unreadMap);
        // Auto-scroll al final
        setTimeout(() => this.scrollToBottom(), 100);
      },
      error: (err: unknown) => {
        console.error('Error loading messages:', err);
        this.isLoading.set(false);
      }
    });
  }

  sendMessage(): void {
    const content = this.newMessage().trim();
    if (!content || !this.activeUser()) return;

    this.chatService.sendMessage(this.activeUser()!.id, content).subscribe({
      next: (message: Message) => {
        this.currentMessages.set([...this.currentMessages(), message]);
        this.newMessage.set('');
        setTimeout(() => this.scrollToBottom(), 100);
      },
      error: (err: unknown) => console.error('Error sending message:', err)
    });
  }

  deleteMessage(messageId: number): void {
    if (!confirm('¿Eliminar este mensaje?')) return;

    this.chatService.deleteMessage(messageId).subscribe({
      next: () => {
        const updatedMessages = this.currentMessages().filter(msg => msg.id !== messageId);
        this.currentMessages.set(updatedMessages);
      },
      error: (err: unknown) => console.error('Error deleting message:', err)
    });
  }

  private scrollToBottom(): void {
    const container = document.querySelector('.chat-messages');
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }

  isCurrentUserSender(message: Message): boolean {
    return message.sender_id === this.authService.user()?.id;
  }

  toggleChat(): void {
    this.isOpen.set(!this.isOpen());
  }

  closeChat(): void {
    this.isOpen.set(false);
  }
}
