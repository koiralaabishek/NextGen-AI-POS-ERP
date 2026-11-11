import { create } from "zustand";
import type { CartItem, ProductVariant, Product } from "@nextgen/shared-types";

interface CartState {
  items: CartItem[];
  customerPhone: string;
  currency: string;
  addItem: (product: Product, variant: ProductVariant) => void;
  updateQuantity: (variantId: string, quantity: number) => void;
  removeItem: (variantId: string) => void;
  setCustomerPhone: (phone: string) => void;
  clearCart: () => void;
  getSubtotal: () => number;
  getTaxTotal: () => number;
  getTotal: () => number;
}

export const useCartStore = create<CartState>((set, get) => ({
  items: [],
  customerPhone: "",
  currency: "NPR",

  addItem: (product, variant) => {
    set((state) => {
      const existing = state.items.find((i) => i.variant_id === variant.id);
      const unitPrice = parseFloat(variant.selling_price) || 0;
      const taxRate = parseFloat(product.tax_rate) || 13;

      if (existing) {
        return {
          items: state.items.map((i) =>
            i.variant_id === variant.id
              ? {
                  ...i,
                  quantity: i.quantity + 1,
                  subtotal: (i.quantity + 1) * i.unit_price,
                }
              : i
          ),
        };
      }

      const newItem: CartItem = {
        variant_id: variant.id,
        sku: variant.sku,
        name: `${product.name} ${variant.sku !== product.sku ? `(${variant.sku})` : ""}`,
        quantity: 1,
        unit_price: unitPrice,
        discount: 0,
        tax_rate: taxRate,
        subtotal: unitPrice,
      };

      return { items: [...state.items, newItem] };
    });
  },

  updateQuantity: (variantId, quantity) => {
    if (quantity <= 0) {
      get().removeItem(variantId);
      return;
    }
    set((state) => ({
      items: state.items.map((i) =>
        i.variant_id === variantId
          ? { ...i, quantity, subtotal: quantity * i.unit_price - i.discount }
          : i
      ),
    }));
  },

  removeItem: (variantId) => {
    set((state) => ({
      items: state.items.filter((i) => i.variant_id !== variantId),
    }));
  },

  setCustomerPhone: (phone) => set({ customerPhone: phone }),
  clearCart: () => set({ items: [], customerPhone: "" }),

  getSubtotal: () => {
    return get().items.reduce((sum, item) => sum + item.quantity * item.unit_price - item.discount, 0);
  },

  getTaxTotal: () => {
    return get().items.reduce((sum, item) => {
      const taxable = item.quantity * item.unit_price - item.discount;
      return sum + taxable * (item.tax_rate / 100);
    }, 0);
  },

  getTotal: () => {
    return get().getSubtotal() + get().getTaxTotal();
  },
}));
