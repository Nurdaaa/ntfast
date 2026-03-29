export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'admin' | 'analyst' | 'viewer' | 'superadmin';
  is_active: boolean;
  created_at: string;
  last_login: string | null;
  previous_login?: string | null;
  session_start?: string | null;
}

export interface Subject {
  id: number;
  name: string;
  iin_bin: string | null;
  type: 'individual' | 'legal_entity' | 'account_owner';
  risk_level: number;
  status: 'active' | 'suspended' | 'blocked';
  phone_number: string | null;
  email: string | null;
  address: string | null;
  created_at: string;
  updated_at: string;
}

export interface Analysis {
  id: number;
  subject_id: number | null;
  analyst_id: number;
  status: 'pending' | 'parsing' | 'analyzing' | 'in_progress' | 'completed' | 'failed';
  risk_score: number;
  analyst_notes: string | null;
  conclusion: string | null;

  // File info
  file_name?: string | null;
  file_type?: string | null;
  file_size?: number | null;

  // Bank info
  bank_type?: string | null;
  bank_name?: string | null;
  account_owner?: string | null;
  account_number?: string | null;

  // Stats
  total_transactions?: number;
  total_amount?: number;
  suspicious_count?: number;
  anomaly_count?: number;
  high_risk_count?: number;

  // Fraud
  fraud_composite_score?: number | null;
  fraud_risk_level?: string | null;
  fraud_report?: any;

  // Timestamps
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
}

export interface Transaction {
  id: number;
  subject_id: number;
  amount: string;
  currency: string;
  transaction_type: 'incoming' | 'outgoing';
  counterparty: string | null;
  description: string | null;
  is_suspicious: boolean;
  transaction_date: string;
  created_at: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  role?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  session_start?: string | null;
}
