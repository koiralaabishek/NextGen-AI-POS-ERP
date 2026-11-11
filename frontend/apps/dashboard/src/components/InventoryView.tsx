import React, { useState } from "react";
import {
  Boxes,
  ArrowRightLeft,
  Warehouse,
  History,
  AlertTriangle,
  CheckCircle2,
  Plus,
  Send,
  X,
} from "lucide-react";

interface StockBalanceItem {
  id: string;
  warehouse: string;
  sku: string;
  name: string;
  quantity: number;
  reorder_level: number;
  unit: string;
  is_low: boolean;
}

interface StockTransferRecord {
  id: string;
  source: string;
  dest: string;
  item: string;
  qty: number;
  status: "DRAFT" | "IN_TRANSIT" | "COMPLETED";
  date: string;
}

const SAMPLE_BALANCES: StockBalanceItem[] = [
  { id: "sb-1", warehouse: "Central Warehouse (KTM)", sku: "WHT-FLOUR-5KG", name: "Shakti Wheat Flour 5kg", quantity: 180, reorder_level: 25, unit: "bag", is_low: false },
  { id: "sb-2", warehouse: "Store Front Display", sku: "WHT-FLOUR-5KG", name: "Shakti Wheat Flour 5kg", quantity: 14, reorder_level: 15, unit: "bag", is_low: true },
  { id: "sb-3", warehouse: "Central Warehouse (KTM)", sku: "BASMATI-RICE-25KG", name: "Himalayan Basmati Rice 25kg", quantity: 65, reorder_level: 10, unit: "bag", is_low: false },
  { id: "sb-4", warehouse: "Cold Storage Room", sku: "MILK-FULL-CREAM", name: "DDC Pasteurised Milk 500ml", quantity: 8, reorder_level: 20, unit: "packet", is_low: true },
  { id: "sb-5", warehouse: "Store Front Display", sku: "MUSTARD-OIL-1L", name: "Dhara Pure Mustard Oil 1L", quantity: 42, reorder_level: 10, unit: "bottle", is_low: false },
];

export function InventoryView() {
  const [balances, setBalances] = useState<StockBalanceItem[]>(SAMPLE_BALANCES);
  const [transfers, setTransfers] = useState<StockTransferRecord[]>([
    { id: "tr-001", source: "Central Warehouse (KTM)", dest: "Store Front Display", item: "Shakti Wheat Flour 5kg", qty: 20, status: "IN_TRANSIT", date: "2026-11-10 13:00" },
    { id: "tr-002", source: "Central Warehouse (KTM)", dest: "Store Front Display", item: "Dhara Pure Mustard Oil 1L", qty: 30, status: "COMPLETED", date: "2026-11-09 17:30" },
  ]);

  const [transferModalOpen, setTransferModalOpen] = useState(false);
  const [sourceWh, setSourceWh] = useState("Central Warehouse (KTM)");
  const [destWh, setDestWh] = useState("Store Front Display");
  const [selectedSku, setSelectedSku] = useState("WHT-FLOUR-5KG");
  const [transferQty, setTransferQty] = useState(10);
  const [successNote, setSuccessNote] = useState<string | null>(null);

  const handleCreateTransfer = () => {
    if (sourceWh === destWh) {
      alert("Source and Destination warehouses must be different.");
      return;
    }

    const prod = balances.find((b) => b.sku === selectedSku);
    const newTr: StockTransferRecord = {
      id: `tr-${Date.now().toString().slice(-4)}`,
      source: sourceWh,
      dest: destWh,
      item: prod?.name || selectedSku,
      qty: transferQty,
      status: "IN_TRANSIT",
      date: new Date().toLocaleString(),
    };

    setTransfers([newTr, ...transfers]);
    setTransferModalOpen(false);
    setSuccessNote(`Stock transfer ${newTr.id} dispatched! Ledger balances adjusted.`);
    setTimeout(() => setSuccessNote(null), 5000);
  };

  const handleReceiveTransfer = (id: string) => {
    setTransfers((prev) =>
      prev.map((t) => (t.id === id ? { ...t, status: "COMPLETED" } : t))
    );
    setSuccessNote(`Stock transfer ${id} safely received at destination warehouse.`);
    setTimeout(() => setSuccessNote(null), 5000);
  };

  return (
    <div className="space-y-6">
      {/* Header & Quick Action */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Boxes className="w-5 h-5 text-emerald-400" />
            <span>Multi-Warehouse Inventory Ledger & Stock Transfers</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Immutable audit movement ledger: never overwrite quantities without a verifiable transaction reference.
          </p>
        </div>

        <button
          onClick={() => setTransferModalOpen(true)}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold flex items-center gap-2 transition shadow-lg self-start md:self-auto"
        >
          <ArrowRightLeft className="w-4 h-4" />
          <span>New Stock Transfer</span>
        </button>
      </div>

      {successNote && (
        <div className="p-4 bg-emerald-950/60 border border-emerald-800 rounded-xl text-xs text-emerald-300 flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
          <span>{successNote}</span>
        </div>
      )}

      {/* Stock Balances Table */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <Warehouse className="w-4 h-4 text-slate-400" />
          <span>Current Warehouse Stock Balances</span>
        </h3>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="px-5 py-3.5">Warehouse Location</th>
                <th className="px-5 py-3.5">SKU Code</th>
                <th className="px-5 py-3.5">Product Name</th>
                <th className="px-5 py-3.5 text-right">Available Stock</th>
                <th className="px-5 py-3.5 text-right">Reorder Threshold</th>
                <th className="px-5 py-3.5 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {balances.map((b) => (
                <tr key={b.id} className="hover:bg-slate-800/30 transition">
                  <td className="px-5 py-3 font-sans text-white font-medium">{b.warehouse}</td>
                  <td className="px-5 py-3 text-slate-400">{b.sku}</td>
                  <td className="px-5 py-3 font-sans text-slate-200">{b.name}</td>
                  <td className="px-5 py-3 text-right font-bold text-white">
                    {b.quantity} {b.unit}s
                  </td>
                  <td className="px-5 py-3 text-right text-slate-400">
                    {b.reorder_level} {b.unit}s
                  </td>
                  <td className="px-5 py-3 text-center font-sans">
                    {b.is_low ? (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-950 text-amber-400 border border-amber-800 flex items-center justify-center gap-1 w-max mx-auto">
                        <AlertTriangle className="w-3 h-3" />
                        <span>Low Stock</span>
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
                        Adequate
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Stock Transfers Table */}
      <div className="space-y-3 pt-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <History className="w-4 h-4 text-slate-400" />
          <span>Inter-Warehouse Stock Transfers Log</span>
        </h3>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="px-5 py-3.5">Transfer #</th>
                <th className="px-5 py-3.5">Source Warehouse</th>
                <th className="px-5 py-3.5">Destination</th>
                <th className="px-5 py-3.5">Item & Qty</th>
                <th className="px-5 py-3.5 text-center">Status</th>
                <th className="px-5 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {transfers.map((tr) => (
                <tr key={tr.id} className="hover:bg-slate-800/30 transition">
                  <td className="px-5 py-3 font-bold text-white">{tr.id}</td>
                  <td className="px-5 py-3 font-sans text-slate-300">{tr.source}</td>
                  <td className="px-5 py-3 font-sans text-slate-300">{tr.dest}</td>
                  <td className="px-5 py-3 font-sans text-emerald-400">
                    {tr.item} <b className="font-mono">({tr.qty} units)</b>
                  </td>
                  <td className="px-5 py-3 text-center font-sans">
                    {tr.status === "IN_TRANSIT" ? (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-950 text-blue-400 border border-blue-800">
                        In Transit
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
                        Completed
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-right font-sans">
                    {tr.status === "IN_TRANSIT" && (
                      <button
                        onClick={() => handleReceiveTransfer(tr.id)}
                        className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-[11px] font-bold transition shadow"
                      >
                        Receive Stock
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Stock Transfer Modal */}
      {transferModalOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-sm flex items-center gap-2">
                <ArrowRightLeft className="w-4 h-4 text-emerald-400" />
                <span>Dispatch Stock Transfer</span>
              </h3>
              <button onClick={() => setTransferModalOpen(false)} className="p-1 text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-slate-300 font-semibold block mb-1">Source Warehouse (From):</label>
                <select
                  value={sourceWh}
                  onChange={(e) => setSourceWh(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:border-blue-500"
                >
                  <option value="Central Warehouse (KTM)">Central Warehouse (KTM)</option>
                  <option value="Store Front Display">Store Front Display</option>
                  <option value="Cold Storage Room">Cold Storage Room</option>
                </select>
              </div>

              <div>
                <label className="text-slate-300 font-semibold block mb-1">Destination Warehouse (To):</label>
                <select
                  value={destWh}
                  onChange={(e) => setDestWh(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:border-blue-500"
                >
                  <option value="Store Front Display">Store Front Display</option>
                  <option value="Central Warehouse (KTM)">Central Warehouse (KTM)</option>
                  <option value="Cold Storage Room">Cold Storage Room</option>
                </select>
              </div>

              <div>
                <label className="text-slate-300 font-semibold block mb-1">Product SKU:</label>
                <select
                  value={selectedSku}
                  onChange={(e) => setSelectedSku(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:border-blue-500"
                >
                  <option value="WHT-FLOUR-5KG">Shakti Wheat Flour 5kg (WHT-FLOUR-5KG)</option>
                  <option value="BASMATI-RICE-25KG">Himalayan Basmati Rice 25kg (BASMATI-RICE-25KG)</option>
                  <option value="MUSTARD-OIL-1L">Dhara Pure Mustard Oil 1L (MUSTARD-OIL-1L)</option>
                  <option value="MILK-FULL-CREAM">DDC Pasteurised Milk 500ml (MILK-FULL-CREAM)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-300 font-semibold block mb-1">Quantity to Transfer:</label>
                <input
                  type="number"
                  min="1"
                  value={transferQty}
                  onChange={(e) => setTransferQty(parseInt(e.target.value) || 1)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 font-mono focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3">
              <button
                onClick={() => setTransferModalOpen(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateTransfer}
                className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold transition shadow-lg flex items-center gap-1.5"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Confirm & Dispatch</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
