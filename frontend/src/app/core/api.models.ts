export interface Stage {
  id: number;
  name: string;
  code: string;
  sequence: number;
  max_hours: number | null;
  folded: boolean;
}

export interface Bank {
  id: number;
  name: string;
  sequence: number;
  active: boolean;
  is_movilize: boolean;
  requires_ctl: boolean;
  requires_vehicle_history: boolean;
  requires_owner_history: boolean;
}

export interface BankLine {
  id: number;
  bank_id: number;
  bank: Bank;
  type: string;
  status: string;
  filed_at: string | null;
  answered_at: string | null;
  approved_amount: number;
  disbursed_value: number;
  term: string | null;
  rate: string | null;
  conditions: string | null;
  rejection_reason: string | null;
}

export interface CreditDocument {
  id: number;
  name: string;
  type: string;
  file_name: string | null;
  file_url: string | null;
  mime_type: string | null;
  file_size: number | null;
  observation: string | null;
  created_at: string;
}

export interface CreditAlert {
  id: number;
  type: string;
  message: string;
  recipients: string;
  email_to: string | null;
  status: string;
  scheduled_at: string | null;
  email_sent: boolean;
  email_sent_at: string | null;
  email_error: string | null;
}

export interface CreditHistory {
  id: number;
  actor: string;
  action: string;
  detail: string | null;
  created_at: string;
}

export interface CreditRequest {
  id: number;
  reference: string;
  odoo_order_ref: string | null;
  stage_id: number;
  stage_started_at: string;
  advisor_name: string | null;
  showroom: string | null;
  business_type: string | null;
  document_type: string | null;
  document_number: string | null;
  customer_name: string;
  phone: string | null;
  plate: string | null;
  vin: string | null;
  brand: string | null;
  line: string | null;
  model: string | null;
  sale_price: number;
  down_payment: number;
  financed_value: number;
  proforma_invoice_ref: string | null;
  final_invoice_ref: string | null;
  viability_bank_id: number | null;
  selected_bank_id: number | null;
  disbursement_bank_id: number | null;
  viability_bank: Bank | null;
  selected_bank: Bank | null;
  disbursement_bank: Bank | null;
  approval_conditions: string | null;
  observations: string | null;
  rejection_reason: string | null;
  ok_runt: boolean;
  ok_runt_at: string | null;
  runt_observation: string | null;
  insured_ok: boolean;
  policy_issued: boolean;
  insurance_company: string | null;
  policy_observation: string | null;
  disbursed_value: number;
  ownership_card_issued: boolean;
  ownership_card_delivery_date: string | null;
  created_at: string;
  updated_at: string;
  stage: Stage;
  bank_lines: BankLine[];
  documents: CreditDocument[];
  alerts: CreditAlert[];
  history: CreditHistory[];
}

export interface DashboardSummary {
  total_requests: number;
  active_requests: number;
  approved_requests: number;
  disbursed_value: number;
  by_stage: Record<string, number>;
  by_selected_bank: Record<string, number>;
}
