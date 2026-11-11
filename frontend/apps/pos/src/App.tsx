import React, { useState, useEffect } from "react";
import {
  ShoppingCart,
  Trash2,
  Plus,
  Minus,
  Search,
  Wifi,
  WifiOff,
  RefreshCw,
  CheckCircle2,
  QrCode,
  Banknote,
  Smartphone,
  Store,
  PauseCircle,
  PlayCircle,
  Printer,
  UserCheck,
  CreditCard,
  Lock,
  Unlock,
  AlertCircle,
  X,
} from "lucide-react";
import { useCartStore } from "./store/useCartStore";
import { syncEngine, localDb } from "@nextgen/offline-sync";
import { NextGenApiClient } from "@nextgen/api-client";
import type { Product, CheckoutPayload } from "@nextgen/shared-types";

const apiClient = new NextGenApiClient({
  baseURL: "http://localhost:8000/api/v1",
});

interface CustomerProfile {
  id: string;
  name: string;
  phone: string;
  credit_limit: number;
  current_debt: number;
  loyalty_points: number;
}

const SAMPLE_CUSTOMERS: CustomerProfile[] = [
  { id: "c1", name: "Ramesh Sharma", phone: "9851001122", credit_limit: 10000, current_debt: 2450, loyalty_points: 340 },
  { id: "c2", name: "Sita Thapa", phone: "9841223344", credit_limit: 5000, current_debt: 0, loyalty_points: 120 },
  { id: "c3", name: "Kushal Shrestha", phone: "9801334455", credit_limit: 25000, current_debt: 14200, loyalty_points: 850 },
];

const SAMPLE_PRODUCTS: Product[] = [
  {
    id: "p1",
    sku: "WHT-FLOUR-5KG",
    name: "Shakti Wheat Flour 5kg",
    tax_rate: "13.00",
    product_type: "STANDARD",
    is_active: true,
    variants: [
      {
        id: "v1",
        sku: "WHT-FLOUR-5KG-DEF",
        barcode: "8901234567890",
        attributes_json: {},
        cost_price: "410.00",
        selling_price: "475.00",
        reorder_level: "10.00",
        is_active: true,
      },
    ],
    created_at: new Date().toISOString(),
  },
  {
    id: "p2",
    sku: "BASMATI-RICE-25KG",
    name: "Himalayan Basmati Rice 25kg",
    tax_rate: "13.00",
    product_type: "STANDARD",
    is_active: true,
    variants: [
      {
        id: "v2",
        sku: "BASMATI-RICE-25KG-DEF",
        barcode: "8909876543210",
        attributes_json: {},
        cost_price: "2400.00",
        selling_price: "2850.00",
        reorder_level: "5.00",
        is_active: true,
      },
    ],
    created_at: new Date().toISOString(),
  },
  {
    id: "p3",
    sku: "MUSTARD-OIL-1L",
    name: "Dhara Pure Mustard Oil 1L",
    tax_rate: "13.00",
    product_type: "STANDARD",
    is_active: true,
    variants: [
      {
        id: "v3",
        sku: "MUSTARD-OIL-1L-DEF",
        barcode: "8901122334455",
        attributes_json: {},
        cost_price: "210.00",
        selling_price: "245.00",
        reorder_level: "20.00",
        is_active: true,
      },
    ],
    created_at: new Date().toISOString(),
  },
  {
    id: "p4",
    sku: "WAI-WAI-NOODLE",
    name: "Wai Wai Quick Chicken 75g",
    tax_rate: "13.00",
    product_type: "STANDARD",
    is_active: true,
    variants: [
      {
        id: "v4",
        sku: "WAI-WAI-NOODLE-DEF",
        barcode: "8905544332211",
        attributes_json: {},
        cost_price: "20.00",
        selling_price: "25.00",
        reorder_level: "50.00",
        is_active: true,
      },
    ],
    created_at: new Date().toISOString(),
  },
  {
    id: "p5",
    sku: "MILK-FULL-CREAM",
    name: "DDC Pasteurised Milk 500ml",
    tax_rate: "0.00",
    product_type: "STANDARD",
    is_active: true,
    variants: [
      {
        id: "v5",
        sku: "MILK-FULL-CREAM-DEF",
        barcode: "8906677889900",
        attributes_json: {},
        cost_price: "42.00",
        selling_price: "50.00",
        reorder_level: "30.00",
        is_active: true,
      },
    ],
    created_at: new Date().toISOString(),
  },
];

interface HeldCart {
  id: string;
  timestamp: string;
  customerName?: string;
  items: any[];
  total: number;
  note: string;
}

export function App() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [isSyncing, setIsSyncing] = useState(false);
  const [pendingSyncCount, setPendingSyncCount] = useState(0);
  const [conflictCount, setConflictCount] = useState(0);
  const [conflictModalOpen, setConflictModalOpen] = useState(false);
  const [conflictsList, setConflictsList] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState("");

  const triggerSync = async () => {
    if (!navigator.onLine) return;
    setIsSyncing(true);
    try {
      await syncEngine.processQueue(async (payload) => {
        return apiClient.checkout(payload);
      });
      const count = await syncEngine.getPendingCount();
      setPendingSyncCount(count);
      const confCount = await localDb.sync_conflicts.count();
      setConflictCount(confCount);
    } catch (e) {
      console.error("Queue sync error:", e);
    } finally {
      setIsSyncing(false);
    }
  };

  const openConflictInspector = async () => {
    const list = await localDb.sync_conflicts.toArray();
    setConflictsList(list);
    setConflictModalOpen(true);
  };

  // Cashier Shift State
  const [activeShift, setActiveShift] = useState<{ id: string; openedAt: string; openingCash: number } | null>({
    id: "shift-001",
    openedAt: "10:00 AM",
    openingCash: 2000,
  });
  const [openShiftModal, setOpenShiftModal] = useState(false);
  const [closeShiftModal, setCloseShiftModal] = useState(false);
  const [closingCashInput, setClosingCashInput] = useState("");
  const [shiftDiscrepancy, setShiftDiscrepancy] = useState<number | null>(null);

  // Customer Khata Selection State
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerProfile | null>(null);
  const [customerModalOpen, setCustomerModalOpen] = useState(false);
  const [customerSearch, setCustomerSearch] = useState("");

  // Held Carts State
  const [heldCarts, setHeldCarts] = useState<HeldCart[]>([]);
  const [heldDrawerOpen, setHeldDrawerOpen] = useState(false);

  // Checkout & Receipt Modal State
  const [checkoutModalOpen, setCheckoutModalOpen] = useState(false);
  const [tenderMethod, setTenderMethod] = useState<"CASH" | "ESEWA" | "KHALTI" | "FONEPAY" | "CREDIT">("CASH");
  const [receiptModalOpen, setReceiptModalOpen] = useState(false);
  const [lastSaleReceipt, setLastSaleReceipt] = useState<any>(null);
  const [receiptWidth, setReceiptWidth] = useState<58 | 80>(80);

  const cart = useCartStore();

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      triggerSync();
    };
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    const checkPending = async () => {
      const count = await syncEngine.getPendingCount();
      setPendingSyncCount(count);
      const confCount = await localDb.sync_conflicts.count();
      setConflictCount(confCount);
    };
    checkPending();
    const interval = setInterval(checkPending, 5000);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
      clearInterval(interval);
    };
  }, []);

  const filteredProducts = SAMPLE_PRODUCTS.filter(
    (p) =>
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.sku.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.variants.some((v) => v.barcode.includes(searchQuery))
  );

  const filteredCustomers = SAMPLE_CUSTOMERS.filter(
    (c) =>
      c.name.toLowerCase().includes(customerSearch.toLowerCase()) ||
      c.phone.includes(customerSearch)
  );

  // Hold current cart
  const handleHoldCart = () => {
    if (cart.items.length === 0) return;
    const newHeld: HeldCart = {
      id: `hold-${Date.now()}`,
      timestamp: new Date().toLocaleTimeString(),
      customerName: selectedCustomer ? selectedCustomer.name : "Walk-in Customer",
      items: [...cart.items],
      total: cart.getTotal(),
      note: "Paused by cashier",
    };
    setHeldCarts((prev) => [newHeld, ...prev]);
    cart.clearCart();
    setSelectedCustomer(null);
  };

  // Resume held cart
  const handleResumeCart = (held: HeldCart) => {
    cart.clearCart();
    held.items.forEach((item) => {
      const prod = SAMPLE_PRODUCTS.find((p) => p.variants.some((v) => v.id === item.variant_id)) || SAMPLE_PRODUCTS[0];
      const variant = prod.variants.find((v) => v.id === item.variant_id) || prod.variants[0];
      for (let i = 0; i < item.quantity; i++) {
        cart.addItem(prod, variant);
      }
    });
    setHeldCarts((prev) => prev.filter((h) => h.id !== held.id));
    setHeldDrawerOpen(false);
  };

  // Perform Checkout & Generate Thermal Receipt
  const handleCheckout = async () => {
    const totalAmount = cart.getTotal();

    // Check Khata credit limit
    if (tenderMethod === "CREDIT") {
      if (!selectedCustomer) {
        alert("Please select a registered customer for Khata credit billing.");
        return;
      }
      const availableCredit = selectedCustomer.credit_limit - selectedCustomer.current_debt;
      if (totalAmount > availableCredit) {
        alert(
          `Credit limit exceeded! Available credit: Rs. ${availableCredit.toLocaleString()}, bill total: Rs. ${totalAmount.toLocaleString()}`
        );
        return;
      }
    }

    const invoiceNum = `INV-KTM-${Date.now().toString().slice(-6)}`;
    const payload: CheckoutPayload = {
      client_transaction_id: `tx-${Date.now()}-${crypto.randomUUID().slice(0, 8)}`,
      branch_id: "branch-hq-01",
      customer_id: selectedCustomer ? selectedCustomer.id : null,
      currency: "NPR",
      items: cart.items.map((i) => ({
        variant_id: i.variant_id,
        quantity: i.quantity,
        unit_price: i.unit_price,
        discount: i.discount,
      })),
      payments: [
        {
          method: tenderMethod,
          amount: totalAmount,
          provider_reference: tenderMethod !== "CASH" && tenderMethod !== "CREDIT" ? `REF-${Date.now()}` : "",
        },
      ],
    };

    // Save offline-first to Dexie IndexedDB
    await syncEngine.enqueueCheckout("org-default-01", "branch-hq-01", "term-01", payload);

    if (navigator.onLine) {
      triggerSync();
    }

    // Prepare Thermal Receipt Object
    setLastSaleReceipt({
      invoiceNumber: invoiceNum,
      date: new Date().toLocaleString(),
      customer: selectedCustomer,
      items: [...cart.items],
      subtotal: cart.getSubtotal(),
      tax: cart.getTaxTotal(),
      total: totalAmount,
      tenderMethod,
    });

    setCheckoutModalOpen(false);
    cart.clearCart();
    setSelectedCustomer(null);
    setReceiptModalOpen(true);

    const count = await syncEngine.getPendingCount();
    setPendingSyncCount(count);
  };

  // Cashier Shift Closure Reconciliation
  const handleCloseShift = () => {
    const closingVal = parseFloat(closingCashInput) || 0;
    const expected = (activeShift?.openingCash || 0) + 14850; // Mock sales
    const diff = closingVal - expected;
    setShiftDiscrepancy(diff);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-900 text-slate-100 font-sans">
      {/* Left side: Product Catalog & Barcode Scanner */}
      <div className="flex flex-col flex-1 border-r border-slate-800">
        {/* Top App Header */}
        <header className="flex items-center justify-between px-6 py-4 bg-slate-950 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-600 rounded-lg">
              <Store className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">NextGen POS Terminal</h1>
              <p className="text-xs text-slate-400">Terminal #01 · Kathmandu Main Branch</p>
            </div>
          </div>

          {/* Shift & Sync Status */}
          <div className="flex items-center gap-3">
            {activeShift ? (
              <button
                onClick={() => setCloseShiftModal(true)}
                className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-xs font-semibold text-emerald-400"
              >
                <Unlock className="w-3.5 h-3.5" />
                <span>Shift Active (Rs. {activeShift.openingCash})</span>
              </button>
            ) : (
              <button
                onClick={() => setOpenShiftModal(true)}
                className="flex items-center gap-2 px-3 py-1.5 bg-amber-950/80 hover:bg-amber-900 border border-amber-700 rounded-xl text-xs font-semibold text-amber-300 animate-pulse"
              >
                <Lock className="w-3.5 h-3.5" />
                <span>Open Shift Required</span>
              </button>
            )}

            {/* Held Sales Button */}
            <button
              onClick={() => setHeldDrawerOpen(true)}
              className="relative flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-xs font-semibold text-slate-200"
            >
              <PauseCircle className="w-3.5 h-3.5 text-amber-400" />
              <span>Held Carts</span>
              {heldCarts.length > 0 && (
                <span className="w-4 h-4 rounded-full bg-amber-500 text-slate-950 text-[10px] font-bold flex items-center justify-center">
                  {heldCarts.length}
                </span>
              )}
            </button>

            {/* Online / Offline Sync Status Badge */}
            <div
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold ${
                isOnline
                  ? "bg-emerald-950/80 text-emerald-400 border border-emerald-800"
                  : "bg-amber-950/80 text-amber-400 border border-amber-800 animate-pulse"
              }`}
            >
              {isOnline ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
              {isOnline ? "Online Cloud Sync" : "Offline (Dexie Queue)"}
            </div>

            {pendingSyncCount > 0 && (
              <button
                onClick={triggerSync}
                disabled={isSyncing || !isOnline}
                title="Click to manually push pending sales to Django API"
                className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-950 hover:bg-blue-900 text-blue-400 border border-blue-800 rounded-full text-xs font-medium transition cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? "animate-spin" : ""}`} />
                <span>{pendingSyncCount} pending upload (Sync Now)</span>
              </button>
            )}

            {conflictCount > 0 && (
              <button
                onClick={openConflictInspector}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-red-950 hover:bg-red-900 text-red-300 border border-red-800 rounded-full text-xs font-semibold animate-pulse transition"
              >
                <AlertCircle className="w-3.5 h-3.5 text-red-400" />
                <span>{conflictCount} Sync Conflicts</span>
              </button>
            )}
          </div>
        </header>

        {/* Search & Barcode Bar */}
        <div className="p-4 bg-slate-900 border-b border-slate-800">
          <div className="relative">
            <Search className="absolute left-3.5 top-3 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Scan barcode or search product name / SKU (e.g. 890123... or Rice)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-sm placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* Product Cards Grid */}
        <div className="flex-1 overflow-y-auto p-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {filteredProducts.map((prod) => {
            const v = prod.variants[0];
            return (
              <button
                key={prod.id}
                onClick={() => cart.addItem(prod, v)}
                className="flex flex-col text-left justify-between p-4 bg-slate-950 hover:bg-slate-800/80 active:scale-[0.98] transition border border-slate-800 rounded-xl group"
              >
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-blue-400">
                    {prod.sku}
                  </span>
                  <h3 className="font-semibold text-sm line-clamp-2 mt-1 text-slate-100 group-hover:text-blue-300">
                    {prod.name}
                  </h3>
                </div>
                <div className="mt-4 flex items-center justify-between">
                  <span className="text-base font-bold text-white">
                    Rs. {parseFloat(v.selling_price).toLocaleString()}
                  </span>
                  <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    VAT {prod.tax_rate}%
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Right side: Shopping Cart & Tender Panel */}
      <div className="w-96 flex flex-col bg-slate-950 border-l border-slate-800">
        {/* Customer Khata Bar */}
        <div className="px-5 py-3 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between">
          {selectedCustomer ? (
            <div className="flex-1 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-1.5">
                  <UserCheck className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-bold text-slate-200">{selectedCustomer.name}</span>
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  Khata Debt: <b className="text-rose-400">Rs. {selectedCustomer.current_debt.toLocaleString()}</b> · Pts: <b className="text-amber-400">{selectedCustomer.loyalty_points}</b>
                </div>
              </div>
              <button
                onClick={() => setSelectedCustomer(null)}
                className="text-[11px] text-slate-400 hover:text-white"
              >
                Change
              </button>
            </div>
          ) : (
            <button
              onClick={() => setCustomerModalOpen(true)}
              className="w-full flex items-center justify-center gap-2 py-1.5 px-3 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs font-semibold text-slate-300 transition"
            >
              <UserCheck className="w-3.5 h-3.5 text-blue-400" />
              <span>Select Customer / Khata Account</span>
            </button>
          )}
        </div>

        {/* Cart Header */}
        <div className="px-5 py-3 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShoppingCart className="w-5 h-5 text-blue-400" />
            <h2 className="font-bold text-sm">Cart Items ({cart.items.length})</h2>
          </div>
          <div className="flex items-center gap-2">
            {cart.items.length > 0 && (
              <>
                <button
                  onClick={handleHoldCart}
                  title="Pause current cart"
                  className="p-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-amber-400 text-xs font-semibold flex items-center gap-1"
                >
                  <PauseCircle className="w-3.5 h-3.5" />
                  <span>Hold</span>
                </button>
                <button
                  onClick={() => cart.clearCart()}
                  className="text-xs text-rose-400 hover:text-rose-300 font-medium"
                >
                  Clear
                </button>
              </>
            )}
          </div>
        </div>

        {/* Cart Items List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {cart.items.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-500 text-center p-6">
              <ShoppingCart className="w-12 h-12 stroke-[1.5] mb-2 opacity-50" />
              <p className="text-sm font-medium">Cart is empty</p>
              <p className="text-xs mt-1">Tap a product or scan a barcode to begin billing</p>
            </div>
          ) : (
            cart.items.map((item) => (
              <div
                key={item.variant_id}
                className="p-3 bg-slate-900 border border-slate-800/80 rounded-xl flex items-center justify-between"
              >
                <div className="flex-1 pr-2">
                  <h4 className="text-xs font-semibold text-slate-200 line-clamp-1">{item.name}</h4>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    Rs. {item.unit_price} × {item.quantity}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <div className="flex items-center bg-slate-950 border border-slate-700 rounded-lg">
                    <button
                      onClick={() => cart.updateQuantity(item.variant_id, item.quantity - 1)}
                      className="p-1 hover:text-blue-400"
                    >
                      <Minus className="w-3.5 h-3.5" />
                    </button>
                    <span className="w-6 text-center text-xs font-bold">{item.quantity}</span>
                    <button
                      onClick={() => cart.updateQuantity(item.variant_id, item.quantity + 1)}
                      className="p-1 hover:text-blue-400"
                    >
                      <Plus className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <button
                    onClick={() => cart.removeItem(item.variant_id)}
                    className="p-1.5 text-slate-500 hover:text-rose-400"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Billing Calculations */}
        <div className="p-4 bg-slate-900/60 border-t border-slate-800 space-y-2 text-sm">
          <div className="flex justify-between text-slate-400">
            <span>Subtotal</span>
            <span>Rs. {cart.getSubtotal().toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>VAT (Nepal 13%)</span>
            <span>Rs. {cart.getTaxTotal().toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-base font-bold text-white pt-2 border-t border-slate-800">
            <span>Total Payable</span>
            <span className="text-emerald-400 font-mono text-lg">
              Rs. {cart.getTotal().toFixed(2)}
            </span>
          </div>

          <button
            disabled={cart.items.length === 0}
            onClick={() => setCheckoutModalOpen(true)}
            className="w-full mt-3 py-3 px-4 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold rounded-xl text-center shadow-lg transition"
          >
            Pay Rs. {cart.getTotal().toFixed(2)}
          </button>
        </div>
      </div>

      {/* Customer Selector Modal */}
      {customerModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-2xl p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-white">Select Khata Customer</h3>
              <button onClick={() => setCustomerModalOpen(false)}>
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>
            <input
              type="text"
              placeholder="Search by customer phone or name..."
              value={customerSearch}
              onChange={(e) => setCustomerSearch(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-sm mb-4 focus:outline-none focus:border-blue-500"
            />
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {filteredCustomers.map((cust) => (
                <button
                  key={cust.id}
                  onClick={() => {
                    setSelectedCustomer(cust);
                    setCustomerModalOpen(false);
                  }}
                  className="w-full p-3 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-xl text-left flex items-center justify-between"
                >
                  <div>
                    <h4 className="font-semibold text-sm text-slate-100">{cust.name}</h4>
                    <span className="text-xs text-slate-400">{cust.phone}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-bold text-rose-400 block">
                      Debt: Rs. {cust.current_debt.toLocaleString()}
                    </span>
                    <span className="text-[10px] text-slate-400">
                      Limit: Rs. {cust.credit_limit.toLocaleString()}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Held Carts Drawer */}
      {heldDrawerOpen && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm">
          <div className="w-96 bg-slate-900 border-l border-slate-800 h-full p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
                <div className="flex items-center gap-2">
                  <PauseCircle className="w-5 h-5 text-amber-400" />
                  <h3 className="font-bold text-base">Suspended Carts</h3>
                </div>
                <button onClick={() => setHeldDrawerOpen(false)}>
                  <X className="w-5 h-5 text-slate-400" />
                </button>
              </div>

              {heldCarts.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-10">No suspended carts</p>
              ) : (
                <div className="space-y-3 overflow-y-auto max-h-[70vh]">
                  {heldCarts.map((h) => (
                    <div key={h.id} className="p-4 bg-slate-950 border border-slate-800 rounded-xl">
                      <div className="flex justify-between items-center text-xs text-slate-400 mb-1">
                        <span>{h.customerName}</span>
                        <span>{h.timestamp}</span>
                      </div>
                      <div className="text-base font-bold text-white mb-3">
                        Rs. {h.total.toFixed(2)} ({h.items.length} items)
                      </div>
                      <button
                        onClick={() => handleResumeCart(h)}
                        className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-xs font-bold text-white flex items-center justify-center gap-1.5"
                      >
                        <PlayCircle className="w-3.5 h-3.5" />
                        <span>Resume Cart</span>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <button
              onClick={() => setHeldDrawerOpen(false)}
              className="w-full py-2.5 bg-slate-800 text-slate-300 rounded-xl text-xs font-semibold"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Checkout Payment Tender Modal */}
      {checkoutModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-2xl p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-1">Select Payment Tender</h3>
            <p className="text-xs text-slate-400 mb-4">Total Due: Rs. {cart.getTotal().toFixed(2)}</p>

            <div className="grid grid-cols-2 gap-3 mb-6">
              {[
                { id: "CASH", label: "Cash", icon: Banknote, color: "text-emerald-400" },
                { id: "ESEWA", label: "eSewa Wallet", icon: Smartphone, color: "text-green-500" },
                { id: "KHALTI", label: "Khalti Wallet", icon: Smartphone, color: "text-purple-400" },
                { id: "FONEPAY", label: "Fonepay QR", icon: QrCode, color: "text-red-400" },
                { id: "CREDIT", label: "Khata Credit", icon: CreditCard, color: "text-amber-400" },
              ].map((m) => {
                const Icon = m.icon;
                const isSelected = tenderMethod === m.id;
                return (
                  <button
                    key={m.id}
                    onClick={() => setTenderMethod(m.id as any)}
                    className={`flex flex-col items-center justify-center p-3.5 rounded-xl border transition ${
                      isSelected
                        ? "bg-blue-950/80 border-blue-500 text-white"
                        : "bg-slate-950 border-slate-800 text-slate-300 hover:bg-slate-800"
                    }`}
                  >
                    <Icon className={`w-6 h-6 mb-1.5 ${m.color}`} />
                    <span className="text-xs font-semibold">{m.label}</span>
                  </button>
                );
              })}
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setCheckoutModalOpen(false)}
                className="flex-1 py-2.5 bg-slate-800 hover:bg-slate-700 rounded-xl text-sm font-semibold text-slate-300"
              >
                Cancel
              </button>
              <button
                onClick={handleCheckout}
                className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-sm font-bold text-white"
              >
                Complete Tender
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Printable Thermal Receipt Modal (58mm / 80mm ESC/POS) */}
      {receiptModalOpen && lastSaleReceipt && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-2xl p-6 shadow-2xl flex flex-col max-h-[90vh]">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
              <div className="flex items-center gap-2">
                <Printer className="w-5 h-5 text-blue-400" />
                <h3 className="font-bold text-sm">Thermal Receipt Preview</h3>
              </div>
              <div className="flex gap-2">
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
              </div>
            </div>

            {/* Simulated Paper Roll */}
            <div className="flex-1 overflow-y-auto bg-white text-black p-4 font-mono text-xs rounded-lg shadow-inner select-text">
              <div className="text-center font-bold text-sm">BIKASH SUPERMART</div>
              <div className="text-center text-[11px]">New Road, Kathmandu</div>
              <div className="text-center text-[11px]">PAN/VAT: 302918273</div>
              <div className="text-center font-bold text-[11px] my-1">TAX INVOICE</div>
              <div className="border-t border-dashed border-black my-1" />
              <div className="flex justify-between text-[11px]">
                <span>Bill: {lastSaleReceipt.invoiceNumber}</span>
                <span>{lastSaleReceipt.date.slice(0, 10)}</span>
              </div>
              <div className="text-[11px]">Tender: {lastSaleReceipt.tenderMethod}</div>
              {lastSaleReceipt.customer && (
                <div className="text-[11px]">Customer: {lastSaleReceipt.customer.name}</div>
              )}
              <div className="border-t border-dashed border-black my-1" />

              {/* Items */}
              {lastSaleReceipt.items.map((i: any, idx: number) => (
                <div key={idx} className="my-1">
                  <div className="font-semibold">{i.name}</div>
                  <div className="flex justify-between text-[11px] pl-2">
                    <span>
                      {i.quantity} x {i.unit_price}
                    </span>
                    <span>Rs. {i.subtotal.toFixed(2)}</span>
                  </div>
                </div>
              ))}

              <div className="border-t border-dashed border-black my-1" />
              <div className="flex justify-between">
                <span>Subtotal:</span>
                <span>Rs. {lastSaleReceipt.subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>VAT (13%):</span>
                <span>Rs. {lastSaleReceipt.tax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between font-bold text-sm border-t border-black pt-1 my-1">
                <span>TOTAL:</span>
                <span>Rs. {lastSaleReceipt.total.toFixed(2)}</span>
              </div>
              <div className="border-t border-dashed border-black my-1" />
              <div className="text-center text-[10px] mt-2">
                Thank You For Shopping With Us!
                <br />
                Goods once sold are non-refundable
              </div>
            </div>

            <div className="mt-4 flex gap-3">
              <button
                onClick={() => setReceiptModalOpen(false)}
                className="flex-1 py-2.5 bg-slate-800 text-slate-300 font-semibold rounded-xl text-xs"
              >
                Close
              </button>
              <button
                onClick={() => window.print()}
                className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl text-xs flex items-center justify-center gap-2"
              >
                <Printer className="w-4 h-4" />
                <span>Print Bill</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Cashier Shift Close Modal */}
      {closeShiftModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="w-full max-w-sm bg-slate-900 border border-slate-700 rounded-2xl p-6 shadow-2xl">
            <h3 className="text-base font-bold text-white mb-2">Close Cashier Shift</h3>
            <p className="text-xs text-slate-400 mb-4">
              Opening float: Rs. {activeShift?.openingCash} · Shift duration: 4 hrs
            </p>
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              Counted Cash in Drawer (NPR)
            </label>
            <input
              type="number"
              placeholder="e.g. 16850"
              value={closingCashInput}
              onChange={(e) => setClosingCashInput(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-sm mb-4 focus:outline-none focus:border-blue-500"
            />
            {shiftDiscrepancy !== null && (
              <div
                className={`p-3 rounded-xl mb-4 text-xs font-semibold ${
                  shiftDiscrepancy === 0
                    ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                    : "bg-rose-950 text-rose-400 border border-rose-800"
                }`}
              >
                {shiftDiscrepancy === 0
                  ? "Exact Match! Discrepancy: Rs. 0.00"
                  : `Discrepancy Detected: Rs. ${shiftDiscrepancy.toFixed(2)} (${
                      shiftDiscrepancy < 0 ? "Shortage" : "Surplus"
                    })`}
              </div>
            )}
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setCloseShiftModal(false);
                  setShiftDiscrepancy(null);
                }}
                className="flex-1 py-2.5 bg-slate-800 text-slate-300 rounded-xl text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleCloseShift}
                className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold"
              >
                Verify & Close
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Sync Conflicts Resolution Modal */}
      {conflictModalOpen && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-rose-400">
                <AlertCircle className="w-5 h-5" />
                <h3 className="font-bold text-sm text-white">Offline Sync Conflicts & Rejections</h3>
              </div>
              <button
                onClick={() => setConflictModalOpen(false)}
                className="p-1 text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-400">
              The following offline transactions could not be auto-reconciled with the central ERP server after multiple retries.
            </p>

            <div className="max-h-60 overflow-y-auto space-y-2">
              {conflictsList.length === 0 ? (
                <div className="p-4 bg-slate-950 rounded-xl text-center text-xs text-slate-500">
                  No active sync conflicts recorded.
                </div>
              ) : (
                conflictsList.map((c, i) => (
                  <div key={i} className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs space-y-1">
                    <div className="flex justify-between font-mono text-slate-300">
                      <span>Event: {c.event_id?.slice(0, 8)}...</span>
                      <span className="text-rose-400 font-bold">{c.status}</span>
                    </div>
                    <div className="text-slate-400">Error: {c.error_message || "Server rejected transaction"}</div>
                  </div>
                ))
              )}
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setConflictModalOpen(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
