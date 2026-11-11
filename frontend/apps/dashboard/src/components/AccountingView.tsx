import React, { useState } from "react";
import {
  BookOpen,
  Scale,
  TrendingUp,
  FileCheck2,
  Calendar,
  CheckCircle2,
  AlertTriangle,
  Download,
} from "lucide-react";

export function AccountingView() {
  const [subTab, setSubTab] = useState<"trial-balance" | "profit-loss" | "vat-registers">("trial-balance");

  return (
    <div className="space-y-6">
      {/* Sub-navigation Tabs */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-purple-400" />
            <span>Accounting, Double-Entry Ledger & Nepal Tax Compliance</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Strict double-entry financial ledger with automatic journal posting from POS checkouts and procurement.
          </p>
        </div>

        <div className="flex items-center gap-1.5 p-1 bg-slate-900 border border-slate-800 rounded-xl text-xs font-medium">
          {[
            { id: "trial-balance", label: "Trial Balance (सन्तुलन परीक्षण)", icon: Scale },
            { id: "profit-loss", label: "P&L Statement (नाफा नोक्सान)", icon: TrendingUp },
            { id: "vat-registers", label: "Nepal VAT Registers (IRD)", icon: FileCheck2 },
          ].map((tab) => {
            const Icon = tab.icon;
            const active = subTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setSubTab(tab.id as any)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition ${
                  active ? "bg-purple-600 text-white font-bold" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Trial Balance SubTab */}
      {subTab === "trial-balance" && (
        <div className="space-y-5">
          <div className="p-4 bg-emerald-950/40 border border-emerald-800/80 rounded-2xl flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <div>
                <h4 className="text-sm font-bold text-emerald-300">Double-Entry Ledger In Perfect Balance</h4>
                <p className="text-xs text-emerald-400/80">Total Debit equals Total Credit: Rs. 18,74,250.00</p>
              </div>
            </div>
            <span className="px-3 py-1 bg-emerald-900/60 border border-emerald-700 rounded-lg text-xs font-mono font-bold text-white">
              Status: BALANCED
            </span>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="px-5 py-3.5">Code</th>
                  <th className="px-5 py-3.5">Account Name</th>
                  <th className="px-5 py-3.5">Account Category</th>
                  <th className="px-5 py-3.5 text-right">Debit (Rs.)</th>
                  <th className="px-5 py-3.5 text-right">Credit (Rs.)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {[
                  { code: "1000", name: "Cash in Hand (POS Till)", cat: "Asset", debit: "85,400.00", credit: "-" },
                  { code: "1010", name: "Bank & Digital Wallets (eSewa/Khalti)", cat: "Asset", debit: "2,42,850.00", credit: "-" },
                  { code: "1100", name: "Accounts Receivable (Khata Debt)", cat: "Asset", debit: "35,200.00", credit: "-" },
                  { code: "1200", name: "Inventory Stock Ledger", cat: "Asset", debit: "15,10,800.00", credit: "-" },
                  { code: "2000", name: "Accounts Payable (Suppliers)", cat: "Liability", debit: "-", credit: "4,20,000.00" },
                  { code: "2200", name: "Output VAT Payable (13% IRD)", cat: "Liability", debit: "-", credit: "48,250.00" },
                  { code: "3000", name: "Owner's Equity & Retained Earnings", cat: "Equity", debit: "-", credit: "8,50,000.00" },
                  { code: "4000", name: "Sales Revenue (Gross)", cat: "Revenue", debit: "-", credit: "5,56,000.00" },
                  { code: "5000", name: "Cost of Goods Sold (COGS)", cat: "Expense", debit: "3,82,000.00", credit: "-" },
                ].map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30 transition">
                    <td className="px-5 py-3 font-bold text-purple-400">{row.code}</td>
                    <td className="px-5 py-3 font-sans text-white font-medium">{row.name}</td>
                    <td className="px-5 py-3 font-sans text-slate-400">{row.cat}</td>
                    <td className="px-5 py-3 text-right text-emerald-400">{row.debit}</td>
                    <td className="px-5 py-3 text-right text-blue-400">{row.credit}</td>
                  </tr>
                ))}
                <tr className="bg-slate-950 font-bold border-t-2 border-slate-700">
                  <td colSpan={3} className="px-5 py-4 font-sans text-white">
                    TOTAL TRIAL BALANCE
                  </td>
                  <td className="px-5 py-4 text-right text-emerald-400">Rs. 22,56,250.00</td>
                  <td className="px-5 py-4 text-right text-blue-400">Rs. 22,56,250.00</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Profit & Loss SubTab */}
      {subTab === "profit-loss" && (
        <div className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 font-mono">
            {[
              { label: "Total Revenue", val: "Rs. 5,56,000.00", desc: "Gross POS billings", color: "text-blue-400" },
              { label: "Cost of Goods Sold", val: "Rs. 3,82,000.00", desc: "Weighted avg cost", color: "text-amber-400" },
              { label: "Gross Profit", val: "Rs. 1,74,000.00", desc: "31.3% gross margin", color: "text-emerald-400" },
              { label: "Net Operating Profit", val: "Rs. 1,32,500.00", desc: "After store expenses", color: "text-purple-400" },
            ].map((card, i) => (
              <div key={i} className="p-5 bg-slate-900 border border-slate-800 rounded-2xl">
                <div className="text-xs font-sans text-slate-400">{card.label}</div>
                <div className={`text-xl font-bold mt-2 ${card.color}`}>{card.val}</div>
                <div className="text-[11px] font-sans text-slate-500 mt-1">{card.desc}</div>
              </div>
            ))}
          </div>

          <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl space-y-4">
            <h3 className="text-sm font-bold text-white">Profit & Loss Summary Breakdown (Fiscal 2083/84)</h3>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between py-2 border-b border-slate-800 text-slate-300">
                <span className="font-sans font-medium">Operating Revenue (POS Sales)</span>
                <span>Rs. 5,56,000.00</span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-800 text-red-400">
                <span className="font-sans font-medium">Less: Cost of Goods Sold (COGS)</span>
                <span>(Rs. 3,82,000.00)</span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-800 font-bold text-emerald-400">
                <span className="font-sans">Gross Profit</span>
                <span>Rs. 1,74,000.00</span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-800 text-slate-400">
                <span className="font-sans">Operating Expenses (Rent, Electricity, Logistics)</span>
                <span>(Rs. 41,500.00)</span>
              </div>
              <div className="flex justify-between py-3 border-t-2 border-slate-700 font-bold text-sm text-purple-400">
                <span className="font-sans">Net Operating Profit</span>
                <span>Rs. 1,32,500.00</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Nepal IRD VAT Registers SubTab */}
      {subTab === "vat-registers" && (
        <div className="space-y-6">
          {/* VAT Return Summary Card */}
          <div className="p-6 bg-gradient-to-r from-purple-950/60 to-blue-950/60 border border-purple-900/60 rounded-2xl">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <span className="px-2.5 py-1 rounded bg-purple-500/20 text-purple-300 font-bold text-[11px]">
                  Nepal IRD Form 101.1
                </span>
                <h3 className="text-base font-bold text-white mt-2">
                  Monthly VAT Return Summary (भ्याट विवरण सारांश)
                </h3>
                <p className="text-xs text-slate-300 mt-0.5">
                  Taxpayer PAN/VAT: <b>601234567</b> · Filing Month: <b>Kartik 2083</b>
                </p>
              </div>

              <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800 text-right">
                <div className="text-xs text-slate-400">Net VAT Payable to Government</div>
                <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">Rs. 28,600.00</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Due on 25th of current month</div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 font-mono text-xs">
              <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                <div className="text-slate-400 font-sans">Output VAT Collected (Annex 5)</div>
                <div className="text-base font-bold text-white mt-1">Rs. 48,250.00</div>
              </div>
              <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                <div className="text-slate-400 font-sans">Input VAT Credit (Annex 7)</div>
                <div className="text-base font-bold text-blue-400 mt-1">(Rs. 19,650.00)</div>
              </div>
              <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                <div className="text-slate-400 font-sans">Net Fiscal Liability</div>
                <div className="text-base font-bold text-emerald-400 mt-1">Rs. 28,600.00</div>
              </div>
            </div>
          </div>

          {/* Annex 5 & Annex 7 Highlights */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Sales Book Annex 5 */}
            <div className="p-5 bg-slate-900 border border-slate-800 rounded-2xl space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-bold text-white">Sales Book (अनुसूची ५ बिक्री खाता)</h4>
                  <p className="text-[11px] text-slate-400">Continuous gapless sequence log</p>
                </div>
                <button
                  onClick={() => alert("Exporting IRD Annex 5 Excel / CSV...")}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Export</span>
                </button>
              </div>

              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between py-1.5 border-b border-slate-800 text-slate-300">
                  <span className="font-sans">Taxable Sales (13% VAT):</span>
                  <span>Rs. 3,71,153.85</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800 text-slate-300">
                  <span className="font-sans">Tax-Exempt Sales (0% VAT):</span>
                  <span>Rs. 1,36,596.15</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800 font-bold text-purple-400">
                  <span className="font-sans">Output VAT Collected:</span>
                  <span>Rs. 48,250.00</span>
                </div>
              </div>
            </div>

            {/* Purchase Book Annex 7 */}
            <div className="p-5 bg-slate-900 border border-slate-800 rounded-2xl space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-bold text-white">Purchase Book (अनुसूची ७ खरिद खाता)</h4>
                  <p className="text-[11px] text-slate-400">Vendor procurement tax invoices</p>
                </div>
                <button
                  onClick={() => alert("Exporting IRD Annex 7 Excel / CSV...")}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Export</span>
                </button>
              </div>

              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between py-1.5 border-b border-slate-800 text-slate-300">
                  <span className="font-sans">Taxable Purchases:</span>
                  <span>Rs. 1,51,153.85</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800 text-slate-300">
                  <span className="font-sans">Exempt Purchases (Agricultural):</span>
                  <span>Rs. 2,11,196.15</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800 font-bold text-blue-400">
                  <span className="font-sans">Input VAT Claimable:</span>
                  <span>Rs. 19,650.00</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
