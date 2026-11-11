import axios, { type AxiosInstance, type AxiosRequestConfig } from "axios";
import type {
  Product,
  Sale,
  CheckoutPayload,
  Organization,
  User,
  Branch,
  StockBalance,
  TrialBalanceReport,
  ProfitLossReport,
  BalanceSheetReport,
  VatRegistersReport,
  CreditNote,
  Customer,
} from "@nextgen/shared-types";

export interface ApiClientConfig {
  baseURL?: string;
  getAuthToken?: () => string | null;
  getOrganizationId?: () => string | null;
  getBranchId?: () => string | null;
}

export class NextGenApiClient {
  private client: AxiosInstance;

  constructor(private config: ApiClientConfig = {}) {
    this.client = axios.create({
      baseURL: config.baseURL || "http://localhost:8000/api/v1",
      headers: {
        "Content-Type": "application/json",
      },
    });

    this.client.interceptors.request.use((req) => {
      const token = this.config.getAuthToken?.();
      if (token) {
        req.headers.Authorization = `Bearer ${token}`;
      }
      const orgId = this.config.getOrganizationId?.();
      if (orgId) {
        req.headers["X-Organization-ID"] = orgId;
      }
      const branchId = this.config.getBranchId?.();
      if (branchId) {
        req.headers["X-Branch-ID"] = branchId;
      }
      return req;
    });
  }

  // Auth & Tenants
  async getProfile(): Promise<User> {
    const res = await this.client.get("/auth/profile/");
    return res.data;
  }

  async getOrganizations(): Promise<Organization[]> {
    const res = await this.client.get("/organizations/");
    return res.data.results || res.data;
  }

  async getBranches(): Promise<Branch[]> {
    const res = await this.client.get("/branches/");
    return res.data.results || res.data;
  }

  // Catalog
  async getProducts(params?: Record<string, any>): Promise<{ results: Product[]; count: number }> {
    const res = await this.client.get("/products/", { params });
    return { results: res.data.results || res.data, count: res.data.pagination?.count || 0 };
  }

  // Inventory
  async getStockBalances(warehouseId?: string): Promise<StockBalance[]> {
    const res = await this.client.get("/inventory/balances/", {
      params: warehouseId ? { warehouse_id: warehouseId } : undefined,
    });
    return res.data.results || res.data;
  }

  // POS Checkout (Authoritative server API)
  async checkout(payload: CheckoutPayload): Promise<Sale> {
    const res = await this.client.post("/pos/checkout/", payload);
    return res.data;
  }

  // Sales History & Receipts
  async getSales(params?: Record<string, any>): Promise<{ results: Sale[]; count: number }> {
    const res = await this.client.get("/sales/", { params });
    return { results: res.data.results || res.data, count: res.data.pagination?.count || 0 };
  }

  async getThermalReceipt(saleId: string, format: "58mm" | "80mm" | "escpos" = "80mm"): Promise<string> {
    const res = await this.client.get(`/sales/${saleId}/receipt/`, {
      params: { format },
    });
    return res.data;
  }

  async issueCreditNote(saleId: string, payload: { reason: string; restock_items?: boolean; refund_amount?: number }): Promise<CreditNote> {
    const res = await this.client.post(`/sales/${saleId}/credit-note/`, payload);
    return res.data;
  }

  // Accounting & Financial Reports
  async getTrialBalance(): Promise<TrialBalanceReport> {
    const res = await this.client.get("/accounting/reports/trial-balance/");
    return res.data;
  }

  async getProfitLoss(params?: { from_date?: string; to_date?: string }): Promise<ProfitLossReport> {
    const res = await this.client.get("/accounting/reports/profit-loss/", { params });
    return res.data;
  }

  async getBalanceSheet(params?: { as_of_date?: string }): Promise<BalanceSheetReport> {
    const res = await this.client.get("/accounting/reports/balance-sheet/", { params });
    return res.data;
  }

  async getVatRegisters(params?: { from_date?: string; to_date?: string }): Promise<VatRegistersReport> {
    const res = await this.client.get("/accounting/reports/vat-registers/", { params });
    return res.data;
  }

  // Customers & Khata
  async getCustomers(params?: Record<string, any>): Promise<{ results: Customer[]; count: number }> {
    const res = await this.client.get("/sales/customers/", { params });
    return { results: res.data.results || res.data, count: res.data.pagination?.count || 0 };
  }

  async settleKhata(customerId: string, payload: { amount: number; payment_method: string; notes?: string }): Promise<any> {
    const res = await this.client.post("/wholesale/credit/settle/", {
      customer_id: customerId,
      ...payload,
    });
    return res.data;
  }

  // Stock Transfers
  async createStockTransfer(payload: {
    source_warehouse: string;
    destination_warehouse: string;
    notes?: string;
    items: { variant_id: string; quantity: number }[];
  }): Promise<any> {
    const res = await this.client.post("/inventory/transfers/", payload);
    return res.data;
  }

  async dispatchStockTransfer(transferId: string): Promise<any> {
    const res = await this.client.post(`/inventory/transfers/${transferId}/dispatch/`);
    return res.data;
  }

  async receiveStockTransfer(transferId: string): Promise<any> {
    const res = await this.client.post(`/inventory/transfers/${transferId}/receive/`);
    return res.data;
  }
}
