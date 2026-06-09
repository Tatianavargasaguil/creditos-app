import { AuthUser } from './auth.models';

export interface NotificationItem {
  id: number;
  subject: string;
  message: string;
  credit_id: number | null;
  read_at: string | null;
  created_at: string;
  sender: AuthUser;
  recipient: AuthUser;
}
