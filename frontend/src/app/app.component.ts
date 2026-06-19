import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Bank, BankLine, CreditDocument, CreditHistory, CreditRequest, DashboardSummary, Stage } from './core/api.models';
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
  userAdminMessage = signal('');
  activeModule = signal<'dashboard' | 'new-credit' | 'reports' | 'notifications' | 'users'>('dashboard');
  activeDetailTab = signal<'summary' | 'banks' | 'documents' | 'alerts' | 'legalization'>('summary');
  notificationBox = signal<'inbox' | 'sent'>('inbox');
  notifications = signal<NotificationItem[]>([]);
  recipients = signal<AuthUser[]>([]);
  notificationError = signal('');
  search = '';
  loginForm = {
    username: '',
    password: ''
  };
  newUser = {
    username: '',
    full_name: '',
    password: '',
    role: 'user' as 'admin' | 'user' | 'advisor'
  };
  userRoleLabels: Record<string, string> = {
    admin: 'Administrador',
    user: 'Usuario',
    advisor: 'Asesor consulta'
  };
  passwordResetValues: Record<number, string> = {};
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
    document_number: '',
    plate: '',
    advisor_name: '',
    showroom: '',
    business_type: 'Crédito',
    sale_price: 0,
    down_payment: 0
  };

  bankLine = {
    bank_id: 0,
    type: 'estudio',
    status: 'radicado',
    conditions: ''
  };

  bankBatch = {
    bank_ids: [] as number[],
    type: 'viabilidad',
    status: 'pendiente',
    conditions: ''
  };

  bankTypeOrder = ['viabilidad', 'estudio', 'aprobacion', 'rechazo', 'desembolso'];
  bankTypeLabels: Record<string, string> = {
    viabilidad: 'Bancos viables',
    estudio: 'Bancos en estudio',
    aprobacion: 'Bancos aprobados',
    rechazo: 'Bancos negados',
    desembolso: 'Banco de desembolso'
  };
  bankStatusLabels: Record<string, string> = {
    pendiente: 'Pendiente',
    radicado: 'Radicado',
    aprobado: 'Aprobado',
    negado: 'Negado',
    desembolsado: 'Desembolsado'
  };
  bankDefaultStatus: Record<string, string> = {
    viabilidad: 'pendiente',
    estudio: 'radicado',
    aprobacion: 'aprobado',
    rechazo: 'negado',
    desembolso: 'desembolsado'
  };
  stagesWithLegalization = ['firmado', 'desembolsado', 'legalizacion'];
  stagesWithDisbursement = ['desembolsado', 'legalizacion'];

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
    message: '',
    classification: 'bancos' as 'bancos' | 'clientes' | 'vendedores'
  };
  selectedAlertDocumentIds = new Set<number>();
  selectedAlertFile: File | null = null;

  alertClassifications: { value: string; label: string }[] = [
    { value: 'bancos', label: 'Alertas Bancos' },
    { value: 'clientes', label: 'Alertas Clientes' },
    { value: 'vendedores', label: 'Alertas Vendedores' }
  ];

  alertTypesByClassification: Record<string, { value: string; label: string }[]> = {
    bancos: [
      { value: 'envio_documentos', label: 'Envío documentos (Estudios)' },
      { value: 'factura_proforma', label: 'Factura proforma' },
      { value: 'aval', label: 'Aval' },
      { value: 'poliza', label: 'Póliza' },
      { value: 'otro', label: 'Otro' }
    ],
    clientes: [
      { value: 'envio_estudio', label: 'Envío estudio' },
      { value: 'aprobado', label: 'Aprobado' },
      { value: 'otro', label: 'Otro' }
    ],
    vendedores: [
      { value: 'viabilidad', label: 'Viabilidad' },
      { value: 'estudio', label: 'Estudio' },
      { value: 'aprobado', label: 'Aprobado' },
      { value: 'negado', label: 'Negado' },
      { value: 'firmado', label: 'Firmado' },
      { value: 'ok_poliza', label: 'OK póliza' },
      { value: 'desembolsado', label: 'Desembolsado' },
      { value: 'legalizacion_tp', label: 'Legalización de la TP' },
      { value: 'otro', label: 'Otro' }
    ]
  };

  getAlertTypesByClassification(): { value: string; label: string }[] {
    return this.alertTypesByClassification[this.alert.classification] || this.alertTypesByClassification['bancos'];
  }

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

  isAdvisor(): boolean {
    return this.auth.user()?.role === 'advisor';
  }

  canManageCredits(): boolean {
    return !this.isAdvisor();
  }

  userRoleLabel(role: string | null | undefined): string {
    if (!role) {
      return '';
    }
    return this.userRoleLabels[role] ?? role;
  }

  ngOnInit(): void {
    if (this.auth.user()) {
      this.activeModule.set('dashboard');
      this.loadCatalogs();
      this.loadCredits();
      if (this.canManageCredits()) {
        this.loadUsers();
        this.loadNotifications();
        this.loadRecipients();
      }
    }
  }

  login(): void {
    this.loginError.set('');
    this.auth.login(this.loginForm.username, this.loginForm.password).subscribe({
      next: () => {
        this.activeModule.set('dashboard');
        this.loadCatalogs();
        this.loadCredits();
        if (this.canManageCredits()) {
          this.loadUsers();
        }
      },
    error: () => this.loginError.set('Usuario o contraseña inválida')
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
    if (this.isAdvisor() && module !== 'dashboard') {
      this.activeModule.set('dashboard');
      return;
    }
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
    if (!this.canManageCredits()) {
      return;
    }
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
    if (!this.canManageCredits()) {
      return;
    }
    this.auth.notificationRecipients().subscribe((recipients) => this.recipients.set(recipients));
  }

  loadNotifications(): void {
    if (!this.canManageCredits()) {
      return;
    }
    this.auth.notifications(this.notificationBox()).subscribe((items) => this.notifications.set(items));
  }

  sendNotification(): void {
    if (!this.canManageCredits()) {
      return;
    }
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
      error: () => this.notificationError.set('No se pudo enviar la notificación')
    });
  }

  markRead(item: NotificationItem): void {
    if (item.read_at) {
      return;
    }
    this.auth.markNotificationRead(item.id).subscribe(() => this.loadNotifications());
  }

  notifyAboutSelectedCredit(): void {
    if (!this.canManageCredits()) {
      return;
    }
    const credit = this.selected();
    if (!credit) {
      return;
    }
    this.notificationForm.credit_id = credit.id;
    this.notificationForm.subject = `Crédito ${credit.reference}`;
    this.notificationForm.message = `Revisar crédito ${credit.reference} del cliente ${credit.customer_name}. Etapa actual: ${credit.stage.name}.`;
    this.setModule('notifications');
  }

  createUser(): void {
    this.userCreateError.set('');
    if (!this.newUser.username.trim() || !this.newUser.full_name.trim() || this.newUser.password.length < 6) {
      this.userCreateError.set('Completa nombre, usuario y clave de mínimo 6 caracteres');
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

  updateUserPassword(user: AuthUser): void {
    this.userCreateError.set('');
    this.userAdminMessage.set('');
    const password = (this.passwordResetValues[user.id] ?? '').trim();
    if (password.length < 6) {
      this.userCreateError.set('La nueva clave debe tener mínimo 6 caracteres');
      return;
    }
    this.auth.updateUserPassword(user.id, password).subscribe({
      next: () => {
        this.passwordResetValues[user.id] = '';
        this.userAdminMessage.set(`Clave actualizada para ${user.full_name}`);
      },
      error: () => this.userCreateError.set('No se pudo cambiar la clave')
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
      error: () => this.loading.set(false),
      complete: () => this.loading.set(false)
    });
  }


  normalizePlateVin(value: string | null | undefined): string {
    return (value ?? '').toUpperCase().trim();
  }

  onlyDigits(value: string | null | undefined): string {
    return (value ?? '').replace(/\D/g, '');
  }

  onDocumentNumberInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    const value = this.onlyDigits(input.value);
    input.value = value;
    this.quickCredit.document_number = value;
  }

  selectCredit(credit: CreditRequest): void {
    this.selected.set(credit);
    this.activeDetailTab.set('summary');
    this.selectedAlertDocumentIds.clear();
    this.selectedAlertFile = null;
  }

  createCredit(): void {
    if (!this.canManageCredits()) {
      return;
    }
    if (!this.quickCredit.customer_name?.trim()) {
      return;
    }
    const payload = {
      ...this.quickCredit,
      document_number: this.onlyDigits(this.quickCredit.document_number),
      plate: this.normalizePlateVin(this.quickCredit.plate),
    };
    this.api.createCredit(payload).subscribe((credit) => {
      this.quickCredit = {
        customer_name: '',
        document_number: '',
        plate: '',
        advisor_name: '',
        showroom: '',
        business_type: 'Crédito',
        sale_price: 0,
        down_payment: 0
      };
      this.selected.set(credit);
      this.loadCredits();
      this.activeModule.set('dashboard');
    });
  }

  moveSelected(stage: Stage): void {
    if (!this.canManageCredits()) {
      return;
    }
    const credit = this.selected();
    if (!credit || credit.stage_id === stage.id) {
      return;
    }
    this.api.updateCredit(credit.id, { stage_id: stage.id }).subscribe((updated) => {
      this.selected.set(updated);
      if (this.activeDetailTab() === 'legalization' && !this.showLegalizationTab(updated)) {
        this.activeDetailTab.set('summary');
      }
      if (!this.showDisbursementFields(updated) && this.bankBatch.type === 'desembolso') {
        this.setBankBatchType('viabilidad');
      }
      this.loadCredits();
    });
  }

  saveSelectedCredit(credit: CreditRequest): void {
    if (!this.canManageCredits()) {
      return;
    }
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
    if (!this.canManageCredits()) {
      return;
    }
    if (!confirm(`¿Deseas eliminar la solicitud ${credit.reference} de ${credit.customer_name}?`)) {
      return;
    }
    this.api.deleteCredit(credit.id).subscribe(() => {
      this.selected.set(null);
      this.loadCredits();
    });
  }

  setBankBatchType(type: string): void {
    this.bankBatch.type = type;
    this.bankBatch.status = this.bankDefaultStatus[type] ?? 'pendiente';
  }

  showLegalizationTab(credit: CreditRequest): boolean {
    return this.stagesWithLegalization.includes(credit.stage.code);
  }

  showDisbursementFields(credit: CreditRequest): boolean {
    return this.stagesWithDisbursement.includes(credit.stage.code);
  }

  visibleBankTypes(credit: CreditRequest): string[] {
    return this.showDisbursementFields(credit)
      ? this.bankTypeOrder
      : this.bankTypeOrder.filter((type) => type !== 'desembolso');
  }

  addBankLine(): void {
    if (!this.canManageCredits()) {
      return;
    }
    const credit = this.selected();
    if (!credit || !this.bankBatch.bank_ids.length) {
      return;
    }

    const bankIds = this.bankBatch.bank_ids.map((id) => Number(id));
    const uniqueBankIds = bankIds.filter((id, index) => bankIds.indexOf(id) === index);
    let pending = uniqueBankIds.length;

    for (const bankId of uniqueBankIds) {
      const exists = credit.bank_lines.some((line) => line.bank_id === bankId && line.type === this.bankBatch.type);
      if (exists) {
        pending -= 1;
        if (!pending) {
          this.afterBankBatch(credit.id);
        }
        continue;
      }

      this.api.addBankLine(credit.id, {
        bank_id: bankId,
        type: this.bankBatch.type,
        status: this.bankBatch.status,
        conditions: this.bankBatch.conditions
      }).subscribe({
        complete: () => {
          pending -= 1;
          if (!pending) {
            this.afterBankBatch(credit.id);
          }
        }
      });
    }
  }

  deleteBankLine(line: BankLine): void {
    if (!this.canManageCredits()) {
      return;
    }
    const credit = this.selected();
    if (!credit || !confirm(`¿Deseas eliminar ${line.bank.name} de ${this.bankTypeLabels[line.type] ?? line.type}?`)) {
      return;
    }
    this.api.deleteBankLine(credit.id, line.id).subscribe(() => this.refreshSelected(credit.id));
  }

  bankLinesByType(credit: CreditRequest, type: string): BankLine[] {
    return credit.bank_lines.filter((line) => line.type === type);
  }

  visibleBankTypesWithLines(credit: CreditRequest): string[] {
    return this.visibleBankTypes(credit).filter((type) => this.bankLinesByType(credit, type).length);
  }

  creditStageBanks(credit: CreditRequest): string {
    const stageType: Record<string, string[]> = {
      viabilidad: ['viabilidad'],
      gestion_documental: ['viabilidad'],
      estudio: ['estudio'],
      respuesta_estudio: ['estudio', 'aprobacion', 'rechazo'],
      aprobado: ['aprobacion'],
      firmado: ['aprobacion'],
      desembolsado: ['desembolso', 'aprobacion'],
      legalizacion: ['desembolso', 'aprobacion'],
      desasignado: ['rechazo']
    };
    const types = stageType[credit.stage.code] ?? [];
    const names = credit.bank_lines
      .filter((line) => types.includes(line.type))
      .map((line) => line.bank.name)
      .filter((name, index, values) => values.indexOf(name) === index);
    if (names.length) {
      return names.join(', ');
    }
    return credit.selected_bank?.name ?? credit.viability_bank?.name ?? '';
  }

  private afterBankBatch(creditId: number): void {
    this.bankBatch = { bank_ids: [], type: 'viabilidad', status: 'pendiente', conditions: '' };
    this.refreshSelected(creditId);
  }

  onDocumentFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedDocumentFile = input.files?.item(0) ?? null;
    if (this.selectedDocumentFile && !this.document.name.trim()) {
      this.document.name = this.selectedDocumentFile.name;
    }
  }

  addDocument(): void {
    if (!this.canManageCredits()) {
      return;
    }
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
    if (!this.canManageCredits()) {
      return;
    }
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
    if (!this.canManageCredits()) {
      return;
    }
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
      this.alert = { type: 'otro', recipients: 'equipo_creditos', email_to: '', message: '', classification: 'bancos' };
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

  downloadDocument(credit: CreditRequest, item: CreditHistory): void {
    const documentId = this.documentIdFromHistory(credit, item);
    if (!documentId) {
      return;
    }
    
    this.api.downloadDocument(credit.id, documentId).subscribe((blob) => {
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = item.detail || `documento_${documentId}`;
      link.click();
      window.URL.revokeObjectURL(url);
    });
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





