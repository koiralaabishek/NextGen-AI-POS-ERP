import Dexie, { type EntityTable } from "dexie";
import type { SyncEvent, Product, Category } from "@nextgen/shared-types";

export interface LocalCustomer {
  id: string;
  name: string;
  phone: string;
  credit_limit: string;
}

export interface TerminalConfig {
  key: string;
  value: any;
}

export class NextGenOfflineDatabase extends Dexie {
  products!: EntityTable<Product, "id">;
  categories!: EntityTable<Category, "id">;
  customers!: EntityTable<LocalCustomer, "id">;
  sync_queue!: EntityTable<SyncEvent, "event_id">;
  sync_conflicts!: EntityTable<SyncEvent, "event_id">;
  terminal_config!: EntityTable<TerminalConfig, "key">;

  constructor() {
    super("NextGenPOSLocalDB");
    this.version(1).stores({
      products: "id, sku, *variants.barcode, category",
      categories: "id, slug",
      customers: "id, phone, name",
      sync_queue: "event_id, local_sequence, status, created_at",
      sync_conflicts: "event_id, status",
      terminal_config: "key",
    });
  }
}

export const localDb = new NextGenOfflineDatabase();
