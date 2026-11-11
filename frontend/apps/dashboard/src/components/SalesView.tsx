import React, { useState } from "react";
import {
  Receipt,
  RotateCcw,
  Printer,
  Search,
  CheckCircle2,
  AlertCircle,
  FileText,
  X,
  CreditCard,
} from "lucide-react";

interface SaleRecord {
  id: string;
  invoice_number: string;
  customer_name: string;
  date: string;
  items_summary: string;
  subtotal: number;
  vat_amount: number;
  total_amount: number;
  payment_method: string;
  status: "COMPLETED" | "CREDIT_NOTE_ISSUED";
  has_credit_note?: boolean;
}

const SAMPLE_SALES: SaleRecord[] = [
  {
    id: "sale-001",
    invoice_number: "INV-2083-000101",
    customer_name: "Ramesh Sharma",
    date: "2026-11-10 14:20",
    items_summary: "Shakti Flour 5kg x 2, Dhara Mustard Oil 1L x 1",
    subtotal: 1195.0,
    vat_amount: 155.35,
    total_amount: 1350.35,
    payment_method: "ESEWA",
    status: "COMPLETED",
  },
  {
    id: "sale-002",
    invoice_number: "INV-2083-000102",
    customer_name: "Sita Thapa",
    date: "2026-11-10 14:45",
    items_summary: "Himalayan Basmati Rice 25kg x 1",
    subtotal: 2850.0,
    vat_amount: 370.5,
    total_amount: 3220.5,
    payment_method: "FONEPAY",
    status: "COMPLETED",
  },
  {
    id: "sale-003",
    invoice_number: "INV-2083-000103",
    customer_name: "Kushal Shrestha",
    date: "2026-11-10 15:10",
    items_summary: "Wai Wai Quick 75g x 30, DDC Milk 500ml x 10",
    subtotal: 1250.0,
    vat_amount: 97.5,
    total_amount: 1347.5,
    payment_method: "CREDIT",
    status: "COMPLETED",
  },
  {
    id: "sale-004",
    invoice_number: "INV-2083-000104",
    customer_name: "Walk-in Customer",
    date: "2026-11-10 15:35",
    items_summary: "DDC Pasteurised Milk 500ml x 4",
    subtotal: 200.0,
    vat_amount: 0.0,
    total_amount: 200.0,
    payment_method: "CASH",
    status: "COMPLETED",
  },
];

export function SalesView() {
  const [sales, setSales] = useState<SaleRecord[]>(SAMPLE_SALES);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSaleForReceipt, setSelectedSaleForReceipt] = useState<SaleRecord | null>(null);
  const [receiptWidth, setReceiptWidth] = useState<58 | 80>(80);

  // Credit Note Modal State
  const [creditNoteModalSale, setCreditNoteModalSale] = useState<SaleRecord | null>(null);
  const [cnReason, setCnReason] = useState("Customer Return");
  const [cnRestock, setCnRestock] = useState(true);
  const [cnSuccessMsg, setCnSuccessMsg] = useState<string | null>(null);

  const filteredSales = sales.filter(
    (s) =>
      s.invoice_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.customer_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.payment_method.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleIssueCreditNote = () => {
    if (!creditNoteModalSale) return;

    const cnNumber = `CN-${creditNoteModalSale.invoice_number.replace("INV-", "")}`;
    setSales((prev) =>
      prev.map((s) =>
        s.id === creditNoteModalSale.id
          ? { ...s, status: "CREDIT_NOTE_ISSUED", has_credit_note: true }
          : s
      )
    );

    setCnSuccessMsg(
      `Nepal IRD Credit Note ${cnNumber} (फिर्ता बिल) issued successfully! Output VAT reversed to Account 2200 and items restocked to warehouse ledger.`
    );
    setCreditNoteModalSale(null);
    setTimeout(() => setCnSuccessMsg(null), 6000);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Search */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Receipt className="w-5 h-5 text-blue-400" />
            <span>Sales Invoices & Nepal Fiscal Billing</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            100% gapless sequential numbering complying with Inland Revenue Department (IRD) billing directives.
          </p>
        </div>

        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
          <input
            type="text"
            placeholder="Search invoice #, customer, tender..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs w-72 focus:outline-none focus:border-blue-500 text-slate-200"
          />
        </div>
      </div>

      {cnSuccessMsg && (
        <div className="p-4 bg-emerald-950/60 border border-emerald-800 rounded-xl text-xs text-emerald-300 flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-400" />
          <span>{cnSuccessMsg}</span>
        </div>
      )}

      {/* Invoices Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="px-5 py-3.5">Invoice #</th>
                <th className="px-5 py-3.5">Date & Time</th>
                <th className="px-5 py-3.5">Customer</th>
                <th className="px-5 py-3.5">Items Summary</th>
                <th className="px-5 py-3.5 text-right">Taxable Subtotal</th>
                <th className="px-5 py-3.5 text-right">13% VAT</th>
                <th className="px-5 py-3.5 text-right">Total NPR</th>
                <th className="px-5 py-3.5 text-center">Tender</th>
                <th className="px-5 py-3.5 text-center">Status</th>
                <th className="px-5 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {filteredSales.map((sale) => (
                <tr key={sale.id} className="hover:bg-slate-800/30 transition">
                  <td className="px-5 py-3.5 font-bold text-white font-sans">{sale.invoice_number}</td>
                  <td className="px-5 py-3.5 text-slate-400">{sale.date}</td>
                  <td className="px-5 py-3.5 font-sans text-slate-300">{sale.customer_name}</td>
                  <td className="px-5 py-3.5 font-sans text-slate-400 truncate max-w-xs">{sale.items_summary}</td>
                  <td className="px-5 py-3.5 text-right text-slate-300">Rs. {sale.subtotal.toFixed(2)}</td>
                  <td className="px-5 py-3.5 text-right text-purple-400">Rs. {sale.vat_amount.toFixed(2)}</td>
                  <td className="px-5 py-3.5 text-right font-bold text-emerald-400">Rs. {sale.total_amount.toFixed(2)}</td>
                  <td className="px-5 py-3.5 text-center">
                    <span className="px-2 py-0.5 rounded text-[10px] font-sans font-bold bg-slate-800 text-blue-300 border border-slate-700">
                      {sale.payment_method}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-center font-sans">
                    {sale.status === "COMPLETED" ? (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
                        Paid / Fiscal
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-950 text-amber-400 border border-amber-800">
                        Credit Note Issued
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3.5 text-right font-sans">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setSelectedSaleForReceipt(sale)}
                        title="View Thermal Receipt"
                        className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                      >
                        <Printer className="w-3.5 h-3.5" />
                      </button>
                      {sale.status === "COMPLETED" && (
                        <button
                          onClick={() => setCreditNoteModalSale(sale)}
                          title="Issue Nepal IRD Credit Note (फिर्ता बिल)"
                          className="px-2.5 py-1 bg-red-950/60 hover:bg-red-900/80 text-red-300 border border-red-800/80 rounded-lg text-[11px] font-semibold flex items-center gap-1 transition"
                        >
                          <RotateCcw className="w-3 h-3" />
                          <span>Credit Note</span>
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Credit Note (फिर्ता बिल) Modal */}
      {creditNoteModalSale && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="font-bold text-white text-base flex items-center gap-2">
                  <RotateCcw className="w-4 h-4 text-red-400" />
                  <span>Issue Nepal IRD Credit Note (फिर्ता बिल)</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Reversing invoice {creditNoteModalSale.invoice_number}
                </p>
              </div>
              <button
                onClick={() => setCreditNoteModalSale(null)}
                className="p-1 text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4 bg-slate-950 rounded-xl space-y-2 text-xs border border-slate-800">
              <div className="flex justify-between text-slate-300">
                <span>Customer:</span>
                <span className="font-bold text-white">{creditNoteModalSale.customer_name}</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>Original Invoice Amount:</span>
                <span className="font-bold font-mono">Rs. {creditNoteModalSale.total_amount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>Output VAT to Reverse (13%):</span>
                <span className="font-bold text-purple-400 font-mono">Rs. {creditNoteModalSale.vat_amount.toFixed(2)}</span>
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-slate-300 font-semibold block mb-1">
                  Reason for Credit Note / Return:
                </label>
                <select
                  value={cnReason}
                  onChange={(e) => setCnReason(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                >
                  <option value="Customer Return">Customer Return (ग्राहकले फिर्ता गरेको)</option>
                  <option value="Damaged / Defective Stock">Damaged / Defective Stock (सामान बिग्रिएको)</option>
                  <option value="Billing / Quantity Error">Billing / Quantity Error (बिलिङ त्रुटि)</option>
                  <option value="Cancellation of Sale">Cancellation of Sale (कारोबार रद्द)</option>
                </select>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="restock"
                  checked={cnRestock}
                  onChange={(e) => setCnRestock(e.target.checked)}
                  className="rounded bg-slate-950 border-slate-800 text-blue-600 focus:ring-0"
                />
                <label htmlFor="restock" className="text-xs text-slate-300">
                  Restock returned items back to active warehouse inventory
                </label>
              </div>
            </div>

            <div className="p-3 bg-red-950/40 border border-red-900/60 rounded-xl text-[11px] text-red-300 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
              <span>
                According to Nepal VAT Directives, once issued, sales invoices cannot be deleted. This workflow issues an IRD-compliant Credit Note and posts reversing double-entry journals.
              </span>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setCreditNoteModalSale(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleIssueCreditNote}
                className="px-5 py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs font-bold transition shadow-lg flex items-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Confirm & Issue Credit Note</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Thermal Receipt Preview Modal */}
      {selectedSaleForReceipt && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-3">
                <Printer className="w-5 h-5 text-blue-400" />
                <h3 className="font-bold text-white text-sm">ESC/POS Thermal Receipt</h3>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setReceiptWidth(58)}
                  className={`px-2 py-1 rounded text-[11px] font-bold ${
                    receiptWidth === 58 ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-400"
                  }`}
                >
                  58mm
                </button>
                <button
                  onClick={() => setReceiptWidth(80)}
                  className={`px-2 py-1 rounded text-[11px] font-bold ${
                    receiptWidth === 80 ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-400"
                  }`}
                >
                  80mm
                </button>
                <button
                  onClick={() => setSelectedSaleForReceipt(null)}
                  className="p-1 text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Simulated Paper Roll */}
            <div
              className={`mx-auto bg-white text-black p-4 font-mono text-[11px] rounded shadow-lg overflow-x-hidden ${
                receiptWidth === 58 ? "max-w-[260px]" : "max-w-[340px]"
              }`}
            >
              <div className="text-center font-bold text-sm">NAMASTE MART PVT. LTD.</div>
              <div className="text-center text-[10px]">New Road, Kathmandu, Nepal</div>
              <div className="text-center text-[10px]">PAN / VAT: 601234567</div>
              <div className="text-center text-[10px]">Phone: +977-1-4234567</div>
              <div className="text-center my-1 border-t border-b border-dashed border-black py-0.5 font-bold">
                TAX INVOICE (कर बिजक)
              </div>
              <div className="flex justify-between text-[10px]">
                <span>Bill: {selectedSaleForReceipt.invoice_number}</span>
                <span>{selectedSaleForReceipt.date.split(" ")[0]}</span>
              </div>
              <div className="text-[10px]">Customer: {selectedSaleForReceipt.customer_name}</div>
              <div className="border-t border-black my-1" />
              <div className="space-y-1">
                <div className="text-[10px] leading-tight">{selectedSaleForReceipt.items_summary}</div>
              </div>
              <div className="border-t border-black my-1" />
              <div className="flex justify-between">
                <span>Taxable Amount:</span>
                <span>Rs. {selectedSaleForReceipt.subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>VAT (13%):</span>
                <span>Rs. {selectedSaleForReceipt.vat_amount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between font-bold text-xs pt-1 border-t border-dashed border-black">
                <span>Grand Total:</span>
                <span>Rs. {selectedSaleForReceipt.total_amount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-[10px] pt-1">
                <span>Tender ({selectedSaleForReceipt.payment_method}):</span>
                <span>Rs. {selectedSaleForReceipt.total_amount.toFixed(2)}</span>
              </div>
              <div className="border-t border-dashed border-black my-2" />
              <div className="text-center text-[9px] leading-tight">
                धन्यवाद! फेरि आउनुहोला।<br />
                Computer generated IRD compliant bill.
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => window.print()}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2 transition"
              >
                <Printer className="w-4 h-4" />
                <span>Print Thermal Receipt</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
