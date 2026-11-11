import React, { useState } from "react";
import {
  Users,
  CreditCard,
  CheckCircle2,
  AlertCircle,
  Plus,
  Coins,
  Search,
  Wallet,
  X,
} from "lucide-react";

interface CustomerKhata {
  id: string;
  name: string;
  phone: string;
  pan_vat?: string;
  credit_limit: number;
  current_debt: number;
  loyalty_points: number;
  last_purchase: string;
}

const SAMPLE_KHATA_CUSTOMERS: CustomerKhata[] = [
  { id: "c1", name: "Ramesh Sharma", phone: "9851001122", pan_vat: "302948571", credit_limit: 10000, current_debt: 2450, loyalty_points: 340, last_purchase: "Today 14:20" },
  { id: "c2", name: "Sita Thapa", phone: "9841223344", credit_limit: 5000, current_debt: 0, loyalty_points: 120, last_purchase: "Today 14:45" },
  { id: "c3", name: "Kushal Shrestha", phone: "9801334455", credit_limit: 25000, current_debt: 14200, loyalty_points: 850, last_purchase: "Today 15:10" },
  { id: "c4", name: "Bikash Adhikari", phone: "9812445566", credit_limit: 15000, current_debt: 6800, loyalty_points: 410, last_purchase: "Yesterday 18:30" },
];

export function CustomersView() {
  const [customers, setCustomers] = useState<CustomerKhata[]>(SAMPLE_KHATA_CUSTOMERS);
  const [search, setSearch] = useState("");
  const [settleModalCustomer, setSettleModalCustomer] = useState<CustomerKhata | null>(null);
  const [settleAmount, setSettleAmount] = useState<number>(0);
  const [settleTender, setSettleTender] = useState<"CASH" | "ESEWA" | "KHALTI" | "FONEPAY">("CASH");
  const [successNote, setSuccessNote] = useState<string | null>(null);

  const filtered = customers.filter(
    (c) => c.name.toLowerCase().includes(search.toLowerCase()) || c.phone.includes(search)
  );

  const handleOpenSettle = (c: CustomerKhata) => {
    setSettleModalCustomer(c);
    setSettleAmount(c.current_debt);
  };

  const handleConfirmSettle = () => {
    if (!settleModalCustomer) return;

    setCustomers((prev) =>
      prev.map((c) =>
        c.id === settleModalCustomer.id
          ? { ...c, current_debt: Math.max(0, c.current_debt - settleAmount) }
          : c
      )
    );

    setSuccessNote(
      `Khata payment of Rs. ${settleAmount.toLocaleString()} received via ${settleTender} for ${settleModalCustomer.name}. Accounts Receivable updated.`
    );
    setSettleModalCustomer(null);
    setTimeout(() => setSuccessNote(null), 5000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-blue-400" />
            <span>Customer Khata (खाता) & Loyalty Rewards</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Credit limits, receivables ledger, and automated Nepal loyalty points calculation.
          </p>
        </div>

        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
          <input
            type="text"
            placeholder="Search customer by name or phone..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs w-72 focus:outline-none focus:border-blue-500 text-slate-200"
          />
        </div>
      </div>

      {successNote && (
        <div className="p-4 bg-emerald-950/60 border border-emerald-800 rounded-xl text-xs text-emerald-300 flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-400" />
          <span>{successNote}</span>
        </div>
      )}

      {/* Customers Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800">
            <tr>
              <th className="px-5 py-3.5">Customer Name</th>
              <th className="px-5 py-3.5">Mobile Phone</th>
              <th className="px-5 py-3.5">PAN / VAT</th>
              <th className="px-5 py-3.5 text-right">Credit Limit</th>
              <th className="px-5 py-3.5 text-right">Khata Debt (बक्यौता)</th>
              <th className="px-5 py-3.5 text-right">Available Credit</th>
              <th className="px-5 py-3.5 text-center">Loyalty Points</th>
              <th className="px-5 py-3.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {filtered.map((c) => {
              const available = c.credit_limit - c.current_debt;
              const isOverLimit = available <= 0;
              return (
                <tr key={c.id} className="hover:bg-slate-800/30 transition">
                  <td className="px-5 py-3 font-sans font-bold text-white">{c.name}</td>
                  <td className="px-5 py-3 text-slate-400">{c.phone}</td>
                  <td className="px-5 py-3 text-slate-500">{c.pan_vat || "N/A"}</td>
                  <td className="px-5 py-3 text-right text-slate-300">Rs. {c.credit_limit.toLocaleString()}</td>
                  <td className="px-5 py-3 text-right font-bold text-red-400">
                    Rs. {c.current_debt.toLocaleString()}
                  </td>
                  <td className={`px-5 py-3 text-right font-bold ${isOverLimit ? "text-amber-400" : "text-emerald-400"}`}>
                    Rs. {available.toLocaleString()}
                  </td>
                  <td className="px-5 py-3 text-center">
                    <span className="px-2 py-0.5 rounded-full text-[11px] font-sans font-bold bg-purple-950 text-purple-300 border border-purple-800 inline-flex items-center gap-1">
                      <Coins className="w-3 h-3 text-purple-400" />
                      <span>{c.loyalty_points} pts</span>
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right font-sans">
                    {c.current_debt > 0 ? (
                      <button
                        onClick={() => handleOpenSettle(c)}
                        className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-[11px] font-bold transition shadow flex items-center gap-1 ml-auto"
                      >
                        <Wallet className="w-3 h-3" />
                        <span>Settle Khata</span>
                      </button>
                    ) : (
                      <span className="text-[11px] text-slate-500">No Debt</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Settle Debt Modal */}
      {settleModalCustomer && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-sm flex items-center gap-2">
                <Wallet className="w-4 h-4 text-emerald-400" />
                <span>Settle Customer Khata Balance (खाता भुक्तानी)</span>
              </h3>
              <button onClick={() => setSettleModalCustomer(null)} className="p-1 text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-3 bg-slate-950 rounded-xl space-y-1.5 text-xs border border-slate-800 font-mono">
              <div className="flex justify-between font-sans text-slate-300">
                <span>Customer:</span>
                <span className="font-bold text-white">{settleModalCustomer.name}</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span className="font-sans">Current Outstanding Debt:</span>
                <span className="font-bold text-red-400">Rs. {settleModalCustomer.current_debt.toLocaleString()}</span>
              </div>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-slate-300 font-semibold block mb-1">Settlement Amount (Rs.):</label>
                <input
                  type="number"
                  min="1"
                  max={settleModalCustomer.current_debt}
                  value={settleAmount}
                  onChange={(e) => setSettleAmount(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 font-mono focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="text-slate-300 font-semibold block mb-1">Payment Method / Gateway:</label>
                <div className="grid grid-cols-2 gap-2">
                  {(["CASH", "ESEWA", "KHALTI", "FONEPAY"] as const).map((method) => (
                    <button
                      key={method}
                      type="button"
                      onClick={() => setSettleTender(method)}
                      className={`py-2 px-3 rounded-xl border text-xs font-bold transition flex items-center justify-center gap-1.5 ${
                        settleTender === method
                          ? "bg-blue-600 border-blue-500 text-white"
                          : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                      }`}
                    >
                      {method}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3">
              <button
                onClick={() => setSettleModalCustomer(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmSettle}
                className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold transition shadow-lg flex items-center gap-1.5"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Confirm Settlement</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
