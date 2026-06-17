import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { Bank, CreditRequest, DashboardSummary, Stage } from './api.models';

const API_URL = '/api';

@Injectable({ providedIn: 'root' })
export class CreditsApiService {
  constructor(private readonly http: HttpClient) {}

  stages(): Observable<Stage[]> {
    return this.http.get<Stage[]>(`${API_URL}/catalogs/stages`);
  }

  banks(): Observable<Bank[]> {
    return this.http.get<Bank[]>(`${API_URL}/catalogs/banks`);
  }

  summary(): Observable<DashboardSummary> {
    return this.http.get<DashboardSummary>(`${API_URL}/credits/reports/summary`);
  }

  credits(search = ''): Observable<CreditRequest[]> {
    let params = new HttpParams();
    if (search.trim()) {
      params = params.set('search', search.trim());
    }
    return this.http.get<CreditRequest[]>(`${API_URL}/credits`, { params });
  }

  creditReport(filters: {
    search?: string;
    stage_id?: number | null;
    bank_id?: number | null;
    date_from?: string;
    date_to?: string;
  }): Observable<CreditRequest[]> {
    let params = new HttpParams();
    if (filters.search?.trim()) {
      params = params.set('search', filters.search.trim());
    }
    if (filters.stage_id) {
      params = params.set('stage_id', String(filters.stage_id));
    }
    if (filters.bank_id) {
      params = params.set('bank_id', String(filters.bank_id));
    }
    if (filters.date_from) {
      params = params.set('date_from', filters.date_from);
    }
    if (filters.date_to) {
      params = params.set('date_to', filters.date_to);
    }
    return this.http.get<CreditRequest[]>(`${API_URL}/credits/reports/detail`, { params });
  }

  downloadCreditReport(filters: {
    search?: string;
    stage_id?: number | null;
    bank_id?: number | null;
    date_from?: string;
    date_to?: string;
  }): Observable<Blob> {
    let params = new HttpParams();
    if (filters.search?.trim()) {
      params = params.set('search', filters.search.trim());
    }
    if (filters.stage_id) {
      params = params.set('stage_id', String(filters.stage_id));
    }
    if (filters.bank_id) {
      params = params.set('bank_id', String(filters.bank_id));
    }
    if (filters.date_from) {
      params = params.set('date_from', filters.date_from);
    }
    if (filters.date_to) {
      params = params.set('date_to', filters.date_to);
    }
    return this.http.get(`${API_URL}/credits/reports/excel`, { params, responseType: 'blob' });
  }

  createCredit(payload: Partial<CreditRequest>): Observable<CreditRequest> {
    return this.http.post<CreditRequest>(`${API_URL}/credits`, payload);
  }

  updateCredit(id: number, payload: Partial<CreditRequest>): Observable<CreditRequest> {
    return this.http.patch<CreditRequest>(`${API_URL}/credits/${id}`, payload);
  }

  deleteCredit(id: number): Observable<void> {
    return this.http.delete<void>(`${API_URL}/credits/${id}`);
  }

  addBankLine(creditId: number, payload: Record<string, unknown>): Observable<unknown> {
    return this.http.post(`${API_URL}/credits/${creditId}/bank-lines`, payload);
  }

  deleteBankLine(creditId: number, lineId: number): Observable<void> {
    return this.http.delete<void>(`${API_URL}/credits/${creditId}/bank-lines/${lineId}`);
  }

  addDocument(creditId: number, payload: Record<string, unknown>): Observable<unknown> {
    return this.http.post(`${API_URL}/credits/${creditId}/documents`, payload);
  }

  uploadDocument(creditId: number, payload: FormData): Observable<unknown> {
    return this.http.post(`${API_URL}/credits/${creditId}/documents/upload`, payload);
  }

  downloadDocument(creditId: number, documentId: number): Observable<Blob> {
    return this.http.get(`${API_URL}/credits/${creditId}/documents/${documentId}/download`, { responseType: 'blob' });
  }

  deleteDocument(creditId: number, documentId: number): Observable<void> {
    return this.http.delete<void>(`${API_URL}/credits/${creditId}/documents/${documentId}`);
  }

  addAlert(creditId: number, payload: FormData): Observable<unknown> {
    return this.http.post(`${API_URL}/credits/${creditId}/alerts`, payload);
  }
}
