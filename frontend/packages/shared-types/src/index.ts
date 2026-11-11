// =============================================================================
// NextGen AI POS & ERP - Shared TypeScript Schema Definitions
// =============================================================================

export type BusinessType = "retail" | "supermarket" | "restaurant" | "wholesale";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  business_type: BusinessType;
  country: string;
  currency: string;
  timezone: string;
  tax_number?: string;
  phone?: string;
  email?: string;
  address?: string;
  logo_url?: string;
  is_active: boolean;
  onboarding_completed: boolean;
  settings?: Record<string, any>;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  avatar_url?: string;
  is_platform_admin: boolean;
  organizations?: OrganizationMembershipSummary[];
}

export interface OrganizationMembershipSummary {
  id: string;
  name: string;
  slug: string;
  business_type: BusinessType;
  role?: string;
  is_owner: boolean;
}

export interface Branch {
  id: string;
  name: string;
  code: string;
  address?: string;
  phone?: string;
  email?: string;
  is_active: boolean;
  is_headquarters: boolean;
}

export interface Warehouse {
  id: string;
  branch: string;
  name: string;
  code: string;
  is_primary: boolean;
  is_active: boolean;
}

export interface Category {
  id: string;
  parent?: string | null;
  name: string;
  slug: string;
  description?: string;
}

export interface ProductVariant {
  id: string;
  sku: string;
  barcode: string;
  attributes_json: Record<string, string>;
  cost_price: string;
  selling_price: string;
  reorder_level: string;
  is_active: boolean;
}

export interface Product {
  id: string;
  category?: string;
  category_name?: string;
  brand?: string;
  unit?: string;
  unit_abbreviation?: string;
  sku: string;
  name: string;
  description?: string;
  product_type: "STANDARD" | "VARIANT" | "SERVICE" | "COMBO";
  tax_rate: string;
  is_active: boolean;
  image_url?: string;
  variants: ProductVariant[];
  created_at: string;
}

export interface StockBalance {
  id: string;
  warehouse: string;
  warehouse_name: string;
  variant: string;
  variant_details?: ProductVariant;
  quantity: string;
  reserved_quantity: string;
  available_quantity: string;
  updated_at: string;
}

export type PaymentMethod =
  | "CASH"
  | "ESEWA"
  | "KHALTI"
  | "FONEPAY"
  | "CARD"
  | "BANK_TRANSFER"
  | "CREDIT";

export interface PaymentItem {
  method: PaymentMethod;
  amount: string;
  provider_reference?: string;
}

export interface CartItem {
  variant_id: string;
  sku: string;
  name: string;
  quantity: number;
  unit_price: number;
  discount: number;
  tax_rate: number;
  subtotal: number;
}

export interface CheckoutPayload {
  client_transaction_id: string;
  branch_id: string;
  terminal_id?: string | null;
  customer_id?: string | null;
  items: {
    variant_id: string;
    quantity: string | number;
    unit_price?: string | number;
    discount?: string | number;
  }[];
  payments: {
    method: PaymentMethod;
    amount: string | number;
    provider_reference?: string;
  }[];
  currency?: string;
  notes?: string;
}

export interface Sale {
  id: string;
  invoice_number: string;
  client_transaction_id: string;
  status: "COMPLETED" | "REFUNDED" | "PARTIALLY_REFUNDED" | "VOID";
  branch: string;
  branch_name: string;
  terminal?: string;
  cashier?: string;
  customer?: string;
  customer_name?: string;
  subtotal: string;
  discount_amount: string;
  tax_amount: string;
  total_amount: string;
  paid_amount: string;
  currency: string;
  notes?: string;
  items: {
    id: string;
    variant: string;
    variant_sku: string;
    product_name: string;
    quantity: string;
    unit_price: string;
    discount_amount: string;
    tax_rate: string;
    tax_amount: string;
    subtotal: string;
  }[];
  payments: {
    id: string;
    payment_method: PaymentMethod;
    amount: string;
    currency: string;
    status: string;
    provider_reference?: string;
  }[];
  synced_at: string;
  created_at: string;
}

// Offline Synchronization Event Contract
export interface SyncEvent {
  event_id: string;
  organization_id: string;
  branch_id: string;
  terminal_id?: string;
  event_type: "sale.created" | "customer.created" | "shift.opened" | "shift.closed";
  schema_version: number;
  local_sequence: number;
  created_at: string;
  payload: CheckoutPayload | Record<string, any>;
  status: "PENDING" | "SYNCING" | "SYNCED" | "CONFLICT" | "FAILED";
  retry_count: number;
  error_message?: string;
}

// Financial and Tax Reports
export interface TrialBalanceItem {
  account_code: string;
  account_name: string;
  account_type: string;
  debit: string;
  credit: string;
}

export interface TrialBalanceReport {
  organization: string;
  currency: string;
  total_debit: string;
  total_credit: string;
  is_balanced: boolean;
  accounts: TrialBalanceItem[];
}

export interface ProfitLossReport {
  organization: string;
  currency: string;
  from_date: string;
  to_date: string;
  total_revenue: string;
  total_cogs: string;
  gross_profit: string;
  total_expenses: string;
  net_profit: string;
}

export interface BalanceSheetReport {
  organization: string;
  currency: string;
  as_of_date: string;
  total_assets: string;
  total_liabilities: string;
  total_equity: string;
  is_balanced: boolean;
}

export interface VatRegistersReport {
  organization: string;
  vat_number: string;
  sales_book_annex_5: {
    total_invoices: number;
    total_taxable_amount: string;
    total_tax_exempt_amount: string;
    total_vat_collected: string;
    entries: any[];
  };
  purchase_book_annex_7: {
    total_purchases: number;
    total_taxable_purchases: string;
    total_vat_paid: string;
    entries: any[];
  };
  vat_return_summary: {
    output_vat_liability: string;
    input_vat_credit: string;
    net_vat_payable: string;
    is_payable: boolean;
  };
}

export interface CreditNote {
  id: string;
  credit_note_number: string;
  original_invoice: string;
  refund_amount: string;
  tax_amount: string;
  reason: string;
  restock_items: boolean;
  status: string;
  issued_at: string;
}

export interface Customer {
  id: string;
  name: string;
  phone: string;
  email?: string;
  pan_vat?: string;
  current_balance: string;
  loyalty_points: number;
}

