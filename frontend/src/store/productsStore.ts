import { create } from 'zustand';

interface ProductsState {
  search: string;
  familyFilter: string | undefined;
  setSearch: (s: string) => void;
  setFamilyFilter: (f: string | undefined) => void;
}

export const useProductsStore = create<ProductsState>()((set) => ({
  search: '',
  familyFilter: undefined,
  setSearch: (search) => set({ search }),
  setFamilyFilter: (familyFilter) => set({ familyFilter }),
}));
