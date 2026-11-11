import { localDb } from "./db";
import type { CheckoutPayload, SyncEvent } from "@nextgen/shared-types";

export class SyncEngine {
  private isSyncing = false;

  /**
   * Saves an offline checkout transaction locally and registers it into the sync queue.
   */
  async enqueueCheckout(
    organizationId: string,
    branchId: string,
    terminalId: string | undefined,
    payload: CheckoutPayload
  ): Promise<SyncEvent> {
    const eventId = crypto.randomUUID();
    const event: SyncEvent = {
      event_id: eventId,
      organization_id: organizationId,
      branch_id: branchId,
      terminal_id: terminalId,
      event_type: "sale.created",
      schema_version: 1,
      local_sequence: Date.now(),
      created_at: new Date().toISOString(),
      payload,
      status: "PENDING",
      retry_count: 0,
    };

    await localDb.transaction("rw", [localDb.sync_queue], async () => {
      await localDb.sync_queue.add(event);
    });

    // Try processing if online
    if (navigator.onLine) {
      this.processQueue().catch(console.error);
    }

    return event;
  }

  /**
   * Iterates through pending queue items and pushes them to the central Django API.
   */
  async processQueue(apiCheckoutFn?: (payload: CheckoutPayload) => Promise<any>): Promise<{ synced: number; failed: number }> {
    if (this.isSyncing) return { synced: 0, failed: 0 };
    if (!navigator.onLine) return { synced: 0, failed: 0 };

    this.isSyncing = true;
    let synced = 0;
    let failed = 0;

    try {
      const pendingEvents = await localDb.sync_queue
        .where("status")
        .equals("PENDING")
        .sortBy("local_sequence");

      for (const event of pendingEvents) {
        try {
          if (apiCheckoutFn && event.event_type === "sale.created") {
            await apiCheckoutFn(event.payload as CheckoutPayload);
          }
          await localDb.sync_queue.update(event.event_id, {
            status: "SYNCED",
          });
          synced++;
        } catch (err: any) {
          failed++;
          const retry = event.retry_count + 1;
          if (retry > 5) {
            // Move permanent errors to sync_conflicts for human cashier inspection
            await localDb.sync_conflicts.add({
              ...event,
              status: "CONFLICT",
              error_message: err?.message || "Sync failed after 5 retries",
            });
            await localDb.sync_queue.delete(event.event_id);
          } else {
            await localDb.sync_queue.update(event.event_id, {
              retry_count: retry,
              error_message: err?.message,
            });
          }
        }
      }
    } finally {
      this.isSyncing = false;
    }

    return { synced, failed };
  }

  async getPendingCount(): Promise<number> {
    return localDb.sync_queue.where("status").equals("PENDING").count();
  }
}

export const syncEngine = new SyncEngine();
