import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Bank, CreditDocument, CreditHistory, CreditRequest, DashboardSummary, Stage } from './core/api.models';
import { AuthUser } from './core/auth.models';
import { AuthService } from './core/auth.service';
import { CreditsApiService } from './core/credits-api.service';
import { NotificationItem } from './core/notification.models';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html'
})
export class AppComponent implements OnInit {
  stages = signal<Stage[]>([]);
  banks = signal<Bank[]>([]);
  credits = signal<CreditRequest[]>([]);
  summary = signal<DashboardSummary | null>(null);
  selected = signal<CreditRequest | null>(null);
  loading = signal(false);
  loginError = signal('');
  users = signal<AuthUser[]>([]);
  userCreateError = signal('');
  activeModule = signal<'dashboard' | 'new-credit' | 'reports' | 'notifications' | 'users'>('dashboard');
  activeDetailTab = signal<'summary' | 'banks' | 'documents' | 'alerts' | 'legalization'>('summary');
  notificationBox = signal<'inbox' | 'sent'>('inbox');
  notifications = signal<NotificationItem[]>([]);
  recipients = signal<AuthUser[]>([]);
  notificationError = signal('');
  search = '';
  loginForm = {
    username: 'admin',
    password: 'admin123'
  };
  newUser = {
    username: '',
    full_name: '',
    password: '',
    role: 'user' as 'admin' | 'user'
  };
  notificationForm = {
    recipient_id: 0,
    subject: '',
    message: '',
    credit_id: null as number | null
  };
  reportFilters = {
    search: '',
    stage_id: null as number | null,
    bank_id: null as number | null,
    date_from: '',
    date_to: ''
  };

  quickCredit: Partial<CreditRequest> = {
    customer_name: '',
    plate: '',
    advisor_name: '',
    showroom: '',
    business_type: 'Credito',
    sale_price: 0,
    down_payment: 0
  };

  bankLine = {
    bank_id: 0,
    type: 'estudio',
    status: 'radicado',
    conditions: ''
  };

  document = {
    name: '',
    type: 'otro',
    observation: ''
  };
  selectedDocumentFile: File | null = null;

  alert = {
    type: 'otro',
    recipients: 'equipo_creditos',
    email_to: '',
    message: ''
  };
  selectedAlertDocumentIds = new Set<number>();
  selectedAlertFile: File | null = null;

  groupedCredits = computed(() => {
    const grouped = new Map<string, CreditRequest[]>();
    for (const stage of this.stages()) {
      grouped.set(stage.code, []);
    }
    for (const credit of this.credits()) {
      grouped.get(credit.stage.code)?.push(credit);
    }
    return grouped;
  });

  constructor(
    private readonly api: CreditsApiService,
    readonly auth: AuthService
  ) {}

  ngOnInit(): void {
    if (this.auth.user()) {
      this.loadCatalogs();
      this.loadCredits();
      this.loadUsers();
      this.loadNotifications();
      this.loadRecipients();
    }
  }

  login(): void {
    this.loginError.set('');
    this.auth.login(this.loginForm.username, this.loginForm.password).subscribe({
      next: () => {
        this.loadCatalogs();
        this.loadCredits();
        this.loadUsers();
      },
      error: () => this.loginError.set('Usuario o contraseña invalida')
    });
  }

  logout(): void {
    this.auth.logout();
    this.stages.set([]);
    this.banks.set([]);
    this.credits.set([]);
    this.summary.set(null);
    this.selected.set(null);
      this.activeModule.set('dashboard');
  }

  setModule(module: 'dashboard' | 'new-credit' | 'reports' | 'notifications' | 'users'): void {
    this.activeModule.set(module);
    if (module === 'users') {
      this.loadUsers();
    }
    if (module === 'notifications') {
      this.loadNotifications();
      this.loadRecipients();
    }
    if (module === 'reports') {
      return;
    }
  }

  clearReportFilters(): void {
    this.reportFilters = { search: '', stage_id: null, bank_id: null, date_from: '', date_to: '' };
  }

  downloadReportExcel(): void {
    this.api.downloadCreditReport(this.reportFilters).subscribe((blob) => {
      const url = URL.createObjectURL(blob);
      const link = globalThis.document.createElement('a');
      link.href = url;
      link.download = `reporte_creditos_${new Date().toISOString().slice(0, 10)}.xlsx`;
      link.click();
      URL.revokeObjectURL(url);
    });
  }

  loadUsers(): void {
    if (this.auth.user()?.role !== 'admin') {
      return;
    }
    this.auth.users().subscribe((users) => this.users.set(users));
  }

  loadRecipients(): void {
    this.auth.notificationRecipients().subscribe((recipients) => this.recipients.set(recipients));
  }

  loadNotifications(): void {
    this.auth.notifications(this.notificationBox()).subscribe((items) => this.notifications.set(items));
  }

  sendNotification(): void {
    this.notificationError.set('');
    if (!this.notificationForm.recipient_id || !this.notificationForm.subject.trim() || !this.notificationForm.message.trim()) {
      this.notificationError.set('Selecciona destinatario, asunto y mensaje');
      return;
    }
    this.auth.createNotification(this.notificationForm).subscribe({
      next: () => {
        this.notificationForm = { recipient_id: 0, subject: '', message: '', credit_id: null };
        this.notificationBox.set('sent');
        this.loadNotifications();
      },
      error: () => this.notificationError.set('No se pudo enviar la notificacion')
    });
  }

  markRead(item: NotificationItem): void {
    if (item.read_at) {
      return;
    }
    this.auth.markNotificationRead(item.id).subscribe(() => this.loadNotifications());
  }

  notifyAboutSelectedCredit(): void {
    const credit = this.selected();
    if (!credit) {
      return;
    }
    this.notificationForm.credit_id = credit.id;
    this.notificationForm.subject = `Credito ${credit.reference}`;
    this.notificationForm.message = `Revisar credito ${credit.reference} del cliente ${credit.customer_name}. Etapa actual: ${credit.stage.name}.`;
    this.setModule('notifications');
  }

  createUser(): void {
    this.userCreateError.set('');
    if (!this.newUser.username.trim() || !this.newUser.full_name.trim() || this.newUser.password.length < 6) {
      this.userCreateError.set('Completa nombre, usuario y clave de minimo 6 caracteres');
      return;
    }
    this.auth.createUser(this.newUser).subscribe({
      next: () => {
        this.newUser = { username: '', full_name: '', password: '', role: 'user' };
        this.loadUsers();
      },
      error: () => this.userCreateError.set('No se pudo crear el usuario')
    });
  }

  deleteUser(user: AuthUser): void {
    if (!confirm(`¿Deseas eliminar el usuario ${user.full_name}?`)) {
      return;
    }
    this.auth.deleteUser(user.id).subscribe({
      next: () => this.loadUsers(),
      error: () => this.userCreateError.set('No se pudo eliminar el usuario')
    });
  }

  loadCatalogs(): void {
    this.api.stages().subscribe((stages) => this.stages.set(stages));
    this.api.banks().subscribe((banks) => this.banks.set(banks));
  }

  loadCredits(): void {
    this.loading.set(true);
    this.api.credits(this.search).subscribe({
      next: (credits) => {
        this.credits.set(credits);
        if (!this.selected() && credits.length) {
          this.selected.set(credits[0]);
        }
        this.api.summary().subscribe((summary) => this.summary.set(summary));
      },
      complete: () => this.loading.set(false)
    });
  }

  selectCredit(credit: CreditRequest): void {
    this.selected.set(credit);
    this.activeDetailTab.set('summary');
    this.selectedAlertDocumentIds.clear();
    this.selectedAlertFile = null;
  }

  createCredit(): void {
    if (!this.quickCredit.customer_name?.trim()) {
      return;
    }
    this.api.createCredit(this.quickCredit).subscribe((credit) => {
      this.quickCredit = {
        customer_name: '',
        plate: '',
        advisor_name: '',
        showroom: '',
        business_type: 'Credito',
        sale_price: 0,
        down_payment: 0
      };
      this.selected.set(credit);
      this.loadCredits();
      this.activeModule.set('dashboard');
    });
  }

  moveSelected(stage: Stage): void {
    const credit = this.selected();
    if (!credit || credit.stage_id === stage.id) {
      return;
    }
    this.api.updateCredit(credit.id, { stage_id: stage.id }).subscribe((updated) => {
      this.selected.set(updated);
      this.loadCredits();
    });
  }

  saveSelectedCredit(credit: CreditRequest): void {
    this.api.updateCredit(credit.id, {
      phone: credit.phone,
      sale_price: credit.sale_price,
      down_payment: credit.down_payment,
      viability_bank_id: credit.viability_bank_id,
      selected_bank_id: credit.selected_bank_id,
      disbursement_bank_id: credit.disbursement_bank_id,
      rejection_reason: credit.rejection_reason,
      ok_runt: credit.ok_runt,
      runt_observation: credit.runt_observation,
      insured_ok: credit.insured_ok,
      policy_issued: credit.policy_issued,
      insurance_company: credit.insurance_company,
      policy_observation: credit.policy_observation,
      ownership_card_issued: credit.ownership_card_issued,
      ownership_card_delivery_date: credit.ownership_card_delivery_date,
      disbursed_value: credit.disbursed_value
    }).subscribe((updated) => {
      this.selected.set(updated);
      this.loadCredits();
    });
  }

  deleteSelectedCredit(credit: CreditRequest): void {
    if (!confirm(`Deseas eliminar la solicitud ${credit.reference} de ${credit.customer_name}?`)) {
      return;
    }
    this.api.deleteCredit(credit.id).subscribe(() => {
      this.selected.set(null);
      this.loadCredits();
    });
  }

  addBankLine(): void {
    const credit = this.selected();
    if (!credit || !this.bankLine.bank_id) {
      return;
    }
    this.api.addBankLine(credit.id, this.bankLine).subscribe(() => {
      this.bankLine = { bank_id: 0, type: 'estudio', status: 'radicado', conditions: '' };
      this.refreshSelected(credit.id);
    });
  }

  onDocumentFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedDocumentFile = input.files?.item(0) ?? null;
    if (this.selectedDocumentFile && !this.document.name.trim()) {
      this.document.name = this.selectedDocumentFile.name;
    }
  }

  addDocument(): void {
    const credit = this.selected();
    if (!credit || !this.document.name.trim() || !this.selectedDocumentFile) {
      return;
    }
    const payload = new FormData();
    payload.append('name', this.document.name);
    payload.append('type', this.document.type);
    payload.append('observation', this.document.observation ?? '');
    payload.append('file', this.selectedDocumentFile);

    this.api.uploadDocument(credit.id, payload).subscribe(() => {
      this.document = { name: '', type: 'otro', observation: '' };
      this.selectedDocumentFile = null;
      this.refreshSelected(credit.id);
    });
  }

  deleteDocument(documentId: number): void {
    const credit = this.selected();
    if (!credit || !confirm('¿Deseas borrar este documento?')) {
      return;
    }
    this.api.deleteDocument(credit.id, documentId).subscribe(() => {
      this.refreshSelected(credit.id);
    });
  }

  openDocument(documentId: number, fileName: string | null): void {
    const credit = this.selected();
    if (!credit) {
      return;
    }
    this.api.downloadDocument(credit.id, documentId).subscribe((blob) => {
      const url = URL.createObjectURL(blob);
      const link = globalThis.document.createElement('a');
      link.href = url;
      link.target = '_blank';
      link.download = fileName || 'documento';
      link.click();
      URL.revokeObjectURL(url);
    });
  }

  addAlert(): void {
    const credit = this.selected();
    if (!credit || !this.alert.message.trim()) {
      return;
    }
    const payload = new FormData();
    payload.append('type', this.alert.type);
    payload.append('recipients', this.alert.recipients);
    payload.append('email_to', this.alert.email_to ?? '');
    payload.append('message', this.alert.message);
    const allowedDocumentIds = new Set(this.alertDocuments(credit).map((doc) => doc.id));
    for (const documentId of this.selectedAlertDocumentIds) {
      if (allowedDocumentIds.has(documentId)) {
        payload.append('selected_document_ids', String(documentId));
      }
    }
    if (this.selectedAlertFile) {
      payload.append('file', this.selectedAlertFile);
    }

    this.api.addAlert(credit.id, payload).subscribe(() => {
      this.alert = { type: 'otro', recipients: 'equipo_creditos', email_to: '', message: '' };
      this.selectedAlertDocumentIds.clear();
      this.selectedAlertFile = null;
      this.refreshSelected(credit.id);
    });
  }

  alertDocuments(credit: CreditRequest): CreditDocument[] {
    const allowedIds = new Set(credit.documents.map((doc) => doc.id));
    for (const documentId of Array.from(this.selectedAlertDocumentIds)) {
      if (!allowedIds.has(documentId)) {
        this.selectedAlertDocumentIds.delete(documentId);
      }
    }
    return credit.documents;
  }

  toggleAlertDocument(documentId: number, event: Event): void {
    const checked = (event.target as HTMLInputElement).checked;
    if (checked) {
      this.selectedAlertDocumentIds.add(documentId);
      return;
    }
    this.selectedAlertDocumentIds.delete(documentId);
  }

  isAlertDocumentSelected(documentId: number): boolean {
    return this.selectedAlertDocumentIds.has(documentId);
  }

  onAlertFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedAlertFile = input.files?.item(0) ?? null;
  }

  bankName(id: number | null | undefined): string {
    return this.banks().find((bank) => bank.id === Number(id))?.name ?? 'Sin banco';
  }

  money(value: number | null | undefined): string {
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(value ?? 0);
  }

  documentHistory(credit: CreditRequest): CreditHistory[] {
    return credit.history.filter((item) => item.action.toLowerCase().includes('documento'));
  }

  documentIdFromHistory(credit: CreditRequest, item: CreditHistory): number | null {
    if (!item.action.toLowerCase().includes('cargado') || !item.detail) {
      return null;
    }
    const detail = this.normalizeDocumentName(item.detail);
    const document = credit.documents.find((doc) => {
      const fileName = this.normalizeDocumentName(doc.file_name);
      const name = this.normalizeDocumentName(doc.name);
      return fileName === detail || name === detail || fileName.includes(detail) || detail.includes(fileName);
    });
    return document?.id ?? null;
  }

  canDeleteDocumentFromHistory(credit: CreditRequest, item: CreditHistory): boolean {
    return this.auth.user()?.role === 'admin' && this.documentIdFromHistory(credit, item) !== null;
  }

  deleteDocumentFromHistory(credit: CreditRequest, item: CreditHistory): void {
    const documentId = this.documentIdFromHistory(credit, item);
    if (!documentId) {
      return;
    }
    this.deleteDocument(documentId);
  }

  private normalizeDocumentName(value: string | null | undefined): string {
    return (value ?? '').trim().toLowerCase().replace(/\s+/g, ' ');
  }

  private refreshSelected(id: number): void {
    this.api.credits(this.search).subscribe((credits) => {
      this.credits.set(credits);
      this.selected.set(credits.find((credit) => credit.id === id) ?? null);
    });
  }
}
